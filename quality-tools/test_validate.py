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


def run(root: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(root / "quality-tools" / "validate.py")],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


S = "skills/"          # everything the CLI reads lives here


def sub(path: Path, old: str, new: str) -> None:
    t = path.read_text(encoding="utf-8")
    assert old in t, f"fixture text not found in {path.name}: {old[:60]!r}"
    path.write_text(t.replace(old, new, 1), encoding="utf-8")


# Each case mutates a copy, then expects that rule id in the output.
CASES: dict[str, callable] = {}
# Each quiet case mutates a copy in a way the rule must accept: a rule that
# fires on the legitimate case is as wrong as one that never fires.
QUIET: dict[str, callable] = {}


def case(rule):
    def deco(fn):
        CASES[rule] = fn
        return fn
    return deco


def quiet(rule):
    def deco(fn):
        QUIET[rule] = fn
        return fn
    return deco


@case("V1")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Owns", "## Owns\n" + "x\n" * 200)


@case("V2")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "Writing tests that can actually fail",
              "Not for quality-regression. Writing tests that can actually fail")


@case("V2-case")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "Writing tests that can actually fail",
              "NOT FOR audits. Writing tests that can actually fail")


@case("V2-name-case")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "Writing tests that can actually fail",
              "Quality-Regression aside. Writing tests that can actually fail")


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


@case("V10-empty")
def _(r): (r / "quality-registry/fixtures.yaml").write_text("[]\n", encoding="utf-8")


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


@case("V15-writes")
def _(r): sub(r / "quality-registry/harness.yaml", "    writes: true", "    writes: false")


@case("V15-multiedit")
def _(r): sub(r / "quality-registry/harness.yaml", "permission_classes:\n",
              "permission_classes:\n  nb:\n    tools: \"Read, NotebookEdit\"\n    writes: false\n")


@case("V15-list")
def _(r): sub(r / "quality-registry/harness.yaml", "permission_classes:\n",
              "permission_classes:\n  listed:\n    tools: [Read, MultiEdit]\n    writes: false\n")


@quiet("V15-list")
def _(r): sub(r / "quality-registry/harness.yaml",
              'tools: "Read, Grep, Glob, Bash, Write"', "tools: [Read, Grep, Glob, Bash, Write]")


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
              """`RED` is the evidence and it is not a formality (`E3`, or `E4` where the oracle's
expectation is traced to the spec, a property, or a prior version — never the code).""",
              "`RED` is the evidence and it is not a formality.")


@case("V22")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when",
              "## Done when\n\n#" + "TODO(agent): tidy this up later\n")


@case("V23")
def _(r): sub(r / f"{S}_quality/CONTRACT.md", "<!-- quality:contract -->", "<!-- quality:guidance -->")


@case("V24")
def _(r): sub(r / f"{S}_quality/ROUTING.md", "`quality-debt`", "`quality-rot`")


@case("V24-hyphenated")
def _(r): sub(r / f"{S}_quality/ROUTING.md", "`quality-debt`",
              "`quality-debt` (once `quality-tech-debt`)")


@case("V23-undeclared")
def _(r): sub(r / "quality-registry/harness.yaml", "document_labels: [contract, guidance, deferred]",
              "document_labels: [contract, deferred]")


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


@quiet("V24-owned-dirs")
def _(r): sub(r / "README.md", "holds every\nthreshold;",
              "holds every\nthreshold (`quality-registry`, read by `quality-tools`);")


@case("V39-none-declared")
def _(r): sub(r / "quality-registry/harness.yaml", "  route_stages_max:", "  unused_stages_max:")


@case("V39")
def _(r): sub(r / "quality-registry/routes.yaml", "chain: [quality-review, quality-test, quality-gate]",
              "chain: [quality-review, quality-test, quality-review, quality-test, "
              "quality-review, quality-test, quality-gate]")


# --- added by review: each fails on the unpatched validator --------------------

@case("V17-duplicate")
def _(r):
    """A second, divergent copy after the real one; only the first was compared."""
    t = (r / f"{S}quality-test/SKILL.md").read_text(encoding="utf-8")
    i = t.index("## Done when\n") + len("## Done when\n")
    j = t.index("<!-- deliver:surface -->")
    (r / f"{S}quality-test/SKILL.md").write_text(
        t[:i] + "<!-- deliver:report -->\n- E0 may ship\n<!-- /deliver:report -->\n" + t[j:], encoding="utf-8")


@case("V17-misplaced")
def _(r):
    t = (r / f"{S}quality-test/SKILL.md").read_text(encoding="utf-8")
    blk = re.search(r"<!-- deliver:values -->.*?<!-- /deliver:values -->\n", t, re.S).group(0)
    t = t.replace(blk, "").replace("## Verify with", blk + "## Verify with", 1)
    (r / f"{S}quality-test/SKILL.md").write_text(t, encoding="utf-8")


@case("V19-link")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "[traps](playbooks/traps.md)",
              "[traps](playbooks/traps.md), [contract](../_quality/CONTRACT.md)")


@case("V19-reference")
def _(r): sub(r / f"{S}quality-test/reference/test-smells.md", "`reference/oracles.md`", "`oracles.md`")


@case("V19-shared-probe")
def _(r): sub(r / f"{S}_quality/VALUES.md", "## 1. Honesty", "## 1. Honesty (`reference/repayment.md`)")


@case("V20-second-cell")
def _(r):
    sub(r / f"{S}_quality/CONTRACT.md", "| `HYPOTHESIS` |", "| HYPOTHESIS | `HYPOTHESIS` |")


@case("V21-token")
def _(r): sub(r / f"{S}quality-test/SKILL.md",
              """`RED` is the evidence and it is not a formality (`E3`, or `E4` where the oracle's
expectation is traced to the spec, a property, or a prior version — never the code).""",
              "`RED` is the evidence; run the E2E suite as well.")


@case("V22-codespan")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when",
              "## Done when\n\n#" + "TODO(agent): tidy `parse()` up later\n")


@case("V25-semver")
def _(r): sub(r / f"{S}quality-test/playbooks/traps.md", "# ", "# pytest 8.3.2 — ")


@case("V25-skill")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Owns\n", "## Owns (as of v2.14)\n")


@case("V29-read-when")
def _(r):
    """Each header is required on its own, not only the one the V29 case renames."""
    f = r / f"{S}quality-test/reference/oracles.md"
    f.write_text(f.read_text(encoding="utf-8").replace("\nRead when:", "\nRead if:", 1), encoding="utf-8")


@case("V29-window")
def _(r):
    """Headers pushed below the first twelve lines are headers nobody reads first."""
    f = r / f"{S}quality-test/reference/oracles.md"
    f.write_text(f.read_text(encoding="utf-8").replace("\nPurpose:", "\n" * 12 + "Purpose:", 1),
                 encoding="utf-8")


@case("V29-inline")
def _(r):
    """`**Verified:**` satisfied V29, and V31 and V37 then skipped the page."""
    f = r / f"{S}quality-test/reference/oracles.md"
    f.write_text(f.read_text(encoding="utf-8").replace("\nVerified:", "\n**Verified:**", 1), encoding="utf-8")


@case("V30-basename")
def _(r): (r / f"{S}quality-test/reference/traps.md").write_text(
    "<!-- quality:deferred -->\nPurpose: x\nRead when: y\nSource: none\n"
    "Verified: 2026-08-21 — no automated check.\n", encoding="utf-8")


@case("V31-bleed")
def _(r):
    """A bare date whose paragraph runs on into a body sentence holding a marker."""
    f = r / f"{S}quality-test/reference/case-design.md"
    t = f.read_text(encoding="utf-8")
    i = t.index("Verified:"); j = t.index("\n\n", i)
    f.write_text(t[:i] + "Verified: 2026-08-21\nCases are found by running the partitions." + t[j:],
                 encoding="utf-8")


@case("V34-whole-dir")
def _(r): (r / f"{S}quality-test/tools").symlink_to("../../quality-tools")


@case("V34-renamed")
def _(r): (r / f"{S}quality-test/render").symlink_to("../../quality-tools/render.py")


@case("V35-vocab")
def _(r):
    f = r / f"{S}_quality/OUTCOMES.md"
    f.write_text(f.read_text(encoding="utf-8").replace("`moot`", "moot"), encoding="utf-8")


@case("V36-form")
def _(r):
    for g in (r / f"{S}quality-review/playbooks/visualise.md",
              r / f"{S}quality-review/reference/diagram-forms.md"):
        g.write_text(re.sub("mermaid", "graph", g.read_text(encoding="utf-8"), flags=re.I), encoding="utf-8")


@case("V36-floor")
def _(r):
    for g in (r / f"{S}quality-review/playbooks/visualise.md",
              r / f"{S}quality-review/reference/diagram-forms.md"):
        g.write_text(g.read_text(encoding="utf-8").replace("`derived`", "derived"), encoding="utf-8")


@case("V37-unpinned")
def _(r): sub(r / "quality-registry/harness.yaml", "  jest: null", '  jest: "29"')


@case("V37-pin-unused")
def _(r):
    sub(r / "quality-registry/harness.yaml", "  jest: null", '  jest: "29"')
    for f in (r / f"{S}").glob("*/reference/*.md"):
        t = f.read_text(encoding="utf-8")
        if re.search(r"^Source:.*\bjest\b", t, re.M):
            f.write_text(re.sub(r"^(Source:.*?)\bjest\b", r"\1jest 29", t, count=1, flags=re.M),
                         encoding="utf-8")


@case("V37-case")
def _(r):
    f = r / f"{S}quality-test/reference/case-design.md"
    f.write_text(f.read_text(encoding="utf-8") + "\nFind the first bad commit with Git bisect.\n",
                 encoding="utf-8")


@case("V37-none-token")
def _(r): sub(r / f"{S}quality-test/reference/case-design.md",
              "Source: none — nothing outside this page can move what it states.",
              "Source: Playwright docs, nonetheless unpinned.")


@case("V38-case")
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
              "SEVERITY:   CRITICAL | HIGH | MEDIUM | low | NIT")


@case("V38-foreign")
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "VERDICT:    GO | GO-WITH-CONDITIONS | NO-GO",
              "VERDICT:    GO | BLOCK | NO-GO")


@quiet("V4-anchor")
def _(r): sub(r / f"{S}quality-test/SKILL.md", "[traps](playbooks/traps.md)", "[traps](playbooks/traps.md#top)")


@quiet("V34-scoped-list")
def _(r):
    import yaml as _y
    sub(r / "quality-registry/harness.yaml", 'tools: "Read, Grep, Glob, Bash, Write"',
        'tools: [Read, Grep, Glob, "Bash(python3:*)", Write]')
    for n, c in _y.safe_load((r / "quality-registry/capabilities.yaml").read_text()).items():
        if c.get("class") == "doc-write":
            sub(r / "skills" / n / "SKILL.md", "allowed-tools: Read, Grep, Glob, Bash, Write\n",
                "allowed-tools: Read, Grep, Glob, Bash(python3:*), Write\n")


def hooks_cases() -> str | None:
    """The hook report follows the installed bytes, for both hooks."""
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "repo"
        shutil.copytree(ROOT, copy, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__"))
        subprocess.run(["git", "init", "-q", str(copy)], check=True)
        hooks = copy / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        src = (copy / "quality-tools" / "githooks" / "pre-commit").read_bytes()
        steps = [("off", lambda: None),
                 ("stale", lambda: (hooks / "pre-commit").write_bytes(src)),
                 ("on", lambda: (hooks / "pre-merge-commit").write_bytes(src)),
                 ("stale", lambda: (hooks / "pre-merge-commit").write_bytes(src + b"#\n"))]
        for want, step in steps:
            step()
            _, out = run(copy)
            if f"hooks {want}" not in out:
                return f"hooks state: expected {want!r}\n{out}"
    return None


def main() -> int:
    # The exit code, not a word in the output: "green" can appear in a failure line.
    rc, baseline = run(ROOT)
    if rc != 0:
        print("the working tree is already failing; fix that first:\n" + baseline)
        return 1

    bad: list[str] = []
    for rule, mutate in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            mutate(copy)
            _, out = run(copy)
            expect = rule.split("-")[0]
            if not re.search(rf"^\s*{expect}: ", out, re.M):
                bad.append(rule)
                print(f"  {rule} did not fire\n{out}")

    print(f"{len(CASES)} rules exercised, {len(bad)} silent")
    if bad:
        print("silent: " + ", ".join(bad))
        return 1

    noisy: list[str] = []
    for rule, mutate in QUIET.items():
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, symlinks=True,
                            ignore=shutil.ignore_patterns(".git", "__pycache__"))
            mutate(copy)
            rc, out = run(copy)
            if rc != 0:
                noisy.append(rule)
                print(f"  {rule} fired on a legitimate case\n{out}")
    if noisy:
        print("noisy: " + ", ".join(noisy))
        return 1
    if (problem := hooks_cases()):
        print(problem)
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
