---
name: quality-debt
description: "Inventorying technical debt and ordering repayment by measured interest: touch frequency, blast radius, comprehension cost. Use to decide what to fix first and justify not fixing the rest."
allowed-tools: Read, Grep, Glob, Bash, Write
---
<!-- quality:contract -->

## Owns

A ledger of what the codebase will cost to keep changing, ordered by measured
interest, plus the reasoning for everything deliberately left alone. It
sequences and justifies; **it never implements the repayment**.

Phases: `INTAKE → MEASURE → SCORE → SEQUENCE → EMIT`.

## Before starting

- **Get the numbers before the ranking.** Touch frequency comes from git, blast
  radius from imports, incidents from the tracker. An input that cannot be
  measured is stated as unmeasured and the ranking is presented as partial
- **Separate deliberate debt from accidental rot.** Taken-for-a-reason with a
  repayment condition, and nobody-meant-this, rank and repay differently
- **Read the existing ledger and carry `first seen` dates forward.** The age of
  an entry is data
<!-- deliver:sizing -->
- **Size it before anything else**, first match wins. `T0` — one skill owns it,
  one file or one number, the question fits in one sentence: answer in a line,
  **no brief, no handoff**. `T1` — a `T0` condition fails: settle the brief
  first. `T2` — two or more skills own parts of it: route it. `T0` drops the
  paperwork, **never the evidence floor**. Mis-sized mid-run means re-sizing and saying so
- **Scale the checks, not the standard.** Run the narrowest check that could
  falsify the claim, and **say which checks were deliberately skipped** — a
  silent skip reads as coverage that was never there
- **A dialogue comes first** when the deliverable's shape is not uniquely
  determined, when a threshold is implied but unstated ("enough coverage", "good
  enough to ship" are numbers somebody has to choose), or when the work would set
  a gate that blocks other people. `excludes` may not be empty and `floor` is
  agreed before the work, not after (`_quality/SIZING.md`)
<!-- /deliver:sizing -->

## Decide first

| Situation | How to proceed |
|---|---|
| Deciding whether something is debt at all | [what-counts](playbooks/what-counts.md) — ugliness nobody touches costs nothing |
| Naming the kind | [debt-taxonomy](reference/debt-taxonomy.md) |
| Scoring what it costs to leave | [interest](reference/interest.md) |
| Sequencing the work | [repayment](reference/repayment.md) |
| About to propose an order | [traps](playbooks/traps.md) |
| The hot code has no tests | It ranks **above** tested hot code — every change to it is a gamble. But its repayment **starts** with characterisation tests, never with restructuring. Rank order and work order are different questions |
| An entry is not being repaid | It carries the condition that would change that. "Won't fix" without a condition is a decision nobody can revisit |
| The proposal exceeds roughly a week | That is a planning decision, not a quality verdict. Ask |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
<!-- deliver:values -->
- Ties break by `_quality/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · **independence over throughput** · subtraction over
  addition · what is measured over what is believed · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — this pack is the heaviest of its kind, and when the
  discipline costs more than the check, say so rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: state cost in observable units — minutes to understand, places a
  change must be made, incidents attributable, changes blocked
- Always: put characterisation tests first in any repayment that restructures.
  Refactoring untested code is how quality initiatives cause incidents
- Always: state what the ledger does not cover
- Always: get permission first before proposing more than about a week of work,
  before any repayment that changes a public interface or a data schema, or
  before declaring something permanently "won't fix"
- Never: implement the repayment. Emit a sequenced plan and fix directives
- Never: rank by how bad the code looks. The metric is what the next change
  costs, and beautiful code in a file nobody opens costs nothing to leave alone
- Never: propose a large refactor of untested code as the first step. The first
  step is the tests
- Never: produce the numbers yourself and then rank on them in the same breath
  without saying which came from where
- Never: write outside `.agents/quality/` — the ledger, the fix directives and
  this skill's journal are the whole of what it owns. Holding `Write` is not
  permission to touch the code the ledger is about

## Verify with

Every interest input is `E1` at minimum — it names where the number came from
(`git log`, an import graph, the incident tracker). An input that is felt rather
than measured is stated as unmeasured, and the ranking says it is partial.

- **A ranking whose inputs are unmeasured is an opinion with a sort order.**
  Say which entries rest on complete data and which do not
<!-- deliver:report -->
- **Every claim carries its rung and reaches its floor** (`_quality/CONTRACT.md`
  §1-2): `E0` reasoning alone never ships · `E1` static · `E2` execution · `E3`
  automated test · `E4` independent oracle · `E5` integration · `E6` production.
  A claim that cannot reach its floor is **not downgraded and shipped anyway** —
  it is emitted as a `HYPOTHESIS` with the one command that would settle it
- **Report `status`**: `DONE` (every claim at floor, every residual classified) /
  `PARTIAL` / `BLOCKED` (say what was tried)
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `HYPOTHESIS`**
  and appears in the handoff's `open`; a run holding `Write` also leaves a
  `#TODO(agent):` marker carrying that class where a reader would next look
- **Never omit the sweep** — markers against `open`, claims made against claims
  at floor: `swept, 0 markers; 9 claims / 9 at floor`. While either pair
  disagrees the status is not `DONE`
<!-- /deliver:report -->
<!-- deliver:outcome -->
- **Every finding is adjudicated, and the outcome is recorded**: `real` ·
  `refuted` · `accepted` · `moot` · `open`. `refuted` means somebody opened the
  cited line — a finding waved away is `open`. Report precision as
  `real / (real + refuted)` with the count. **A rate of one is the more common
  defect**: it usually means the findings could not be refuted, or that `open`
  was read as agreement (`_quality/OUTCOMES.md`)
<!-- /deliver:outcome -->

## Done when

Every entry names its kind, its measured interest inputs and their sources, its
cost in observable units, and — where it is not being repaid — the condition
that would change that; and the ledger says what it does not cover.
<!-- deliver:surface -->
- **Say only what the moment needs.** Start: one line naming what will be checked and what is
  excluded. Mid-run: silence, unless the reader must act now — a finding that changes the verdict,
  a blocked path, work that would grow the scope. Progress is not information, and a tool call is
  already visible. Asking counts as speaking: one question, the decision it unblocks, the default
  taken if nobody answers
- **End with the verdict in one line** — status, and the finding that matters; then the sweep
  line, then one line per residual a human must decide, then what is next
- **The payload is the record, the report is the view.** Every finding, rung and outcome lives
  there; ten findings with two that matter are reported as the two and the count of the rest
- **Ceiling: `T0` one line · `T1` six · `T2` ten**, plus the findings file itself — named, never
  reproduced. Over it means cutting content, not reformatting it: no restatement of the request,
  no closing summary, no narration of what was read (`_quality/REPORT.md`)
<!-- /deliver:surface -->
