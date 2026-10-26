#!/usr/bin/env python3
"""Run a checker on an engine that did not produce the work.

`routes.yaml` defers every loop route's `checker` to run time, because all three
CLIs read the same SKILL.md and any of them may be the one running. This resolves
it: given the engine that is running, it picks one that is not.

    make engines                     every declared engine answers, or says why
    python3 quality-tools/engine.py --selftest
    python3 quality-tools/engine.py --running claude --prompt-file p.txt --schema s.json

**The running engine is stated, never sniffed.** codex launched from inside
Claude Code inherits `CLAUDECODE` and `CLAUDE_CODE_*`, so a nested run reads as
its parent and any env heuristic silently mis-identifies it — which would hand
back a verdict from the very engine that was supposed to be excluded. `--running`
is required, and absent it this stops (exit 2); only `--selftest` runs without it.

**A checker that did not run is not a checker that passed.** Every failure path
here raises. Nothing returns a default verdict, nothing degrades to "assume
fine": an engine missing from PATH, an engine that starts and produces no
parseable object, a response that does not match the schema — each is an error
with the engine's own words attached, because the alternative is a green run
that verified nothing.

Engine quirks, re-checked by `make engines` rather than dated:

* `codex exec` rejects a schema without `additionalProperties: false`, at every
  level. Schemas are normalised here so callers write ordinary JSON Schema.
* `agy --print` returns an envelope; the validated object is `structured_output`.
* `claude -p` takes `--json-schema`; the validated object is `structured_output`
  in the JSON envelope, the same field name as agy.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "quality-registry" / "harness.yaml").read_text(encoding="utf-8"))
ENGINES = H.get("engines") or {}
TIMEOUT = 600


class EngineError(RuntimeError):
    """The engine did not answer. Never a verdict."""


# Keywords whose value is a list of subschemas. Left unwalked, an object under
# anyOf stays open and codex rejects the whole schema.
SUBSCHEMA_LISTS = ("anyOf", "oneOf", "allOf", "prefixItems")
# Keywords whose value is data, not a schema: a `default` that happens to look
# like an object schema must reach the engine as written.
VALUE_KEYWORDS = ("default", "const", "examples", "enum")


def strict(schema):
    """Every object closed unless it says otherwise. Returns a new schema.

    An object that leaves `additionalProperties` out is closed here, so an
    engine cannot add a key nobody asked for. One that sets it — `true`, or a
    schema for the extra keys — is kept as written: that is the caller's call,
    and claude and agy honour it. codex does not; `codex_ready` says so.
    """
    if not isinstance(schema, dict):
        return copy.deepcopy(schema)
    out = {}
    for k, v in schema.items():
        if k in VALUE_KEYWORDS:
            out[k] = copy.deepcopy(v)
        elif k == "properties" and isinstance(v, dict):
            out[k] = {name: strict(spec) for name, spec in v.items()}
        elif k in SUBSCHEMA_LISTS and isinstance(v, list):
            out[k] = [strict(s) for s in v]
        elif isinstance(v, dict):
            out[k] = strict(v)
        else:
            out[k] = copy.deepcopy(v)
    if _is_object(out):
        out.setdefault("additionalProperties", False)
        out.setdefault("properties", {})
    return out


def codex_ready(schema, where: str = "schema") -> None:
    """Raise unless codex can take `schema`; the other engines are not bound by it.

    codex answers through OpenAI structured outputs, which require every object
    closed and every property listed in `required` — an optional field is a
    required one that also admits null. Sent anyway, the request fails inside
    codex with no verdict; refused here, it says why.
    """
    well_formed(schema, where)              # a direct caller gets the same refusal run() gives
    if not isinstance(schema, dict):
        return                              # true or false: nothing for codex to object to
    if _is_object(schema):
        if schema.get("additionalProperties", False) is not False:
            raise EngineError(f"{where} admits undeclared keys (additionalProperties: "
                              f"{schema['additionalProperties']!r}); codex requires every "
                              "object closed")
        optional = sorted(set(schema.get("properties", {})) - set(schema.get("required", [])))
        if optional:
            raise EngineError(f"{where} properties {optional} are not in `required`; codex "
                              "requires every property listed — make an optional one "
                              "required and nullable")
    for k, v in schema.items():
        if k in VALUE_KEYWORDS:
            continue
        if k == "properties" and isinstance(v, dict):
            for name, spec in v.items():
                codex_ready(spec, f"{where}.{name}")
        elif k in SUBSCHEMA_LISTS and isinstance(v, list):
            for i, s in enumerate(v):
                codex_ready(s, f"{where}.{k}[{i}]")
        elif isinstance(v, dict):
            codex_ready(v, f"{where}.{k}")


def _is_object(schema: dict) -> bool:
    kind = schema.get("type")
    if kind is None:
        return "properties" in schema       # describes an object's keys: closed like one
    return kind == "object" or (isinstance(kind, list) and "object" in kind)


def _closes(schema) -> bool:
    """The value here must be an object, and strict() will close it.

    Only `type: "object"` forces an object: a nullable or typeless schema also
    admits values its object keywords never apply to, so a key conflict there
    leaves the schema satisfiable. Refusing less is the safe side — a schema
    this misses still fails closed, after the engine answers.
    """
    return (isinstance(schema, dict) and schema.get("type") in ("object", ["object"])
            and schema.get("additionalProperties", False) is False)


# bool is a subclass of int in Python, so integer/number exclude it explicitly.
# An integer is a value, not a spelling: JSON Schema counts 1.0 as one.
JSON_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: (isinstance(v, int) and not isinstance(v, bool))
                         or (isinstance(v, float) and v.is_integer()),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}

# Checked by mismatch(). Annotations change nothing about validity and pass;
# any other keyword does, so meeting one is an error rather than a silent pass.
CHECKED = {"type", "enum", "const", "required", "properties", "additionalProperties",
           "items", "prefixItems", "anyOf", "oneOf", "allOf"}
ANNOTATIONS = {"title", "description", "default", "examples", "$schema", "$id",
               "$comment", "format", "deprecated", "readOnly", "writeOnly"}
# The meta-schema's shape for each annotation; `default` may be anything. With
# these, every keyword well_formed() admits has its shape checked.
ANNOTATION_SHAPES = {"title": str, "description": str, "$comment": str, "format": str,
                     "$schema": str, "$id": str, "examples": list,
                     "deprecated": bool, "readOnly": bool, "writeOnly": bool}


def well_formed(schema, where: str = "schema") -> None:
    """Raise unless every keyword in `schema` has the shape it must have.

    Run once, before anything reads the schema, so that nothing downstream
    meets a malformed keyword half-way through: a value present but of the
    wrong kind — `required: 0`, `properties: []` — is an error even when it
    is empty or falsy, never read as if it were absent.
    """
    if isinstance(schema, bool):
        return
    if not isinstance(schema, dict):
        raise EngineError(f"{where} is {type(schema).__name__}, not a schema")
    unknown = sorted(set(schema) - CHECKED - ANNOTATIONS)
    if unknown:
        raise EngineError(f"{where} uses {unknown}, which this does not check")
    for key, shape in ANNOTATION_SHAPES.items():
        if key in schema and not isinstance(schema[key], shape):
            raise EngineError(f"{where}: {key} must be a {shape.__name__}, not {schema[key]!r}")
    if "type" in schema:
        kinds = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if (not kinds or len(set(map(repr, kinds))) != len(kinds)
                or not all(isinstance(k, str) and k in JSON_TYPES for k in kinds)):
            raise EngineError(f"{where}: type {schema['type']!r} is not a JSON type or a list of them")
    # An empty enum admits no value at all, so no engine could ever answer it.
    if "enum" in schema and not (isinstance(schema["enum"], list) and schema["enum"]):
        raise EngineError(f"{where}: enum must be a non-empty list, not {schema['enum']!r}")
    if "required" in schema and not (isinstance(schema["required"], list)
                                     and all(isinstance(r, str) for r in schema["required"])
                                     and len(set(schema["required"])) == len(schema["required"])):
        raise EngineError(f"{where}: required must be a list of distinct names, "
                          f"not {schema['required']!r}")
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise EngineError(f"{where}: properties must be an object, not {schema['properties']!r}")
        for name, spec in schema["properties"].items():
            well_formed(spec, f"{where}.{name}")
    if "additionalProperties" in schema:
        well_formed(schema["additionalProperties"], f"{where}.additionalProperties")
    if "items" in schema:
        if isinstance(schema["items"], list):
            raise EngineError(f"{where}: items as a list is the old tuple form; use prefixItems")
        well_formed(schema["items"], f"{where}.items")
    for key in SUBSCHEMA_LISTS:
        if key in schema:
            # JSON Schema requires these non-empty; read empty, anyOf and oneOf
            # would constrain nothing instead of being refused.
            if not (isinstance(schema[key], list) and schema[key]):
                raise EngineError(f"{where}: {key} must be a non-empty list, not {schema[key]!r}")
            for i, sub in enumerate(schema[key]):
                well_formed(sub, f"{where}.{key}[{i}]")
    if _closes(schema):
        undeclared = sorted(set(schema.get("required", [])) - set(schema.get("properties", {})))
        if undeclared:
            raise EngineError(f"{where}: required {undeclared} not in properties; closed, "
                              "the object admits no answer")
    _satisfiable(schema, where)


def _keys(s) -> tuple[set, set]:
    """(declared, required) keys of a subschema; a non-dict declares nothing."""
    if not isinstance(s, dict):
        return set(), set()
    return set(s.get("properties", {})), set(s.get("required", []))


def _satisfiable(schema: dict, where: str) -> None:
    """Refuse a composition no answer could match once strict() closes its objects.

    Closing is not the conflict; a key some part requires that a closed part
    does not declare is. Under allOf every part holds at once, so each closed
    part must declare every required key. Under anyOf/oneOf one branch must be
    usable: closed, it declares what the parent and allOf require; and what it
    requires, a closed parent declares.
    """
    declared, required = _keys(schema)
    parts = [b for b in schema.get("allOf", []) if isinstance(b, dict)]
    for b in parts:
        required |= _keys(b)[1]
    for s, at in [(schema, where)] + [(b, f"{where}.allOf[{i}]") for i, b in enumerate(parts)]:
        if _closes(s) and not required <= _keys(s)[0]:
            raise EngineError(f"{at}: required {sorted(required - _keys(s)[0])} is not declared "
                              "in this closed object, so no answer can match; declare it there "
                              "or set its additionalProperties")
    for key in ("anyOf", "oneOf"):
        branches = schema.get(key)
        if not branches:
            continue
        usable = [b for b in branches
                  if not (_closes(b) and not required <= _keys(b)[0])
                  and not (_closes(schema) and not _keys(b)[1] <= declared)]
        if not usable:
            raise EngineError(f"{where}: no {key} branch can match once objects are closed — "
                              "each requires a key a closed object beside it does not declare")


def conforms(engine: str, got, schema: dict) -> dict:
    """The answer matches the schema, nested objects and arrays included.

    The engines are asked to honour the schema, not trusted to: a `"false"` where
    a boolean was asked for is truthy, and would read as a refutation.
    """
    if not isinstance(got, dict):
        raise EngineError(f"{engine} answered {type(got).__name__}, not an object: {got!r}"[:400])
    try:
        well_formed(schema)
        problem = mismatch(got, schema, "answer")
    except RecursionError:
        raise EngineError(f"{engine} answered an object, or was held to a schema, "
                          "nested too deeply to check") from None
    if problem:
        raise EngineError(f"{engine}: {problem}"[:400])
    return got


def same(a, b) -> bool:
    """JSON equality: 1 equals 1.0, and true is not 1 (Python says it is)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def _subschemas(schema: dict, key: str, where: str) -> list:
    subs = schema.get(key)
    if subs is None:
        return []
    if not isinstance(subs, list):
        raise EngineError(f"schema at {where}: {key} is {type(subs).__name__}, not a list")
    return subs


def mismatch(value, schema, where: str) -> str | None:
    """The first way `value` breaks `schema`, or None.

    Checks type (integer accepts 1.0, never a boolean), enum and const (JSON
    equality, so true is not 1), required, properties, additionalProperties
    (false or a schema), items and prefixItems, anyOf, allOf, oneOf (exactly
    one branch), and true/false as whole schemas. Annotations such as
    description and default are ignored. Any other keyword, or one of these
    malformed, raises EngineError: a schema this cannot check is not checked.
    """
    if schema is True:
        return None
    if schema is False:
        return f"{where}={value!r} is not allowed here (schema false)"
    if not isinstance(schema, dict):
        raise EngineError(f"schema at {where} is {type(schema).__name__}, not a schema")
    unknown = sorted(set(schema) - CHECKED - ANNOTATIONS)
    if unknown:
        raise EngineError(f"schema at {where} uses {unknown}, which this does not check")

    want = schema.get("type")
    if want is not None:
        kinds = want if isinstance(want, list) else [want]
        for w in kinds:
            if w not in JSON_TYPES:
                raise EngineError(f"schema at {where}: unknown type {w!r}")
        if not any(JSON_TYPES[w](value) for w in kinds):
            return f"{where}={value!r} is not {want}"
    if "enum" in schema:
        if not isinstance(schema["enum"], list):
            raise EngineError(f"schema at {where}: enum is not a list")
        if not any(same(value, e) for e in schema["enum"]):
            return f"{where}={value!r} is not one of {schema['enum']}"
    if "const" in schema and not same(value, schema["const"]):
        return f"{where}={value!r} is not {schema['const']!r}"

    for sub in _subschemas(schema, "allOf", where):
        if (problem := mismatch(value, sub, where)):
            return problem
    any_of = _subschemas(schema, "anyOf", where)
    if any_of and all(mismatch(value, s, where) for s in any_of):
        return f"{where}={value!r} matches none of its anyOf"
    one_of = _subschemas(schema, "oneOf", where)
    if one_of:
        hits = sum(1 for s in one_of if not mismatch(value, s, where))
        if hits != 1:
            return f"{where}={value!r} matches {hits} of its oneOf, not exactly one"

    if isinstance(value, dict):
        required = schema.get("required", [])
        if not isinstance(required, list):
            raise EngineError(f"schema at {where}: required is not a list")
        missing = [k for k in required if k not in value]
        if missing:
            return f"{where} is missing {missing}"
        props = schema.get("properties", {})
        if not isinstance(props, dict):
            raise EngineError(f"schema at {where}: properties is not an object")
        for k, spec in props.items():
            if k in value and (problem := mismatch(value[k], spec, f"{where}.{k}")):
                return problem
        rest = schema.get("additionalProperties", True)
        extra = sorted(set(value) - set(props))
        if rest is False and extra:
            return f"{where} carries undeclared {extra}"
        if rest is not True:
            for k in extra:
                if (problem := mismatch(value[k], rest, f"{where}.{k}")):
                    return problem

    if isinstance(value, list):
        prefix = _subschemas(schema, "prefixItems", where)
        for i, (item, spec) in enumerate(zip(value, prefix)):
            if (problem := mismatch(item, spec, f"{where}[{i}]")):
                return problem
        items = schema.get("items", True)
        if isinstance(items, list):
            raise EngineError(f"schema at {where}: items as a list is the old tuple "
                              "form; use prefixItems")
        for i, item in enumerate(value[len(prefix):], len(prefix)):
            if (problem := mismatch(item, items, f"{where}[{i}]")):
                return problem
    return None


def run(engine: str, prompt: str, schema: dict) -> dict:
    """Ask `engine` for one object matching `schema`. Raises rather than guessing.

    The answer is held to the schema that was sent — closed objects included —
    not to the caller's open one, or an undeclared key the engine was told it
    could not add would pass.
    """
    if not isinstance(schema, dict):
        raise EngineError(f"the schema must be an object, not {type(schema).__name__}")
    if "type" in schema and not _is_object(schema):
        raise EngineError(f"the schema's root type is {schema['type']!r}; every engine "
                          "answers an object, so no answer could match")
    try:
        well_formed(schema)
        sent = strict(schema)
        if engine == "codex":
            codex_ready(sent)
    except RecursionError:
        raise EngineError("the schema is nested too deeply to check") from None
    return conforms(engine, _ask(engine, prompt, sent), sent)


def _ask(engine: str, prompt: str, schema: dict):
    known = ENGINES.get("runs_on") or []
    if engine not in known:
        raise EngineError(f"{engine} is not one of {known}")

    with tempfile.TemporaryDirectory(prefix="quality-engine-") as tmp:
        d = pathlib.Path(tmp)
        s = d / "schema.json"
        s.write_text(json.dumps(schema), encoding="utf-8")
        # `--` goes last, just before the prompt: a prompt that opens with a dash
        # (front matter, a list item) is otherwise parsed as an unknown option,
        # and options placed after `--` would be read as the prompt instead.
        if engine == "codex":
            out = d / "answer.json"
            argv = ["codex", "exec", "--output-schema", str(s), "-o", str(out),
                    "--sandbox", "read-only", "--skip-git-repo-check", "--", prompt]
            r = _spawn(engine, argv)
            body = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
            if not body.strip():
                raise EngineError(f"codex wrote no answer.\n{_tail(r)}")
            return _parse(engine, body, r)
        if engine == "claude":
            argv = ["claude", "-p", "--output-format", "json",
                    "--json-schema", json.dumps(schema), "--", prompt]
            r = _spawn(engine, argv)
            envelope = _parse(engine, r.stdout, r)
            body = envelope.get("structured_output")
            if not isinstance(body, dict):
                raise EngineError(f"claude returned no structured_output.\n{_tail(r)}")
            return body
        if engine == "agy":
            argv = ["agy", f"--print={prompt}", "--output-format", "json",
                    "--json-schema", str(s)]
            r = _spawn(engine, argv)
            envelope = _parse(engine, r.stdout, r)
            if envelope.get("structured_output") is None:
                raise EngineError(f"agy returned no structured_output "
                                  f"(status {envelope.get('status')!r}).\n{_tail(r)}")
            return envelope["structured_output"]
    raise EngineError(f"no invocation is known for {engine}")


def _spawn(engine: str, argv: list[str]) -> subprocess.CompletedProcess:
    try:
        # One engine printing bad UTF-8 must not take down a run that asked
        # several: decoded leniently, it fails as an unparseable answer instead.
        # stdin is closed: an engine reads a piped stdin as more prompt, so the
        # caller's input would reach it unasked, or an open pipe would hold it.
        p = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, encoding="utf-8",
                             errors="replace")
    except FileNotFoundError:
        raise EngineError(f"{engine} is not on PATH") from None
    except OSError as e:                     # not executable, argv too long, ...
        raise EngineError(f"{engine} could not be started: {e}") from None
    except ValueError as e:                  # a NUL in the prompt: argv cannot carry it
        raise EngineError(f"{engine} could not be started: {e}") from None
    try:
        out, err = p.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        _kill_tree(p)
        raise EngineError(f"{engine} did not answer within {TIMEOUT}s") from None
    except BaseException:                    # ^C to the caller alone: subprocess.run
        _kill_tree(p)                        # killed the engine here, and so must this
        raise
    # A non-zero exit is not fatal here — an answer may still be on stdout — but
    # every error raised after it carries the code, via _tail and _parse.
    return subprocess.CompletedProcess(argv, p.returncode, out, err)


def _kill_tree(p: subprocess.Popen) -> None:
    """The engine and what it started. A launcher killed alone leaves its worker
    running, and billing, after the run has given up on it. The engine stays in
    the caller's process group, so whatever stops the caller stops it too; the
    tree is read from /proc where there is one, and elsewhere only the engine is
    killed, as before."""
    pids = [p.pid]
    try:
        children: dict[int, list[int]] = {}
        for stat in pathlib.Path("/proc").glob("[0-9]*/stat"):
            try:
                ppid = int(stat.read_text().rsplit(")", 1)[1].split()[1])
            except (OSError, IndexError, ValueError):
                continue                     # exited while being read
            children.setdefault(ppid, []).append(int(stat.parent.name))
        for pid in pids:                     # grows as it goes: breadth first
            pids.extend(children.get(pid, []))
    except OSError:
        pass
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        p.communicate(timeout=5)
    except subprocess.TimeoutExpired:        # held open by something that escaped
        p.stdout.close()
        p.stderr.close()
        p.wait()


def _loads(text: str):
    """The parsed value, or None. Nesting deep enough to exhaust the stack is
    just another answer that does not parse."""
    try:
        return json.loads(text, parse_constant=_not_json, parse_float=_finite)
    except (ValueError, RecursionError):
        return None


def _not_json(name: str):
    raise ValueError(f"{name} is not JSON")


def _finite(text: str) -> float:
    f = float(text)
    if f != f or f in (float("inf"), float("-inf")):
        raise ValueError(f"{text} does not fit a double")
    return f


def _parse(engine: str, body: str, r: subprocess.CompletedProcess) -> dict:
    stripped = body.strip()
    for candidate in [stripped, *reversed(stripped.splitlines())]:
        got = _loads(candidate)
        if isinstance(got, dict):
            return got
    raise EngineError(f"{engine} printed nothing that parses as an object:\n{body[:400]}"
                      f"\n{_tail(r)}")


def _tail(r: subprocess.CompletedProcess) -> str:
    tail = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-6:])
    return f"[exit {r.returncode}] {tail}" if r.returncode else tail


def other_than(running: str) -> str:
    """An engine that is not the one running. Raises rather than falling back."""
    known = ENGINES.get("runs_on") or []
    if running not in known:
        raise EngineError(f"the running engine {running!r} is not one of {known}; "
                          "state it correctly rather than letting this guess")
    for candidate in known:
        if candidate != running:
            return candidate
    raise EngineError(f"{known} leaves nothing to check {running} with")


SELFTEST = {"type": "object", "properties": {"ok": {"type": "boolean"}},
            "required": ["ok"]}


def selftest() -> int:
    """Ask each declared engine for one object. Reachability, not correctness."""
    bad = 0
    for engine in ENGINES.get("runs_on") or []:
        try:
            got = run(engine, "Reply with ok=true and nothing else.", SELFTEST)
        except EngineError as e:
            print(f"  {engine}: UNAVAILABLE — {e}")
            bad += 1
            continue
        print(f"  {engine}: answered {got}")
    known = ENGINES.get("runs_on") or []
    print(f"engines reachable: {len(known) - bad}/{len(known)} of {known}   "
          f"any of them may be the one running")
    # Unreachable is reported, never fatal: a machine without one of these still
    # runs every other check, and a hook that fails on a missing CLI gets removed.
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", nargs="?", help="the checker; omit to resolve from --running")
    ap.add_argument("--running", help="the engine running this harness — required, never guessed")
    ap.add_argument("--prompt-file")
    ap.add_argument("--schema")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.running:
        # Stated, never sniffed: with no --running there is nothing to exclude.
        print("need --running <engine> (or --selftest)", file=sys.stderr)
        return 2
    if not (a.prompt_file and a.schema):
        print("need --prompt-file and --schema", file=sys.stderr)
        return 2
    try:
        prompt = pathlib.Path(a.prompt_file).read_text(encoding="utf-8")
        schema = json.loads(pathlib.Path(a.schema).read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as e:
        # Bad input is a usage error with a message, never a traceback.
        print(f"cannot read the prompt or schema: {e}", file=sys.stderr)
        return 2
    try:
        # Resolved even when a checker is named: other_than() refuses an unknown
        # --running, and a misspelt one would otherwise exclude nothing.
        fallback = other_than(a.running)
        engine = a.engine or fallback
        if engine == a.running:
            raise EngineError(f"{engine} is the engine running this; "
                              "a verdict from it is not a check")
        got = run(engine, prompt, schema)
    except EngineError as e:
        print(f"{a.engine or 'checker'}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(got, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    # The answer prints after the engine has been paid for; a non-UTF-8 console
    # must not turn it, or --selftest's report, into a UnicodeEncodeError.
    sys.stdout.reconfigure(errors="replace")
    sys.exit(main())
