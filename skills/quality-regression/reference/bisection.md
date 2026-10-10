<!-- quality:deferred -->
# Bisection — Locating the Culprit

Purpose: Narrowing to the change that did it, including when the range is not clean.
Read when: finding the culprit commit.
Source: git, pytest, jest, cargo, go test — the bisect mechanics and the exit codes are theirs.
Verified: 2026-10-10 — the exit table, the false-good table and its compounding are re-run and recomputed by `make figures`; the runner table by running pytest, jest, go test and cargo test.

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
| `126`, `127` | **bad** — after one check, below | never deliberately: these are the shell reporting on the script, not the script reporting on the code |
| `126`, `127` on the first step and again on the good revision | **abort** — `error: bogus exit code N for good revision` | nothing: the script cannot run at all (no execute bit, wrong path) |
| `128`+ | **abort the bisect** | the predicate itself is broken |

`126` and `127` are bad, as git's manual says: "normal errors in the script, as far as bisect run
is concerned". The one check is on the **first** step only: if it returns 126 or 127, git re-runs
the predicate on the good revision and aborts only if that returns the same code. Otherwise — the
good revision passes, or the 126 first appears on a later step — it is a bad verdict like any
other, and a predicate that loses a helper command partway through the range names a wrong culprit
in silence. Both rows are re-run by `make figures`.

The trap is the second row, and it is quiet. A usage error, a collection error, or a
missing test file lands inside `1`–`124` alongside a genuine assertion failure, and git will
happily call the first commit it looked at the culprit. Never let the runner's raw status reach
git:

```sh
#!/bin/sh
# bisect-predicate.sh — see the exit table above
<build command, test code included> >/dev/null 2>&1 || exit 125   # unbuildable: skip, do not mark bad
<check the one test exists here> >/dev/null 2>&1 || exit 125       # not written yet: skip
<test command selecting the one test> >/dev/null 2>&1
status=$?
case $status in
  0) exit 0 ;;                       # passed
  <runner's failure status>) exit 1 ;;   # failed — after the two lines above, nothing else is left
  4|5) exit 125 ;;                   # pytest: node id not found (4), nothing collected (5)
  *) echo "predicate broken: status $status" >&2; exit 128 ;;
esac
```

The two guard lines exist because the runners' statuses cannot do this job alone — re-run
against pytest, jest, go test and cargo test:

| Runner | Fails with | Also exits that for | Selects nothing → | Build / exists |
|--------|-----------|---------------------|-------------------|----------------|
| pytest | `1` | a fixture or setup error | `4` missing node id, `5` `-k` matched nothing (a collection error is `2`) | `pytest --collect-only -q <node id>` exits `4` when absent |
| jest | `1` | no test file matching the path; a file that fails to parse | `0` when `-t` matches nothing | grep the file for the test name — `--listTests` lists files, not tests |
| go test | `1` | a compile failure | `0` — `-run` matching nothing passes | build `go test -run '^$' <pkg>`; exists `go test -list '^TestX$' <pkg> \| grep -qx TestX` |
| cargo test | `101` | a compile failure | `0` — a filter matching nothing passes | build `cargo test --no-run`; exists `cargo test -- --list --exact <path> \| grep -q ': test$'` |

A filter that selects nothing exits `0` on go test, cargo test and jest's `-t`: without the exists
line, every commit before the test was written is good, and when the defect predates the test the
bisect blames the commit that added it instead of saying so. A pytest setup error is `1`, the same as a failure — read the output (`-rE`) when the fixture is
what changed. Do **not** use `set -e` here: it exits on the first non-zero status and destroys the
branching the whole script exists for. Replace the placeholder with the invocation your runner
actually accepts — `--filter` is not a universal flag (`pytest -k`, `jest -t`, `go test -run`,
`cargo test --`).

```
git bisect start <known-bad> <known-good>
git bisect run sh ./bisect-predicate.sh
git bisect reset
```

Invoke it as `sh ./bisect-predicate.sh`, or `chmod +x` it first. A freshly written script has no
execute bit and the shell returns 126 on every revision, the good one included, so the first-step
check stops the bisect with `error: bogus exit code 126 for good revision`. That is the loud failure
and the cheap one. The expensive one is the status that only some revisions produce — a runner
that exits `2` on a usage error, a `127` from a tool that does not exist yet: both are inside the
bad range, so nothing complains and the answer is wrong.

## Intermittent failures need repetition in the predicate

A test failing 1 in 5 will mark good commits as good by luck. Run it N times and threshold:

```sh
#!/bin/sh
# unset, the loop runs zero times and every commit is good; `${N:?}` is no
# guard either — dash exits 2 on it, which git reads as bad
[ -n "$N" ] && [ -n "$K" ] || { echo "set N and K" >&2; exit 128; }
<build command, test code included> >/dev/null 2>&1 || exit 125
<check the one test exists here> >/dev/null 2>&1 || exit 125
fails=0
for i in $(seq 1 "$N"); do
  <test command selecting the one test> >/dev/null 2>&1
  status=$?
  case $status in
    0) ;;
    <runner's failure status>) fails=$((fails+1)) ;;
    *) echo "predicate broken: status $status" >&2; exit 128 ;;   # infra, not a failure: never counted
  esac
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
already evidence and this is the row that reaches usable confidence at a practical N. Raise K
only when the runner produces unrelated spurious failures you cannot separate by exit status, and
then pay for it with N: at `K=3` you need N≥46 to get under 15%.

**The table is per tested commit, and a bisect tests several.** Every step that lands on a bad
commit is another chance to call it good, and one such error sends the search into the wrong half.
With `q` the table's cell for your K and N and `b` bad-commit steps, P(wrong culprit) ≈
1 − (1 − q)^b. A 100-commit range takes up to
⌈log2 100⌉ = 7 steps, all of them on bad commits at worst — at `K=1`, N=20: `1 − (1 − 0.12)^7 ≈ 59%`, and at N=46:
`1 − (1 − 0.008)^7 ≈ 5.5%`. Size N for the whole bisect, not for one run.

Measure `p` first (`triage.md` § Reproduction quality). Choosing N without it is guesswork, and a
bisect run at the wrong N returns a wrong answer with no indication that it did.

## Establishing known-good

- The last release tag that was verified working is better than "a week ago".
- If no known-good exists, bisect the *appearance in CI* instead: find the last green CI run and the first red one, and bisect between the commits they built. Pushes are batched, so the two are rarely parent and child — the range between them is what bisect is for.
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
