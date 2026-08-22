<!-- quality:guidance -->
# Verdicts, inputs, and risk tiers

## Acquiring the inputs

Gate produces no findings, so it must fetch them. Two routes, in order:

**1. Read the persisted payload.** Every contributing skill writes to a fixed path
(`_quality/HANDOFF.md` §0). Read the latest record per `ID` from:

| Criterion needs | Read |
|-----------------|------|
| blocking findings | `.agents/quality/findings.jsonl` |
| coverage / oracle evidence | `.agents/quality/gaps.md` + the test run |
| thresholds and reliability | `.agents/quality/metrics.jsonl` |
| standing debt | `.agents/quality/debt.md` |

**2. Invoke the skill when the payload is missing or stale.** A payload whose `ref` is not the ref
under decision is stale, and stale evidence is absent evidence. Invoke the owning skill directly —
via the Skill tool, or as a subagent — passing `_AGENT_CONTEXT` with the scope and the criterion
being evaluated, and collect its `_STEP_COMPLETE` envelope (`_quality/HANDOFF.md` §7).

| Missing | Invoke |
|---------|--------|
| findings on the change | `quality-review` |
| coverage for new behaviour | `quality-test` |
| a threshold value | `quality-metrics` |
| suite reliability | `quality-regression` |
| debt ceiling | `quality-debt` |

**`NO-GO (insufficient evidence)` is for evidence that cannot be obtained** — the suite will not
run, the environment is unavailable, a human check has no owner. It is never the answer to
"nobody has run `quality-review` yet"; run it.

**Floors** (`suite pass rate ≥ floor`, `mutation score ≥ floor`) are read from the `floors:` block
of `.agents/quality/gate.yml`. A criterion whose floor is unrecorded is unevaluable: author it via
the `design` recipe rather than inventing a number.

## The three verdicts

| Verdict | Means | Requires |
|---------|-------|----------|
| `GO` | every criterion for this tier is met, on evidence | the evidence, cited |
| `GO-WITH-CONDITIONS` | ship now; specified follow-up is owed | each condition with owner + date |
| `NO-GO` | a criterion is unmet and shipping is not justified | the criterion, the finding ID, and the smallest change that clears it |

A fourth state exists and is frequently the honest one: **`NO-GO (insufficient evidence)`** — the
tests did not run, the metrics are stale, the review did not happen. It is not the same as "there
is a defect", and saying so precisely is what keeps the gate trusted.

## Risk tiers

| Tier | Surface |
|------|---------|
| `T0` | docs, comments, non-shipped config |
| `T1` | internal refactor with existing coverage |
| `T2` | feature, business logic, UI |
| `T3` | auth, money, data mutation, migration, public API |
| `T4` | irreversible: data deletion, one-way migration, external commitment |

**Required inputs per tier are defined once, in `reference/risk-tiers.md`** — read that table at
`TIER`, not this one. Duplicating it here is how the two drift apart and a `T1` change with a
`BLOCK` finding resolves differently depending on which file was opened last.

Tier comes from the **surface**, never from urgency or from how the change was described. An
urgent `T3` change is a `T3` change with less time, which is an argument for a smaller change, not
a smaller gate.
