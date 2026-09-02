<!-- quality:deferred -->
# Review Axes — Defect Catalogue

Purpose: What each axis looks for, in depth.
Read when: going deep on correctness, robustness, or clarity.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read during `AXES`. Ordered by yield, not by category tidiness.

---

## Reading order

1. **Deletions first.** Removed guards, removed error handling, removed tests. Highest yield per line, lowest attention in practice.
2. **Then boundaries.** Every place the change touches an edge: user input, an external call, a DB write, a file, a queue, another team's module.
3. **Then the happy path.** Cheapest to read, least likely to be wrong, so it goes last — not first, which is where the eye wants to start.
4. **Then names.** Only after behaviour is settled. A misleading name is a real defect but grading it early crowds out the correctness pass.

## Axis 1 — Correct

| Pattern | What to look for |
|---------|------------------|
| Off-by-one | `<` vs `<=`, slice bounds, loop terminators, pagination `offset` reuse |
| Inverted condition | negation added or removed; `!` inside a compound; early-return polarity flipped |
| Wrong unit | ms vs s, bytes vs KB, cents vs currency units, 0-indexed vs 1-indexed month |
| Lost update | read-modify-write with no lock, no version, no atomic operation |
| Wrong default | a new optional parameter whose default changes existing callers' behaviour |
| Copy-paste divergence | a duplicated block where one copy was updated |
| Precedence | mixed `&&`/`||`, `??` with `||`, ternary nesting, bit ops without parens |
| Type coercion | string/number comparison, truthiness on `0`/`""`, `NaN` propagation |
| Async ordering | missing `await`, fire-and-forget, `Promise.all` where order matters, unawaited cleanup |

## Axis 2 — Robust

| Pattern | What to look for |
|---------|------------------|
| Empty and singular | zero rows, one row, exactly-at-limit; the code was written for "several" |
| Null / undefined | a new field on an existing record is absent on old rows — always |
| Unbounded growth | an array, cache, map, or log line inside a loop with no ceiling |
| Missing timeout | any network, subprocess, lock, or queue wait without one |
| Partial write | multi-step mutation with no transaction, no rollback, no idempotency key |
| Swallowed error | `catch` with no rethrow, no log, no metric; `except: pass`; ignored return code |
| Retry without backoff | a retry loop that turns one failure into a thundering herd |
| Resource leak | opened and not closed on the error path specifically |
| Concurrency | shared mutable state reachable from two requests; a "singleton" cache written per-request |
| Failure mode | when this dependency is down, does the system degrade or does it lie? |

## Axis 3 — Clear

| Pattern | What to look for |
|---------|------------------|
| A name that lies | `isValid` that mutates, `get*` that writes, `count` holding a list |
| Invariant with no home | a rule enforced by convention across three files and stated in none |
| Boolean parameter | `render(true, false)` at the call site |
| Three jobs in one function | the summary sentence needs an "and" |
| Comment contradicting code | one of them is wrong; find out which before assuming it's the comment |
| Magic value | a literal whose meaning is not derivable at the call site |

Grade `Clear` findings `LOW` or `NIT` **unless** the unclarity is producing a wrong result — a
misleading name that has already caused a caller to misuse the function is a `MEDIUM` correctness
finding wearing a readability costume.

## Intent alignment

Independent of the three axes, and frequently the highest-severity finding in a PR:

- Does the diff do something its description does not mention? (unrelated refactor, dependency bump, flag default, log removal)
- Does the description promise something the diff does not do?
- Does the change alter behaviour for existing data or existing callers, without saying so?
- Is a migration required and absent?

An unmentioned behaviour change is at minimum `MEDIUM` regardless of how correct it is, because
nobody downstream is expecting it.

## Framework-specific hot spots

| Stack | Look at |
|-------|---------|
| React / Vue / Svelte | effect dependency arrays, state updates in render, keys on lists, stale closures over props |
| Node / server | unhandled rejection, missing `await` on a mutation, per-process cache treated as per-request |
| SQL / ORM | N+1 introduced by a new field access, missing index on a new filter column, transaction scope |
| Python | mutable default argument, broad `except`, generator consumed twice |
| Go | error shadowed by `:=`, goroutine leak, loop-variable capture, ignored `err` |
| Rust | `unwrap` on a path reachable from input, lock held across `await` |
| Any typed language | a widened type (`any`, `interface{}`, `Object`) added to make an error disappear |
