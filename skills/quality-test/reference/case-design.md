<!-- quality:deferred -->
# Case Design — What to Actually Test

Purpose: Partitions, boundaries, and error paths, applied per input.
Read when: enumerating the cases a behaviour needs.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `CASES`. The goal is not many cases; it is the **fewest cases that would catch the
defects this code can plausibly have**.

---

## Per-input: the standard five

For every input, from every source:

| Case | Why it finds things |
|------|---------------------|
| **Empty** | the code was written for "some"; zero takes a path nobody imagined |
| **One** | singular/plural logic, `join`, pagination arithmetic, "the last one" |
| **Maximum** | the declared limit, exactly at it |
| **Over maximum** | one past — is it rejected, truncated, or accepted? All three happen. |
| **Malformed** | wrong type, wrong encoding, null, injected control characters |

Write the ones that could plausibly fail. Skipping is fine; skipping *without having asked* is
how the empty-list crash reaches production.

## Equivalence partitioning

Split the input domain into classes where every member is expected to behave the same, then test
**one member per class plus every boundary between classes**.

```
discount(age):
  0-5    free
  6-17   half
  18-64  full
  65+    senior
```

Cases: one from each class (3, 10, 30, 70) plus boundaries (0, 5, 6, 17, 18, 64, 65) plus
malformed (-1, 65.5, null). Twelve cases, not "a few ages".

**Boundaries are where the defects are.** Off-by-one lives at 5/6 and 64/65, never at 30.

## Error paths

Coverage tends to prove the success path twice and the failure path never.

For each failure mode: does the system **degrade, fail loudly, or lie**? The third is the one to
test for, and the one nobody writes a test for.

- Dependency returns an error → is it surfaced or swallowed?
- Dependency times out → is there a timeout at all?
- Dependency returns success with a garbage body → is it validated?
- Step 2 of 3 fails → what state is left behind?
- The same request arrives twice → one effect or two?

## State-dependent behaviour

For anything with state, test the **transition**, not the state:

- valid transition happens
- invalid transition is rejected, and rejected *without* partial mutation
- the same transition twice (idempotence)
- transition from the terminal state
- concurrent transitions from the same source state

## Concurrency

Deterministic tests for concurrency are hard, so most codebases have none, so most concurrency
defects reach production. Reachable options, in order of value:

1. **Property test on the invariant** — after N concurrent operations, the sum/count/balance must hold.
2. **Forced interleaving** — inject a barrier or a controllable scheduler at the known-dangerous point.
3. **Loop-and-assert** — run 1,000 iterations; flaky-by-design, so run it in a separate suite, never in the blocking gate.

## What not to test

Every test costs maintenance forever. Do not write:

- tests of the language, the framework, or a well-maintained library
- tests of pure delegation (a function whose whole body is one call, asserted with a mock)
- multiple tests differing only in a value that exercises the same branch
- tests asserting the shape of internal data structures
- tests whose assertion is `not null`

The test: **what defect would this catch?** No answer → do not write it. Already written and no
answer → it is a `PRUNE` candidate.
