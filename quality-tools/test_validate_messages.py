#!/usr/bin/env python3
"""What each rule says, not only that it fires.

test_validate.py proves every rule fires on a violation and stays quiet on a
legitimate case. Mutation testing showed that is not enough: a rule could
report the wrong file, lose a branch, or crash on a malformed registry, and the
rule id would still appear. Each case here mutates a throwaway copy and names
the message that must (or must not) appear, and a failing copy must exit 1.
It never imports validate, so a validate.py that exits on import cannot end
this run green.

Run: make test
"""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = "skills/"


def run(root, env=None):
    r = subprocess.run([sys.executable, str(root / "quality-tools" / "validate.py")],
                       capture_output=True, text=True, env=env, errors="replace")
    return r.returncode, r.stdout + r.stderr


def sub(path, old, new, count=1):
    t = path.read_text(encoding="utf-8")
    assert old in t, f"fixture text not found in {path.name}: {old[:60]!r}"
    path.write_text(t.replace(old, new, count), encoding="utf-8")


CASES = []           # (name, mutate, must_appear: list[str], must_not_appear: list[str])


def case(name, must=(), must_not=()):
    def deco(fn):
        CASES.append((name, fn, list(must), list(must_not)))
        return fn
    return deco


# ---- V1 / V5 / V6 / V11 / V13 budgets, including the boundary itself
@case("V1-description", must=["V1: quality-test description is"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "Writing tests that can actually fail",
              "Writing tests that can actually fail " + "x" * 200)

@case("V1-at-limit", must_not=["V1:"])
def _(r):
    p = r / f"{S}quality-test/SKILL.md"; t = p.read_text(encoding="utf-8")
    p.write_text(t + "\n" * (152 - len(t.splitlines())), encoding="utf-8")

@case("V5-count", must=["V5: quality-test has 9 playbooks"])
def _(r):
    d = r / f"{S}quality-test/playbooks"
    for i in range(9 - len(list(d.glob("*.md")))):
        (d / f"extra{i}.md").write_text("<!-- quality:guidance -->\n", encoding="utf-8")

@case("V6-shared-total", must=["V6: _quality totals"])
def _(r): (r / f"{S}_quality/EXTRA.md").write_text("<!-- quality:contract -->\n" + "x\n" * 40, encoding="utf-8")

@case("V6-repo-total", must=["V6: repo markdown totals"])
def _(r): (r / "docs").mkdir(exist_ok=True); (r / "docs/big.md").write_text("x\n" * 400, encoding="utf-8")

@case("V11-at-limit", must_not=["V11:"])
def _(r):
    for i in range(2):
        d = r / f"{S}quality-extra{i}"; d.mkdir()
        shutil.copy(r / f"{S}quality-test/SKILL.md", d / "SKILL.md")

@case("V13-at-limit", must_not=["V13:"])
def _(r):
    import yaml
    n = len(yaml.safe_load((r / "quality-registry/routes.yaml").read_text(encoding="utf-8")))
    t = (r / "quality-registry/routes.yaml").read_text(encoding="utf-8")
    t += "".join(f"\nfiller{i}:\n  pattern: linear\n  when: x\n  chain: [quality-test]\n"
                 for i in range(12 - n))
    (r / "quality-registry/routes.yaml").write_text(t, encoding="utf-8")

# ---- V9 / V10
@case("V9-no-signals", must=["V9: quality-test declares no signals"])
def _(r):
    p = r / "quality-registry/capabilities.yaml"; t = p.read_text(encoding="utf-8")
    i = t.index("quality-test:"); j = t.index("signals:", i); k = t.index("\n", j)
    p.write_text(t[:j] + "signals: []" + t[k:], encoding="utf-8")

@case("V10-mapping", must=["V10: fixtures.yaml is not a non-empty list"])
def _(r): (r / "quality-registry/fixtures.yaml").write_text("a: 1\n", encoding="utf-8")

@case("V10-no-match", must=["V10: no signal matches 'zzzz qqqq'"])
def _(r):
    p = r / "quality-registry/fixtures.yaml"
    p.write_text(p.read_text(encoding="utf-8") + '\n- ask: "zzzz qqqq"\n  expect: quality-test\n', encoding="utf-8")

# ---- V14
@case("V14-loop-key", must=["is missing max_cycles"])
def _(r):
    p = r / "quality-registry/routes.yaml"
    p.write_text(re.sub(r"^  max_cycles:.*\n", "", p.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")

@case("V14-report-only", must=["is missing stops_at"])
def _(r):
    p = r / "quality-registry/routes.yaml"
    p.write_text(re.sub(r"^  stops_at:.*\n", "", p.read_text(encoding="utf-8"), count=1, flags=re.M), encoding="utf-8")

# ---- V15
@case("V15-unknown-class", must=["V15: quality-test declares unknown class 'bogus'"])
def _(r):
    p = r / "quality-registry/capabilities.yaml"; t = p.read_text(encoding="utf-8")
    i = t.index("quality-test:"); j = t.index("class:", i); k = t.index("\n", j)
    p.write_text(t[:j] + "class: bogus" + t[k:], encoding="utf-8")

@case("V15-no-writes-key", must_not=["Traceback", "V15:"])
def _(r): sub(r / "quality-registry/harness.yaml", "permission_classes:\n",
              "permission_classes:\n  ro:\n    tools: \"Read\"\n")

# ---- V19
@case("V19-bare-root", must=["V19: quality-test/SKILL.md references 'playbooks/nonexistent'"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Done when\n\nSee `playbooks/nonexistent`.\n")

@case("V19-http", must_not=["V19:", "V8:"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when",
              "## Done when\n\n[spec](https://example.com/spec) and `https://example.com/a.md`.\n")

@case("V19-self-link", must_not=["V19:"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Done when\n\n[here](./)\n")

@case("V19-shared-link", must=["V19: _quality/VALUES.md (as read by"])
def _(r): sub(r / f"{S}_quality/VALUES.md", "## 1. Honesty", "## 1. Honesty\n\n[readme](../../README.md)\n")

# ---- V22 / V23
@case("V22-delivered-source-skipped", must_not=["V22: quality-registry/delivered"])
def _(r):
    p = r / "quality-registry/delivered/values.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n#" + "TODO(agent): x\n", encoding="utf-8")

@case("V23-empty-file", must=["V23: skills/quality-test/playbooks/empty.md label is ''"], must_not=["Traceback"])
def _(r): (r / f"{S}quality-test/playbooks/empty.md").write_text("", encoding="utf-8")

# ---- V24
@case("V24-routing-omits", must=["V24: _quality/ROUTING.md does not list quality-debt"])
def _(r):
    p = r / f"{S}_quality/ROUTING.md"
    p.write_text(p.read_text(encoding="utf-8").replace("`quality-debt`", "the debt skill"), encoding="utf-8")

@case("V24-readme-omits", must=["V24: README.md does not list quality-debt"])
def _(r):
    p = r / "README.md"
    p.write_text(p.read_text(encoding="utf-8").replace("quality-debt", "the debt skill"), encoding="utf-8")

# ---- V28
@case("V28-prefix", must=["V28: prefix is 'q'"])
def _(r): sub(r / "quality-registry/harness.yaml", "prefix: quality-", "prefix: q")

@case("V28-shared-dir", must=["V28: shared_dir is '_qa'"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "shared_dir: _quality", "shared_dir: _qa")
    (r / f"{S}_quality").rename(r / f"{S}_qa")

# ---- V30
@case("V30-tick-path-from-playbook", must_not=["V30:"])
def _(r):
    (r / f"{S}quality-test/reference/extra.md").write_text(
        "<!-- quality:deferred -->\n# Extra\n\nPurpose: x\nRead when: y\nSource: none\n"
        "Verified: 2026-08-21 — no automated check.\n", encoding="utf-8")
    p = r / f"{S}quality-test/playbooks/traps.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nSee `reference/extra.md`.\n", encoding="utf-8")

# ---- V31 / V32 / V34 / V35 / V36 / V37
@case("V31-no-markers", must=["V31: harness.yaml declares no verified_markers"])
def _(r):
    p = r / "quality-registry/harness.yaml"; t = p.read_text(encoding="utf-8")
    p.write_text(t.replace("verified_markers:", "unused_markers:"), encoding="utf-8")

@case("V31-no-verified-line", must_not=["states a `Verified:` date"])
def _(r):
    f = r / f"{S}quality-test/reference/oracles.md"
    f.write_text(f.read_text(encoding="utf-8").replace("\nVerified:", "\nChecked:", 1), encoding="utf-8")

@case("V32-two-engines", must_not=["V32:"])
def _(r): sub(r / "quality-registry/harness.yaml", "runs_on: [claude, codex, agy]", "runs_on: [claude, codex]")

@case("V32-no-vocab", must=["V32: harness.yaml declares no checker vocabulary"])
def _(r): sub(r / "quality-registry/harness.yaml", "  checkers: [other-engine]\n", "")

@case("V32-pinned", must=["pins its checker to 'claude'"])
def _(r): sub(r / "quality-registry/routes.yaml", "checker: ", "checker: claude  # ")

@case("V34-unknown-skill", must=["V34: linked_tools[render.py] names ['quality-ghost']"])
def _(r): sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: all\n  render.py: [quality-ghost]")

@case("V34-none-declared-message", must=["V34: harness.yaml declares no linked_tools"])
def _(r): sub(r / "quality-registry/harness.yaml", "linked_tools:", "unlinked_tools:")

@case("V34-missing-tool-message", must=["V34: linked_tools names nosuch.py"])
def _(r): sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: all\n  nosuch.py: all")

@case("V35-no-signature", must=["V35: harness.yaml declares no signature mapping",
                                 "V28: _quality/ does not exist"], must_not=["Traceback"])
def _(r):
    # One rule's missing key is that rule's finding: the others still run and report.
    sub(r / "quality-registry/harness.yaml", "\nsignature:", "\nunused_signature:")
    shutil.rmtree(r / f"{S}_quality")

@case("V28-no-platform-dirs", must=["V28: harness.yaml platform_dirs is None",
                                    "V35: signature names _quality/"], must_not=["Traceback"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "\nplatform_dirs:", "\nunused_platform_dirs:")
    shutil.rmtree(r / f"{S}_quality")

@case("V34-bare-skill-name", must=["V34: linked_tools[refute.py] is 'quality-debt'; it is `all` or a list"],
      must_not=["which are not skills", "does not name it"])
def _(r): sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: quality-debt")

@case("V34-bare-skill-name-wrong-target", must=["is 'quality-debt'; it is `all`",
      "quality-test/refute.py points at"])
def _(r):
    # The value being unreadable must not hide a link that points at the wrong file.
    sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: quality-debt")
    link = r / f"{S}quality-test/refute.py"; link.unlink(); link.symlink_to("../../quality-tools/render.py")

@case("V35-signature-incomplete", must=["V35: signature declares no own_word"], must_not=["Traceback"])
def _(r): sub(r / "quality-registry/harness.yaml", "  own_word:", "  unused_own_word:")

@case("V35-unknown-vocabulary", must=["V35: signature.vocabulary names 'nope'"], must_not=["Traceback"])
def _(r):
    import re as _re
    p = r / "quality-registry/harness.yaml"; t = p.read_text(encoding="utf-8")
    p.write_text(_re.sub(r"(?m)^  vocabulary: \w+", "  vocabulary: nope", t, count=1), encoding="utf-8")

@case("V35-contract-missing", must=["V35: signature names _quality/NOPE.md"], must_not=["Traceback"])
def _(r): sub(r / "quality-registry/harness.yaml", "  contract: OUTCOMES.md", "  contract: NOPE.md")

@case("V35-required-not-a-skill", must=["V35: signature.required_of names 'quality-ghost'"], must_not=["Traceback"])
def _(r): sub(r / "quality-registry/harness.yaml", "required_of: [quality-review, quality-gate, quality-regression]",
              "required_of: [quality-review, quality-gate, quality-regression, quality-ghost]")

@case("V36-required-none", must=["V36: finding_visuals declares no required_of"])
def _(r): sub(r / "quality-registry/harness.yaml", "  required_of: [quality-review]\n", "")

@case("V36-empty-no-why", must=["required_of is empty and says nothing"])
def _(r): sub(r / "quality-registry/harness.yaml", "  required_of: [quality-review]", "  required_of: []")

@case("V36-empty-with-why", must_not=["V36:"])
def _(r): sub(r / "quality-registry/harness.yaml", "  required_of: [quality-review]",
              "  required_of: []\n  why: this set has no review skill")

@case("V36-no-forms", must=["declares no triggers, floor or forms"])
def _(r): sub(r / "quality-registry/harness.yaml", "  forms: [ascii, mermaid]", "  forms: []")

@case("V36-no-words", must=["declares no triggers, floor or forms"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "  triggers: [hops, ordering, disagreement, location]", "  triggers: []")
    sub(r / "quality-registry/harness.yaml", "  floor: [labelled, derived, bounded]", "  floor: []")

@case("V36-not-a-skill", must=["finding_visuals.required_of names 'quality-ghost'"], must_not=["Traceback"])
def _(r): sub(r / "quality-registry/harness.yaml", "  required_of: [quality-review]", "  required_of: [quality-review, quality-ghost]")

@case("V37-no-none-marker", must=["V37: harness.yaml declares no source_authorities"], must_not=["Traceback"])
def _(r): sub(r / "quality-registry/harness.yaml", 'source_none_marker: "none"', 'unused_marker: "none"')

# ---- main
@case("main-green-line", must=["\ngreen\n"])
def _(r): pass

@case("main-failure-count", must=["\n2 failure(s)"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Finished when")


# ---- second batch
def ref(r, text):
    (r / f"{S}quality-test/reference/extra.md").write_text("<!-- quality:deferred -->\n# Extra\n\n" + text, encoding="utf-8")
    p = r / f"{S}quality-test/playbooks/traps.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nSee `reference/extra.md`.\n", encoding="utf-8")

@case("V37-continuation", must_not=["V37:"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nSource: the counts come from\n  git, its own commands.\n"
                 "Verified: 2026-08-21 — no automated check.\n\nRun git log to count.\n")

@case("V37-source-last-line", must_not=["V37:", "Traceback"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nVerified: 2026-08-21 — no automated check.\n"
                 "Source: none — nothing outside this page.")

@case("V37-source-after-verified", must_not=["V37:"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nVerified: 2026-08-21 — no automated check.\n"
                 "Source: git — counts.\n\nRun git log to count.\n")

@case("V37-verified-is-body", must_not=["V37:"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nSource: git — counts.\n"
                 "Verified: 2026-08-21 — confirmed by running git log in a fixture.\n\nNothing else here.\n")

@case("V37-read-when-is-body", must_not=["V37:"])
def _(r): ref(r, "Purpose: x.\nRead when: counting with git.\nSource: git — counts.\n"
                 "Verified: 2026-08-21 — no automated check.\n")

@case("V37-none-on-previous-line", must=["names no source"])
def _(r): ref(r, "Purpose: x.\nRead when: none of the above.\nSource:\n"
                 "Verified: 2026-08-21 — no automated check.\n")

@case("V37-continuation-at-eof", must_not=["V37:"])
def _(r): ref(r, "Run git log to count.\nPurpose: x.\nRead when: y.\nVerified: 2026-08-21 — no automated check.\n"
                 "Source: counts from\ngit")

@case("V37-fully-pinned", must_not=["V37:"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "  jest: null", '  jest: "29"')
    for f in (r / "skills").glob("*/reference/*.md"):
        t = f.read_text(encoding="utf-8")
        if re.search(r"^Source:.*\bjest\b", t, re.M):
            t = re.sub(r"^(Source:.*?)\bjest\b", r"\1jest 29", t, count=1, flags=re.M)
            f.write_text(t + "\nChecked against jest 29.\n", encoding="utf-8")

@case("V37-unpinned-message", must=["without the pinned version"])
def _(r): sub(r / "quality-registry/harness.yaml", "  jest: null", '  jest: "29"')

def window(r, line):
    f = r / f"{S}quality-test/reference/oracles.md"
    ls = f.read_text(encoding="utf-8").split("\n")
    i = next(k for k, l in enumerate(ls) if l.startswith("Verified:"))
    ls[i:i] = [""] * (line - 1 - i)
    f.write_text("\n".join(ls), encoding="utf-8")

@case("V29-line-12", must_not=["V29:"])
def _(r): window(r, 12)

@case("V29-line-13", must=["V29: skills/quality-test/reference/oracles.md has no 'Verified:'"])
def _(r): window(r, 13)

@case("V25-delivered-block-skipped", must_not=["V25:"])
def _(r):
    p = r / "quality-registry/delivered/values.md"
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\nas of v2.14.0\n", encoding="utf-8")
    subprocess.run([sys.executable, str(r / "quality-tools/render.py")], check=True, capture_output=True)

@case("V25-line-number", must=["skills/quality-test/playbooks/rot.md:2 pins"])
def _(r): (r / f"{S}quality-test/playbooks/rot.md").write_text("<!-- quality:guidance -->\nas of v2.14.0\n", encoding="utf-8")

@case("V22-line-number", must=["skills/quality-test/playbooks/todo.md:2 marker"])
def _(r): (r / f"{S}quality-test/playbooks/todo.md").write_text("<!-- quality:guidance -->\n#" + "TODO(agent): tidy\n", encoding="utf-8")

@case("V22-classified", must_not=["V22:"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Done when\n\n#" + "TODO(agent): DEFERRED tidy this\n")

@case("V38-line-number", must=["skills/quality-test/playbooks/enum.md:2 switches on"])
def _(r): (r / f"{S}quality-test/playbooks/enum.md").write_text("<!-- quality:guidance -->\nverdict: KEEP | DROP\n", encoding="utf-8")

@case("V38-miscased-once", must=["lists low, not as"])
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
              "SEVERITY:   CRITICAL | HIGH | MEDIUM | low | NIT")

@case("V38-unbound-mixed", must=["no vocabulary in harness.yaml is keyed by it"])
def _(r):
    p = r / f"{S}quality-test/playbooks/traps.md"
    p.write_text(p.read_text(encoding="utf-8") + "\nSEVERITYY: CRITICAL | foo\n", encoding="utf-8")

@case("V39-at-limit", must_not=["V39:"])
def _(r): sub(r / "quality-registry/routes.yaml", "chain: [quality-review, quality-test, quality-gate]",
              "chain: [quality-review, quality-test, quality-review, quality-test, quality-review, quality-gate]")

@case("V5-at-limit", must_not=["V5:"])
def _(r):
    p = r / f"{S}quality-test/playbooks/traps.md"; t = p.read_text(encoding="utf-8")
    p.write_text(t + "\n" * (300 - len(t.splitlines())), encoding="utf-8")

@case("V26-outside-target", must_not=["V26:"])
def _(r): sub(r / "quality-registry/capabilities.yaml", "      go: quality-debt", "      go: the team lead")

@case("V27-outside", must=["points outside the repo"])
def _(r): (r / f"{S}quality-test/outside").symlink_to(tempfile.gettempdir())

@case("V27-nested-outside", must=["V27: quality-test/playbooks/ext.md points outside the repo"])
def _(r): (r / f"{S}quality-test/playbooks/ext.md").symlink_to(tempfile.gettempdir())

@case("V27-nested-broken", must=["V27: quality-test/assets/gone is a broken symlink"])
def _(r):
    (r / f"{S}quality-test/assets").mkdir()
    (r / f"{S}quality-test/assets/gone").symlink_to("../../_gone")

# A file one level down is read by none of the per-file rules: refused, not skipped.
@case("V4-subdirectory", must=["V4: quality-test/playbooks/more/ is a subdirectory"])
def _(r):
    (r / f"{S}quality-test/playbooks/more").mkdir()
    (r / f"{S}quality-test/playbooks/more/huge.md").write_text("x\n" * 400, encoding="utf-8")

@case("V30-subdirectory", must=["V30: quality-test/reference/more/ is a subdirectory"])
def _(r):
    (r / f"{S}quality-test/reference/more").mkdir()
    (r / f"{S}quality-test/reference/more/bare.md").write_text("x\n", encoding="utf-8")

# A link to reference/oracles.md is not a link to playbooks/oracles.md.
@case("V4-same-name-elsewhere", must=["V4: quality-test/playbooks/oracles.md is not linked"])
def _(r): (r / f"{S}quality-test/playbooks/oracles.md").write_text("<!-- quality:guidance -->\n", encoding="utf-8")

# A mention in prose is not a row in the table.
@case("V24-readme-row-removed", must=["V24: README.md does not list quality-test"])
def _(r):
    p = r / "README.md"
    lines = [l for l in p.read_text(encoding="utf-8").splitlines(keepends=True)
             if not l.startswith("| [`quality-test`]")]
    p.write_text("".join(lines), encoding="utf-8")

@case("V38-bulleted", must=["traps.md:", "lists low, not as"])
def _(r):
    p = r / f"{S}quality-test/playbooks/traps.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n- SEVERITY: CRITICAL | HIGH | MEDIUM | low | NIT\n",
                 encoding="utf-8")

# Below a delivered block, the line reported is the line in the file.
_SKILL = (ROOT / f"{S}quality-test/SKILL.md").read_text(encoding="utf-8").splitlines()
@case("V25-line-after-delivered-block",
      must=[f"V25: skills/quality-test/SKILL.md:{_SKILL.index('## Done when') + 2} pins"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when\n", "## Done when\nPinned to v2.14.0.\n")

@case("V34-class-without-bash", must=["links refute.py and its class grants no Bash"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "permission_classes:\n",
        "permission_classes:\n  ro:\n    tools: \"Read, Grep, Glob, Write\"\n    writes: true\n")
    p = r / "quality-registry/capabilities.yaml"; t = p.read_text(encoding="utf-8")
    i = t.index("quality-test:"); j = t.index("class:", i); k = t.index("\n", j)
    p.write_text(t[:j] + "class: ro" + t[k:], encoding="utf-8")

@case("V34-scoped-tool", must_not=["V34:"])
def _(r):
    sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: all\n  render.py: [quality-test]")
    (r / f"{S}quality-test/render.py").symlink_to("../../quality-tools/render.py")

@case("V34-not-named", must=["linked_tools[refute.py] does not name it"])
def _(r): sub(r / "quality-registry/harness.yaml", "  refute.py: all", "  refute.py: [quality-test]")

@case("V34-plain-py", must=["quality-test/helper.py is a tool link nothing declares"])
def _(r): (r / f"{S}quality-test/helper.py").write_text("print(1)\n", encoding="utf-8")

@case("V34-nested-declared-name", must=["reaches quality-tools/refute.py"])
def _(r):
    (r / f"{S}quality-test/sub").mkdir()
    (r / f"{S}quality-test/sub/refute.py").symlink_to("../../../quality-tools/refute.py")

@case("V36-no-triggers-key", must_not=["Traceback", "V36:"])
def _(r): sub(r / "quality-registry/harness.yaml", "  triggers: [hops, ordering, disagreement, location]\n", "")

@case("V36-no-floor-key", must_not=["Traceback", "V36:"])
def _(r): sub(r / "quality-registry/harness.yaml", "  floor: [labelled, derived, bounded]\n", "")

@case("V36-playbook-missing", must=["V36: quality-review owes quality-review/playbooks/visualise.md"], must_not=["Traceback"])
def _(r): (r / f"{S}quality-review/playbooks/visualise.md").unlink()

@case("V39-route-without-chain", must_not=["Traceback"])
def _(r):
    p = r / "quality-registry/routes.yaml"
    p.write_text(p.read_text(encoding="utf-8") + "\nbare:\n  pattern: linear\n  when: x\n", encoding="utf-8")

@case("V33-key-missing", must=["declares no refutation refuted_when"], must_not=["Traceback"])
def _(r):
    p = r / "quality-registry/harness.yaml"
    p.write_text(re.sub(r"  refuted_when: >-\n(    .*\n)+", "", p.read_text(encoding="utf-8")), encoding="utf-8")

@case("V19-shared-link-anchor", must=["V19: _quality/VALUES.md (as read by"])
def _(r): sub(r / f"{S}_quality/VALUES.md", "## 1. Honesty", "## 1. Honesty\n\n[readme](../../README.md#top)\n")

@case("V30-anchored-link", must_not=["V30:"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "[oracles](reference/oracles.md)", "[oracles](reference/oracles.md#top)")

@case("V17-open-missing", must=["missing the values delivery block"], must_not=["Traceback"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "<!-- deliver:values -->\n", "")

@case("V17-close-missing", must=["missing the values delivery block"], must_not=["Traceback"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "<!-- /deliver:values -->\n", "")

@case("V17-stray-open", must=["carries the values block 2 times"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "<!-- /deliver:values -->\n", "<!-- /deliver:values -->\n<!-- deliver:values -->\n")

@case("V17-stray-close", must=["carries the values block"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "<!-- /deliver:values -->\n", "<!-- /deliver:values -->\n<!-- /deliver:values -->\n")

@case("V18-body-key-is-not-frontmatter", must_not=["V18:", "V1:"])
def _(r): sub(r / f"{S}quality-test/SKILL.md", "## Done when", "## Done when\n\ndescription: x\n")

@case("V19-empty-roster", must_not=["Traceback"])
def _(r):
    for d in (r / "skills").glob("quality-*"):
        shutil.rmtree(d)


# ---- third batch: the limits themselves, and what the header block swallows
def md_lines(paths):
    return sum(len(f.read_text(encoding="utf-8").splitlines()) for f in paths)

def shared_pad(r, total):
    have = md_lines((r / f"{S}_quality").glob("*.md"))
    (r / f"{S}_quality/EXTRA.md").write_text("<!-- quality:contract -->\n" + "x\n" * (total - have - 1), encoding="utf-8")

@case("V6-shared-total-at-limit", must_not=["V6:"])
def _(r): shared_pad(r, 1020)

@case("V6-shared-total-over", must=["V6: _quality totals 1021 lines"])
def _(r): shared_pad(r, 1021)

@case("V6-one-shared-file-over", must=["V6: _quality/CONTRACT.md is 161 lines"])
def _(r):
    p = r / f"{S}_quality/CONTRACT.md"; p.write_text(p.read_text(encoding="utf-8") + "x\n", encoding="utf-8")

@case("V6-repo-total-at-limit", must_not=["V6:"])
def _(r):
    have = md_lines(f for f in r.rglob("*.md") if ".git" not in f.parts)
    (r / "docs").mkdir(exist_ok=True); (r / "docs/pad.md").write_text("x\n" * (4900 - have), encoding="utf-8")

@case("V1-description-at-limit", must_not=["V1:"])
def _(r):
    p = r / f"{S}quality-test/SKILL.md"; t = p.read_text(encoding="utf-8")
    m = re.search(r'^description: "(.*)"$', t, re.M)
    p.write_text(t.replace(m.group(1), m.group(1) + " " + "x" * (200 - len(m.group(1)) - 1), 1), encoding="utf-8")

@case("V5-count-at-limit", must_not=["V5:"])
def _(r):
    d = r / f"{S}quality-test/playbooks"
    for i in range(8 - len(list(d.glob("*.md")))):
        (d / f"extra{i}.md").write_text("<!-- quality:guidance -->\n", encoding="utf-8")

@case("V36-reference-missing", must=["V36: quality-review owes quality-review/reference/diagram-forms.md"], must_not=["Traceback"])
def _(r): (r / f"{S}quality-review/reference/diagram-forms.md").unlink()

@case("V27-link-to-repo-root", must_not=["V27:", "Traceback"])
def _(r): (r / f"{S}quality-test/root").symlink_to("../..")

@case("V37-odd-continuation", must_not=["V37:"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nSource: counts from\n  git.\n"
                 "Verified: 2026-08-21 — confirmed by running git log in a fixture.\n\nNothing else here.\n")

@case("V37-next-line-is-not-header", must=["leans on git and its `Source:` does not name it"])
def _(r): ref(r, "Purpose: x.\nRead when: y.\nSource: none — x.\n"
                 "Verified: 2026-08-21 — confirmed by running git log in a fixture.\n")

@case("V38-trailing-prose", must=["HANDOFF.md:32 SEVERITY lists low, not as"])
def _(r):
    """The value list ends at its last value; prose after it hid the line from V38."""
    sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
        "SEVERITY:   CRITICAL | HIGH | MEDIUM | low | NIT — graded per SEVERITY.md §2")

@case("V38-foreign-before-prose", must=["HANDOFF.md:32 SEVERITY lists MINOR, not as"])
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
              "SEVERITY:   CRITICAL | HIGH | MINOR | LOW | NIT   (one per finding)")

@case("V38-backticked", must=["HANDOFF.md:32 SEVERITY lists low, not as"])
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
              "SEVERITY:   `CRITICAL` | `HIGH` | `MEDIUM` | `low` | `NIT`")

@case("V38-prose-after-declared-values", must_not=["V38:"])
def _(r): sub(r / f"{S}_quality/HANDOFF.md", "SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT",
              "SEVERITY:   `CRITICAL` | `HIGH` | `MEDIUM` | `LOW` | `NIT` — graded per SEVERITY.md §2")

@case("V6-shared-subdirectory", must=["V6: skills/_quality/extra/ is a subdirectory"])
def _(r):
    """The shared budgets read _quality/*.md; a file one level down escaped both."""
    (r / f"{S}_quality/extra").mkdir()
    (r / f"{S}_quality/extra/BIG.md").write_text("<!-- quality:contract -->\n" + "x\n" * 300,
                                                 encoding="utf-8")

@case("V17-blank-inside-markers", must=["V17: quality-test/SKILL.md outcome block differs"])
def _(r):
    """render writes one newline each side; a blank line added inside is drift it undoes."""
    sub(r / f"{S}quality-test/SKILL.md", "<!-- deliver:outcome -->\n", "<!-- deliver:outcome -->\n\n")

@case("V23-unclosed-frontmatter", must_not=["V23: skills/quality-test/playbooks/fm.md"])
def _(r): (r / f"{S}quality-test/playbooks/fm.md").write_text("---\n<!-- quality:guidance -->\nx\n", encoding="utf-8")


@case("V28-dir-under-skills", must=["V28: stray/ carries no set name"])
def _(r): (r / f"{S}stray").mkdir()


@case("V28-shared-missing", must=["V28: _quality/ does not exist"], must_not=["Traceback"])
def _(r): shutil.rmtree(r / f"{S}_quality")

def main():
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"
        shutil.copytree(ROOT, base, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        # a non-UTF-8 console must not turn the report into a traceback
        rc, out = run(base, env={**os.environ, "PYTHONIOENCODING": "ascii"})
        if rc != 0 or "Traceback" in out:
            bad.append(f"ascii console: rc={rc}\n{out[-800:]}")
        # importing validate must not run it
        r = subprocess.run([sys.executable, "-c", "import validate; print('imported')"],
                           cwd=base / "quality-tools", capture_output=True, text=True)
        if "imported" not in r.stdout or "rules" in r.stdout:
            bad.append(f"import ran the validator or exited: {r.stdout[-300:]}")
        for name, fn, must, must_not in CASES:
            copy = Path(tmp) / name
            shutil.copytree(base, copy, symlinks=True)
            fn(copy)
            rc, out = run(copy)
            for m in must:
                if m not in out:
                    bad.append(f"{name}: expected {m!r}\n{out[-1500:]}")
            for m in must_not:
                if m in out:
                    bad.append(f"{name}: did not expect {m!r}\n{out[-1500:]}")
            if must and rc != 1 and name != "main-green-line":
                bad.append(f"{name}: exit {rc} with a failure expected (want 1)")
            shutil.rmtree(copy)
    print("\n\n".join(bad) if bad else f"{len(CASES)} message cases ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
