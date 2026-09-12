#!/usr/bin/env python3
"""Prove each rule in validate.py fires.

A check only ever seen passing may be checking nothing. Every rule below gets a
deliberate violation injected into a throwaway copy of the repo, and the test
fails if the validator stays quiet.

Run: make test
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True                     # no __pycache__ in the tools dir
import validate                                    # noqa: E402  — for RULES only


def run(root: Path) -> str:
    r = subprocess.run([sys.executable, str(root / "quality-tools" / "validate.py")],
                       capture_output=True, text=True)
    return r.stdout + r.stderr


S = "skills/"          # everything the CLI reads lives here


def sub(path: Path, old: str, new: str) -> None:
    t = path.read_text(encoding="utf-8")
    assert old in t, f"fixture text not found in {path.name}: {old[:60]!r}"
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


# Each case mutates a copy, then expects that rule id in the output.
CASES: dict[str, callable] = {}


def case(rule):
    def deco(fn):
        CASES[rule] = fn
        return fn
    return deco


@case("V1")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Owns", "## Owns\n" + "x\n" * 200)


@case("V2")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "Writing tests that can actually fail",
              "Not for quality-regression. Writing tests that can actually fail")


@case("V3")
def _(r): (r / f"{S}quality-ghost").mkdir(); (r / f"{S}quality-ghost/SKILL.md").write_text("x")


@case("V4")
def _(r): (r / f"{S}quality-test/playbooks/orphan.md").write_text("<!-- quality:guidance -->\n")


@case("V5")
def _(r): (r / f"{S}quality-test/playbooks/traps.md").write_text("y\n" * 400)


@case("V6")
def _(r): sub(r / f"{S}_quality/VALUES.md", "## 1. Honesty", "z\n" * 300 + "## 1. Honesty")


@case("V7")
def _(r): sub(r / "quality-registry/routes.yaml", "chain: [quality-regression, quality-test]",
              "chain: [quality-regression, quality-nonexistent]")


@case("V8")
def _(r): sub(r / "README.md", "](skills/_quality/CONTRACT.md)", "](skills/_quality/GONE.md)")


@case("V9")
def _(r): sub(r / "quality-registry/capabilities.yaml", "signals: [regression, bisection",
              "signals: [oracle, bisection")


@case("V10")
def _(r): sub(r / "quality-registry/fixtures.yaml",
              '- ask: "grade these findings and say what evidence each one has"\n  expect: quality-review',
              '- ask: "grade these findings and say what evidence each one has"\n  expect: quality-gate')


@case("V11")
def _(r):
    import shutil
    for i in range(4):
        d = r / f"{S}quality-extra{i}"
        d.mkdir()
        shutil.copy(r / f"{S}quality-test/SKILL.md", d / "SKILL.md")


@case("V12")
def _(r): (r / f"{S}rogue").mkdir(); (r / f"{S}rogue/SKILL.md").write_text("x")


@case("V13")
def _(r):
    t = (r / "quality-registry/routes.yaml").read_text(encoding="utf-8")
    t += "".join(f"\nfiller{i}:\n  pattern: linear\n  when: x\n  chain: [quality-test]\n"
                 for i in range(20))
    (r / "quality-registry/routes.yaml").write_text(t, encoding="utf-8")


@case("V14")
def _(r): sub(r / "quality-registry/routes.yaml", "  pattern: loop", "  pattern: spiral")


@case("V15")
def _(r): sub(r / f"{S}quality-review/SKILL.md", "allowed-tools: Read, Grep, Glob, Bash, Write",
              "allowed-tools: Read, Grep, Glob, Edit, Write, Bash")


@case("V16")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Finished when")


@case("V17")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "- **Report `status`**", "- **Mention status**")


@case("V18")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "coverage gap", "untested behaviour")


@case("V19")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "`_quality/CONTRACT.md`", "`../_quality/CONTRACT.md`")


@case("V19-shared")
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "`_quality/OPERATIONAL.md` §3", "`OPERATIONAL.md` §3")


@case("V20")
def _(r):
    """The definition row becomes a mention; the word is still on the page."""
    sub(r / f"{S}_quality/CONTRACT.md", "| `HYPOTHESIS` |", "| HYPOTHESIS |")


@case("V21")
def _(r): sub(r / f"{S}quality-test/SKILL.md",
              """`RED` is the evidence and it is not a formality (`E3`, or `E4` where the oracle
is a property, metamorphic relation, or mutation).""",
              "`RED` is the evidence and it is not a formality.")


@case("V22")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when",
              "## Done when\n\n#" + "TODO(agent): tidy this up later\n")


@case("V23")
def _(r): sub(r / f"{S}_quality/CONTRACT.md", "<!-- quality:contract -->", "<!-- quality:guidance -->")


@case("V24")
def _(r): sub(r / f"{S}_quality/ROUTING.md", "`quality-debt`", "`quality-rot`")


@case("V25")
def _(r): sub(r / f"{S}quality-test/playbooks/traps.md", "# ", "# pinned at v2.14.0 — ")


@case("V26")
def _(r): sub(r / "quality-registry/capabilities.yaml", "      go: quality-debt",
              "      go: quality-rot")


@case("V27")
def _(r):
    (r / f"{S}quality-test/_quality").unlink()
    (r / f"{S}quality-test/_quality").symlink_to("../_gone")


@case("V28")
def _(r): sub(r / "quality-registry/harness.yaml", "set: quality", "set: qa")


@case("V28-generic-dir")
def _(r): (r / "registry").mkdir()


@case("V29")
def _(r):
    f = r / f"{S}quality-test/reference/oracles.md"
    f.write_text(f.read_text(encoding="utf-8").replace("Verified:", "Checked:"), encoding="utf-8")


@case("V30")
def _(r): (r / f"{S}quality-test/reference/orphan.md").write_text(
    "<!-- quality:deferred -->\n# Orphan\n\nPurpose: x\nRead when: y\nVerified: 2026-08-21\n")


@case("V31")
def _(r):
    for f in sorted((r / f"{S}").glob("*/reference/*.md")):
        t = f.read_text()
        i = t.index("Verified:")
        j = t.index("\n\n", i)
        f.write_text(t[:i] + "Verified: 2026-08-21" + t[j:])
        return


@case("V32")
def _(r):
    sub(r / "quality-registry/routes.yaml", "checker: ", "checker: claude  # ")


@case("V32-unknown")
def _(r):
    sub(r / "quality-registry/routes.yaml", "checker: ", "checker: nosuchengine  # ")



@case("V32-single")
def _(r):
    sub(r / "quality-registry/harness.yaml",
        "runs_on: [claude, codex, agy]", "runs_on: [claude]")



@case("V33")
def _(r):
    sub(r / "quality-registry/harness.yaml", "  lens: |", "  lens: ''\n  unused: |")



@case("V34")
def _(r):
    """Reachable and runnable must move together, whichever way they are split."""
    for d in sorted((r / "skills").glob("quality-*")):
        link = d / "refute.py"
        if link.is_symlink():
            link.unlink()                      # runnable, and now out of reach
            return
    # No set-wide link to remove: make a skill runnable instead, and leave it
    # unreachable. Widening a class trips V15 too, which the harness allows —
    # it only asks that V34 appear.
    sub(r / "quality-registry/harness.yaml",
        "tools: \"Read, Grep, Glob, Write", "tools: \"Read, Grep, Glob, Bash, Write")


@case("V34-decoration")
def _(r):
    """A link where the class grants no shell reads like a capability and is not one."""
    import yaml as _y
    caps = _y.safe_load((r / "quality-registry/capabilities.yaml").read_text())
    cls = _y.safe_load((r / "quality-registry/harness.yaml").read_text())["permission_classes"]
    for name, e in caps.items():
        if "Bash" not in cls[e["class"]]["tools"]:
            (r / "skills" / name / "refute.py").symlink_to("../../quality-tools/refute.py")
            return
    for d in sorted((r / "skills").glob("quality-*")):
        link = d / "refute.py"
        if link.is_symlink():
            link.unlink()
            link.symlink_to("../../quality-tools/render.py")   # the set's own, but the wrong tool
            return


@case("V34-undeclared")
def _(r):
    """A tool link nothing declares is a capability nobody decided to grant."""
    (r / "skills/quality-test/render.py").symlink_to("../../quality-tools/render.py")


@case("V34-missing-tool")
def _(r): sub(r / "quality-registry/harness.yaml",
              "  refute.py: all", "  refute.py: all\n  nosuch.py: all")


@case("V34-none-declared")
def _(r): sub(r / "quality-registry/harness.yaml", "linked_tools:", "unlinked_tools:")


@case("V35")
def _(r): sub(r / f"{S}quality-regression/SKILL.md", "adjudicated the same way",
              "settled the same way")


@case("V36")
def _(r): (r / f"{S}quality-review/playbooks/visualise.md").unlink()


@case("V36-undefined")
def _(r):
    """A trigger the registry declares and the pages never define."""
    for g in (r / f"{S}quality-review/playbooks/visualise.md",
              r / f"{S}quality-review/reference/diagram-forms.md"):
        g.write_text(g.read_text(encoding="utf-8").replace("`ordering`", "sequencing"),
                     encoding="utf-8")


@case("V36-unreachable")
def _(r): sub(r / f"{S}quality-review/SKILL.md",
              "[visualise](playbooks/visualise.md)", "the visualise guidance")


@case("V36-none-declared")
def _(r): sub(r / "quality-registry/harness.yaml", "finding_visuals:", "unused_visuals:")


@case("V38")
def _(r): sub(r / f"{S}quality-review/playbooks/traps.md", "<!-- quality:guidance -->\n",
              "<!-- quality:guidance -->\nverdict: KEEP | DROP\n")


@case("V37")
def _(r):
    """A page that leans on a declared source and does not say so."""
    sub(r / f"{S}quality-debt/reference/interest.md",
        'Source: git — the touch-frequency counts come from its own commands.',
        "Source: none — nothing outside this page can move what it states.")


@case("V37-unused")
def _(r):
    """A source named in the header that the page never uses."""
    sub(r / f"{S}quality-test/reference/case-design.md",
        "Source: none — nothing outside this page can move what it states.",
        'Source: git — the touch-frequency counts come from its own commands.')


@case("V37-silent")
def _(r):
    """Neither a source nor the admission that there is none."""
    sub(r / f"{S}quality-test/reference/case-design.md",
        "Source: none — nothing outside this page can move what it states.", "Source:")


@case("V37-none-declared")
def _(r): sub(r / "quality-registry/harness.yaml", "source_authorities:", "unused_authorities:")


def main() -> int:
    baseline = run(ROOT)
    if "green" not in baseline:
        print("the working tree is already failing; fix that first:\n" + baseline)
        return 1

    bad: list[str] = []
    for rule, mutate in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            mutate(copy)
            out = run(copy)
            expect = rule.split("-")[0]
            if not re.search(rf"^\s*{expect}: ", out, re.M):
                bad.append(rule)
                print(f"  {rule} did not fire\n{out}")

    print(f"{len(CASES)} rules exercised, {len(bad)} silent")
    if bad:
        print("silent: " + ", ".join(bad))
        return 1

    # Counting the cases that exist says nothing about the rules that do. A rule
    # added without a case left this printing "every rule fires" about it.
    covered = {c.split("-")[0] for c in CASES}
    declared = {fn.__name__.split("_")[0].upper() for fn in validate.RULES}
    untested = sorted(declared - covered, key=lambda r: int(r[1:]))
    if untested:
        print("no deliberate violation is injected for: " + ", ".join(untested))
        return 1
    print(f"every rule fires ({len(declared)} rules, {len(CASES)} cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
