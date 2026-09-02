<!-- quality:deferred -->
# Test Smells — Auditing an Existing Suite

Purpose: The shapes a test takes when it proves nothing.
Read when: auditing a suite, or before committing a new test.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read when auditing a suite. A suite can be large, green, fast, and prove nothing. These are the
patterns that produce that state, ordered by how common they are.

---

## Tier 1 — Proves nothing

| Smell | Detection | Fix |
|-------|-----------|-----|
| **No assertion** | test body ends after the call; only "it didn't throw" is verified | assert on the value, or delete |
| **Tautology** | `expect(x).toBe(x)`; expected value computed by the same call | derive the oracle (`oracles.md`) |
| **Asserting the mock** | the asserted value is the mock's configured return | assert on the transformation, not the input |
| **Implementation-copied expectation** | the expected value was pasted from a run | re-derive from spec; check it fails on the parent commit |
| **`expect(result).toBeTruthy()`** on an object | always passes | assert a field with a value |
| **Snapshot of everything** | multi-hundred-line golden, updated in most PRs | shrink to the assertion-worthy subset |

Tier 1 tests are worse than no test: they occupy a coverage line and a name that reads like
protection.

## Tier 2 — Fails for the wrong reason

| Smell | Detection | Fix |
|-------|-----------|-----|
| **Shared mutable fixture** | setup builds a record that tests modify | build per test, explicitly |
| **Order dependence** | passes alone, fails in suite (or vice versa) | see `_quality/SEVERITY.md` `FLAKY-ORDER` |
| **Real clock / timezone / locale** | `new Date()`, `time.Now()`, no TZ pin | inject the clock; pin TZ and locale in the runner |
| **`sleep`** | any fixed wait | await the condition, or use a fake timer |
| **Real network** | a hostname in a unit test | stub the boundary; keep one contract test that doesn't |
| **Shared DB across parallel workers** | intermittent unique-constraint failures | per-worker schema or transactional rollback |
| **Randomness without a seed** | `Math.random`, `uuid4` in the assertion path | seed it; log the seed on failure |

## Tier 3 — Costs more than it earns

| Smell | Detection | Fix |
|-------|-----------|-----|
| **Testing privates** | test imports an underscore-prefixed symbol | test through the public surface, or the code is dead |
| **Mock pyramid** | more than ~3 mocks to construct one test | wrong level (`test-levels.md`), not more mocks |
| **Duplicate coverage** | 12 tests differing only in a value in the same branch | one parameterized test with the boundaries |
| **Test with logic** | `if`/loops in the test deciding what to assert | one test per branch; the test should be readable top to bottom |
| **Unreadable failure** | failure message needs the source open to interpret | assert on named values; add a message |

## Audit procedure

1. **Run the suite in random order.** Order dependence surfaces immediately, and it is the highest-value single check.
2. **Run each test file alone.** Anything that only passes as part of the whole is Tier 2.
3. **Grep for the Tier 1 detections.** Assertion-free tests and truthiness assertions are mechanically findable.
4. **Break the code on purpose.** Invert one condition in the most important function. If the suite stays green, you have measured its real value, in one minute. This is manual mutation testing and it is worth doing before automating it.
5. **Sample five tests and ask, per test: what defect does this catch?** No answer in one sentence → `PRUNE` candidate.

## On deleting tests

Every proposed deletion carries the defect class it fails to catch, and goes to the owner rather
than straight into a commit (`quality-test/SKILL.md` § Always / Never). A suite that shrinks is usually healthier
— but "usually" is not a mandate, and a deleted test is invisible in every future review.
