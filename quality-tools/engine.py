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
import pathlib
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
    """Every object closed, which is what codex requires and agy tolerates.

    Returns a new schema; the caller's is not touched. An object that leaves
    `additionalProperties` out is closed here. One that opens it — `true`, or a
    schema for the extra keys — is refused: codex rejects any object that is not
    closed, and quietly closing it would change what the caller asked for.
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
    kind = out.get("type")
    if kind == "object" or (isinstance(kind, list) and "object" in kind):
        if out.get("additionalProperties", False) is not False:
            raise EngineError("an object schema admits undeclared keys "
                              f"(additionalProperties: {out['additionalProperties']!r}); "
                              "codex requires every object closed")
        out["additionalProperties"] = False
        out.setdefault("properties", {})
    return out


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


def conforms(engine: str, got, schema: dict) -> dict:
    """The answer matches the schema, nested objects and arrays included.

    The engines are asked to honour the schema, not trusted to: a `"false"` where
    a boolean was asked for is truthy, and would read as a refutation.
    """
    if not isinstance(got, dict):
        raise EngineError(f"{engine} answered {type(got).__name__}, not an object: {got!r}"[:400])
    try:
        problem = mismatch(got, schema, "answer")
    except RecursionError:
        raise EngineError(f"{engine} answered an object nested too deeply to check") from None
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
        required = schema.get("required") or []
        if not isinstance(required, list):
            raise EngineError(f"schema at {where}: required is not a list")
        missing = [k for k in required if k not in value]
        if missing:
            return f"{where} is missing {missing}"
        props = schema.get("properties") or {}
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
    sent = strict(schema)
    return conforms(engine, _ask(engine, prompt, sent), sent)


def _ask(engine: str, prompt: str, schema: dict):
    known = ENGINES.get("runs_on") or []
    if engine not in known:
        raise EngineError(f"{engine} is not one of {known}")

    with tempfile.TemporaryDirectory(prefix="quality-engine-") as tmp:
        d = pathlib.Path(tmp)
        s = d / "schema.json"
        s.write_text(json.dumps(schema), encoding="utf-8")
        if engine == "codex":
            out = d / "answer.json"
            argv = ["codex", "exec", "--output-schema", str(s), "-o", str(out),
                    "--sandbox", "read-only", "--skip-git-repo-check", prompt]
            r = _spawn(engine, argv)
            body = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
            if not body.strip():
                raise EngineError(f"codex wrote no answer.\n{_tail(r)}")
            return _parse(engine, body, r)
        if engine == "claude":
            argv = ["claude", "-p", prompt, "--output-format", "json",
                    "--json-schema", json.dumps(schema)]
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
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
    except FileNotFoundError:
        raise EngineError(f"{engine} is not on PATH") from None
    except subprocess.TimeoutExpired:
        raise EngineError(f"{engine} did not answer within {TIMEOUT}s") from None
    except OSError as e:                     # not executable, argv too long, ...
        raise EngineError(f"{engine} could not be started: {e}") from None
    # A non-zero exit is not fatal here — an answer may still be on stdout — but
    # every error raised after it carries the code, via _tail and _parse.
    return r


def _loads(text: str):
    """The parsed value, or None. Nesting deep enough to exhaust the stack is
    just another answer that does not parse."""
    try:
        return json.loads(text)
    except (ValueError, RecursionError):
        return None


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
        engine = a.engine or other_than(a.running)
        if a.running and engine == a.running:
            raise EngineError(f"{engine} is the engine running this; "
                              "a verdict from it is not a check")
        got = run(engine,
                  pathlib.Path(a.prompt_file).read_text(encoding="utf-8"),
                  json.loads(pathlib.Path(a.schema).read_text(encoding="utf-8")))
    except EngineError as e:
        print(f"{a.engine or 'checker'}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(got, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
