#!/usr/bin/env python3
"""engine.py, against fake engines: what it accepts, and every way it refuses.

No network and no real CLI: each test puts its own `claude` / `codex` / `agy`
on a PATH that holds nothing else, so a real engine on this machine can never
answer in a fake's place.

Run: make units
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True
import engine                                       # noqa: E402

OK = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}


def fake(bindir: Path, name: str, body: str, executable: bool = True) -> None:
    """A stand-in CLI. `argv` and `answer(obj)` are in scope for the body;
    for codex, `answer` writes the -o file the way codex does."""
    script = textwrap.dedent(f"""\
        #!{sys.executable}
        import json, sys, time
        argv = sys.argv[1:]
        def answer(obj):
            text = obj if isinstance(obj, str) else json.dumps(obj)
            if "-o" in argv:
                open(argv[argv.index("-o") + 1], "w", encoding="utf-8").write(text)
            else:
                print(text)
        """) + textwrap.dedent(body)
    path = bindir / name
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755 if executable else 0o644)


class Fakes(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.bin = Path(tmp.name)
        patcher = mock.patch.dict(os.environ, {"PATH": str(self.bin)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def refused(self, name: str, schema=OK) -> str:
        with self.assertRaises(engine.EngineError) as cm:
            engine.run(name, "p", schema)
        return str(cm.exception)


class Mismatch(unittest.TestCase):
    def bad(self, value, schema):
        self.assertIsNotNone(engine.mismatch(value, schema, "v"), (value, schema))

    def good(self, value, schema):
        self.assertIsNone(engine.mismatch(value, schema, "v"), (value, schema))

    def test_enum_and_const_do_not_equate_bool_with_int(self):
        self.bad(True, {"enum": [1]})
        self.bad(1, {"enum": [True]})
        self.bad(0, {"const": False})
        self.bad(False, {"const": 0})
        self.bad([True], {"const": [1]})
        self.good(1.0, {"enum": [1]})
        self.good(True, {"enum": [True, "x"]})
        self.good({"a": [1]}, {"const": {"a": [1.0]}})

    def test_types(self):
        self.good(1.0, {"type": "integer"})
        self.bad(1.5, {"type": "integer"})
        self.bad(True, {"type": "integer"})
        self.bad(True, {"type": "number"})
        self.bad("false", {"type": "boolean"})
        self.good(None, {"type": ["string", "null"]})

    def test_one_of_needs_exactly_one(self):
        self.bad(3, {"oneOf": [{"type": "integer"}, {"type": "number"}]})
        self.good("x", {"oneOf": [{"type": "integer"}, {"type": "string"}]})
        self.bad(None, {"oneOf": [{"type": "integer"}, {"type": "string"}]})

    def test_any_of_and_all_of(self):
        self.good(1, {"anyOf": [{"type": "string"}, {"type": "integer"}]})
        self.bad(1, {"allOf": [{"type": "integer"}, {"const": 2}]})

    def test_additional_properties_as_schema_and_false(self):
        s = {"type": "object", "properties": {"a": {}},
             "additionalProperties": {"type": "string"}}
        self.good({"a": 1, "b": "x"}, s)
        self.bad({"a": 1, "b": 2}, s)
        self.bad({"b": 1}, {"type": "object", "additionalProperties": False})

    def test_boolean_subschemas(self):
        self.good(1, True)
        self.bad(1, False)
        self.bad({"a": 1}, {"type": "object", "properties": {"a": False}})
        self.bad([1], {"type": "array", "items": False})

    def test_prefix_items(self):
        s = {"type": "array", "prefixItems": [{"type": "string"}], "items": {"type": "integer"}}
        self.good(["a", 1, 2], s)
        self.bad([1], s)
        self.bad(["a", "b"], s)

    def test_malformed_or_unchecked_schema_raises_engine_error(self):
        for schema in ({"anyOf": {"type": "string"}}, {"oneOf": "x"}, {"allOf": 3},
                       {"type": "object", "properties": ["a"]},
                       {"type": "object", "required": "a"},
                       {"enum": "ab"}, {"type": "strnig"}, {"minimum": 3},
                       {"type": "array", "items": [{"type": "string"}]}, "string"):
            with self.subTest(schema=schema), self.assertRaises(engine.EngineError):
                engine.mismatch({"a": 1} if isinstance(schema, dict) and
                                schema.get("type") == "object" else ["a"], schema, "v")

    def test_annotations_pass(self):
        self.good("x", {"type": "string", "description": "d", "default": "y", "title": "t"})

    def test_deep_answer_is_an_engine_error(self):
        s = {"type": "array"}
        s["items"] = s
        v = []
        for _ in range(sys.getrecursionlimit() * 2):
            v = [v]
        with self.assertRaises(engine.EngineError):
            engine.conforms("x", {"a": v}, {"type": "object", "properties": {"a": s}})

    def test_deep_json_is_an_engine_error(self):
        r = subprocess.CompletedProcess([], 0, "", "")
        with self.assertRaises(engine.EngineError):
            engine._parse("x", "[" * 200000 + "]" * 200000, r)


class Strict(unittest.TestCase):
    def test_closes_nested_objects_without_mutating(self):
        schema = {"type": "object", "required": ["a", "c", "d"], "properties": {
            "a": {"type": "object", "required": ["b"], "properties": {"b": {"type": "string"}}},
            "c": {"type": "array", "items": {"type": "object"}},
            "d": {"anyOf": [{"type": "object"}, {"type": "null"}]}}}
        before = copy.deepcopy(schema)
        out = engine.strict(schema)
        self.assertEqual(schema, before)
        self.assertIs(out["additionalProperties"], False)
        self.assertIs(out["properties"]["a"]["additionalProperties"], False)
        self.assertIs(out["properties"]["c"]["items"]["additionalProperties"], False)
        self.assertIs(out["properties"]["d"]["anyOf"][0]["additionalProperties"], False)
        self.assertNotIn("additionalProperties", out["properties"]["d"]["anyOf"][1])

    def test_values_are_not_schemas(self):
        val = {"type": "object", "properties": {}}
        schema = {"type": "object", "default": val, "const": val,
                  "examples": [val], "enum": [val]}
        out = engine.strict(schema)
        for k in ("default", "const"):
            self.assertEqual(out[k], val)
        self.assertEqual(out["examples"], [val])
        self.assertEqual(out["enum"], [val])

    def test_keeps_an_explicit_open_object(self):
        # The caller's call: claude and agy honour it. codex_ready is codex's.
        for rest in (True, {"type": "string"}):
            with self.subTest(additionalProperties=rest):
                out = engine.strict({"type": "object", "additionalProperties": rest})
                self.assertEqual(out["additionalProperties"], rest)

    def test_codex_ready_refuses_what_codex_cannot_take(self):
        for schema in (
            {"type": "object", "additionalProperties": True},
            {"type": "object", "additionalProperties": {"type": "string"}},
            {"type": "object", "properties": {"a": {"type": "string"}}},
            {"type": "object", "required": ["a"], "additionalProperties": False,
             "properties": {"a": {"type": "object", "additionalProperties": False,
                                  "properties": {"b": {"type": "string"}}}}},
        ):
            with self.subTest(schema=schema):
                with self.assertRaises(engine.EngineError):
                    engine.codex_ready(engine.strict(schema))

    def test_codex_ready_malformed_is_an_engine_error(self):
        for bad in ({"required": 1}, {"required": [["a"]]}, {"properties": ["a"]}):
            with self.subTest(bad=bad):
                with self.assertRaises(engine.EngineError):
                    engine.codex_ready({"type": "object", "additionalProperties": False, **bad})

    def test_well_formed_refuses_falsy_malformed_values(self):
        # Present but wrong is an error even when empty: never read as absent.
        for bad in ({"required": 0}, {"required": {}}, {"properties": []},
                    {"enum": {}}, {"anyOf": {}}, {"items": []}, {"type": ""},
                    {"type": []}, {"properties": {"a": 0}}, {"pattern": "x"}):
            with self.subTest(bad=bad):
                with self.assertRaises(engine.EngineError):
                    engine.well_formed({"type": "object", **bad})
                with self.assertRaises(engine.EngineError):
                    engine.codex_ready({"type": "object", "additionalProperties": False, **bad})

    def test_well_formed_accepts_the_shapes_in_use(self):
        engine.well_formed(OK)
        engine.well_formed({"type": "object", "required": [], "properties": {},
                            "additionalProperties": {"type": "string"},
                            "anyOf": [True, {"type": "null"}], "description": "x"})

    def test_codex_ready_accepts_required_and_nullable(self):
        engine.codex_ready(engine.strict({"type": "object", "required": ["a"],
                                          "properties": {"a": {"type": ["string", "null"]}}}))
        engine.codex_ready(engine.strict(OK))

    def test_keeps_an_explicit_false(self):
        out = engine.strict({"type": "object", "additionalProperties": False})
        self.assertIs(out["additionalProperties"], False)


class Run(Fakes):
    def test_each_engine_answers(self):
        fake(self.bin, "codex", 'answer({"ok": True})')
        fake(self.bin, "claude", 'answer({"structured_output": {"ok": True}})')
        fake(self.bin, "agy", 'answer({"status": "ok", "structured_output": {"ok": False}})')
        self.assertEqual(engine.run("codex", "p", OK), {"ok": True})
        self.assertEqual(engine.run("claude", "p", OK), {"ok": True})
        self.assertEqual(engine.run("agy", "p", OK), {"ok": False})

    def test_codex_without_an_answer(self):
        fake(self.bin, "codex", 'print("thinking")')
        self.assertIn("wrote no answer", self.refused("codex"))

    def test_null_structured_output(self):
        fake(self.bin, "claude", 'answer({"structured_output": None})')
        fake(self.bin, "agy", 'answer({"status": "error", "structured_output": None})')
        self.assertIn("no structured_output", self.refused("claude"))
        self.assertIn("no structured_output", self.refused("agy"))

    def test_missing_binary(self):
        self.assertIn("not on PATH", self.refused("claude"))

    def test_not_executable(self):
        fake(self.bin, "agy", 'answer({"structured_output": {"ok": True}})', executable=False)
        self.assertIn("could not be started", self.refused("agy"))

    def test_bad_utf8_is_decoded_not_fatal(self):
        fake(self.bin, "claude", r'''
            sys.stdout.buffer.write(b"\xff\xfe noise\n")
            sys.stdout.flush()
            answer({"structured_output": {"ok": True}})''')
        self.assertEqual(engine.run("claude", "p", OK), {"ok": True})
        fake(self.bin, "codex", r'''
            open(argv[argv.index("-o") + 1], "wb").write(b"\xff\xfe")''')
        self.assertIn("parses as an object", self.refused("codex"))

    def test_undeclared_key_is_refused(self):
        fake(self.bin, "codex", 'answer({"ok": True, "extra": 1})')
        self.assertIn("undeclared", self.refused("codex"))

    def test_wrong_type_is_refused(self):
        fake(self.bin, "claude", 'answer({"structured_output": {"ok": "false"}})')
        self.assertIn("is not boolean", self.refused("claude"))

    def test_timeout(self):
        fake(self.bin, "agy", "time.sleep(30)")
        with mock.patch.object(engine, "TIMEOUT", 1):
            self.assertIn("did not answer within", self.refused("agy"))

    def test_malformed_schema_is_refused_for_every_engine(self):
        fake(self.bin, "claude", 'answer({"structured_output": {"ok": True}})')
        with self.assertRaises(engine.EngineError):
            engine.run("claude", "p", {"type": "object", "required": 0,
                                        "properties": {"ok": {"type": "boolean"}}})

    def test_codex_only_constraints_bind_codex_only(self):
        optional = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
        fake(self.bin, "codex", 'answer({"ok": True})')
        fake(self.bin, "claude", 'answer({"structured_output": {"ok": True}})')
        with self.assertRaises(engine.EngineError):
            engine.run("codex", "p", optional)
        self.assertEqual(engine.run("claude", "p", optional), {"ok": True})

    def test_unknown_engine(self):
        self.assertIn("is not one of", self.refused("gpt"))

    def test_schema_sent_is_closed(self):
        fake(self.bin, "codex", '''
            s = json.load(open(argv[argv.index("--output-schema") + 1]))
            answer({"ok": s["additionalProperties"] is False})''')
        self.assertEqual(engine.run("codex", "p", OK), {"ok": True})


class Main(Fakes):
    def main(self, *argv) -> int:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["engine.py", *argv]), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = engine.main()
        self.output = out.getvalue() + err.getvalue()
        return rc

    def files(self):
        p, s = self.bin / "prompt.txt", self.bin / "schema.json"
        p.write_text("p", encoding="utf-8")
        s.write_text(json.dumps(OK), encoding="utf-8")
        return ["--prompt-file", str(p), "--schema", str(s)]

    def test_exit_codes(self):
        fake(self.bin, "codex", 'answer({"ok": True})')
        self.assertEqual(self.main(*self.files()), 2)            # no --running
        self.assertEqual(self.main("--running", "claude"), 2)    # no prompt/schema
        self.assertEqual(self.main("--running", "claude", *self.files()), 0)
        self.assertEqual(json.loads(self.output), {"ok": True})
        self.assertEqual(self.main("codex", "--running", "codex", *self.files()), 1)
        self.assertEqual(self.main("--running", "gpt", *self.files()), 1)
        self.assertEqual(self.main("agy", "--running", "claude", *self.files()), 1)

    def test_bad_input_files_are_usage_errors(self):
        fake(self.bin, "codex", 'answer({"ok": True})')
        args = self.files()
        (self.bin / "schema.json").write_text("{bad", encoding="utf-8")
        self.assertEqual(self.main("--running", "claude", *args), 2)    # not JSON
        missing = ["--prompt-file", str(self.bin / "nope.txt"), *args[2:]]
        self.assertEqual(self.main("--running", "claude", *missing), 2)  # no such file
        (self.bin / "schema.json").write_text("[1]", encoding="utf-8")
        self.assertEqual(self.main("--running", "claude", *args), 1)    # not an object

    def test_selftest_reports_and_does_not_fail(self):
        self.assertEqual(self.main("--selftest"), 0)
        self.assertIn("UNAVAILABLE", self.output)


if __name__ == "__main__":
    unittest.main(verbosity=1)
