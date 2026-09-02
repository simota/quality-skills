<!-- quality:deferred -->
# Flaky Repair — By Cause Class

Purpose: Repairing each cause class at the cause, not at the symptom.
Read when: the class is known and the repair has to hold.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `REPAIR`. Each class has one correct repair and one tempting wrong one.
The wrong one is listed first, by name, because it is what gets reached for under time pressure.

---

## `FLAKY-ORDER` — shared state

**Wrong fix:** force the test order, or add a cleanup that happens to run first.
**Why wrong:** the shared state remains; the next test to touch it re-creates the flake, and the
forced order becomes load-bearing infrastructure nobody understands.

**Right fix:** remove the sharing.

| Shared thing | Repair |
|--------------|--------|
| module-level variable / singleton | construct per test, or reset in a framework-level hook |
| database rows | per-test transaction rolled back, or per-worker schema |
| filesystem paths | unique temp dir per test, removed in teardown |
| environment variables | set and restore around each test |
| HTTP mock registry | reset between tests, asserted empty |
| a cache | inject it; do not reach for the global |

**Verification:** the suite passes in ten different random orders, not one.

## `FLAKY-TIME` — clock, timing, or race

**Wrong fix:** `sleep`, a longer timeout, or a retry wrapper.
**Why wrong:** these hide a race that also exists in production, and they make the suite slower in
exchange for less information.

**Right fix depends on which it is:**

| Symptom | Cause | Repair |
|---------|-------|--------|
| fails near midnight or month end | date-boundary logic | inject the clock; add explicit boundary cases |
| fails in one timezone | implicit local time | pin TZ in the runner; store and compare in UTC |
| fails ~1 in N, no pattern | a real race | find it — this is a product defect, not a test defect |
| fails waiting for async work | polling by wall-clock | await the condition or the completion signal |
| fails only under load | contention | reproduce at CI's parallelism; fix the contention |

For "a real race", the test is currently your **only** detector. Do not delete or retry it.
Instrument, force the interleaving, and fix the product. A property test on the invariant — request one from
`quality-test` as a Coverage Gap with `ORACLE: property` — usually reproduces it faster than the
original test did.

## `FLAKY-ENV` — machine, network, or fixture

**Wrong fix:** `if (process.env.CI) skip`.
**Why wrong:** the test now verifies nothing where it matters most, while still reporting as a test.

**Right fix:** remove the environmental dependency, or make it explicit.

- Real network call → stub it; keep exactly one contract test that does hit the boundary, in a non-blocking suite.
- Depends on CPU count / worker count → make the assertion independent of parallelism.
- Depends on a fixture file, a port, a locale, an image version → pin it in the runner config and assert the precondition at setup, so the failure says *what* is missing.
- Container clock skew → use a monotonic source for durations.

## `STALE` — behaviour changed on purpose

**Wrong fix:** quietly update the assertion in the same commit as the feature.
**Why wrong:** a changed assertion is a changed specification, and burying it means nobody
reviewed the specification change.

**Right fix:** update the test, and make the change **visible**: separate commit or a called-out
section in the PR, with the reason. If the old assertion came from a spec, the spec is updated too,
or the test change is unjustified.

## `WRONG-ORACLE` — never valid

**Wrong fix:** leave it; it's green.
**Why wrong:** it occupies a name that reads like protection and a line on the coverage report.

**Right fix:** re-derive from a real oracle — hand a Coverage Gap to `quality-test`, which owns
oracle selection. If no oracle
exists, the behaviour is unspecified — that is the finding. Delete with an owner's confirmation
and file the gap.

## `REGRESSION` — the code broke

Not a test problem at all. Bisect (`bisection.md`), grade the culprit diff via `quality-review`,
emit a fix directive, and keep the failing test exactly as it is — it is working correctly and is
the guard.

---

## The refusal list

These appear in a repair only with an explicit, written reason, and never as the fix itself:

- `sleep(n)` / `waitFor(fixed ms)`
- raising a timeout to make a test pass
- `retry(3)` around a test body
- widening an assertion (`toBe` → `toBeTruthy`, exact → `contains`)
- `skip` without owner and expiry
- `if CI: skip`
- catching and ignoring the failure the test exists to detect

Each of these has the same shape: it removes the detector rather than the defect.
