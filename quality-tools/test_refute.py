#!/usr/bin/env python3
"""refute.py's verdicts and exit codes, against fake engines.

The exit code is what a script reads, so each one is pinned here with and
without `--json`. Engines are stand-ins on a PATH holding nothing else: no
network, and no real CLI can answer in a fake's place.

Run: make units
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import refute                                       # noqa: E402

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


if __name__ == "__main__":
    unittest.main(verbosity=1)
