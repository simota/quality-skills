<!-- quality:deferred -->
# Criteria — Designing What the Gate Checks

Purpose: What a criterion must state to be worth having.
Read when: designing or revising the gate definition.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `EVALUATE` and `DECIDE`, and whenever the gate definition is being designed or revised.

---

## The three questions a criterion must survive

1. **What decision does it change?** If nothing happens differently when it fails, it is a report, not a criterion.
2. **How is it measured, exactly?** A command, a query, or a named human check. "Code quality is acceptable" is not measurable and will be interpreted differently by every reader.
3. **What would remove it?** A criterion with no removal condition is permanent by default, and permanent criteria accumulate until the gate is bypassed as a matter of routine.

A criterion failing any of the three is not adopted. This is the discipline that keeps a gate
short enough to be respected.

## Criteria that hold up

| Criterion | Measured by | Resists gaming because |
|-----------|-------------|------------------------|
| No `BLOCK` findings on the change | `quality-review` output | severity/blocking split is explicit and cited |
| New behaviour has a test with a named oracle | `quality-test` deliverable | the oracle must be named, so "a test exists" is not enough |
| Suite green with zero skips added | test runner + skip count | skip count is the counterweight to a green run |
| Suite pass rate ≥ `floors.suite_pass_rate` over the last N runs | `quality-metrics` | measures reliability, not one lucky run |
| Mutation score on the touched module ≥ `floors.mutation_score[<module>]` | `quality-metrics` | cannot be raised by assertion-free tests |
| Rollback verified for `R3`+ | a documented, exercised undo | requires an artifact, not a statement |
| Migration is reversible or has a stated forward-fix | migration review | forces the question before the deploy |
| No new `CRITICAL` dependency advisory | audit tool | mechanical |

## Criteria that fail in practice

| Criterion | Why it fails |
|-----------|--------------|
| Line coverage ≥ 80% | produces assertion-free tests within a sprint; measures execution, not verification |
| Zero lint warnings | blocks on cosmetics, and trains bypass |
| "Two approvals" | approval count is not review depth; two rubber stamps pass |
| "No known bugs" | unfalsifiable, and punishes the honest |
| Complexity ≤ N per function | gamed by splitting into trivial functions with worse coupling |
| "Documentation updated" | unmeasurable as stated; specify which document and what it must say |

## Definition of Done

A DoD is a criteria set applied per work item rather than per release. The one rule that
distinguishes a useful DoD from a wish list:

> **Every item must be checkable by someone other than the author.**

| Good | Bad |
|------|-----|
| "AC-114 has a passing test citing the AC" | "adequately tested" |
| "the error path returns a message naming the failing field" | "errors handled gracefully" |
| "the flag-off path is exercised in CI" | "feature flagged" |
| "runbook entry added for the new alert" | "observable" |

Keep it under about seven items. A longer DoD is not checked; it is scrolled past and ticked.

## Conditions for GO-WITH-CONDITIONS

```
CONDITION: <what must become true — observable>
OWNER:     <a person>
BY:        YYYY-MM-DD
IF NOT:    <what happens — revert, flag off, follow-up blocks the next release>
```

`IF NOT` is what makes the condition real. Without it, an unmet condition produces a conversation
rather than a consequence, and the next conditional GO is worth less than this one.

Do not issue `GO-WITH-CONDITIONS` for anything that could cause harm before the date. Conditions
are for follow-up work, not for deferred safety.

## Evaluating: the one-line-per-criterion shape

```
[✓] no BLOCK findings           — quality-review, 0 BLOCK / 3 FOLLOW-UP (Q-REV-041..043)
[✓] new behaviour tested        — quality-test, oracle: AC-114, RED evidence attached
[✗] suite pass rate ≥ 0.98      — quality-metrics, 0.94 over last 20 runs (2 quarantined, 1 expired)
[–] mutation score              — not measured; tier T2 does not require it
```

`[–]` for not-applicable and `[?]` for not-measured are different states and must render
differently. Collapsing "we checked and it's fine" with "we didn't check" is the failure mode
this whole file exists to prevent.
