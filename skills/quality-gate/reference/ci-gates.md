<!-- quality:deferred -->
# CI Gates — Encoding and Auditing

Purpose: Encoding a criterion as something CI can decide, and auditing the set.
Read when: a criterion has to run automatically, or the existing set needs pruning.
Verified: 2026-08-21 — no automated check.

Read for the `ci` recipe. A gate in a document is advice; a gate in the pipeline is a gate. But a
pipeline full of checks nobody can act on is how bypass becomes routine.

---

## Every check declares its failure mode

Before a check is added, write its row:

| Field | Example |
|-------|---------|
| Check | `mutation score (src/billing) ≥ 0.60` |
| Command | `npx stryker run --mutate 'src/billing/**'` |
| Red means | the suite cannot detect injected defects in billing |
| Developer does | add a test with a named oracle for the surviving mutant listed in the report |
| Runtime | ~4 min |
| Blocking? | yes, `T3`+ only |
| Removal condition | when billing is retired or the score holds above 0.8 for two quarters |

**"Developer does"** is the field that decides whether the check helps. A red with no obvious next
action is noise, and noise is what gets bypassed.

## Blocking vs reporting

Not every check blocks. Split deliberately:

| Blocking | Reporting |
|----------|-----------|
| build, type check | complexity trend |
| test suite, zero new skips | coverage delta |
| security advisories at `CRITICAL` | duplication |
| the tier's required inputs | bundle size (unless it has a hard budget) |
| an explicitly agreed hard budget | style, formatting (auto-fix instead) |

Formatting is auto-applied, never gated. Blocking a merge on whitespace spends the gate's
authority on the one thing that never mattered.

## Speed is a correctness property of a gate

A gate slower than roughly 10 minutes gets worked around: people push and walk away, batch
changes, or merge on green-so-far. Structure for feedback speed:

```
stage 1  (< 2 min, blocking)   lint --quiet, type check, unit tests, changed-file checks
stage 2  (< 10 min, blocking)  integration tests, build, security advisories
stage 3  (nightly, reporting)  mutation, full e2e, load, dependency drift
stage 4  (on T3+ only)         preview deploy, migration dry run, rollback exercise
```

Anything expensive belongs in stage 3 with a **trend alert**, not in the blocking path — except
where the tier requires it (`risk-tiers.md`), in which case it is scoped to the touched module and
runs in stage 4.

## Auditing an existing pipeline

For each check, answer with data:

1. **When did it last block something?** Never → it is either redundant or checking nothing.
2. **Was that block correct?** A check with a history of false blocks is training bypass.
3. **What is its p95 runtime, and what fraction of pipeline time is that?**
4. **Is it flaky?** A check that fails spuriously is worse than absent, because it teaches people that red means "re-run".
5. **Does its red have an actionable next step?**

Output a keep / demote-to-reporting / remove list, each with the evidence. Removing a check is a
real improvement when the evidence supports it; a shorter, trusted gate blocks more real problems
than a long, bypassed one.

## Anti-patterns

- **`continue-on-error: true` on a blocking check.** It reports green. It is not a gate; delete it or fix it.
- **`--passWithNoTests`.** A pipeline that passes when the test command matched nothing has, at some point, been passing for months.
- **Snapshot update flags in CI** (`-u`, `--update-snapshots`). The gate approves whatever happened.
- **Retrying the whole test job on failure.** Hides flakiness and doubles the mean time to red. Retry at the test level, with the flake recorded to the registry (`quality-regression`).
- **A gate that only runs on the default branch.** It finds the problem after the merge, which is after the decision.
- **Required checks that do not run on all paths.** A path filter that excludes the changed file makes the check pass by not existing.

## Minimal gate config skeleton

```yaml
# .agents/quality/gate.yml — the criteria, independent of any CI vendor

# Thresholds referenced as "the project's floor" by criteria and by skill Removal conditions.
# A floor that is not recorded here does not exist; do not invent one at evaluation time.
floors:
  suite_pass_rate: 0.98          # over the last 20 runs
  mutation_score:
    src/billing: 0.60            # per-module; unlisted modules have no mutation floor

tiers:
  T2:
    criteria:
      - id: no-block-findings
        command: "<quality-review invocation>"
        blocking: true
        red_means: "a defect introduced by this change, MEDIUM or above"
        next_step: "address the cited finding or argue it down with evidence"
        remove_when: "never — this is the core criterion"
      - id: new-behaviour-tested
        command: "<project-specific changed-scope test invocation>"
        blocking: true
        red_means: "changed behaviour has no test with a named oracle"
        next_step: "quality-test gap closure"
        remove_when: "never"
  T3:
    inherits: T2
    criteria:
      - id: rollback-verified
        command: "manual — link the exercised rollback"
        blocking: true
        red_means: "no verified undo exists for an irreversible-class change"
        next_step: "exercise the rollback in staging and link the run"
        remove_when: "never"
```

Every tier is a mapping with a `criteria:` list. Mixing a mapping key (`inherits:`) with bare
sequence items at the same level is not valid YAML — verify with a parser before committing, and
make that check part of the `ci` recipe.

Keeping the criteria in a vendor-neutral file is what lets the pipeline be rewritten without
quietly losing a criterion in the translation.
