<!-- quality:contract -->
# Operational Defaults (quality-* pack)

> **Tier:** `spine` — in effect on every run of every `quality-*` skill.

Shared operational contract for the six quality skills. This pack is **self-contained**: it never
reads from `~/.claude/skills/_quality/`. Everything a `quality-*` skill needs is in this directory.

---

## 1. Read-only by default

`quality-review`, `quality-metrics`, and `quality-debt` **never modify source files.** They emit
findings, ledgers, and plans. `quality-test` and `quality-regression` write tests and test
infrastructure only. `quality-gate` writes CI/gate configuration only.

Whenever a quality skill concludes that production code must change, it emits a **fix directive**
(`_quality/HANDOFF.md` § Fix Directive) rather than editing. The reason is not timidity: a reviewer
that also writes the fix loses the independence that made the review worth anything
(`_quality/CONTRACT.md` § Independence).

## 2. Journal

Each skill maintains `.agents/quality/<skill>.md` — append-only, one entry per invocation:

```
## YYYY-MM-DD — <scope: PR #, path, or release tag>
- Verdict: <the skill's headline output>
- Evidence: <E-level reached, per _quality/CONTRACT.md>
- Carried forward: <what the next run must re-check>
```

**Carried forward is the load-bearing line.** A quality run that leaves nothing behind is a run
whose findings get rediscovered from scratch next quarter.

Activity log: append one row to `.agents/PROJECT.md` if that file exists:
`| YYYY-MM-DD | quality-<name> | (action) | (scope) | (verdict) |`

Never create `.agents/PROJECT.md` if it does not already exist — that is the host project's file.
This prohibition is specific to that one file; `.agents/quality/` and its contents are created
freely on first use (§3 First run).

## 3. State files

Findings, metrics, debt inventories, and flaky registries are **stateful**. Store them as
committed data, not chat output. Payload shapes for each are in `_quality/HANDOFF.md` §0.

| Artifact | Path | Owner | Kind |
|----------|------|-------|------|
| Findings | `.agents/quality/findings.jsonl` | `quality-review`, `quality-regression` | event log |
| Fix directives | `.agents/quality/fixes.md` | any quality skill | event log |
| Coverage gaps | `.agents/quality/gaps.md` | `quality-review`, `quality-regression` | event log |
| Metric snapshots | `.agents/quality/metrics.jsonl` | `quality-metrics` | event log |
| Debt ledger | `.agents/quality/debt.md` | `quality-debt` | event log |
| Flaky registry | `.agents/quality/flaky.jsonl` | `quality-regression` | event log |
| Gate verdicts | `.agents/quality/verdicts.md` | `quality-gate` | event log |
| Gate definition | `.agents/quality/gate.yml` | `quality-gate` | **mutable definition** |

**Event logs are append-only.** Never rewrite history — a trend line reconstructed after the fact
is a story, not data. State changes by **appending a superseding record with the same `ID` and a
later date**; current state is the latest record per `ID`. Every event-log record carries a
`status` (or `outcome`) field so that open/closed is derivable without deleting anything.

**`gate.yml` is the one exception**: it is the current criteria set, edited in place. Criteria are
added, demoted to reporting, and removed (`quality-gate` audits them), which
an append-only log cannot express. Its history is git's job.

### First run

`.agents/quality/` and any state file a skill owns are **created on first use** — this is
authorized, expected, and needs no confirmation. The prohibition in §2 applies only to
`.agents/PROJECT.md`, which belongs to the host project.

A missing state file means **empty, not broken**. Specifically:

| Skill | Missing state | Behaviour |
|-------|---------------|-----------|
| `quality-gate` | no `gate.yml` | run the `design` recipe first, then the requested one — never `NO-GO` for want of criteria that were never authored |
| `quality-debt` | no debt ledger | empty ledger; the run is pure intake |
| `quality-regression` | no `flaky.jsonl` | empty registry; no quarantine list to review |
| `quality-metrics` | no `metrics.jsonl` | `baseline` recipe; report that no comparison is possible yet |
| `quality-review` / `quality-test` | no findings log or gap list | nothing carried forward; proceed |

## 4. Output language

Follows the CLI global config (`settings.json` `language`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`).
Code, identifiers, file paths, CLI commands, metric names, and severity labels stay in English.
`SKILL.md` structure itself — headings, tables, subcommands — is authored in English.

## 5. AUTORUN

When a `quality-*` skill receives `_AGENT_CONTEXT`, parse `task_type`, `description`, and
`Constraints`; run the standard workflow without narration; return the `_STEP_COMPLETE` envelope
defined in `_quality/HANDOFF.md` §7, carrying the payload named there.
