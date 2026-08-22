<!-- quality:deferred -->
# Trends — Reading Change Over Time

Purpose: What a given number of snapshots licenses you to claim.
Read when: comparing snapshots, or being asked whether something is improving.
Verified: 2026-08-21 — no automated check.

Read during `COMPARE` and `REPORT`. Most metric misuse happens here, not at measurement time.

---

## Comparability check — run before comparing

A comparison is valid only if all of these held constant between the two snapshots:

| Dimension | Invalidated by |
|-----------|----------------|
| Scope | a directory added, excluded, or moved; a monorepo merge |
| Tool | a version bump that changes the definition (complexity, mutation operators) |
| Configuration | changed thresholds, changed test selection, changed parallelism |
| Denominator | repository growth, for anything per-KLoC or per-file |
| Collection method | switching from CI-collected to locally-collected |

If any changed: report it as a **break**, not a trend. Re-baseline and say so. Silently
normalizing across a scope change produces a number that is wrong in a way nobody can later detect.

## Two points is a line, not a trend

| Snapshots | What may be said |
|-----------|------------------|
| 1 | the current value, with its command |
| 2 | the delta, with the interval, explicitly not a rate |
| 3–5 | direction, with the caveat that it may be noise |
| 6+ | a trend, with variance |

Establish the noise floor before reading a delta as signal: re-run the same measurement twice on
the same commit and see how much it moves on its own. Coverage drifts with test selection,
complexity moves with any refactor, and defect counts on a small team are dominated by who was on
holiday. A delta smaller than the measured noise floor is not a change.

## Report shape

```
METRIC:      mutation_score (src/billing)
NOW:         0.62   (2026-08-21, a1b2c3d)
PREVIOUS:    0.55   (2026-07-15, 9f8e7d6)
DELTA:       +0.07 over 37 days
COMPARABLE:  yes — same scope, stryker@8.2.0 both runs
COMMAND:     npx stryker run --mutate 'src/billing/**'
READS AS:    the suite now detects 62% of injected defects in billing, up from 55%
NOT SHOWN:   nothing outside src/billing; no mutation data for the payment gateway adapter
```

`READS AS` is the line that stops a number being misquoted. `NOT SHOWN` is the line that stops it
being over-read.

## Interpretation traps

- **A metric that improves the week a target is introduced has been gamed, not improved.** Check the counterweight before celebrating (`metric-catalog.md`).
- **Percentages on small denominators.** 2 → 3 is "+50%" and also nothing. Report counts under ~30.
- **Survivorship in defect data.** Defects found are a function of looking. A quiet quarter may be a quarter with no QA capacity.
- **Correlated metrics double-count.** Coverage and test count move together; reporting both as independent evidence of improvement is one fact told twice.
- **Seasonality.** Deploy frequency drops at holidays and quarter-end freezes; comparing December to October measures the calendar.
- **A break in the series is information.** When collection changes, the discontinuity is worth reporting explicitly — it is often the most useful thing in the report.

## When the trend is bad

Report it plainly and stop. Explaining *why* it is bad and *what to do* is `quality-debt`'s job
(`_quality/ROUTING.md` §3). A measurement function that also proposes remediation loses the
independence that made the measurement worth reading — and in practice starts selecting metrics
that support the proposal.
