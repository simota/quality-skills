#!/usr/bin/env python3
"""render.py on a throwaway copy of the repo: all or nothing, and only where asked.

Each test copies the repo, renders the copy clean, then breaks it one way. A
run that cannot render every file must write none of them.

Run: make units
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "quality-registry" / "harness.yaml").read_text(encoding="utf-8"))
SKILLS = H.get("skills_dir") or "."


class Render(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"
        shutil.copytree(ROOT, self.root, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__"))
        r = self.render()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def render(self, *args) -> subprocess.CompletedProcess:
        r = subprocess.run([sys.executable, str(self.root / "quality-tools" / "render.py"), *args],
                           capture_output=True, text=True, timeout=60)
        self.assertNotIn("Traceback", r.stderr)
        return r

    def skill(self, name: str) -> Path:
        return self.root / SKILLS / name / "SKILL.md"

    def snapshot(self) -> dict[Path, bytes]:
        return {p: p.read_bytes() for p in (self.root / SKILLS).glob("*/SKILL.md")}

    def edit(self, name: str, old: str, new: str) -> None:
        p = self.skill(name)
        t = p.read_text(encoding="utf-8")
        self.assertIn(old, t)
        p.write_text(t.replace(old, new, 1), encoding="utf-8")

    def strip_block(self, name: str, key: str) -> None:
        p = self.skill(name)
        t = p.read_text(encoding="utf-8")
        head, rest = t.split(f"<!-- deliver:{key} -->\n", 1)
        _, tail = rest.split(f"<!-- /deliver:{key} -->\n", 1)
        p.write_text(head + tail, encoding="utf-8")

    def make_stale(self, name: str) -> None:
        self.edit(name, "<!-- deliver:values -->\n", "<!-- deliver:values -->\nstale line\n")

    def test_clean_check_and_idempotent(self):
        before = self.snapshot()
        self.assertEqual(self.render("--check").returncode, 0)
        r = self.render()
        self.assertEqual(r.returncode, 0)
        self.assertIn("0 changed", r.stdout)
        self.assertEqual(self.snapshot(), before)

    def test_stale_check_fails_and_writes_nothing(self):
        self.make_stale("quality-test")
        before = self.snapshot()
        r = self.render("--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("quality-test", r.stdout)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.render().returncode, 0)
        self.assertEqual(self.render("--check").returncode, 0)

    def test_bad_markers_change_nothing(self):
        self.edit("quality-test", "<!-- /deliver:values -->\n",
                  "<!-- /deliver:values -->\n<!-- deliver:values -->\n")
        before = self.snapshot()
        for args in ((), ("--check",)):
            r = self.render(*args)
            self.assertEqual(r.returncode, 1)
            self.assertIn("markers must appear once", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_missing_section_changes_nothing(self):
        self.strip_block("quality-test", "values")
        self.edit("quality-test", "## Decide first\n", "## Decide later\n")
        before = self.snapshot()
        r = self.render()
        self.assertEqual(r.returncode, 1)
        self.assertIn("no section 'Decide first'", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_stale_and_broken_writes_nothing(self):
        self.make_stale("quality-debt")
        self.edit("quality-test", "<!-- /deliver:values -->\n", "")
        before = self.snapshot()
        self.assertEqual(self.render().returncode, 1)
        self.assertEqual(self.snapshot(), before)

    def test_heading_is_a_whole_line(self):
        """`### Decide first` earlier in the file is not the section."""
        self.strip_block("quality-test", "values")
        self.edit("quality-test", "## Owns\n", "## Owns\n\n### Decide first\n\ndecoy\n")
        self.assertEqual(self.render().returncode, 0)
        t = self.skill("quality-test").read_text(encoding="utf-8")
        at = t.index("<!-- deliver:values -->")
        self.assertLess(t.index("### Decide first"), t.index("\n## Decide first\n"))
        self.assertLess(t.index("\n## Decide first\n"), at)
        self.assertLess(at, t.index("\n## Always / Never"))
        self.assertEqual(self.render("--check").returncode, 0)

    def test_missing_delivered_block(self):
        (self.root / "quality-registry" / "delivered" / "values.md").unlink()
        before = self.snapshot()
        r = self.render()
        self.assertEqual(r.returncode, 1)
        self.assertIn("values.md", r.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_no_skills_is_not_clean(self):
        for p in list(self.snapshot()):
            p.unlink()
        r = self.render("--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no ", r.stderr)

    def test_unknown_argument(self):
        before = self.snapshot()
        r = self.render("--chek")
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main(verbosity=1)
