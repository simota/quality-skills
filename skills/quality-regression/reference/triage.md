<!-- quality:deferred -->
# Triage — Sorting a Red Suite

Purpose: Deciding what a failure is worth before spending on it.
Read when: several things are failing and not all of them can be chased.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `REPRODUCE` and `CLASSIFY`. The goal of triage is **not** to fix anything. It is to know what
you have, so that fixing effort goes where it pays.

---

## Order of operations

1. **Count.** How many reds, how many distinct failures, how many are the same root cause.
2. **Date.** For each: is this new, or has it been red? A long-standing red is not a regression; it is normalized failure and it is why nobody reads the pipeline.
3. **Isolate.** Run each failing test alone. Note pass/fail.
4. **Randomize.** Run the suite in random order, twice. Note which failures move.
5. **Classify.** Assign every failure a class from `_quality/SEVERITY.md` §5. No exceptions, no "misc".
6. **Route.** Only now decide what gets worked on.

Steps 3 and 4 take minutes and determine the class for most failures. Skipping them and reasoning
from the stack trace is the classic time sink.

## The classification matrix

| Alone | In suite | Random order | Class |
|-------|----------|--------------|-------|
| fail | fail | fail | deterministic → `REGRESSION` / `STALE` / `WRONG-ORACLE` |
| pass | fail | varies | `FLAKY-ORDER` |
| varies | varies | varies | race → `FLAKY-TIME` |
| pass | pass | pass | environment-only → `FLAKY-ENV` (reproduce at CI's config) |

For deterministic failures, the follow-up question separates the three:

- Did product code change in the failing area? → `REGRESSION`
- Was the behaviour changed on purpose? → `STALE`
- Was the assertion ever right? → `WRONG-ORACLE`

## Reproduction quality

A reproduction is complete when someone else can produce the failure from the artifact alone:

```
REPRO
COMMAND:  <exact command, including flags>
SEED:     <random seed, if any>
ORDER:    <test order or shard, if it matters>
ENV:      <workers, TZ, locale, container image, node/python version>
RATE:     <observed failures / runs>
```

`RATE` is what turns "flaky" into a number. A 1-in-50 failure needs 150 runs to be confident a fix
worked; without the rate, a fix gets declared successful after three green runs and the failure
returns in a fortnight.

## Bug report → reproduction

For an incoming bug report or incident:

1. **Restate the observable.** What did the user see, and what should they have seen? Not "the API is broken" — a request and a wrong response.
2. **Find the smallest input that shows it.** Delete fields, shrink the data, remove steps until removing one more makes it pass.
3. **Prove it on unfixed code.** The reproduction must fail against the current `main`.
4. **Write the guard at the lowest level that shows it** — hand the reproduction to `quality-test`, which owns level selection.
5. **Then, and only then, fix.**

Reversing 3 and 5 produces a test derived from the fix, which passes on any code that resembles
the fix and catches nothing (`_quality/CONTRACT.md` §3).

## Quarantine review

Open every triage with the expiry list. For each entry:

| State | Action |
|-------|--------|
| Expired, fixed | Append a closure record (`outcome: "fixed"`) for that test id; never delete the original line |
| Expired, not fixed, owner present | Delete the test; append `outcome: "deleted"`; file the `BLIND SPOT` as a debt entry |
| Expired, owner gone | Delete the test; append `outcome: "deleted"`; file debt; note the orphaning in the journal |
| Not expired | Leave; count it |

The registry is append-only (`_quality/OPERATIONAL.md` §4): the active quarantine list is the set of
test ids whose **latest** record has no closing `outcome`. Nothing is ever removed.

The count matters. A quarantine list that only grows is a suite being retired one test at a time
without anyone deciding to retire it.

## When triage should stop and escalate

- More than ~30% of the suite is red → this is not triage, it is a broken environment or a bad merge. Fix that first.
- The same root cause produces reds across unrelated areas → a shared fixture, a global, or a dependency. One finding, not twenty.
- Reds correlate with time of day or with CI worker count → `FLAKY-TIME` / `FLAKY-ENV` at suite scope; fix the runner configuration, not the tests.
