<!-- quality:contract -->
# SIZING — how much ceremony the request is worth

Ceremony **above** what a request needs is what gets a harness worked around.
Ceremony **below** it is how an unevidenced claim ships. Both come from the same
move — choosing the tier for comfort — so the tier is read on first match.

## The three tiers

| Tier | All of these hold | What it costs |
|---|---|---|
| `T0` | One skill obviously owns it · one file or one number · the question fits in one sentence | Answer in a line. **No brief, no handoff** |
| `T1` | One skill owns it, but a `T0` condition fails | Settle the brief, then run. Handoff on return |
| `T2` | Two or more skills own parts of it, or a verdict depends on another skill's output | Route it: settle the brief once, run the chain, one report covers every stage |

`T0` drops the paperwork. **It never drops the evidence floor** — a one-line
answer still names its rung, and a `T0` that cannot reach `E1` is a `HYPOTHESIS`,
not a finding.

**Finding mid-run that the tier was wrong means re-sizing and saying so.** A
`T0` review of one file that has turned into a debt inventory is a `T1` that was
mis-sized.

## Scale the checks, not the standard

The default is **the narrowest check that could falsify the claim being made**,
not the full battery. A one-line copy change does not get a mutation-testing
pass.

**State which checks ran and which were deliberately skipped.** A silent skip
reads as coverage that was never there — which is the same failure as an
unevidenced claim, arriving by a quieter route.

## When a dialogue is required first

Before executing, any of these makes the dialogue mandatory:

- The shape of the deliverable is not uniquely determined
- What counts as achieved does not fit in one sentence
- The request carries a word with no achievement condition — "improve quality",
  "make it more reliable", "clean up the tests", "raise the bar"
- A **threshold** is implied but unstated. "Enough coverage", "acceptable
  flakiness", and "good enough to ship" are numbers somebody has to choose, and
  an agent choosing them silently has taken the decision
- The work would set or move a gate that blocks other people's merges
- A term in the request, the code or the suite carries two meanings, or one
  concept goes by two names, and the host's glossary does not settle it

**Reading to find out is not executing.** The suite, the history, the existing
gate definition, and the journal answer more questions than the person can. And
never open a dialogue over one file with one obvious check.

## The brief the dialogue produces

Conclusions recorded as data, not as an understanding. Execution reads only this.

```yaml
goal: "<one sentence describing the state once achieved>"
delivers: "<a single artifact>"   # split the work if this goes plural
axes: [...]                       # what counts as achieved. Never one axis
excludes: [...]                   # what will not be checked. May not be empty
baseline: "<the observed starting state, with the command that produced it>"
floor: "<the evidence rung this run must reach>"   # _quality/CONTRACT.md §2
open_questions: []                # execution does not begin until empty
terms: {}                         # the names this run uses, spelled as the glossary spells them
```

- **`baseline` carries its command or it is not a baseline.** "The suite was
  green" is a memory; `pytest -q` with its output is a starting state
- **`floor` is agreed before the work, not after.** Choosing the rung once the
  evidence is in is how a hunch becomes a finding
- **`excludes` may not be empty.** It is the only thing a downstream skill can
  check itself against
- **Execution does not begin while `open_questions` is non-empty**

## Terms — one name per concept, one concept per name

The host's glossary is `.agents/glossary.md` when it exists. Read it before the
brief is settled and write with its names only — finding, directive, journal,
report alike. A term the work has to coin goes into `terms`, and at `T1` or
above it is proposed in the dialogue rather than invented on the way.

**An ambiguous or inconsistent term is never resolved by a silent choice.**
Two meanings for one word, or two names for one concept, is a question
(`_quality/REPORT.md`): one question, with the default named — the spelling
the code already uses most. The answer lands in `terms` and is appended to the
glossary as `term · means · not to be called`, so the next run inherits the
decision rather than the ambiguity. A `T1` may create the glossary for its
first settled term; a `T0` never does — it marks what it found `OUT-OF-SCOPE`
and moves on.

## Constraints do not loosen mid-run

`axes`, `floor`, `baseline`, and `excludes` are fixed at the start. About to
break one — stop and hand back. **A floor quietly lowered to let a finding ship
is the failure this pack exists to catch**, arriving from the inside.
