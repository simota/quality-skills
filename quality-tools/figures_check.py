#!/usr/bin/env python3
"""Re-derive what the reference layer states, from the tools and the arithmetic.

A `Verified:` date has no failure mode. These are the claims that do: two files
stating one model, a table of git exit codes, a probability table, and a handful
of command behaviours a later git could change under the page.

    make figures

Interest model — `_quality/SEVERITY.md` §4 against `quality-debt/reference/interest.md`:

* the formula is byte-identical in both files
* every band value SEVERITY fixes is exactly the set interest.md scores
* every worked example's arithmetic is right, to the precision it claims
* every divisor a worked example uses is one of SEVERITY's canonical values

Bisection — `quality-regression/reference/bisection.md`, against the installed git:

* every row of the exit-code table, by running a bisect whose predicate returns
  that code and reading what git did with it
* that a script without its execute bit exits 126, which the page's advice rests on
* the false-good table, recomputed as a binomial tail

Extraction — `quality-metrics/reference/extraction.md`, against the installed git:

* `--reverse | head -1` is the oldest pickaxe match and `-1` is the newest
* `-S` fires when an occurrence count drops, not only when it rises
* `--shortstat` field 4 counts deletions on a deletion-only diff

Every claim is parsed out of the page rather than restated here, so a page edited
to say something false fails as loudly as a tool that changed underneath it.
"""
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEVERITY = ROOT / "skills/_quality/SEVERITY.md"
INTEREST = ROOT / "skills/quality-debt/reference/interest.md"
BISECTION = ROOT / "skills/quality-regression/reference/bisection.md"
EXTRACTION = ROOT / "skills/quality-metrics/reference/extraction.md"
failures: list[str] = []


def fail(where: str, msg: str) -> None:
    failures.append(f"  {where}: {msg}")


FORMULA = re.compile(r"^interest\s*=.*$", re.M)


def check_formula() -> str:
    a = FORMULA.findall(SEVERITY.read_text())
    b = [l for l in FORMULA.findall(INTEREST.read_text()) if "(" in l]
    if not a or not b:
        fail("formula", "no `interest = ...` line found in "
                        f"{'SEVERITY.md' if not a else 'interest.md'} — "
                        "the checker has stopped checking anything")
        return ""
    if a[0].strip() != b[0].strip():
        fail("formula", f"SEVERITY.md says {a[0].strip()!r}, "
                        f"interest.md says {b[0].strip()!r}")
    return a[0].strip()


NUM = re.compile(r"\d+\.\d+")
OPERAND_ROW = re.compile(r"^\|\s*`(\w+_score|confidence_of_fix)`\s*\|[^|]*\|([^|]*)\|", re.M)
BAND_TABLE = re.compile(r"^\|[^|]*\|\s*(\d+\.\d+)\s*(?:—[^|]*)?\|\s*$", re.M)


def severity_bands() -> dict[str, set[str]]:
    out = {}
    for name, scale in OPERAND_ROW.findall(SEVERITY.read_text()):
        vals = set(NUM.findall(scale))
        if vals:
            out[name] = vals
    if len(out) != 4:
        fail("bands", f"SEVERITY.md defines {len(out)} operands, expected 4 — "
                      "the band-scale table has changed shape")
    return out


def interest_bands() -> dict[str, set[str]]:
    """Each `## Input n — <operand>` section owns the band table under it."""
    text = INTEREST.read_text()
    sections = re.split(r"^## ", text, flags=re.M)
    out = {}
    for s in sections:
        m = re.match(r"Input \d+ — (\w+)", s)
        if not m:
            continue
        vals = set(BAND_TABLE.findall(s))
        if vals:
            out[m.group(1)] = vals
    return out


def confidence_values() -> set[str]:
    """SEVERITY's canonical divisor table."""
    text = SEVERITY.read_text()
    block = text.split("canonical values.")[-1]
    rows = re.findall(r"^\|\s*[^|]+\|\s*(\d+\.\d+)\s*\|", block, re.M)
    if not rows:
        fail("confidence", "no canonical divisor table found — "
                           "the checker has stopped checking anything")
    return set(rows)


def check_bands() -> int:
    sev, inte = severity_bands(), interest_bands()
    conf = confidence_values()
    if conf and "confidence_of_fix" in sev and sev["confidence_of_fix"] != conf:
        fail("bands", f"confidence_of_fix scale is {sorted(sev['confidence_of_fix'])} "
                      f"but the canonical table lists {sorted(conf)}")
    checked = 0
    for name, want in sev.items():
        if name == "confidence_of_fix":
            continue
        got = inte.get(name)
        if got is None:
            fail("bands", f"interest.md has no band table for {name}")
            continue
        checked += 1
        if got != want:
            fail("bands", f"{name}: SEVERITY fixes {sorted(want)}, "
                          f"interest.md scores {sorted(got)}")
    if checked == 0:
        fail("bands", "no operand was compared — the checker has stopped checking anything")
    return checked


EXAMPLE = re.compile(
    r"interest\s*=\s*\(\s*([\d.]+)\s*×\s*([\d.]+)\s*×\s*([\d.]+)\s*\)\s*/\s*([\d.]+)\s*≈\s*([\d.]+)")


def check_examples(conf: set[str]) -> int:
    n = 0
    for a, b, c, d, claimed in EXAMPLE.findall(INTEREST.read_text()):
        n += 1
        actual = (float(a) * float(b) * float(c)) / float(d)
        # the page reports to two significant figures
        digits = len(claimed.replace(".", "").lstrip("0")) or 1
        rounded = float(f"%.{digits}g" % actual)
        if rounded != float(claimed):
            fail("worked example",
                 f"({a} × {b} × {c}) / {d} = {actual:.4f}, "
                 f"which to {digits} s.f. is {rounded}, not {claimed}")
        if conf and d not in conf:
            fail("worked example",
                 f"divisor {d} is not one of SEVERITY's canonical values {sorted(conf)}")
    if n == 0:
        fail("worked example", "no worked example matched — "
                               "the checker has stopped checking anything")
    return n


# ---------------------------------------------------------------- git behaviour


class Repo:
    """A throwaway history with a known-good root and a known-bad tip."""

    def __init__(self, d: pathlib.Path):
        self.d = d
        self.git("init", "-q")
        self.git("config", "user.email", "check@example.invalid")
        self.git("config", "user.name", "check")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(("git", *args), cwd=self.d,
                              capture_output=True, text=True)

    def out(self, *args: str) -> str:
        r = self.git(*args)
        return (r.stdout + r.stderr).strip()

    def commit(self, name: str, body: str, msg: str) -> None:
        (self.d / name).write_text(body)
        self.git("add", "-A")
        self.git("commit", "-qm", msg)


EXIT_ROW = re.compile(r"^\|\s*(`\d+`[^|]*)\|\s*([^|]+?)\s*\|", re.M)
CODE = re.compile(r"`(\d+)`")
VERDICT = re.compile(r"[a-z]+")
CEILING = 128          # the table's last row is open-ended; 128 stands for all of it


def verdict_of(cell: str) -> str:
    """The verdict word, without the emphasis and the parenthetical after it."""
    m = VERDICT.search(cell.lower())
    return m.group(0) if m else cell.strip()


def exit_table() -> list[tuple[range, str]]:
    """Each row as (the codes it claims, the verdict word)."""
    rows = []
    for spec, cell in EXIT_ROW.findall(BISECTION.read_text()):
        codes = [int(c) for c in CODE.findall(spec)]
        if not codes:
            continue
        word = verdict_of(cell)
        if "–" in spec and len(codes) == 2:                 # `1`–`124`
            rows.append((range(codes[0], codes[1] + 1), word))
        elif "+" in spec:                                   # `128`+
            rows.append((range(codes[0], CEILING + 1), word))
        else:                                               # `125`, or `126`, `127`
            for c in codes:
                rows.append((range(c, c + 1), word))
    if not rows:
        fail("bisect", "no exit-code table found in bisection.md — "
                       "the checker has stopped checking anything")
    return rows


def check_table_covers(rows: list[tuple[range, str]]) -> None:
    """Every status a predicate can return must land in exactly one row.

    Without this, narrowing a row passes: the checker would dutifully test the
    ends the page now names and agree with itself. A gap is what catches it.
    """
    seen: dict[int, str] = {}
    for codes, word in rows:
        for c in codes:
            if c in seen:
                fail("bisect", f"exit {c} is claimed by both {seen[c]!r} and {word!r}")
            seen[c] = word
    missing = [c for c in range(CEILING + 1) if c not in seen]
    if missing:
        fail("bisect", f"the exit table says nothing about {len(missing)} status(es) "
                       f"a predicate can return, starting at {missing[0]}")


def observed(repo: Repo, good: str, bad: str, code: int) -> str:
    """What git actually did with a predicate that exits `code`."""
    repo.git("bisect", "start", bad, good)
    try:
        r = repo.git("bisect", "run", "sh", "-c", f"exit {code}")
        text = r.stdout + r.stderr
        if "bogus exit code" in text or "is < 0 or >= 128" in text:
            return "abort"
        if "cannot bisect more" in text:
            # every commit skipped: nothing is left to test, which is what a
            # predicate that always says "untestable" should produce
            return "skip"
        if "first bad commit" in text:
            return "bad"
        return f"unrecognised (rc={r.returncode})"
    finally:
        repo.git("bisect", "reset")


def check_exit_table(tmp: pathlib.Path) -> int:
    (tmp / "bisect").mkdir(parents=True)
    repo = Repo(tmp / "bisect")
    for i in range(6):
        repo.commit("f.txt", f"{i}\n", f"c{i}")
    good = repo.out("rev-list", "--max-parents=0", "HEAD")
    bad = repo.out("rev-parse", "HEAD")

    rows = exit_table()
    check_table_covers(rows)
    n = 0
    for codes, want in rows:
        # both ends of a range, so that widening one cannot pass either
        for code in sorted({codes[0], codes[-1]}):
            if code == 0:
                continue      # "good" everywhere is not a bisect, it is an error
            n += 1
            got = observed(repo, good, bad, code)
            if got != want:
                fail("bisect", f"a predicate exiting {code} is read as {got!r}, "
                               f"but the exit table says {want!r}")
    return n


def check_execute_bit(tmp: pathlib.Path) -> int:
    """The page's advice rests on a script without +x exiting 126."""
    claimed = re.search(r"the shell returns (\d+)", BISECTION.read_text())
    if not claimed:
        fail("bisect", "bisection.md no longer states the shell's status for a "
                       "script without its execute bit — the checker has stopped "
                       "checking anything")
        return 0
    script = tmp / "noexec.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o644)
    rc = subprocess.run(["/bin/sh", "-c", str(script)], capture_output=True).returncode
    if rc != int(claimed.group(1)):
        fail("bisect", f"a script without its execute bit exits {rc}, "
                       f"the page states {claimed.group(1)}")
    return 1


FLAKE_ROW = re.compile(r"^\|\s*`K=(\d+)`\s*\|([^\n]*)\|\s*$", re.M)
HEADER_N = re.compile(r"N=(\d+)")
PCT = re.compile(r"([\d.]+)%")


def check_flake_table() -> int:
    """The false-good table is a binomial tail: P(fewer than K of N fail)."""
    text = BISECTION.read_text()
    rate = re.search(r"At `p = ([\d.]+)`", text)
    header = re.search(r"^\|\s*K \(threshold\)\s*\|([^\n]*)\|\s*$", text, re.M)
    if not (rate and header):
        fail("false-good", "no `p = ...` or no N header row in bisection.md — "
                           "the checker has stopped checking anything")
        return 0
    p_fail = float(rate.group(1))
    ns = [int(x) for x in HEADER_N.findall(header.group(1))]
    checked = 0
    for k, cells in FLAKE_ROW.findall(text):
        claims = PCT.findall(cells)
        if len(claims) != len(ns):
            fail("false-good", f"K={k} has {len(claims)} cells for {len(ns)} N columns")
            continue
        for n, claimed in zip(ns, claims):
            checked += 1
            actual = sum(math.comb(n, i) * p_fail**i * (1 - p_fail)**(n - i)
                         for i in range(int(k))) * 100
            digits = len(claimed.replace(".", "").lstrip("0")) or 1
            if float(f"%.{digits}g" % actual) != float(claimed):
                fail("false-good",
                     f"K={k}, N={n} at p={p_fail}: P(fewer than {k} of {n} fail) "
                     f"= {actual:.2f}%, not {claimed}%")
    if checked == 0:
        fail("false-good", "no cell was recomputed — the checker has stopped checking anything")
    return checked


def check_pickaxe(tmp: pathlib.Path) -> int:
    """extraction.md: --reverse|head -1 is the oldest match, -1 is the newest,
    and -S fires on a drop in occurrences as well as a rise."""
    d = tmp / "pickaxe"
    d.mkdir(parents=True)
    repo = Repo(d)
    repo.commit("g.txt", "alpha beta\n", "first")
    repo.commit("g.txt", "alpha beta alpha\n", "second")
    repo.commit("g.txt", "alpha\n", "drop")

    text = EXTRACTION.read_text()
    if "--reverse" not in text or '-S"<test name>"' not in text:
        fail("pickaxe", "extraction.md no longer shows the `--reverse ... -S` recipe — "
                        "the checker has stopped checking anything")
        return 0

    oldest = repo.out("log", "--reverse", "--format=%s", "-S", "alpha", "--", "g.txt")
    oldest = oldest.splitlines()[0] if oldest else ""
    newest = repo.out("log", "-1", "--format=%s", "-S", "alpha", "--", "g.txt")
    if oldest != "first":
        fail("pickaxe", f"`--reverse | head -1` returned {oldest!r}, not the oldest match")
    if newest != "drop":
        fail("pickaxe", f"`-1` returned {newest!r}, not the newest match")
    if newest == oldest:
        fail("pickaxe", "`--reverse | head -1` and `-1` returned the same commit; "
                        "the distinction the page draws no longer exists")
    hits = repo.out("log", "--format=%s", "-S", "alpha", "--", "g.txt").splitlines()
    if "drop" not in hits:
        fail("pickaxe", "`-S` did not fire on the commit that reduced the occurrence "
                        "count; the page warns that it does")
    return 3


def check_shortstat(tmp: pathlib.Path) -> int:
    """extraction.md: field 4 is insertions, and becomes deletions on a
    deletion-only diff — which is why PR size is not derived from it."""
    d = tmp / "shortstat"
    d.mkdir(parents=True)
    repo = Repo(d)
    repo.commit("f.txt", "a\nb\nc\n", "add")
    repo.commit("f.txt", "a\n", "delete only")
    line = repo.out("show", "--shortstat", "--format=", "HEAD").splitlines()[-1]
    fields = line.split()          # "1 file changed, 2 deletions(-)" -> field 4 is "2"
    if len(fields) < 5:
        fail("shortstat", f"`--shortstat` printed {line!r}, which has no field 4")
        return 0
    if not fields[3].isdigit() or "deletion" not in fields[4]:
        fail("shortstat", f"a deletion-only diff printed {line!r}; the page states "
                          "field 4 is a count and what follows it is deletions")
    if "insertion" in line:
        fail("shortstat", f"a deletion-only diff printed {line!r} — it reports "
                          "insertions, so the page's warning no longer applies")
    return 1


def main() -> int:
    check_formula()
    operands = check_bands()
    examples = check_examples(confidence_values())
    cells = check_flake_table()

    if shutil.which("git"):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="quality-figures-"))
        try:
            codes = check_exit_table(tmp)
            bits = check_execute_bit(tmp)
            pick = check_pickaxe(tmp)
            stat = check_shortstat(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        version = subprocess.run(["git", "--version"], capture_output=True,
                                 text=True).stdout.strip()
        ran = f", {codes + bits + pick + stat} git behaviours re-run against {version}"
    else:
        ran = ", git not installed so its behaviours went unchecked"

    if failures:
        print(f"{len(failures)} problem(s):")
        print("\n".join(failures))
        return 1
    print(f"figures green - formula agrees across 2 files, {operands} band scales "
          f"matched, {examples} worked examples recomputed, {cells} false-good "
          f"cells recomputed{ran}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
