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

* every row of the exit-code table, by running a bisect whose predicate passes
  on the good side and returns that code on the bad side, and reading what git
  did with it — including which commit it then blamed
* the first-step guard row, by a predicate that returns the code everywhere,
  good revision included: the only case in which git aborts on 126 or 127
* that a script without its execute bit exits 126, which the page's advice rests on
* the false-good table, recomputed as a binomial tail
* the compounding example: the step count as ⌈log2 range⌉, and each
  `1 − (1 − q)^b` the page works out

Extraction — `quality-metrics/reference/extraction.md`, against the installed git:

* `--reverse | head -1` is the oldest pickaxe match and `-1` is the newest
* `-S` fires when an occurrence count drops, not only when it rises
* `--shortstat` field 4 counts deletions on a deletion-only diff

The interest and bisection claims are parsed out of the page rather than restated
here, so a page edited to say something false fails as loudly as a tool that
changed underneath it. The extraction checks re-run the git behaviours the page
rests on, and hold its pickaxe recipe to the one line that reads the oldest match;
the prose around that line is not parsed.
"""
import math
import os
import pathlib
import re
import shlex
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

# Run from the pre-commit hook, git exports GIT_DIR and GIT_INDEX_FILE; inherited,
# they point the throwaway `git init`/`commit` below at the developer's own
# repository. Every git here sees only its own tree, and no user or system config
# can change what it prints.
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
# LC_ALL: the strings matched below are translated in a gettext build of git.
GIT_ENV.update(LC_ALL="C", LANGUAGE="",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME="check", GIT_AUTHOR_EMAIL="check@example.invalid",
               GIT_COMMITTER_NAME="check", GIT_COMMITTER_EMAIL="check@example.invalid")


def fail(where: str, msg: str) -> None:
    failures.append(f"  {where}: {msg}")


FORMULA = re.compile(r"^interest\s*=.*$", re.M)


def check_formula() -> str:
    a = FORMULA.findall(SEVERITY.read_text(encoding="utf-8"))
    # interest.md's worked examples carry digits; check_examples recomputes
    # them, and fails on any digit-bearing line that does not parse as one.
    b = [l for l in FORMULA.findall(INTEREST.read_text(encoding="utf-8"))
         if not re.search(r"\d", l)]
    if not a or not b:
        fail("formula", "no `interest = ...` line found in "
                        f"{'SEVERITY.md' if not a else 'interest.md'} — "
                        "the checker has stopped checking anything")
        return ""
    # Every statement of it, not the first: a second one further down that
    # disagrees is a second formula. SEVERITY.md has no worked examples, so
    # every line there is a statement, digits or not.
    for page, lines in (("SEVERITY.md", a), ("interest.md", b)):
        for line in lines:
            if line.strip() != a[0].strip():
                fail("formula", f"SEVERITY.md says {a[0].strip()!r}, "
                                f"{page} says {line.strip()!r}")
    return a[0].strip()


NUM = re.compile(r"\d+\.\d+")
ORDERED = ("touch_score", "blast_score", "comprehension_score")
OPERAND_ROW = re.compile(r"^\|\s*`(\w+_score|confidence_of_fix)`\s*\|[^|]*\|([^|]*)\|", re.M)
BAND_TABLE = re.compile(r"^\|[^|]*\|\s*(\d+\.\d+)\s*(?:—[^|]*)?\|\s*$", re.M)


def severity_bands() -> dict[str, set[str]]:
    out = {}
    for name, scale in OPERAND_ROW.findall(SEVERITY.read_text(encoding="utf-8")):
        vals = NUM.findall(scale)
        if vals:
            out[name] = vals
    if len(out) != 4:
        fail("bands", f"SEVERITY.md defines {len(out)} operands, expected 4 — "
                      "the band-scale table has changed shape")
    return out


def interest_bands() -> dict[str, set[str]]:
    """Each `## Input n — <operand>` section owns the band table under it."""
    text = INTEREST.read_text(encoding="utf-8")
    sections = re.split(r"^## ", text, flags=re.M)
    out = {}
    for s in sections:
        m = re.match(r"Input \d+ — (\w+)", s)
        if not m:
            continue
        vals = BAND_TABLE.findall(s)
        if vals:
            out[m.group(1)] = vals
    return out


def confidence_values() -> set[str]:
    """SEVERITY's canonical divisor table."""
    text = SEVERITY.read_text(encoding="utf-8")
    block = text.split("canonical values.")[-1]
    rows = re.findall(r"^\|\s*[^|]+\|\s*(\d+\.\d+)\s*\|", block, re.M)
    if not rows:
        fail("confidence", "no canonical divisor table found — "
                           "the checker has stopped checking anything")
    return set(rows)


def check_bands() -> int:
    sev, inte = severity_bands(), interest_bands()
    conf = confidence_values()
    if "confidence_of_fix" in inte:
        # interest.md says not to restate them: a second table is a second rubric.
        fail("bands", f"interest.md restates confidence_of_fix as {inte['confidence_of_fix']}; "
                      "its values live only in SEVERITY.md §4")
    if conf and "confidence_of_fix" in sev and set(sev["confidence_of_fix"]) != conf:
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
            fail("bands", f"{name}: SEVERITY fixes {want}, top to bottom, "
                          f"interest.md scores {got}")
    if checked == 0:
        fail("bands", "no operand was compared — the checker has stopped checking anything")
    return checked


# A number, not a run of digits and dots: a sentence's full stop is not a decimal.
_N = r"(\d+(?:\.\d+)?)"
EXAMPLE = re.compile(
    rf"interest\s*=\s*\(\s*{_N}\s*×\s*{_N}\s*×\s*{_N}\s*\)\s*/\s*{_N}\s*≈\s*{_N}")


ARROW = re.compile(r"→\s*(\d+\.\d+)")


def check_examples(conf: set[str]) -> int:
    n = 0
    text = INTEREST.read_text(encoding="utf-8")
    bands = interest_bands()
    stated = [l for l in FORMULA.findall(text) if re.search(r"\d", l)]
    found = EXAMPLE.findall(text)
    if len(found) != len(stated):
        fail("worked example", f"{len(stated)} `interest = <numbers>` lines, but only "
                               f"{len(found)} parse; an unparsed one is not checked")
    for block in re.findall(r"```(.*?)```", text, re.S):
        m = EXAMPLE.search(block)
        if m and ARROW.findall(block) != list(m.groups()[:4]):
            fail("worked example", f"the arrows give {ARROW.findall(block)}, "
                                   f"the formula line uses {list(m.groups()[:4])}")
    for a, b, c, d, claimed in found:
        for name, v in zip(ORDERED, (a, b, c)):
            if name in bands and v not in bands[name]:
                fail("worked example", f"{name} {v} is not one of its bands {bands[name]}")
        n += 1
        if conf and d not in conf:
            fail("worked example",
                 f"divisor {d} is not one of SEVERITY's canonical values {sorted(conf)}")
        if float(d) == 0:
            continue                      # not canonical, so reported above; nothing to recompute
        actual = (float(a) * float(b) * float(c)) / float(d)
        # the page reports to two significant figures
        digits = len(claimed.replace(".", "").lstrip("0")) or 1
        rounded = float(f"%.{digits}g" % actual)
        if rounded != float(claimed):
            fail("worked example",
                 f"({a} × {b} × {c}) / {d} = {actual:.4f}, "
                 f"which to {digits} s.f. is {rounded}, not {claimed}")
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
        return subprocess.run(("git", *args), cwd=self.d, env=GIT_ENV,
                              capture_output=True, text=True)

    def out(self, *args: str) -> str:
        r = self.git(*args)
        return (r.stdout + r.stderr).strip()

    def commit(self, name: str, body: str, msg: str) -> None:
        (self.d / name).write_text(body, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", msg)


EXIT_ROW = re.compile(r"^\|\s*(`\d+`[^|]*)\|\s*([^|]+?)\s*\|", re.M)
CODE = re.compile(r"`(\d+)`")
VERDICT = re.compile(r"[a-z]+")
CEILING = 128          # the table's last row is open-ended; 128 stands for all of it
# A row whose codes cell names the good revision is the first-step guard: git
# re-runs the predicate there and aborts only when it returns the same code.
# It qualifies another row rather than claiming codes of its own.
GUARD = "good revision"
BOUNDARY = 1           # the first commit the non-constant predicate calls bad


def verdict_of(cell: str) -> str:
    """The verdict word, without the emphasis and the parenthetical after it."""
    m = VERDICT.search(cell.lower())
    return m.group(0) if m else cell.strip()


def exit_table() -> tuple[list[tuple[range, str]], list[tuple[int, str]]]:
    """The ordinary rows as (the codes they claim, the verdict word), and the
    first-step guard rows as (code, verdict word)."""
    rows, guards = [], []
    for spec, cell in EXIT_ROW.findall(BISECTION.read_text(encoding="utf-8")):
        codes = [int(c) for c in CODE.findall(spec)]
        if not codes:
            continue
        word = verdict_of(cell)
        if GUARD in spec:
            guards.extend((c, word) for c in codes)
        elif "–" in spec and len(codes) == 2:               # `1`–`124`
            rows.append((range(codes[0], codes[1] + 1), word))
        elif "+" in spec:                                   # `128`+
            rows.append((range(codes[0], CEILING + 1), word))
        else:                                               # `125`, or `126`, `127`
            for c in codes:
                rows.append((range(c, c + 1), word))
    for codes, word in rows:
        if not codes:
            fail("bisect", f"the {word!r} row names an empty range of exit codes")
    rows = [(c, w) for c, w in rows if c]
    if not rows:
        fail("bisect", "no exit-code table found in bisection.md — "
                       "the checker has stopped checking anything")
    if not guards:
        fail("bisect", "the exit table has no first-step guard row (codes on the "
                       f"{GUARD!r}) — the execute-bit advice rests on it, and "
                       "nothing would notice it going wrong")
    return rows, guards


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


def observed(repo: Repo, good: str, bad: str, code: int, everywhere: bool) -> str:
    """What git actually did with a predicate that exits `code`.

    By default the predicate passes on the good side and returns `code` from
    commit BOUNDARY on, which is what a real one does. A predicate that returns
    the same code everywhere cannot tell 126 read as bad from 126 aborted: it
    fails on the good revision too, which is exactly the case git's first-step
    guard aborts on. `everywhere` runs that case, for the guard row only.
    """
    script = (f"exit {code}" if everywhere else
              f'[ "$(cat f.txt)" -ge {BOUNDARY} ] && exit {code}; exit 0')
    repo.git("bisect", "start", bad, good)
    try:
        r = repo.git("bisect", "run", "sh", "-c", script)
        text = r.stdout + r.stderr
        if "bogus exit code" in text or "is < 0 or >= 128" in text:
            return "abort"
        if "cannot bisect more" in text:
            # every bad-side commit skipped: nothing is left to test, which is
            # what a predicate that says "untestable" there should produce
            return "skip"
        # git 2.43 prints "is the first bad commit"; later versions quote the
        # term: "is the first 'bad' commit".
        m = re.search(r"(\w+) is the first '?bad'? commit", text)
        if m:
            subject = repo.out("log", "-1", "--format=%s", m.group(1))
            want = f"c{BOUNDARY}"
            if not everywhere and subject != want:
                return f"bad, but blamed {subject} rather than {want}"
            return "bad"
        return f"unrecognised (rc={r.returncode})"
    finally:
        repo.git("bisect", "reset")


def observed_good(repo: Repo, good: str, bad: str) -> str:
    """Exit 0 below the tip, 1 at it: if 0 reads as good, the tip is blamed."""
    repo.git("bisect", "start", bad, good)
    try:
        r = repo.git("bisect", "run", "sh", "-c",
                     '[ "$(cat f.txt)" -ge 5 ] && exit 1; exit 0')
        m = re.search(r"(\w+) is the first '?bad'? commit", r.stdout + r.stderr)
        if m and repo.out("log", "-1", "--format=%s", m.group(1)) == "c5":
            return "good"
        return f"not good (rc={r.returncode})"
    finally:
        repo.git("bisect", "reset")


def check_exit_table(tmp: pathlib.Path) -> int:
    (tmp / "bisect").mkdir(parents=True)
    repo = Repo(tmp / "bisect")
    for i in range(6):
        repo.commit("f.txt", f"{i}\n", f"c{i}")
    good = repo.out("rev-list", "--max-parents=0", "HEAD")
    bad = repo.out("rev-parse", "HEAD")

    rows, guards = exit_table()
    check_table_covers(rows)
    guarded = dict(guards)
    n = 0
    for codes, want in rows:
        # both ends of a range, so that widening one cannot pass either
        for code in sorted({codes[0], codes[-1]}):
            n += 1
            if code == 0:
                # read as good, a predicate that fails only on the tip blames the tip
                got = observed_good(repo, good, bad)
            else:
                got = observed(repo, good, bad, code, everywhere=False)
            if got != want:
                fail("bisect", f"a predicate exiting {code} on the bad side only is "
                               f"read as {got!r}, but the exit table says {want!r}")
            if code and code not in guarded:
                # the guard row must name every code git aborts on everywhere
                got = observed(repo, good, bad, code, everywhere=True)
                if got == "abort" and want != "abort":
                    fail("bisect", f"a predicate exiting {code} on every revision aborts, "
                                   "but the guard row does not name it")
    for code, want in guards:
        n += 1
        got = observed(repo, good, bad, code, everywhere=True)
        if got != want:
            fail("bisect", f"a predicate exiting {code} on every revision, the good "
                           f"one included, is read as {got!r}, but the guard row "
                           f"says {want!r}")
    return n


def check_execute_bit(tmp: pathlib.Path) -> int:
    """The page's advice rests on a script without +x exiting 126."""
    claimed = re.search(r"the shell returns (\d+)", BISECTION.read_text(encoding="utf-8"))
    if not claimed:
        fail("bisect", "bisection.md no longer states the shell's status for a "
                       "script without its execute bit — the checker has stopped "
                       "checking anything")
        return 0
    script = tmp / "noexec.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o644)
    rc = subprocess.run(["/bin/sh", "-c", shlex.quote(str(script))], env=GIT_ENV,
                        capture_output=True).returncode
    if rc != int(claimed.group(1)):
        fail("bisect", f"a script without its execute bit exits {rc}, "
                       f"the page states {claimed.group(1)}")
    return 1


FLAKE_ROW = re.compile(r"^\|\s*`K=(\d+)`\s*\|([^\n]*)\|\s*$", re.M)
HEADER_N = re.compile(r"N=(\d+)")
PCT = re.compile(r"([\d.]+)%")


def check_flake_table() -> int:
    """The false-good table is a binomial tail: P(fewer than K of N fail)."""
    text = BISECTION.read_text(encoding="utf-8")
    rate = re.search(r"At `p = ([\d.]+)`", text)
    header = re.search(r"^\|\s*K \(threshold\)\s*\|([^\n]*)\|\s*$", text, re.M)
    if not (rate and header):
        fail("false-good", "no `p = ...` or no N header row in bisection.md — "
                           "the checker has stopped checking anything")
        return 0
    p_fail = float(rate.group(1))
    ns = [int(x) for x in HEADER_N.findall(header.group(1))]
    checked = 0
    loose = re.findall(r"^\|[^|\n]*K=\d+[^|\n]*\|", text, re.M)
    if len(loose) != len(FLAKE_ROW.findall(text)):
        fail("false-good", f"{len(loose)} K= rows, but only {len(FLAKE_ROW.findall(text))} "
                           "parse; an unparsed row is not checked")
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


STEPS = re.compile(r"⌈log2 (\d+)⌉ = (\d+)")
COMPOUND = re.compile(r"1 − \(1 − ([\d.]+)\)\^(\d+) ≈ ([\d.]+)%")


def check_compounding() -> int:
    """The table is per tested commit; the page compounds it over a bisect."""
    text = BISECTION.read_text(encoding="utf-8")
    steps, worked = STEPS.findall(text), COMPOUND.findall(text)
    if not steps or not worked:
        fail("compounding", "no `⌈log2 R⌉ = b` or no `1 − (1 − q)^b ≈ x%` in "
                            "bisection.md — the checker has stopped checking anything")
        return 0
    if len(re.findall(r"1\s*[−-]\s*\(1\s*[−-]\s*\d", text)) != len(worked):
        fail("compounding", "a `1 − (1 − q)^b` line does not parse; it is not checked")
    header = re.search(r"^\|\s*K \(threshold\)\s*\|([^\n]*)\|\s*$", text, re.M)
    ns = [int(x) for x in HEADER_N.findall(header.group(1))] if header else []
    table = {(int(k), n): float(c) for k, cells in FLAKE_ROW.findall(text)
             for n, c in zip(ns, PCT.findall(cells))}
    k = None
    cited = re.findall(r"(?:`K=(\d+)`, )?N=(\d+):\s*`1 − \(1 − ([\d.]+)\)", text)
    if len(cited) != len(worked):
        fail("compounding", "a `1 − (1 − q)^b` does not say which K and N its q is from")
    for kk, n, q in cited:
        k = int(kk) if kk else k
        cell = table.get((k, int(n)))
        if cell is None or round(float(q) * 100, 6) != cell:
            fail("compounding", f"q = {q} at K={k}, N={n}, but that cell of the "
                                f"table is {cell}%")
    for r, b in steps:
        if math.ceil(math.log2(int(r))) != int(b):
            fail("compounding", f"⌈log2 {r}⌉ is {math.ceil(math.log2(int(r)))}, not {b}")
    for q, b, claimed in worked:
        actual = (1 - (1 - float(q)) ** int(b)) * 100
        digits = len(claimed.replace(".", "").lstrip("0")) or 1
        if float(f"%.{digits}g" % actual) != float(claimed):
            fail("compounding", f"1 − (1 − {q})^{b} = {actual:.2f}%, not {claimed}%")
        if steps and int(b) != int(steps[0][1]):
            fail("compounding", f"the example compounds over {b} steps; the page "
                                f"derives {steps[0][1]}")
    return len(steps) + len(worked)


def check_pickaxe(tmp: pathlib.Path) -> int:
    """extraction.md: --reverse|head -1 is the oldest match, -1 is the newest,
    and -S fires on a drop in occurrences as well as a rise."""
    d = tmp / "pickaxe"
    d.mkdir(parents=True)
    repo = Repo(d)
    repo.commit("g.txt", "alpha beta\n", "first")
    repo.commit("g.txt", "alpha beta alpha\n", "second")
    repo.commit("g.txt", "alpha\n", "drop")

    text = EXTRACTION.read_text(encoding="utf-8")
    recipe = re.search(r'^git log --reverse\b[^\n]*-S"<test name>"[^\n]*\| head -n 1$', text, re.M)
    if not recipe:
        fail("pickaxe", "extraction.md no longer shows the `git log --reverse ... -S ... | "
                        "head -n 1` recipe — the line whose oldest match the checks below hold")
        return 0
    # git limits before it reverses: `--reverse -1` is the newest match, reversed.
    # The match ends in `| head -n 1`, so the last pipe is the pipeline; an
    # earlier one may sit inside a quoted format.
    if re.search(r"\s(?:-\d+|-n\s*\d+|--max-count\b)", recipe.group(0).rsplit("|", 1)[0]):
        fail("pickaxe", f"the recipe {recipe.group(0)!r} limits the log, and git applies the "
                        "limit before --reverse, so it reads the newest match")

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
    cells = check_flake_table() + check_compounding()

    if shutil.which("git"):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="quality-figures-"))
        try:
            codes = check_exit_table(tmp)
            bits = check_execute_bit(tmp)
            pick = check_pickaxe(tmp)
            stat = check_shortstat(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        version = subprocess.run(["git", "--version"], env=GIT_ENV, capture_output=True,
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
          f"figures recomputed{ran}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
