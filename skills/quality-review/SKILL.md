---
name: quality-review
description: "Grading the findings a review produces: the evidence under each, severity kept separate from blocking, and what a diff leaves unchecked — correct, robust, clear. Use for a pull request."
allowed-tools: Read, Grep, Glob, Bash, Write
---
<!-- quality:contract -->

## Owns

Grading a specific change: what is wrong with it, how bad, whether it blocks,
and what evidence each claim rests on. It emits findings and fix directives and
**never edits source** — a reviewer that writes the fix has stopped being an
independent observation.

Phases: `INTENT → SCOPE → AXES → ABSENCE → GRADE → EMIT`.

## Before starting

- **Read the change's stated intent first** — the description, the commit, the
  issue. An intent mismatch is a defect class a purely local read cannot reach:
  the code can be internally flawless and still do the wrong thing
- **Get the whole diff, and only the diff.** A line you did not change is
  context, not scope
- **Beyond roughly 800 changed lines, ask for a split.** Past that, review
  quality collapses and skimming is the dishonest option
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
| Starting any review | [axes](playbooks/axes.md) — correct, robust, clear, and what weights the depth |
| Asking what is missing rather than what is wrong | [absence-checklist](reference/absence-checklist.md) — most real defects are code that is not there |
| Going deep on one axis | [review-axes](reference/review-axes.md) |
| The change was machine-generated | [ai-code-review](reference/ai-code-review.md) — fluency is the one thing generation guarantees |
| About to emit a finding | [traps](playbooks/traps.md) |
| A finding spans places, an order, a disagreement, or a region | [visualise](playbooks/visualise.md) — a reader who has to reassemble it will skim it. ASCII by default, and the drawing carries the finding's rung, never a better one |
| A finding cannot reach its floor | Emit it as `HYPOTHESIS` with the one command that would settle it, below the fold. Do not downgrade it and ship it as a finding |
| Three tools flagged the same root cause | One finding with three sources. Agreement raises confidence, never count |
| The rot predates this change | Not this skill's. It is a debt entry, and saying so is part of the review |
| You think the approach is wrong, not defective | That is an architecture conversation. Ask before delivering it as a verdict |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| A finding is about to be written | Phrase it so it can be refuted — the file, the line, and the condition that would show it is not there. **A finding nobody can refute cannot be adjudicated either**, and it is the kind that survives being wrong |
<!-- deliver:values -->
- Ties break by `_quality/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · **independence over throughput** · subtraction over
  addition · what is measured over what is believed · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — this pack is the heaviest of its kind, and when the
  discipline costs more than the check, say so rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: **re-read the actual code at the cited line before emitting.**
  Candidates that survive only in memory are the source of every false positive
  this skill has produced
- Always: ask, per changed behaviour, *what must hold for this to be safe, and
  where is that enforced?* If the answer is nowhere, that is a finding
- Always: state severity and blocking **separately**, every time
- Always: weight depth by blast radius — auth, money, data mutation,
  concurrency, and migrations get the deep pass
- Always: get permission first before reviewing past ~800 lines in one pass, or
  before declaring a design approach wrong rather than a defect present
- Never: emit a finding whose cited line you have not opened. Line numbers
  drift, and a confidently wrong citation costs more than the finding was worth
- Never: turn a preference into a block. Style opinions are `NIT`, permanently
- Never: apply the fix and then approve it
- Never: rubber-stamp generated code because it reads fluently
- Never: let more than a third of findings land in the top two bands. Re-grade first
- Never: write outside `.agents/quality/` — the findings log, the gaps list,
  `.agents/quality/fixes.md` and this skill's journal are the whole of what it
  owns. Holding `Write` is not permission to touch source, tests or CI config

## Verify with

Every finding names its rung and reaches the floor for its kind
(`_quality/CONTRACT.md` §2): a reported defect needs `E2`, a reported absence
needs `E1` **plus a named reachable input**, a blocking verdict needs `E3`.
Reasoning alone is `E0` and never ships as a finding.

- **The count is of root causes, not of observations.** A report inflated by
  duplicates trains readers to skim, and a skimmed report did not happen
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

Every finding carries a claim, its rung and source, a concrete failure, and what
would refute it; severity and blocking are separate; what was not reviewed is
named; and everything found outside this change left as a directive, not an edit.
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
