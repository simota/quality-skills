<!-- quality:deferred -->
# Metric Catalog

Purpose: What each metric measures, and what it does not.
Read when: choosing a metric, or being asked what one means.
Verified: 2026-08-21 — no automated check.

Read during `QUESTION` and `SELECT`. Organised by the decision each metric can change. A metric
that changes no decision is not measured, however easy it is to collect.

---

## Selection rule

> Name the decision. Name the value that would change it. If no threshold flips a decision,
> the metric is a dashboard ornament.

Four to six metrics is a healthy set. Beyond that, nobody reads them, and unread numbers drift
into being wrong without anyone noticing.

---

## Test-signal metrics

| Metric | Definition | Decision it changes | Watch out |
|--------|------------|---------------------|-----------|
| **Mutation score** | killed mutants ÷ viable mutants | whether the suite may be trusted as gate evidence | expensive; scope it to critical modules |
| Line / branch coverage | executed ÷ executable | where to look for unverified behaviour | rises with assertion-free tests; never a headline |
| Suite pass rate | green runs ÷ total runs, over a window | whether CI signal is usable at all | falls silently as quarantine grows |
| Quarantine count | tests skipped with an expiry | whether coverage is quietly shrinking | must include expiry breaches |
| Suite runtime | wall-clock, p50 and p95 | whether developers will keep running it locally | p95 matters more than p50 |

## Defect metrics

| Metric | Definition | Decision it changes | Watch out |
|--------|------------|---------------------|-----------|
| **Escape rate** | defects found post-release ÷ total found | whether pre-release verification is working | falls when reporting falls |
| Defect density | defects ÷ KLoC changed | where to concentrate review depth | depends on how hard anyone looked |
| Origin phase | where the defect was introduced (spec/design/impl) | which stage to invest in | needs honest post-mortems |
| Reopen rate | reopened ÷ closed | whether fixes are addressing causes | the counterweight to MTTR |
| Time-to-detect | ship → first report | whether monitoring is adequate | needs incident timestamps |

## Delivery metrics (DORA)

| Metric | Definition | Decision it changes | Watch out |
|--------|------------|---------------------|-----------|
| Deploy frequency | deploys ÷ time | whether batch size is the bottleneck | needs deploy data, not merge data |
| Lead time for change | commit → production | where the pipeline stalls | commit → merge is a different metric; label it honestly |
| **Change failure rate** | deploys needing remediation ÷ deploys | whether to invest in verification or in recovery | pairs with deploy frequency, always |
| MTTR | incident start → resolved | whether to invest in rollback capability | gamed by closing early; pair with reopen rate |

## Code-structure metrics

| Metric | Definition | Decision it changes | Watch out |
|--------|------------|---------------------|-----------|
| Churn × complexity | commits in 90d × cyclomatic complexity | supplies `quality-debt`'s ranking inputs | formatting sweeps destroy the churn signal |
| Cognitive complexity | nesting- and flow-weighted | which function is genuinely hard to change | tool-defined; pin the tool and version |
| Coupling / fan-in | modules importing this one | blast radius of a change | counts declared imports, not runtime coupling |
| Duplication | duplicated blocks above N tokens | whether a change must be made in 6 places | some duplication is correct; do not target it blindly |

## Review metrics

| Metric | Definition | Decision it changes | Watch out |
|--------|------------|---------------------|-----------|
| PR size | changed lines, p50/p95 | whether reviews can be meaningful at all | the highest-leverage number in this table |
| Time to first review | open → first comment | whether review is a bottleneck | gamed by drive-by "LGTM" |
| Escaped defects per reviewed PR | post-merge defects ÷ PRs | whether review is finding anything | needs defect attribution |

## Explicitly not measured

- **Individual output** — lines, commits, PRs per person. Measures typing, not quality, and changes behaviour destructively.
- **Composite quality scores** — the weights are arbitrary and let one bad axis be hidden by four good ones.
- **Test count** — a large number of worthless tests is worse than a small number of good ones.
- **Comment density** — measures comment writing.
- **Industry benchmarks as targets** — the comparison is never valid; the contexts differ in every way that matters.
