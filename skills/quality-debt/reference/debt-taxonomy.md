<!-- quality:deferred -->
# Debt Taxonomy — Classifying and Costing an Entry

Purpose: The kinds of debt, and what distinguishes one from the next.
Read when: naming what a ledger entry actually is.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `MEASURE` and `SCORE`. Different debt types have different interest drivers, and
misclassifying one produces a ranking that is confidently wrong.

---

## Types and their drivers

| Type | Example | Interest driven by | Repayment risk |
|------|---------|--------------------|----------------|
| **Duplication** | one rule implemented in six places | touch frequency of any copy | low, once tests exist |
| **Coupling** | a change here forces a change there | blast radius | high — that is what coupling means |
| **Missing tests** | hot module, no characterization | touch frequency × statefulness | low; this *is* the enabling repayment |
| **Leaky abstraction** | every caller works around it | number of callers working around it | high; the workarounds encode behaviour |
| **Dependency** | pinned three majors back | **calendar time**, not churn | rises non-linearly per major skipped |
| **Data / schema** | a column meaning two things | number of readers, plus migration cost | highest; usually irreversible |
| **Process** | a manual step before every deploy | frequency of the process | low, and usually cheap |
| **Knowledge** | one person understands it | bus factor | not repayable by refactoring — by documentation and pairing |
| **Untestable seam** | a constructor doing I/O | blocks all other repayment here | low; usually a one-line injection |

**Dependency debt is the one that breaks the formula.** It compounds with time even when nobody
touches the code, and repayment cost grows faster than linearly with each skipped major version.
Rank it on age and on what it blocks (a security patch, a runtime upgrade, a required feature),
not on churn.

## Cost today — the required field

State cost in units someone can verify. Not "this is messy".

| Unit | Example |
|------|---------|
| places | "adding a currency requires edits in 6 files" |
| minutes | "~40 min to safely change the discount rule; measured on the last two attempts" |
| incidents | "3 production incidents in 2026 traced to this module" |
| blocked work | "blocks the Node 22 upgrade" |
| rejected changes | "2 PRs abandoned after review found unrelated breakage" |
| review load | "every PR touching this file needs the one reviewer who knows it" |

If no unit applies, the honest entry is: **cost today ≈ 0**. Record it anyway — a zero-cost entry
is useful, because it is the evidence for not repaying, and it stops the same argument recurring
every quarter.

## Deliberate debt entries

Deliberate debt carries two extra fields:

```
TAKEN:     YYYY-MM-DD — <the reason, as stated at the time>
CONDITION: <what makes it due>     e.g. "when a second tenant onboards"
CONDITION MET? <yes/no — checked this review>
```

Check the condition **before** computing interest. Deliberate debt whose condition is met is
usually the best entry in the ledger: the shape was intentional, someone documented it, and the
repayment path was considered when it was taken.

Deliberate debt with no written condition has silently become accidental debt. Re-classify it and
say so — that reclassification is itself worth reporting.

## Not debt — the discard list

Check every candidate against this before it enters the ledger:

- Code that works, is never touched, and blocks nothing.
- A pattern the team has moved away from, where the old pattern still functions.
- A dependency that is merely not the latest, with no security, feature, or runtime pressure.
- Duplication that has never had to be changed in more than one place.
- Anything whose cost statement is "it's ugly" or "I wouldn't have done it that way".

Filtering aggressively here is what makes the rest of the ledger credible. A ledger containing
every imperfection is a ledger that gets closed unread.

## Entry shape

The row shape is defined once, in `_quality/HANDOFF.md` §4:

```
| ID | Location | Type | Cost today | Interest | Confidence of fix | Deliberate? | Status | First seen |
```

`First seen` never changes. An entry that has been open for eighteen months at a stable interest
is telling you something true: either the interest is overstated, or the team has decided — by
revealed preference — not to repay it. Both are worth writing down at the next review.
