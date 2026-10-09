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


def strict(schema: dict) -> dict:
    """Every object closed, which is what codex requires and agy tolerates."""
    if not isinstance(schema, dict):
        return schema
    out = {k: strict(v) if isinstance(v, dict) else v for k, v in schema.items()}
    for k in SUBSCHEMA_LISTS:
        if isinstance(out.get(k), list):
            out[k] = [strict(s) for s in out[k]]
    kind = out.get("type")
    if kind == "object" or (isinstance(kind, list) and "object" in kind):
        out["additionalProperties"] = False
        out["properties"] = {k: strict(v) for k, v in (out.get("properties") or {}).items()}
    if isinstance(out.get("items"), dict):
        out["items"] = strict(out["items"])
    return out


# bool is a subclass of int in Python, so integer/number exclude it explicitly.
JSON_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "null": lambda v: v is None,
}


def conforms(engine: str, got, schema: dict) -> dict:
    """The answer has every required key, each property of its declared type.

    The engines are asked to honour the schema, not trusted to: a `"false"` where
    a boolean was asked for is truthy, and would read as a refutation.
    """
    if not isinstance(got, dict):
        raise EngineError(f"{engine} answered {type(got).__name__}, not an object: {got!r}"[:400])
    missing = [k for k in schema.get("required") or [] if k not in got]
    if missing:
        raise EngineError(f"{engine} answered without {missing}: {got!r}"[:400])
    for k, spec in (schema.get("properties") or {}).items():
        want = spec.get("type") if isinstance(spec, dict) else None
        if k not in got or want is None:
            continue
        kinds = want if isinstance(want, list) else [want]
        if not any(JSON_TYPES.get(w, lambda v: True)(got[k]) for w in kinds):
            raise EngineError(f"{engine} answered {k}={got[k]!r}, not {want}")
    return got


def run(engine: str, prompt: str, schema: dict) -> dict:
    """Ask `engine` for one object matching `schema`. Raises rather than guessing."""
    return conforms(engine, _ask(engine, prompt, schema), schema)


def _ask(engine: str, prompt: str, schema: dict):
    known = ENGINES.get("runs_on") or []
    if engine not in known:
        raise EngineError(f"{engine} is not one of {known}")

    with tempfile.TemporaryDirectory(prefix="quality-engine-") as tmp:
        d = pathlib.Path(tmp)
        s = d / "schema.json"
        s.write_text(json.dumps(strict(schema)), encoding="utf-8")
        if engine == "codex":
            out = d / "answer.json"
            argv = ["codex", "exec", "--output-schema", str(s), "-o", str(out),
                    "--sandbox", "read-only", "--skip-git-repo-check", prompt]
            r = _spawn(engine, argv)
            body = out.read_text(encoding="utf-8") if out.exists() else ""
            if not body.strip():
                raise EngineError(f"codex wrote no answer.\n{_tail(r)}")
            return _parse(engine, body, r)
        if engine == "claude":
            argv = ["claude", "-p", prompt, "--output-format", "json",
                    "--json-schema", json.dumps(strict(schema))]
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
        r = subprocess.run(argv, capture_output=True, text=True, timeout=TIMEOUT)
    except FileNotFoundError:
        raise EngineError(f"{engine} is not on PATH") from None
    except subprocess.TimeoutExpired:
        raise EngineError(f"{engine} did not answer within {TIMEOUT}s") from None
    except OSError as e:                     # not executable, argv too long, ...
        raise EngineError(f"{engine} could not be started: {e}") from None
    # A non-zero exit is not fatal here — an answer may still be on stdout — but
    # every error raised after it carries the code, via _tail and _parse.
    return r


def _parse(engine: str, body: str, r: subprocess.CompletedProcess) -> dict:
    stripped = body.strip()
    try:
        got = json.loads(stripped)
        if isinstance(got, dict):
            return got
    except ValueError:
        pass
    for line in reversed(stripped.splitlines()):
        try:
            got = json.loads(line)
        except ValueError:
            continue
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
