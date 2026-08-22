<!-- quality:guidance -->
# Boundaries (quality-* pack)

> **Tier:** `spine`. Precedence: `_quality/VALUES.md` § Rule precedence.

Six skills, one domain. This file is the tie-breaker when two of them could plausibly take a task.

**Boundaries are defined in `registry/capabilities.yaml`, not here and not in any
skill's description.** Each entry carries what a skill does, what it does not
(`not:`, with where that work goes instead), and the words that select it.
Writing an exclusion into a description makes every skill added rewrite its
neighbours; keeping it in one file makes an addition cost O(1). The tables below
are a reading of that file — how to tell which case you are in — not a second
copy of it.

The chains that recur are in `registry/routes.yaml`, with their control
structure. Where a stage repeats until a condition holds, the entry carries the
stopping condition, the judge, and a hard cycle limit — and **the judge is never
the skill that produced the thing being judged**.

---

## 1. One-line ownership

| Skill | Owns | Question it answers |
|-------|------|---------------------|
| `quality-gate` | the release decision and the gate that encodes it | *May this ship?* |
| `quality-review` | defects in a specific change | *What is wrong with this diff?* |
| `quality-test` | test design, coverage, and test-suite health | *What is untested, and what should the test be?* |
| `quality-metrics` | measurement, baselines, trends | *Is quality moving, and by how much?* |
| `quality-debt` | accumulated cost and its repayment order | *What should we fix first, and why that?* |
| `quality-regression` | failures over time — regressions, flakes, quarantine | *Why did this break, and what stops it recurring?* |

## 2. The routing rule

Route by **the artifact the user wants back**, not by the words they used.

| The user wants back… | Skill |
|----------------------|-------|
| a GO / NO-GO with conditions | `quality-gate` |
| a list of findings on a diff | `quality-review` |
| new or improved tests | `quality-test` |
| numbers and a trend | `quality-metrics` |
| a prioritized remediation plan | `quality-debt` |
| a root cause for a failing/flaky test | `quality-regression` |

"Improve quality" with no artifact named → `quality-metrics` first. You cannot improve what has no
baseline, and a baseline is cheap. Then `quality-debt` to order the work.

## 3. Boundary pairs that actually collide

| Pair | The line |
|------|----------|
| `review` vs `test` | Review says *"the empty-list case is unhandled"*. Test writes the failing case and the fix's proof. Review never writes the test; test never grades the diff. |
| `review` vs `debt` | Review is scoped to the change. Anything pre-existing that review notices is **handed to debt**, not smuggled into the PR verdict. |
| `test` vs `regression` | Test builds coverage **forward** from a spec. Regression builds it **backward** from an observed failure. A bug report always enters through regression. |
| `metrics` vs `debt` | Metrics owns the measured series — what is trended, snapshotted, and reported — and proposes nothing. Debt proposes and sequences, and takes the one-off inputs its ranking needs (churn, importer counts) directly, because they are single git and grep queries with no trend attached. Debt never establishes or reads a trend; that is metrics' output. |
| `gate` vs everyone | Gate never finds anything on its own. It **consumes** the other five and renders a verdict. A gate that does its own analysis has no independent input left to check. |
| `debt` vs `regression` | An expired quarantine becomes a debt entry. A debt item that keeps causing incidents escalates back as a regression class. The handoff is bidirectional and both directions are used. |

## 4. What this pack does not do

Explicitly out of scope — say so and stop, rather than half-doing it:

- **Shipping the fix.** This pack diagnoses and proves. Implementation belongs to whoever owns the code.
- **Security depth.** Surface-level exposure is graded (`_quality/SEVERITY.md` `CRITICAL`), but threat modelling, exploitation, and crypto review are a different discipline.
- **Performance engineering.** A measured regression is a finding; profiling and optimization are not.
- **Product decisions.** "Is this feature worth building" is never a quality verdict. Gate answers *may this ship*, never *should this exist*.

## 5. Independence rule

The skill that writes a fix does not grade the fix. If `quality-test` writes a test to close a
`quality-review` finding, the verdict on whether the finding is closed comes from `quality-review`
re-running against the new state, or from `quality-gate` — never from `quality-test` asserting its
own success. This is the same principle as `_quality/CONTRACT.md` §3, applied at skill scope.
