#!/usr/bin/env python3
"""refute.py's verdicts and exit codes, against fake engines.

The exit code is what a script reads, so each one is pinned here with and
without `--json`. Engines are stand-ins on a PATH holding nothing else: no
network, and no real CLI can answer in a fake's place.

Run: make units
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
try:
    import refute  # noqa: E402
except SystemExit:                  # it ran main() on import: no test below would run
    sys.exit("importing refute ran its main()")

CLAIM = [{"id": "c1", "claim": "the cache is invalidated on every write"}]


def vote(refuted) -> dict:
    return {"refuted": refuted, "reason": "r", "what_would_settle_it": "s"}


class Verdict(unittest.TestCase):
    def test_table(self):
        for votes, want in [
            ({}, "UNCHECKED"),
            ({"a": vote(True)}, "REFUTED"),
            ({"a": vote(True), "b": vote(True)}, "REFUTED"),
            ({"a": vote(False)}, "STANDS"),
            ({"a": vote(False), "b": vote(False)}, "STANDS"),
            ({"a": vote(True), "b": vote(False)}, "CONTESTED"),
            # Only a real boolean true refutes.
            ({"a": vote("true")}, "STANDS"),
            ({"a": vote(1)}, "STANDS"),
        ]:
            with self.subTest(votes=votes):
                self.assertEqual(refute.verdict(votes), want)


class Runs(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.bin = self.dir / "bin"
        self.bin.mkdir()

    def fake(self, name: str, refuted: bool) -> None:
        """An engine that answers every claim with one fixed vote."""
        obj = json.dumps(vote(refuted))
        script = textwrap.dedent(f"""\
            #!{sys.executable}
            import json, sys
            argv = sys.argv[1:]
            obj = {obj!r}
            if "-o" in argv:
                open(argv[argv.index("-o") + 1], "w").write(obj)
            else:
                print(json.dumps({{"structured_output": json.loads(obj)}}))
            """)
        (self.bin / name).write_text(script, encoding="utf-8")
        (self.bin / name).chmod(0o755)

    def run_refute(self, claims, *args, raw: str | None = None):
        path = self.dir / "claims.json"
        path.write_text(raw if raw is not None else json.dumps(claims), encoding="utf-8")
        env = {**os.environ, "PATH": str(self.bin)}
        return subprocess.run([sys.executable, str(HERE / "refute.py"), *args, str(path)],
                              capture_output=True, text=True, env=env, timeout=60)

    def codes(self, claims, *args, raw: str | None = None) -> tuple[int, int]:
        plain = self.run_refute(claims, *args, raw=raw)
        as_json = self.run_refute(claims, "--json", *args, raw=raw)
        self.assertNotIn("Traceback", plain.stderr + as_json.stderr)
        return plain.returncode, as_json.returncode

    def test_ascii_console_still_reports(self):
        # The text report carries non-ASCII; printing it must not cost the verdicts.
        self.fake("codex", True)
        path = self.dir / "claims.json"
        path.write_text(json.dumps(CLAIM), encoding="utf-8")
        env = {**os.environ, "PATH": str(self.bin), "PYTHONIOENCODING": "ascii"}
        r = subprocess.run([sys.executable, str(HERE / "refute.py"), "--running", "claude", str(path)],
                           capture_output=True, text=True, env=env, timeout=60)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_claims_checked_nothing(self):
        self.assertEqual(self.codes([], "--running", "claude"), (3, 3))

    def test_one_refuter_answers(self):
        self.fake("codex", True)                    # agy is absent
        self.assertEqual(self.codes(CLAIM, "--running", "claude"), (0, 0))
        out = json.loads(self.run_refute(CLAIM, "--json", "--running", "claude").stdout)
        self.assertEqual(out[0]["verdict"], "REFUTED")
        self.assertEqual(out[0]["independent_readings"], 1)
        self.assertIn("agy", out[0]["unreachable"])

    def test_single_object_is_one_claim(self):
        self.fake("codex", True)
        out = json.loads(self.run_refute(CLAIM[0], "--json", "--running", "claude").stdout)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["verdict"], "REFUTED")

    def test_split_is_contested(self):
        self.fake("codex", True)
        self.fake("agy", False)
        out = json.loads(self.run_refute(CLAIM, "--json", "--running", "claude").stdout)
        self.assertEqual(out[0]["verdict"], "CONTESTED")

    def test_running_engine_is_never_asked(self):
        self.fake("claude", False)                  # would vote STANDS if asked
        self.assertEqual(self.codes(CLAIM, "--running", "claude"), (3, 3))

    def test_no_refuter_answers(self):
        self.assertEqual(self.codes(CLAIM, "--running", "claude"), (3, 3))

    def test_unknown_running_engine(self):
        self.assertEqual(self.codes(CLAIM, "--running", "gpt"), (1, 1))

    def test_missing_running_is_usage(self):
        self.assertEqual(self.run_refute(CLAIM).returncode, 2)

    def test_malformed_claims(self):
        for claims, raw in [
            (None, "not json"),
            ({"id": "c1"}, None),                   # a single object still needs a claim
            ("a string", None),
            (["just a string"], None),
            ([{"id": "c1"}], None),
            ([{"id": "c1", "claim": 3}], None),
            ([{"id": "c1", "claim": "   "}], None),
        ]:
            with self.subTest(claims=claims, raw=raw):
                self.assertEqual(self.codes(claims, "--running", "claude", raw=raw), (2, 2))

    def test_missing_claims_file(self):
        env = {**os.environ, "PATH": str(self.bin)}
        r = subprocess.run([sys.executable, str(HERE / "refute.py"), "--running", "claude",
                            str(self.dir / "absent.json")],
                           capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_one_unchecked_claim_fails_the_run(self):
        """Exit 3 when ANY claim is UNCHECKED, not only when all are."""
        (self.bin / "codex").write_text(textwrap.dedent(f"""\
            #!{sys.executable}
            import json, sys
            argv = sys.argv[1:]
            if "SECOND" in argv[-1]:
                sys.exit(1)                      # no answer for this claim
            open(argv[argv.index("-o") + 1], "w").write(json.dumps(
                {{"refuted": True, "reason": "r", "what_would_settle_it": "s"}}))
            """), encoding="utf-8")
        (self.bin / "codex").chmod(0o755)
        claims = [CLAIM[0], {"id": "c2", "claim": "SECOND claim"}]
        self.assertEqual(self.codes(claims, "--running", "claude"), (3, 3))

    def test_a_claim_argv_cannot_carry_is_unchecked_not_a_crash(self):
        # A NUL is valid JSON but cannot reach an engine's argv. That claim goes
        # unchecked; the verdict already paid for on the one before it still prints.
        self.fake("codex", True)
        claims = [CLAIM[0], {"id": "c2", "claim": "pasted \u0000 bytes"}]
        self.assertEqual(self.codes(claims, "--running", "claude"), (3, 3))
        out = json.loads(self.run_refute(claims, "--json", "--running", "claude").stdout)
        self.assertEqual([r["verdict"] for r in out], ["REFUTED", "UNCHECKED"])

    def test_where_and_evidence_reach_the_refuter(self):
        seen = {}
        def fake_run(name, prompt, schema):
            seen["prompt"] = prompt
            return vote(False)
        with mock.patch.object(refute.engine, "run", fake_run):
            refute.ask("codex", {"id": "c", "claim": "x", "where": "src/a.py:10",
                                 "evidence": "test_a passes"})
        self.assertIn("where: src/a.py:10", seen["prompt"])
        self.assertIn("evidence offered: test_a passes", seen["prompt"])

    def test_no_lens_cannot_start(self):
        for lens in ({}, {"lens": "x"}, {"refuted_when": "y"}):
            with self.subTest(lens=lens), mock.patch.object(refute, "REFUTATION", lens), \
                    mock.patch.object(sys, "argv", ["refute.py", "--running", "claude", "c.json"]):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    self.assertEqual(refute.main(), 1)
                self.assertIn("no refutation lens", err.getvalue())

    def test_non_list_claims_is_usage(self):
        self.assertEqual(self.codes(None, "--running", "claude", raw="3"), (2, 2))

    def test_plain_report(self):
        self.fake("codex", True)
        r = self.run_refute([dict(CLAIM[0])], "--running", "claude")
        self.assertIn("[REFUTED] c1", r.stdout)
        self.assertIn("codex: refuted=True", r.stdout)
        self.assertIn("would settle it: s", r.stdout)
        self.assertIn("agy: NO VERDICT", r.stdout)
        self.assertIn("1 refuted · 0 contested · 0 unrefuted · 0 unchecked", r.stdout)
        self.assertIn("Unrefuted means nothing was found", r.stdout)

    def test_errors_say_why(self):
        r = self.run_refute(None, "--running", "claude", raw="not json")
        self.assertIn("refute:", r.stderr)
        r = self.run_refute(CLAIM, "--running", "gpt")
        self.assertIn("not one of", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
