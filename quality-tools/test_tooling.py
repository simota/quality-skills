#!/usr/bin/env python3
"""The plumbing around the checks: the hook, the Makefile and CI.

Each git test builds a throwaway repo with its own config, so nothing here
reads or writes the user's git settings or this checkout's hooks.

Run: make units
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "quality-tools" / "githooks" / "pre-commit"
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
GIT_ENV.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")


class Repo(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.d = self.tmp / "repo"
        self.d.mkdir()
        self.git("init", "-q")

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.d, env=GIT_ENV, check=check,
                              capture_output=True, text=True, timeout=60)


class HookExport(Repo):
    """The hook checks exactly the tree the commit will hold."""

    def setUp(self):
        super().setUp()
        (self.d / "a").write_text("a\n")
        (self.d / "sub").mkdir()
        (self.d / "sub" / "b").write_text("b\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.seen = self.tmp / "seen"
        # The check is replaced by a listing of what it would have been given.
        text = HOOK.read_text(encoding="utf-8")
        line = re.search(r'^make -s -C "(\$tmp[^"]*)" check$', text, re.M)
        self.assertIsNotNone(line, "the hook no longer ends in make check")
        listing = (f'(cd "{line.group(1)}" && find . -type f | sort | '
                   f'while read -r f; do echo "$f:$(cat "$f")"; done) > "{self.seen}"')
        hook = self.d / ".git" / "hooks" / "pre-commit"
        hook.parent.mkdir(exist_ok=True)
        hook.write_text(text.replace(line.group(0), listing), encoding="utf-8")
        hook.chmod(0o755)

    def commit(self) -> list[str]:
        (self.d / "a").write_text("a2\n")
        self.git("add", "a")
        self.git("commit", "-qm", "x")
        return self.seen.read_text().split()

    def test_sparse_checkout_exports_every_file(self):
        self.git("sparse-checkout", "set", "--no-cone", "/a")
        self.assertFalse((self.d / "sub" / "b").exists())
        self.assertIn("./sub/b:b", self.commit())

    def test_intent_to_add_is_not_exported(self):
        (self.d / "c").write_text("c\n")
        self.git("add", "-N", "c")
        self.assertNotIn("./c:", self.commit())

    def test_commit_paths_exports_the_commit(self):
        # `commit <paths>` commits a temporary index; a staged change outside
        # those paths is not in that commit and must not be checked as if it were.
        (self.d / "sub" / "b").write_text("b2\n")
        self.git("add", "sub/b")
        (self.d / "a").write_text("a3\n")
        self.git("commit", "-qm", "only a", "a")
        self.assertEqual(self.seen.read_text().split(), ["./a:a3", "./sub/b:b"])
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout.split(), ["sub/b"])


class MakeHooks(Repo):
    def setUp(self):
        super().setUp()
        shutil.copy(ROOT / "Makefile", self.d / "Makefile")
        (self.d / "quality-tools" / "githooks").mkdir(parents=True)
        shutil.copy(HOOK, self.d / "quality-tools" / "githooks" / "pre-commit")

    def make_hooks(self):
        return subprocess.run(["make", "-s", "hooks"], cwd=self.d, env=GIT_ENV,
                              capture_output=True, text=True, timeout=60)

    def test_foreign_hook_is_kept(self):
        shared = self.tmp / "shared"
        shared.mkdir()
        foreign = shared / "pre-commit"
        foreign.write_text("#!/bin/sh\necho another repo's hook\n")
        self.git("config", "core.hooksPath", str(shared))
        r = self.make_hooks()
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertEqual(foreign.read_text(), "#!/bin/sh\necho another repo's hook\n")

    def test_own_hook_is_reinstalled(self):
        self.assertEqual(self.make_hooks().returncode, 0)
        r = self.make_hooks()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("pre-merge-commit installed", r.stdout)


class MakeLink(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name) / "home with space"
        (self.home / ".claude").mkdir(parents=True)

    def make(self, *args):
        env = {**os.environ, "HOME": str(self.home)}
        return subprocess.run(["make", "-s", "-C", str(ROOT), *args], env=env,
                              capture_output=True, text=True, timeout=60)

    def test_home_with_a_space(self):
        r = self.make("link")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        skills = self.home / ".claude" / "skills"
        linked = sorted(p.name for p in skills.iterdir() if p.is_symlink())
        self.assertEqual(linked, sorted(p.parent.name for p in ROOT.glob("skills/quality-*/SKILL.md")))
        self.assertEqual(sorted(p.name for p in self.home.parent.iterdir()), ["home with space"])
        self.assertEqual(self.make("unlink").returncode, 0)
        self.assertEqual([p for p in skills.iterdir() if p.is_symlink()], [])

    def test_relative_host_is_refused(self):
        r = self.make("link", "CLAUDE_DIR=.claude/skills")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("relative", r.stdout)


class CiParity(unittest.TestCase):
    """The hook runs `make check`; CI spells the same commands out step by step."""

    def test_ci_runs_what_make_check_runs(self):
        mk = (ROOT / "Makefile").read_text(encoding="utf-8")
        targets = re.search(r"^check:(.*)$", mk, re.M).group(1).split()
        want = set()
        for t in targets:
            body = re.search(rf"^{t}:.*\n((?:\t.*\n)+)", mk, re.M).group(1)
            want |= {line.strip().lstrip("@") for line in body.splitlines()}
        ci = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
        got = {line.strip() for job in ci["jobs"].values() for step in job["steps"]
               for line in str(step.get("run", "")).splitlines()}
        self.assertEqual(sorted(want - got), [], "make check runs these; CI does not")


if __name__ == "__main__":
    unittest.main(verbosity=1)
