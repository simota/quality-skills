---
name: quality-gate
description: "Rendering the ship decision from evidence, and designing the gate criteria that encode it: conditions, blocking, and overrides. Use before a release, or when defining a definition of done."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- quality:contract -->

## Owns

The verdict — and the criteria that make the verdict reproducible next time. It
**consumes evidence and never produces it**: if the inputs are unobtainable the
verdict is insufficient evidence, never a guess in their place. It writes CI and
gate configuration only.

Phases: `SCOPE → ACQUIRE → EVALUATE → DECIDE → RECORD`.

## Before starting

- **Fix the scope precisely**: this diff, this release tag, this deploy to this
  environment. A verdict whose scope is vague is read as covering everything
- **Acquire the inputs by the two named routes, never by analysing the change
  yourself.** The moment this skill re-derives evidence, it is grading its own work
- **Name which skills contributed and which did not run.** An absent input is
  part of the verdict, not a gap in it
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
| Rendering any verdict | [verdicts](playbooks/verdicts.md) — the three outcomes, how inputs are acquired, and how deep the gate goes per risk tier |
| Designing or auditing criteria | [criteria](reference/criteria.md) — every criterion names the decision it changes |
| Encoding a criterion in CI | [ci-gates](reference/ci-gates.md) |
| Someone wants past a gate | [overrides](reference/overrides.md) |
| Sizing the gate to the change | [risk-tiers](reference/risk-tiers.md) — applying the payments gate to a README change trains people to bypass gates |
| About to decide | [traps](playbooks/traps.md) |
| No gate definition exists yet | Design one first, then decide. **Never render a stop for want of criteria nobody ever authored** |
| The evidence is stale | Evidence produced against a different ref is absent evidence. Say so rather than reusing it |
| Conditions are attached to a pass | Each needs an owner and a date. Without both it is a pass with wishful thinking attached |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| An override is granted | It is a finding adjudicated as `accepted`, with a name and a reason, and it is recorded like one. An override with no recorded outcome can never be shown to have been wrong |
<!-- deliver:values -->
- Ties break by `_quality/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · **independence over throughput** · subtraction over
  addition · what is measured over what is believed · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — this pack is the heaviest of its kind, and when the
  discipline costs more than the check, say so rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: emit `NOT COVERED` with every verdict. A verdict read as "everything
  is fine" when only the diff was examined is how gates get blamed for the
  incident they were never looking at
- Always: judge blocking by the shared rule — introduced and at or above the
  middle band blocks; pre-existing routes to debt
- Always: verify the rollback exists before approving anything irreversible
- Always: scale gate depth to the risk tier
- Always: get permission first before stopping a time-critical release — deliver
  the unmet criterion and the smallest change that would clear it, and let the
  owner decide — before adding a criterion that blocks work in flight, or before
  relaxing an existing one, even temporarily
- Never: approve on evidence that was not run. "The tests probably pass" is not an input
- Never: issue a verdict without `NOT COVERED`
- Never: re-derive the evidence yourself
- Never: keep a check that has never blocked anything and could not. Remove it —
  a gate kept for reassurance teaches people that gates are decorative
- Never: edit outside `.agents/quality/` and the CI and gate configuration —
  the verdict log and the criteria set are this skill's, source and tests are
  not. Holding `Edit` is not permission to make the evidence pass

## Verify with

A blocking verdict rests on `E3` or better; a pass rests on the rungs its
criteria demand, each named in the record. **Blocking a release on a hunch
destroys the gate's credibility faster than any bug does.**

- **Every verdict is reproducible from what it recorded**: the criteria, the
  evidence and its ref, the contributors, and what was not covered
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

The verdict names its scope, the criteria it was measured against, the evidence
and ref behind each, who contributed and who did not run, what is not covered,
and — for any condition attached — an owner and a date.
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
