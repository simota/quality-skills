<!-- quality:guidance -->
# Reading coverage honestly

- Coverage measures **what was executed**, not what was verified. A test with no assertions raises coverage.
- Branch coverage is more informative than line; neither says anything about the oracle.
- Uncovered code is a **map**, not a score: read the list of uncovered lines and ask which represent behaviour a user can reach.
- A coverage *target* changes behaviour predictably: people write tests that execute code without asserting on it. If a target exists, pair it with mutation score, which cannot be gamed the same way.
- 100% coverage of a wrong oracle is 0% evidence.
