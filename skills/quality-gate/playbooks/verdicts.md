<!-- quality:guidance -->
# Verdicts, inputs, and risk tiers

## Acquiring the inputs

Gate produces no findings, so it must fetch them, in this order:

**1. Read the persisted payload.** Every contributing skill writes to a fixed path
(`_quality/HANDOFF.md` §0). Read the latest record per `ID` from:

| Criterion needs | Read |
|-----------------|------|
| blocking findings | `.agents/quality/findings.jsonl` |
| coverage / oracle evidence | `.agents/quality/gaps.md` + the test run |
| metric values, pass rate included | `.agents/quality/metrics.jsonl` |
| why the suite is unreliable, quarantines | `.agents/quality/flaky.jsonl` |
| standing debt | `.agents/quality/debt.md` |

**2. Invoke the skill when the payload is missing or stale.** A payload whose `ref` is not the ref
under decision is stale, and stale evidence is absent evidence. Invoke the owning skill directly —
via the Skill tool, or as a subagent — passing `_AGENT_CONTEXT` with the scope and the criterion
being evaluated, and collect its `_STEP_COMPLETE` envelope (`_quality/HANDOFF.md` §7).

Invoke only the owner of what is missing or stale, as named under `quality-gate`'s `not:` in
`registry/capabilities.yaml` — the one place that boundary is written, so it is not copied here.
The floors those values are compared against are not evidence to acquire: they are this skill's
own, in `gate.yml`.

**`NO-GO (insufficient evidence)` is for evidence that cannot be obtained** — the suite will not
run, the environment is unavailable, a human check has no owner. It is never the answer to
"nobody has run `quality-review` yet"; run it.

**Floors** (`suite pass rate ≥ floor`, `mutation score ≥ floor`) are read from the `floors:` block
of `.agents/quality/gate.yml`. A criterion whose floor is unrecorded is unevaluable: author it via
`reference/criteria.md` rather than inventing a number.

## The three verdicts

| Verdict | Means | Requires |
|---------|-------|----------|
| `GO` | every criterion for this tier is met, on evidence | the evidence, cited |
| `GO-WITH-CONDITIONS` | ship now; specified follow-up is owed | each condition with owner + date |
| `NO-GO` | a criterion is unmet and shipping is not justified | the criterion, the finding ID, and the smallest change that clears it |

`NO-GO` carries one of two reasons, and the record names which. **`NO-GO (insufficient
evidence)`** is frequently the honest one: evidence still unobtainable **after** acquisition — the
suite will not run, the environment is gone, a required human check has no owner. Stale metrics
or a review nobody ran are acquired, not reported. It is not the same as "there is a defect", and
saying so precisely is what keeps the gate trusted.

## Risk tiers

`R0` (docs) up to `R4` (irreversible). **The surfaces and the required inputs per tier are
defined once, in `reference/risk-tiers.md`** — read that table at `SCOPE`. A copy here is how the
two drift apart and an `R1` change with a `BLOCK` finding resolves differently depending on which
file was opened last.

Tier comes from the **surface**, never from urgency or from how the change was described. An
urgent `R3` change is an `R3` change with less time, which is an argument for a smaller change, not
a smaller gate.
