<!-- quality:contract -->
# Severity & Priority (quality-* pack)

> **Tier:** `spine`. Precedence: `_quality/VALUES.md` § Rule precedence.

One ranking vocabulary for all six skills, so a `quality-review` finding, a `quality-debt` item,
and a `quality-regression` failure can sit in the same list without renegotiating what "high" means.

---

## 1. Two orthogonal axes

They are routinely conflated, and conflating them is why quality reports get ignored.

**Severity** — how bad it is if it fires. A property of the defect.
**Blocking** — whether this particular change may proceed. A property of the *situation*.

A `CRITICAL` bug in code that is already in production for two years is severe and usually
**non-blocking** for the unrelated PR that revealed it. A `MEDIUM` bug newly introduced by the PR
under review is **blocking**. Emit both; never collapse them into one number.

## 2. Severity bands

Assign the **highest band whose full description is true.**

| Band | Fires as | Test |
|------|----------|------|
| `CRITICAL` | data loss, corruption, auth bypass, secret exposure, money moved wrongly, unrecoverable state | Can this destroy something a user cannot get back? |
| `HIGH` | crash, wrong result on a normal path, broken core flow, unbounded resource growth | Would a routine user hit this and be blocked or misled? |
| `MEDIUM` | wrong result on an edge path, degraded performance, poor failure mode, missing rollback | Real, but needs an unusual input or state. |
| `LOW` | confusing behaviour, weak error message, inconsistency with neighbours | Costs comprehension, not correctness. |
| `NIT` | naming, formatting, personal preference | Never blocking. Never counted in defect metrics. |

**Do not inflate.** A report where everything is `HIGH` conveys exactly as much as one where
everything is `LOW`. If more than a third of findings land in the top two bands, re-grade before
emitting — the bands are being used as emphasis rather than as classification.

## 3. Blocking decision

| Blocking | Condition |
|----------|-----------|
| `BLOCK` | introduced by this change **and** ≥ `MEDIUM`; or any `CRITICAL` reachable from the changed surface |
| `FOLLOW-UP` | pre-existing, or `LOW`, or requires design agreement to fix properly |
| `NIT` | cosmetic; author's discretion, no response required |

Pre-existing `CRITICAL` findings are `BLOCK` only when the change makes them newly reachable.
Otherwise they route to `quality-debt` as a ledger entry with a date — not as a surprise merge veto.

## 4. Debt priority (`quality-debt`)

Debt is not ranked by severity alone; it is ranked by **interest**.

```
interest = (touch_score × blast_score × comprehension_score) / confidence_of_fix
```

**The operands are band scores, not raw measurements.** Take the raw measurement first, then map
it to a band. Multiplying raw units directly is a category error: 18 commits × 9 importers × 90
minutes is not a quantity, and it lands three orders of magnitude off the scale below. The band
tables and the extraction command for each raw input live in `quality-debt`'s
`reference/interest.md`, which scores them; this file fixes the scale they map onto, and
`make figures` holds the two in agreement.

| Operand | Raw measurement | Band scale |
|---------|-----------------|------------|
| `touch_score` | commits to the file in the last 90 days, from git — not guessed | 0.1 (frozen) · 0.5 · 1.0 · 2.0 · 3.0 (hottest) |
| `blast_score` | modules importing it, transitively, capped at the boundary layer | 0.5 (leaf) · 1.0 · 2.0 · 3.0 (crosses a service boundary) |
| `comprehension_score` | minutes for a competent stranger to safely change it — the one estimated input, always flagged as such | 0.5 · 1.0 · 2.0 · 3.0 |
| `confidence_of_fix` | the divisor, below | 1.0 · 0.6 · 0.3 · 0.2 |

**`confidence_of_fix` — canonical values.** Any other rubric is a loosening
(`_quality/OPERATIONAL.md` §1) and is invalid.

| State | Value |
|-------|-------|
| characterization tests exist and are trusted | 1.0 |
| tests exist but their oracle is the implementation | 0.6 |
| no tests; behaviour is pure, with no state or I/O | 0.6 |
| no tests; stateful, I/O, or concurrent | 0.3 |
| no tests and behaviour is unspecified anywhere | 0.2 |

**Low confidence raises interest, and that is correct.** Dividing by a smaller number ranks an
untested item *above* an otherwise identical tested one, because every change to it is a gamble.
That is a statement about **rank**, not about **order of work**: a high-interest, low-confidence
entry is repaid by writing characterization tests first, never by restructuring first. Refactoring
untested hot code is how quality initiatives generate incidents.

Interest is **ordinal**. Use it to order the ledger. Do not report it as a measurement, and do not
read the gap between two adjacent entries as meaningful.

## 5. Regression / flaky classes (`quality-regression`)

| Class | Meaning | Action |
|-------|---------|--------|
| `REGRESSION` | passed before, fails now, product code changed | Bisect, then fix product code. Never the test. |
| `FLAKY-ORDER` | passes alone, fails in suite | Shared state. Fix isolation, not the assertion. |
| `FLAKY-TIME` | timing, clock, timezone, or race dependent | Inject the clock; remove sleeps. |
| `FLAKY-ENV` | machine, network, or fixture dependent | Pin or stub the boundary. |
| `STALE` | asserts behaviour that was deliberately changed | Update the test, and say so loudly in the PR. |
| `WRONG-ORACLE` | test was never valid; both sides agree wrongly | Delete and re-derive from spec (`_quality/CONTRACT.md` §3). |
| `PREEXISTING-DEFECT` | a new test reveals a bug that was always there | Nothing to bisect — the defect predates the test. Fix the product; the test is already the guard. |

**Quarantine is a countdown, not a cupboard.** A quarantined test carries an owner and an expiry
date. Expired quarantine deletes the test and files the coverage gap as debt — an indefinitely
skipped test is worse than no test, because it reads as coverage on the dashboard.

## 6. Confidence labels

Attached to a finding, independent of severity.

| Label | Meaning |
|-------|---------|
| `CONFIRMED` | reproduced, or proven from code with the path shown |
| `LIKELY` | strong static evidence, not executed |
| `HYPOTHESIS` | worth checking; carries the one command that would settle it |

`HYPOTHESIS` findings never block and are never counted. They are listed last, under their own
heading, so a reader can stop reading before them.
