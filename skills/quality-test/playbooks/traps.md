<!-- quality:guidance -->
# Traps — tests

- **A test written after the fix, from the fixed code, is not a regression test.** It encodes the fix, not the bug. Write it from the reproduction, and confirm it fails on the parent commit.
- **Mocking the thing under test's collaborator is fine; mocking its behaviour into the assertion is not.** If the mock's return value is what you assert on, the test verifies your mock.
- **Shared fixture bases are the single largest source of order-dependent flakes.** A fixture mutated by one test and read by another passes locally and fails in CI shards, forever.
- **`assertTrue(result)` on a function returning a truthy object always passes.** Assert on a value, not on existence.
- **Snapshot tests approve whatever happened.** An updated snapshot in a diff is an unreviewed behaviour change; treat `-u` in CI as a gate failure.
- **Time, timezone, locale, and random seed are inputs.** A test that reads the system clock has an input you did not choose and cannot reproduce.
- **Testing private methods to raise coverage couples the test to structure.** The behaviour is reachable from the public surface, or it is dead code — find out which.
