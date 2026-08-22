<!-- quality:deferred -->
# Interest — Ranking What to Repay

Purpose: The inputs that make up an interest score, and where each number comes from.
Read when: scoring an entry, or explaining why one outranks another.
Verified: 2026-08-21 — `make figures` re-derives this page against `_quality/SEVERITY.md` §4 on
every run: the formula byte-identical in both files, every band scale the same set on both sides,
and both worked examples recomputed to the precision they claim. The three command warnings below
were confirmed by running them in a fixture repository: `rev-list --count` on one path returned
the commit count, the `--name-only | grep -c` form on a directory returned commits × files, and
`grep -c` printed 0 and exited 1 on no matches.

Read during `MEASURE-INTEREST` and `RANK`. The formula and the canonical band scale are in
`_quality/SEVERITY.md` §4; this file is how to get each raw input from data rather than from
feeling, and how to map it to a band.

```
interest = (touch_score × blast_score × comprehension_score) / confidence_of_fix
```

Every operand below is a **band score**. Measure the raw value, then map it. Substituting raw
counts and minutes into the formula produces a number off the scale by three orders of magnitude.

---

## Input 1 — touch_score

Commits touching **one file** in the last 90 days.

```sh
git rev-list --count --since="90 days ago" HEAD -- <file>
```

Count commits, not changed-file lines. The `--name-only | grep -c` form counts one line per file
per commit, so pointing it at a directory multiplies the count by the files each commit touched —
and `grep -c` exits 1 on zero matches, which is a legitimate band (0 commits), not an error.

Exclude sweeps that destroy the signal — mass formatting, renames, license headers — by hash or
by message pattern, and **record which you excluded**.

| Commits / 90d | Value |
|---------------|-------|
| 0 | 0.1 — near-frozen; almost nothing here is worth repaying |
| 1–3 | 0.5 |
| 4–10 | 1.0 |
| 11–25 | 2.0 |
| 26+ | 3.0 — this file is where the team lives |

The zero row is doing most of the work in this table. Ugly frozen code has an interest of
approximately zero, and every ledger contains some.

## Input 2 — blast_score

Modules that import it, transitively, stopping at a boundary layer (package, service, bounded
context). Note the direction: you want **importers of** the target, not the target's own
dependencies.

```sh
# rough, per ecosystem — count importers
grep -rln "from '.*<module>'" src/ | wc -l      # JS/TS
grep -rln "import .*<module>" --include='*.py' . | wc -l

# Go — transitive importers. `go list -deps` points the other way (it lists what a
# package depends ON), so it cannot answer this question.
go list -json ./... | jq -s --arg m '<module/package>' \
  '[.[] | select((.Deps // []) | index($m))] | length'
# direct importers only: replace .Deps with .Imports
```

| Importers | Value |
|-----------|-------|
| 0–1 (leaf) | 0.5 |
| 2–5 | 1.0 |
| 6–20 | 2.0 |
| 20+, or crosses a service boundary | 3.0 |

A public API or a shared type crosses boundaries you cannot grep. Say so and take the top value.

## Input 3 — comprehension_score

Minutes for a competent stranger to safely make a small change. This is the one **estimated**
input — there is no command for it — and it is always flagged as estimated in the output.

Estimate the minutes, then map to a band. The signals below are **evidence for choosing a higher
band**, not additive modifiers: they are how you justify an estimate someone else can challenge,
not a second arithmetic on top of it.

| Signal | Points toward |
|--------|---------------|
| cognitive complexity > 15 in the entry function | the hour-plus bands |
| the invariant is enforced in more than one file | the hour-plus bands |
| no tests covering the behaviour | the hour-plus bands |
| naming contradicts behaviour | the hour-plus bands |
| a comment says "do not change this" with no reason | the top band, plus a separate finding |

| Estimate | Value |
|----------|-------|
| under 15 min | 0.5 |
| 15–60 min | 1.0 |
| 1–4 hours | 2.0 |
| "ask the one person who knows" | 3.0 |

The last row is a bus-factor finding as much as a debt entry; note it as both.

## Input 4 — confidence_of_fix

The divisor, and the one that most changes the answer. **Values are defined once, in
`_quality/SEVERITY.md` §4** — do not restate or extend them here; a second rubric is a loosening of
a higher-precedence file.

Dividing by a small number **raises** interest — correct, and frequently misread. High interest
with low confidence does not mean "refactor it now". It means the entry is expensive *and*
dangerous, so it ranks high **and** its repayment sequence starts with characterization tests
(`repayment.md`), not with restructuring.

## Worked example

Raw measurement on the left of each arrow, band score on the right. Only band scores enter the
formula.

```
Entry:  src/billing/invoice.ts — invoice total assembled across 4 call sites
touch:  18 commits / 90d                 → 2.0   (git rev-list --count, sweeps excluded: none)
blast:  9 importers                      → 2.0   (grep, src/ only)
compr:  ~90 min (complexity 22, no tests) → 2.0  (ESTIMATED)
conf:   no tests, money, stateful        → 0.3
interest = (2.0 × 2.0 × 2.0) / 0.3 ≈ 27
```

Compare against a competing entry:

```
Entry:  src/legacy/reportBuilder.ts — 900-line class, universally disliked
touch:  0 commits / 90d                  → 0.1
blast:  1 importer                       → 0.5
compr:  ~4 h                             → 2.0   (ESTIMATED)
conf:   no tests                         → 0.3
interest = (0.1 × 0.5 × 2.0) / 0.3 ≈ 0.3
```

Two orders of magnitude apart — and the low one is the file everyone complains about. That gap is
the entire reason the ledger is ordered by measured inputs rather than by discussion. What the
numbers license is the **order**: invoice.ts is repaid before reportBuilder.ts. They do not
license "invoice.ts is 80× worse".

## Reporting the ranking

- Show the four inputs per entry — raw measurement **and** band score — with sources, and mark the estimated one.
- Order by interest; break ties by blast score.
- State the arithmetic. A ranking whose numbers are not shown is an opinion with decimals.
- Where an input could not be measured, say which, and present the ranking as partial.
- Report interest to no more than two significant figures, and report **rank position** as the result. The band values are a fixed convention of this pack, not a measurement; showing the arithmetic does not make the calibration sourced, and a decimal implies a precision the bands do not carry.
