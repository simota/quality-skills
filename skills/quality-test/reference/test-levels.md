<!-- quality:deferred -->
# Test Levels — Choosing the Altitude

Purpose: What each level can falsify, and what it costs.
Read when: deciding where a case belongs.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Pick the level by **what must be falsifiable**, then pay the cost knowingly. Convention ("we write
unit tests here") is not a reason.

---

## The levels

| Level | Falsifies | Runs in | Fails because |
|-------|-----------|---------|---------------|
| **Unit** | one function's logic, given inputs | ms | the logic is wrong |
| **Integration** | two or more real components agreeing | 100ms–s | an assumption at the seam was wrong |
| **Contract** | a producer and consumer still agree | ms, both sides | one side changed unilaterally |
| **E2E** | the user-visible flow works end to end | s–min | anything, anywhere |

## The decision

> What is the *defect* I am trying to catch, and at what altitude does it become visible?

| The defect lives in… | Level | Not |
|----------------------|-------|-----|
| a calculation, a parser, a state machine transition | unit | e2e — slow feedback for a defect visible in 1ms |
| the mapping between your model and the DB schema | integration (real DB) | unit with a mocked repository — the mock encodes the assumption that is wrong |
| the shape of a payload between two services | contract | e2e — passes until the deploys are ordered differently |
| a wiring problem: DI, config, routing, middleware order | integration | unit — every unit passes; the app does not start |
| a user flow with real navigation and auth | e2e | integration — the defect is the assembly |

## Costs that are usually underestimated

- **E2E is not "more realistic", it is more informative and less specific.** A red e2e says something is wrong. It rarely says what. Budget for the diagnosis, not just the run.
- **Every mock is a claim about a collaborator.** The claim is unverified unless a contract or integration test checks it. A unit-test suite over a fully mocked boundary tests your beliefs about the boundary.
- **In-memory substitutes for databases lie about the interesting parts**: transactions, isolation, constraint enforcement, collation, JSON semantics. Use the real engine for anything that depends on those.
- **E2E count grows quadratically with flake surface.** Ten e2e tests at 99% reliability each fail a clean pipeline ~10% of the time.

## The shape

The classic pyramid still holds, with one correction: the ratio should follow **where your defects
actually come from**, which the `quality-metrics` defect-origin data can tell you.

- Many unit tests: cheap, specific, fast — where logic defects live.
- Fewer integration tests: at every seam that a mock currently asserts.
- A contract test per external boundary that a second team owns.
- A small e2e set covering the flows whose breakage is a business incident. Not "the main features" — the flows that would cost money by lunchtime.

An hourglass (many unit, many e2e, no integration) is the common failure shape: the seams — where
most production defects actually originate — go unverified in both directions.

## Placement rule for a specific case

1. Write it at the **lowest level where the defect is visible**.
2. If it needs more than two mocks to get there, that is a signal the level is wrong, not that you need a third mock.
3. If it cannot be reached from the public surface at any level, the code is untestable — that is a `quality-debt` entry naming the seam, not a reason to test privates.
