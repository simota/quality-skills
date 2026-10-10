#!/usr/bin/env python3
"""Write the delivered blocks back into every SKILL.md.

A contract kept only in the shared directory is not read on most launches, so the operative
part is carried verbatim in each skill. That only stays true if changing one
line does not cost eight hand edits — this is that cost, paid once.

Idempotent: run it, commit the diff.

Nothing is written unless every file renders cleanly: a marker missing, repeated
or out of order, or a section missing, is an error and the run exits 1 with the
tree untouched — a half-rendered set is worse than a stale one.

`--check` writes nothing and exits 1 if any file would change: the drift test,
without needing git to diff the result.

Exit codes: 0 rendered (or, with `--check`, nothing stale); 1 a file cannot be
rendered, a delivered block is missing, no skill was found, or `--check` found
drift; 2 an unknown argument.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "quality-registry" / "harness.yaml").read_text(encoding="utf-8"))
PREFIX = H["prefix"]
SKILLS_ROOT = ROOT / H["skills_dir"] if H.get("skills_dir") else ROOT
USAGE = "usage: render.py [--check]"


def delivered(errors: list[str]) -> dict[str, str]:
    """Each delivered block's text, appending to errors for any that is missing."""
    blocks = {}
    for key in H["delivered"]:
        path = ROOT / "quality-registry" / "delivered" / f"{key}.md"
        try:
            blocks[key] = path.read_text(encoding="utf-8").rstrip("\n")
        except OSError as e:
            errors.append(f"{path.relative_to(ROOT)}: {e.strerror or e}")
    return blocks


def render(path: Path, blocks: dict[str, str], errors: list[str]) -> str | None:
    """The rendered text, or None after appending why it cannot be rendered."""
    text = path.read_text(encoding="utf-8")
    where = path.parent.name
    for key, spec in H["delivered"].items():
        block = blocks[key]
        open_m, close_m = f"<!-- deliver:{key} -->", f"<!-- /deliver:{key} -->"
        payload = f"{open_m}\n{block}\n{close_m}"
        n_open, n_close = text.count(open_m), text.count(close_m)
        if (n_open, n_close) not in ((0, 0), (1, 1)) or (
                n_open and text.index(open_m) > text.index(close_m)):
            # Splitting on the first of a repeated or reversed pair would
            # silently swallow whatever lies between them.
            errors.append(f"{where}/SKILL.md: {key} markers must appear once each, "
                          f"opening first (found {n_open} opening, {n_close} closing)")
            return None
        if n_open:
            head, rest = text.split(open_m, 1)
            _, tail = rest.split(close_m, 1)
            text = head + payload + tail
        else:
            # The whole heading line: a substring match would take `### Decide
            # first` or `## Decide first, then` for `## Decide first`.
            m = re.search(rf"^## {re.escape(spec['section'])}[ \t]*(?:\n|\Z)", text, re.M)
            if not m:
                errors.append(f"{where}/SKILL.md: no section {spec['section']!r} "
                              f"to deliver {key} into")
                return None
            head, rest = text[:m.end()], text[m.end():]
            # append at the end of that section, before the next heading
            nxt = re.search(r"^## ", rest, re.M)
            body, tail = (rest[:nxt.start()], "\n" + rest[nxt.start():]) if nxt else (rest, "")
            text = head + body.rstrip("\n") + "\n" + payload + "\n" + tail
    return text


def main() -> int:
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return 0
    if [a for a in args if a != "--check"]:
        print(USAGE, file=sys.stderr)
        return 2
    check = "--check" in args
    skills = [d for d in sorted(SKILLS_ROOT.glob(f"{PREFIX}*")) if (d / "SKILL.md").exists()]
    if not skills:
        # Zero files rendered reads as zero stale: a check of nothing must not pass.
        print(f"render: no {PREFIX}*/SKILL.md under {SKILLS_ROOT}", file=sys.stderr)
        return 1
    errors: list[str] = []
    blocks = delivered(errors)
    rendered = {}
    if not errors:
        for d in skills:
            rendered[d] = render(d / "SKILL.md", blocks, errors)
    if errors:
        print("\n".join(f"  {e}" for e in errors), file=sys.stderr)
        print(f"render: {len(errors)} error(s), nothing written", file=sys.stderr)
        return 1
    changed = []
    for d, text in rendered.items():
        if text != (d / "SKILL.md").read_text(encoding="utf-8"):
            if not check:
                (d / "SKILL.md").write_text(text, encoding="utf-8")
            changed.append(d.name)
    names = f" ({', '.join(changed)})" if changed else ""
    if check:
        print(f"render: {len(changed)} stale{names}" + (" — run: make render" if changed else ""))
        return 1 if changed else 0
    print(f"rendered: {len(changed)} changed{names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
