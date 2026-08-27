<!-- quality:deferred -->
# Bisection — Locating the Culprit

Purpose: Narrowing to the change that did it, including when the range is not clean.
Read when: finding the culprit commit.
Source: git, pytest, jest, cargo, go test — the bisect mechanics and the exit codes are theirs.
Verified: 2026-08-21 — the exit table and the false-good table are re-run and recomputed by `make figures`.

Read during `LOCATE`. Bisection is fast and reliable when the predicate is scripted, and
confidently wrong when it is not.

---

## Precondition: a scripted predicate

Never bisect by running the test and eyeballing it. Write a script whose exit status means exactly
one thing to git, and nothing else:

| Exit | git reads it as | Use for |
|------|-----------------|---------|
| `0` | good | the test passed |
| `1`–`124` | **bad** | the test failed its assertion — and nothing else |
| `125` | skip | this commit cannot be tested (won't build, test doesn't exist yet) |
| `126`, `127` | **abort** — `error: bogus exit code` | never deliberately: these are the shell reporting on the script, not the script reporting on the code |
| `128`+ | **abort the bisect** | the predicate itself is broken |

git's own manual disagrees with git here — it says to exit "between 1 and 127
(inclusive), except 125" for bad, and calls 126 and 127 "normal errors in the
script, as far as bisect run is concerned". The binary rejects both. The table
above is what the installed git does, re-run by `make figures`; where the two
disagree, trust the table.

The trap is the second row, and it is quiet. A usage error, a collection error, or a
missing test file lands inside `1`–`124` alongside a genuine assertion failure, and git will
happily call the first commit it looked at the culprit. Never let the runner's raw status reach
git:

```sh
#!/bin/sh
# bisect-predicate.sh — see the exit table above
<build command> >/dev/null 2>&1 || exit 125   # unbuildable: skip, do not mark bad
<test command selecting the one test> >/dev/null 2>&1
status=$?
case $status in
  0) exit 0 ;;                       # passed
  <runner's assertion-failure status>) exit 1 ;;   # genuinely failed — e.g. 1 for pytest, 1 for jest
  5) exit 125 ;;                     # pytest: no tests collected — the test does not exist here
  *) echo "predicate broken: status $status" >&2; exit 128 ;;
esac
```

Do **not** use `set -e` here: it exits on the first non-zero status and destroys the branching the
whole script exists for. Replace the placeholder with the invocation your runner actually accepts
— `--filter` is not a universal flag (`pytest -k`, `jest -t`, `go test -run`, `cargo test --`).

```
git bisect start <known-bad> <known-good>
git bisect run sh ./bisect-predicate.sh
git bisect reset
```

Invoke it as `sh ./bisect-predicate.sh`, or `chmod +x` it first. A freshly written script has no
execute bit and the shell returns 126, which stops the bisect with `error: bogus exit code 126`.
That is the loud failure and the cheap one. The expensive one is the runner that exits `2` on a
usage error: `2` is inside the bad range, so nothing complains and the answer is wrong.

## Intermittent failures need repetition in the predicate

A test failing 1 in 5 will mark good commits as good by luck. Run it N times and threshold:

```sh
#!/bin/sh
<build command> >/dev/null 2>&1 || exit 125
fails=0
for i in $(seq 1 "$N"); do
  <test command selecting the one test> >/dev/null 2>&1 || fails=$((fails+1))
done
[ "$fails" -ge "$K" ] && exit 1
exit 0
```

**N and K are chosen together, and K drives the cost.** With failure rate `p`, a commit is falsely
called good when fewer than `K` of `N` runs fail. At `p = 0.10`:

| K (threshold) | N=5 | N=20 | N=46 | N=60 |
|---------------|-----|------|------|------|
| `K=1` | 59% | 12% | 0.8% | 0.2% |
| `K=3` | 99% | 68% | 15% | 5% |

`K=1` — mark bad on a single observed failure — is the right default, because a genuine failure is
already evidence and this is the column that reaches usable confidence at a practical N. Raise K
only when the runner produces unrelated spurious failures you cannot separate by exit status, and
then pay for it with N: at `K=3` you need N≥46 to get under 15%.

Measure `p` first (`triage.md` § Reproduction quality). Choosing N without it is guesswork, and a
bisect run at the wrong N returns a wrong answer with no indication that it did.

## Establishing known-good

- The last release tag that was verified working is better than "a week ago".
- If no known-good exists, bisect the *appearance in CI* instead: find the first CI run that shows the failure, and bisect between its parent and it.
- If the test itself is new, there is nothing to bisect — the defect predates the test. Reclassify as `PREEXISTING-DEFECT` (`_quality/SEVERITY.md` §5) and route the fix directly.

## Reading the culprit

The first bad commit is where the failure **became visible**, which is not always where the defect
is. Before assigning blame:

| The culprit is a… | Consider |
|-------------------|----------|
| dependency bump | the changelog is your oracle; the defect may be an intentional upstream change |
| refactor with no behaviour change | it exposed a latent defect by reordering or re-timing something |
| config or flag change | the defect is in code that was already there; the flag revealed it |
| test-infrastructure change | parallelism, ordering, or fixture change surfaced a pre-existing `FLAKY-ORDER` |
| genuine logic change | the ordinary case — route the diff to `quality-review` |

Say which of these it is in the deliverable. "Commit abc123 broke it" without this distinction
leads to a revert that does not fix the defect.

## When bisection is the wrong tool

- **History is squashed or rebased** — the granularity is a whole feature; bisect to the merge, then read the diff.
- **The failure depends on data, not code** — bisect finds nothing; the variable is the environment.
- **Both branches of the range are red for different reasons** — clean the other failure first, or bisect with a predicate that distinguishes them.
- **The range is under ~10 commits** — reading the diffs is faster than scripting the predicate.

## Deliverable

```
CULPRIT:    <sha> — <subject>
RANGE:      <good sha>..<bad sha>  (N commits)
PREDICATE:  <the script, verbatim>
CONFIDENCE: CONFIRMED (deterministic) | LIKELY (thresholded over N runs)
MECHANISM:  <why this commit produces the failure, in one sentence>
LATENT?:    <yes/no — did this commit create the defect or expose it?>
```
