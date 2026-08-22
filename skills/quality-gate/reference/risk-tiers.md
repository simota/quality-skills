<!-- quality:deferred -->
# Risk Tiers — Scaling the Gate to the Change

Purpose: How deep the gate goes, by what the change can cost.
Read when: sizing a gate to a change.
Verified: 2026-08-21 — no automated check.

Read during `TIER`. Tier is determined by the **surface the change touches** and by
**reversibility** — never by urgency, size, or how the change was described in the PR title.

---

## Assignment

Walk the list top-down and take the **first** tier whose description matches. A change touching
several surfaces takes the highest.

This file is the single source for both the tier surfaces and the required inputs; the table in
`quality-gate/SKILL.md` lists surfaces only and defers here for inputs.

| Tier | Matches when the change touches… |
|------|----------------------------------|
| `T4` | anything irreversible: data deletion, a one-way migration, an external commitment (email sent, payment captured, public API removed) |
| `T3` | auth, permissions, tenancy, money, data mutation, schema migration, a published API contract, cryptographic material, or concurrency primitives |
| `T2` | business logic, user-visible behaviour, a new dependency, a feature flag default, or infrastructure configuration |
| `T1` | internal refactor with existing passing coverage, test-only changes, developer tooling |
| `T0` | documentation, comments, non-shipped configuration |

## Required inputs per tier

Floor values (`floors.*`) live in `.agents/quality/gate.yml`. A criterion whose floor is not
recorded there is unevaluable — author it via the `design` recipe rather than inventing a number.

| Input | T0 | T1 | T2 | T3 | T4 |
|-------|:--:|:--:|:--:|:--:|:--:|
| Build passes | ● | ● | ● | ● | ● |
| Suite green, zero skips added | | ● | ● | ● | ● |
| `quality-review`, no `BLOCK` | | ● | ● | ● | ● |
| New behaviour has a test with a named oracle | | | ● | ● | ● |
| Suite pass rate ≥ `floors.suite_pass_rate` | | | ● | ● | ● |
| Mutation score on touched module ≥ `floors.mutation_score[<module>]` | | | | ● | ● |
| Integration or preview-environment evidence | | | | ● | ● |
| Rollback verified (exercised, not asserted) | | | | ● | ● |
| Migration reversibility or forward-fix stated | | | | ● | ● |
| Named human approver | | | | | ● |
| Dry run against production-like data | | | | | ● |
| Explicit undo plan, written before execution | | | | | ● |

## Traps in assignment

- **A one-line config change can be `T3`.** A timeout, a retry count, a pool size, or a feature-flag default has production blast radius and a two-character diff. Tier follows surface, not line count.
- **"Just a refactor" is `T1` only if coverage is shown to exist.** Without it, a behaviour-preserving claim is unverifiable and the change is `T2` at minimum.
- **A dependency bump is `T2`**, and `T3` if the dependency touches auth, crypto, serialization, or the database driver. The diff is one line; the behaviour change is unbounded.
- **Urgency does not lower the tier.** It shortens the time available, which is an argument for a smaller change — not for a smaller gate. Say this plainly when it comes up; it is the most common pressure on a gate and the one that most damages it when it succeeds.
- **A revert is not automatically `T0`.** Reverting a `T3` change is a `T3` change, especially if data was written under the new behaviour.

## Tier and verdict interaction

- At `T0`/`T1`, `NO-GO` should be rare. If it is not, the gate is checking the wrong things at those tiers.
- At `T3`/`T4`, `GO-WITH-CONDITIONS` is rarely appropriate: the conditions are usually about safety, and deferred safety is not a condition (`criteria.md`).
- At `T4`, an override is not available. If a `T4` criterion is unmet, the change waits.
