# quality-skills

Six agent skills covering the quality loop, the contracts they share, and the
budgets that keep the set from growing into something nobody can route through.
Each skill owns one question and answers it with evidence that names its source.

| Skill | Owns | Answers |
|---|---|---|
| [`quality-review`](skills/quality-review/SKILL.md) | Defects in a specific change | *What is wrong with this diff?* |
| [`quality-test`](skills/quality-test/SKILL.md) | Test design, coverage, suite health | *What is untested, and what should the test be?* |
| [`quality-regression`](skills/quality-regression/SKILL.md) | Failures over time | *Why did this break, and what stops it recurring?* |
| [`quality-metrics`](skills/quality-metrics/SKILL.md) | Measurement, baselines, trends | *Is quality moving, and by how much?* |
| [`quality-debt`](skills/quality-debt/SKILL.md) | Accumulated cost and repayment order | *What should we fix first, and why that?* |
| [`quality-gate`](skills/quality-gate/SKILL.md) | The release decision and its criteria | *May this ship?* |

## The three ideas the set is built on

**Evidence has rungs, and each output has a floor.** `E0` reasoning alone never
ships. `E1` static · `E2` execution · `E3` automated test · `E4` independent
oracle · `E5` integration · `E6` production. What rises is not effort but
**distance from the hypothesis that produced the code** — `E0` and `E3` can
share the same misunderstanding; `E4` and above cannot. A claim that cannot
reach its floor is not downgraded and shipped anyway: it becomes a `HYPOTHESIS`
carrying the one command that would settle it.

**Independence is the property that makes any of it worth having.** The reviewer
does not write the fix; the author's test is not the oracle; the gate does not
re-derive the evidence it consumes. Every shortcut here is invisible in the
result — a same-author test passes exactly as convincingly as an independent one.

**A finding is graded on the day it is written and never afterwards, so
precision drifts unmeasured.** The findings that were wrong cost the author an
argument, a re-read, sometimes a change that made the code worse — and none of
that cost lands near the review that produced them. So every finding is
adjudicated once its fate is known: `real` · `refuted` · `accepted` · `moot` ·
`open`, with precision reported as `real / (real + refuted)` and its count.

**A rate of one is the more common defect.** No refuted findings almost never
means the review was perfect; it means the findings were phrased so they could
not be refuted, or nobody adjudicated them and `open` was read as agreement. An
unchallengeable review is worth less than an imprecise one
([`_quality/OUTCOMES.md`](skills/_quality/OUTCOMES.md)).

## How it is put together

A skill is loaded in three stages. The **listing** carries `name` and
`description` only, on every turn. **`SKILL.md`** is read in full once a skill
is chosen. Anything it points at is read only when the situation calls for it.

**Selection happens on the description alone**, so every word that selects a
skill appears literally in its description, and
[`quality-registry/capabilities.yaml`](quality-registry/capabilities.yaml) lists
those words per skill. A rule checks the two agree.

**Boundaries live in one file** — that same registry's `not:`. Descriptions
never name a neighbour. If they did, adding a seventh skill would mean editing
the other six.

**Contracts are delivered, not referenced.** A rule kept in `skills/_quality/` is read
on a minority of launches, so the operative part is copied verbatim into every
`SKILL.md` between `<!-- deliver:… -->` markers. `make render` writes it back
and a rule fails on drift.

**Knowledge splits by whether it rots.** `playbooks/` holds judgement and is
budgeted. `reference/` holds what goes stale, carries no line budget, and states
its purpose and a checked-on date instead.

**A model stated in two files needs a check, not a date.** `interest` is fixed in
`_quality/SEVERITY.md` §4 and scored in `quality-debt/reference/interest.md`.
Nothing held the two together, so a band could move in one and not the other and
the only thing standing behind either page was a date, which has no failure mode.
`make figures` re-derives the model from both files — the formula byte-identical,
every band scale the same set on both sides, every worked example recomputed to
the precision it claims, and every divisor drawn from the canonical list. It runs
in `make check` and the pre-commit hook, and five deliberate breaks were each
observed failing it, including one that changes a table's shape so the checker
matches nothing.

Repairing it turned up a sentence in SEVERITY.md §4 that had lost its middle:
it named where the band tables live and then did not say where. The pointer is
restored.

**Budgets are enforced, not intended.**
[`quality-registry/harness.yaml`](quality-registry/harness.yaml) holds every
threshold; `quality-tools/validate.py` decides them and CI fails on a violation.

## Names, and why none of them are generic

A skills directory is flat and shared with every other set on the machine, so a
generic name placed there is a silent collision. **This set is why the rule
exists.** Its install line used to be `cp -R quality-* _common <skills dir>`,
and `_common` in that directory belongs to an unrelated set — running it wrote
into someone else's repository.

**One declaration.** `set: quality` in the harness file is the only place the
name is written; the prefix, the shared directory (`skills/_quality/`), and the label
every document carries all derive from it.

**Every directory this set owns carries the set name.** Carrying the prefix is
not what makes something installable: a skill is a directory holding a
`SKILL.md`, and only those are linked.

**Everything a skill reads lives inside the skill**, reached through symlinks
named `_quality` and `registry`. Relative paths are normalised *lexically*, so
`../_quality/X.md` does not travel back through the install symlink — a shell
follows the link and finds the file, which is what makes this fail quietly.

## Files

| File | What it fixes |
|---|---|
| [`skills/_quality/CONTRACT.md`](skills/_quality/CONTRACT.md) | The rungs, the floor per output, independence, status, residuals, the sweep |
| [`skills/_quality/SEVERITY.md`](skills/_quality/SEVERITY.md) | Severity bands, blocking, debt priority, flaky classes, confidence |
| [`skills/_quality/HANDOFF.md`](skills/_quality/HANDOFF.md) | The seven payloads that cross a skill edge, and the receiver's checks |
| [`skills/_quality/SIZING.md`](skills/_quality/SIZING.md) | How much ceremony a request is worth; when a dialogue is mandatory; the brief |
| [`skills/_quality/VALUES.md`](skills/_quality/VALUES.md) | The order when two goods conflict, rule precedence, and the escape hatch |
| [`skills/_quality/OPERATIONAL.md`](skills/_quality/OPERATIONAL.md) | Read-only defaults, the journal, state files, language, AUTORUN |
| [`skills/_quality/ROUTING.md`](skills/_quality/ROUTING.md) | Guidance. Which skill owns the call when two could take it |
| [`skills/_quality/REPORT.md`](skills/_quality/REPORT.md) | What a person reads: the order, the ceiling per tier, and why the payload is the record |

## Layout

```
quality-skills/
├── README.md
├── Makefile
├── quality-registry/             # budgets, boundaries, routes, delivered blocks
├── quality-tools/                # validate · test_validate · render · pre-commit
└── skills/                       # everything the CLI reads
    ├── _quality/                 # contracts in force on every run
    └── quality-<facet>/          # a SKILL.md is what makes this a skill, and
        │                         # only skills are installed
        ├── SKILL.md              # Owns / Before starting / Decide first /
        │                         # Always·Never / Verify with / Done when
        ├── _quality  -> ../_quality         # short names: the parent scopes them
        ├── registry  -> ../../quality-registry
        ├── playbooks/            # judgement. Budgeted, and must not rot
        └── reference/            # what goes stale. No line budget, dated instead
```

State the skills write — findings, gaps, metrics, debt, flaky registry, verdicts
— lives in the **host project** under `.agents/quality/`, append-only, one
record per event. Those paths are declared as external so the path checker does
not read them as references into this repo.

## Working on it

```sh
make check      # what CI runs: the rules, then proof the rules still fire
make render     # after editing anything in quality-registry/delivered/
make hooks      # run the rules on every commit
```

## Installing

```sh
make link                       # into ~/.claude/skills
make link CLAUDE_DIR=.claude/skills
```

Each `quality-*` skill is linked individually. Nothing un-prefixed is copied
anywhere.

## What this does not guarantee

- **`allowed-tools` is one CLI's mechanism.** Where a tool grant is not
  enforced, the `Never` lines are discipline and nothing more
- **Read-only by class is not "sends nothing".** The class governs local writes
- **The fixtures do not model how a model chooses.** They catch a missing or
  duplicated signal, not a misroute
- **`Verified:` dates are not checked against anything.** A stale reference file
  with a fresh date passes; the date makes staleness visible, it does not detect it
- **Nothing here checks that a floor was actually reached.** The contract says
  which rung an output needs; whether the run honoured it is read by a person
- **This set overlaps another.** Installed alongside `coding-skills`, both
  `quality-test` and `coding-test` sit in the same listing and compete. The
  namespace rule prevents directory collisions, not selection competition

## The published overview

[`docs/index.html`](docs/index.html) is a generated page — every figure on it is
read off this repository, the way `make figures` recomputes what the reference
layer states. **Do not edit it by hand**: `tools/pages.py` in the `agent-toolkit`
repository writes it, `tools/pages.py --check` fails when it is behind, and
`.github/workflows/pages.yml` here only publishes what is committed.

