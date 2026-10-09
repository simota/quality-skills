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
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
H = yaml.safe_load((ROOT / "quality-registry" / "harness.yaml").read_text(encoding="utf-8"))
PREFIX = H["prefix"]
SKILLS_ROOT = ROOT / H["skills_dir"] if H.get("skills_dir") else ROOT


def render(path: Path, errors: list[str]) -> str | None:
    """The rendered text, or None after appending why it cannot be rendered."""
    text = path.read_text(encoding="utf-8")
    where = path.parent.name
    for key, spec in H["delivered"].items():
        block = (ROOT / "quality-registry" / "delivered" / f"{key}.md").read_text(
            encoding="utf-8").rstrip("\n")
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
            heading = f"## {spec['section']}\n"
            if heading not in text:
                errors.append(f"{where}/SKILL.md: no section {spec['section']!r} "
                              f"to deliver {key} into")
                return None
            head, rest = text.split(heading, 1)
            # append at the end of that section, before the next heading
            nxt = rest.find("\n## ")
            body, tail = (rest[:nxt], rest[nxt:]) if nxt != -1 else (rest, "")
            text = head + heading + body.rstrip("\n") + "\n" + payload + "\n" + tail
    return text


def main() -> int:
    errors: list[str] = []
    rendered = {}
    for d in sorted(SKILLS_ROOT.glob(f"{PREFIX}*")):
        if (d / "SKILL.md").exists():
            rendered[d] = render(d / "SKILL.md", errors)
    if errors:
        print("\n".join(f"  {e}" for e in errors), file=sys.stderr)
        print(f"render: {len(errors)} error(s), nothing written", file=sys.stderr)
        return 1
    check = "--check" in sys.argv[1:]
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
