---
name: quality-metrics
description: "Measuring quality with numbers that have a source: coverage, mutation score, defect density, complexity, and DORA, captured as reproducible snapshots. Use to set a baseline or read a trend."
allowed-tools: Read, Grep, Glob, Bash, Write
---
<!-- quality:contract -->

## Owns

Numbers that can be reproduced — captured with the command that produced them,
the scope they cover, and the commit they were taken against. It measures and
reports. **It proposes nothing and decides nothing**: noticing that a file is
both complex and hot is a measurement; deciding to refactor it is not.

Phases: `SCOPE → EXTRACT → SNAPSHOT → COMPARE → REPORT`.

## Before starting

- **Fix the scope precisely first** — which paths, which window, which branch,
  which commit. A number whose scope moved between snapshots is not a trend
- **Check what already exists in the baseline.** A first snapshot and a
  comparison are different deliverables, and only one of them can claim a delta
- **Decide what will not be measured**, and plan to say so. A report on coverage
  that is silent about mutation score reads as a complete picture
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
- **A term with two meanings, or a concept with two names, is a question, never
  a silent choice** — one question with its default, the answer into the
  brief's `terms` and `.agents/glossary.md`, and the glossary's names only from
  then on (`_quality/SIZING.md` § Terms)
<!-- /deliver:sizing -->

## Decide first

| Situation | How to proceed |
|---|---|
| Choosing what to measure at all | [core-metrics](playbooks/core-metrics.md) — and the counterweight each one needs |
| Needing the definition of a specific metric | [metric-catalog](reference/metric-catalog.md) |
| Producing the number | [extraction](reference/extraction.md) — the command is part of the value |
| Reading two or more snapshots | [trends](reference/trends.md) — two points license a delta, direction needs three, a trend needs six |
| About to report | [traps](playbooks/traps.md) |
| Someone asks for a single quality score | Refuse and report the axes. A weighted composite lets a bad axis be offset by good ones, and the weights are always arbitrary |
| A number is wanted that nobody measured | Say it is unmeasured. Not an estimate, not "roughly", not an industry average |
| A prior line turns out to be wrong | Append a corrected line with a note. Never edit history — a trend reconstructed after the fact is a story |
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

- Always: run the command yourself and paste its real output, **or** carry
  another skill's snapshot line forward verbatim with its source command and
  ref. A number from memory is the failure this skill exists to prevent
- Always: emit metric name, value, unit, exact command, scope, and commit ref
- Always: report the metric **and** its counterweight, or neither
- Always: name what was not measured
- Always: get permission first before adopting a metric as a **target** —
  targets change behaviour, and a badly chosen one degrades what it measures —
  before publishing per-person numbers, or before installing a tool into the project
- Never: present a composite quality score
- Never: report a percentage without its numerator and denominator
- Never: propose remediation. That is a different skill's call, and mixing them
  is how a measurement arrives pre-loaded with its own conclusion
- Never: rewrite a prior snapshot line
- Never: write outside `.agents/quality/` — the snapshot log and this skill's
  journal are the whole of what it owns. Holding `Write` is not permission to
  touch source, tests or CI config

## Verify with

Every value is `E1` at minimum — it names the command that produced it — and a
value carried from another skill keeps that skill's command and ref rather than
being re-stated. A number whose command cannot be shown is deleted, not caveated.

- **One snapshot is not a trend.** Say when each was taken, and say which claim
  the number of points actually licenses
<!-- deliver:report -->
- **Every claim carries its actual rung and claim-specific warrant** (`_quality/CONTRACT.md`
  §1-3). Choose the cheapest sufficient check; an executed command or named test form alone
  proves nothing about a different claim. `E4` needs a traced independent expectation,
  not a different agent. A bounded `E1` proof may establish a defect; a gate's unmet fixed
  criterion may justify `NO-GO` without `E3`. Missing evidence is not a proved defect
- **Preserve the original question's unresolved parts**; narrowing a claim does not close them.
  Unsupported claims remain `HYPOTHESIS` with the observation or safe check needed
- **Report `status`**: `DONE` (claims warranted, residuals classified) / `PARTIAL` / `BLOCKED`
- **Every residual is `BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `HYPOTHESIS`**
  and appears in the handoff's `open`; a run holding `Write` also leaves a
  `#TODO(agent):` marker carrying that class where a reader would next look
- **Never omit the sweep** — markers against `open`, claims made against claims
  at floor. While either pair disagrees the status is not `DONE`
<!-- /deliver:report -->
<!-- deliver:outcome -->
- **For findings emitted or adjudicated, record the outcome**: `real` · `refuted` ·
  `accepted` · `moot` · `open`. Refutation needs checked evidence; disagreement stays `open`.
  When reporting `real / (real + refuted)`, include all five counts and scope/source/method;
  a zero denominator is undefined. The rate alone says nothing about open work, missed
  defects or overall quality, and one is not suspicious by itself (`_quality/OUTCOMES.md`).
  A run with no findings owes no precision report and must not manufacture findings
<!-- /deliver:outcome -->

## Done when

Every value carries name, unit, command, scope and ref; every metric has its
counterweight or neither is reported; what was not measured is named; and the
snapshot is appended rather than an earlier one edited.
<!-- deliver:surface -->
- **Say what the moment needs.** Start: one line naming what will be checked and what is
  excluded. Mid-run: a line whenever the reader must act now — a finding that changes the verdict,
  a blocked path, work that would grow the scope. Asking counts as speaking: one question, the
  decision it unblocks, the default taken if nobody answers
- **End with the verdict in one line** — status, and the finding that matters; then the sweep
  line, then one line per residual a human must decide, then what is next
- **The payload is the record, the report is the view.** Every finding, rung and outcome lives
  there; ten findings with two that matter are reported as the two and the count of the rest
- **The report is the four parts above and nothing else** — verdict, sweep, residuals, next; the
  findings file is named, never reproduced. It carries only what the payload does not, and its
  length follows the residuals a human must decide (`_quality/REPORT.md`)
- **Not bigger than it is.** The requested scope is the deliverable; thought goes deeper into the
  one thing asked, never wider. **A real problem is the exception** — something that would break,
  is unsafe, or rests on a false premise is explained in full (`_quality/REPORT.md`)
<!-- /deliver:surface -->
