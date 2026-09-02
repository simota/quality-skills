<!-- quality:deferred -->
# Repayment — Sequencing and Seams

Purpose: Sequencing repayment, and what has to exist before restructuring starts.
Read when: turning a ranked ledger into an order of work.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `SEQUENCE`, and when justifying what is left alone. The order of repayment matters more than the total
effort: a sequence where each step lowers the cost of the next finishes; one that starts with the
hardest step stalls and gets reverted.

---

## The universal first step

**Characterization tests, before any restructuring.** Not tests of what the code *should* do —
tests of what it *does*, including the behaviour that is wrong, so that the restructuring is
provably behaviour-preserving.

Be precise about what they prove. A characterization suite is `E4` evidence for
*"this refactor changed no behaviour"* — the pre-change system is the reference implementation and
the comparison is differential. It is `E0` evidence for *"this behaviour is correct"*, and must
never be cited for that (`_quality/CONTRACT.md` §3). Correctness is a separate question, answered
after the restructuring, one deliberate change at a time.

```
1. Pin current behaviour with tests derived from real inputs (production capture is ideal).
2. Confirm they fail if you deliberately break the code. A characterization suite that stays
   green under an injected defect is pinning nothing.
3. Restructure. The suite is the oracle.
4. Only then change behaviour, one deliberate change at a time, each with its own test.
```

Steps 3 and 4 are separated for a reason: a commit that both moves code and changes behaviour is
unreviewable and unbisectable, and when it goes wrong nobody can tell which half did it.

Skip step 1 only when coverage is *shown* to exist — a coverage report plus an injected-defect
check, not an assumption.

## Sequencing rules

| Rule | Why |
|------|-----|
| Enabling debt first | An untestable seam blocks everything else in that module; it is usually a one-line fix and it unlocks the rest. |
| Smallest reversible step | Each step ships and is revertible on its own. A four-week branch is not repayment; it is a second codebase. |
| Highest interest within a module, not across | Context switching between modules multiplies the comprehension cost you are trying to reduce. |
| Attach to work already happening | Repayment scheduled next to the feature it makes cheaper survives planning; standalone "cleanup sprints" get cut. |
| Stop when interest drops below the next item | Repayment has diminishing returns and there is always a next item. |

## Naming a seam

For the entry whose blocker is untestable code. "This code is untestable" is not actionable; the seam is.

| Blocker | Seam | Smallest opening |
|---------|------|------------------|
| constructor performs I/O | construction | inject the client; construct it in the caller |
| module-level singleton | initialization | pass it in, or add a reset for tests |
| direct `new Date()` / `time.Now()` | the clock | inject a clock function, defaulted |
| static/global config read inline | configuration | read once at the boundary, pass down |
| direct filesystem or network call in logic | the boundary | one thin adapter interface at the edge |
| private method holding the logic | visibility | the behaviour is reachable publicly, or it is dead — determine which |
| framework-instantiated class | the framework | test through the framework's own test harness, not around it |

The deliverable names the file, the line, and the one-line change. That is what makes the first
step small enough to actually happen.

## Justifying non-repayment

Every entry not being repaid carries a condition. Without one, the argument recurs every quarter
and is re-litigated from scratch.

```
ENTRY:      Q-DEBT-014 — src/legacy/reportBuilder.ts
DECISION:   not now
BECAUSE:    0 commits in 90d; 1 importer; blocks nothing
UNLESS:     the reporting feature is revived, or this file is touched twice in one quarter
REVIEW:     next ledger review (quarterly)
```

`UNLESS` is the load-bearing line. "Won't fix" without a condition is a decision that cannot be
revisited on evidence, which means it will be revisited on mood.

## When a rewrite is actually right

Rarely, and never as a default. The conditions, all of which must hold:

- The current behaviour is **specified somewhere other than the code** — otherwise the rewrite loses every bug fix embedded in it and nobody can tell what regressed.
- The old system can keep running while the new one is built and verified against it (the old system is the reference oracle; hand it to `quality-test` as a Coverage Gap with `ORACLE: reference-impl`).
- There is a migration path for data and for callers, written down before starting.
- The cost is compared honestly against incremental repayment, including the year of parallel maintenance.

If the argument for the rewrite is that the code is hard to understand, that is an argument for
characterization tests, which are the first step of the rewrite anyway — and often the last step
needed.
