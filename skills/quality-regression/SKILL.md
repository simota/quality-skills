---
name: quality-regression
description: "Diagnosing failures over time: regression bisection, flaky test classification and repair, quarantine with expiry, and turning a reproduction into a permanent guard. Use when a test now fails."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- quality:contract -->

## Owns

Failures that appear over time — something that passed and now does not, or a
suite that fails without a change. It classifies the cause, repairs the cause
class, and turns the reproduction into a guard. It writes tests and test
infrastructure only.

Phases: `REPRODUCE → CLASSIFY → LOCATE → REPAIR → GUARD`.

## Before starting

- **Reproduce before diagnosing.** A cause derived from reading alone is `E0`
- **Run it in isolation and in the full suite, in random order.** The difference
  between those two runs is the classification, most of the time
- **Check whether the failure is new or long-standing before bisecting.** A
  "regression" that was always red in CI is a different problem
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
| Anything, before acting | [classification](playbooks/classification.md) — every subsequent action is determined by the class, and acting first is how tests get "fixed" by widening the assertion |
| Finding the change that did it | [bisection](reference/bisection.md) |
| Repairing the cause once classified | [flaky-repair](reference/flaky-repair.md) |
| Deciding what a failure is worth | [triage](reference/triage.md) |
| About to make it green | [traps](playbooks/traps.md) |
| The test looks wrong rather than the code | **The default hypothesis is that the product code is wrong.** Concluding otherwise requires the spec or an acceptance criterion saying so, cited |
| It cannot be fixed today | Quarantine needs an owner and a date. No owner, no quarantine — fix it or delete it today |
| It turned out to be a one-off | Record it anyway. A registry of one-offs is how the third occurrence gets recognised |
| A claim here would be expensive to get wrong | [refute](refute.py) — put it to the engines that did not make it, asked to break it rather than to agree. Unrefuted is n engines finding nothing, never proof |
| A test is called flaky | That is a finding, and it is adjudicated the same way: `real` once the mechanism is shown, `refuted` once the failure reproduces as a genuine defect. **Quarantining is neither** |
<!-- deliver:values -->
- Ties break by `_quality/VALUES.md`, read top to bottom: honesty over speed ·
  mechanism over intent · **independence over throughput** · subtraction over
  addition · what is measured over what is believed · the human decides what,
  the agent decides how. Against all of them: **a harness that is correct and
  avoided has failed** — this pack is the heaviest of its kind, and when the
  discipline costs more than the check, say so rather than performing it
<!-- /deliver:values -->

## Always / Never

- Always: classify before repairing, and name the class in the deliverable
- Always: fix the **cause class**. A repair that changes only this occurrence
  leaves the class in place
- Always: observe every guard failing on the pre-fix state. Not observed, not a guard
- Always: record class, evidence, and outcome to the flaky registry — including
  failures that turned out to be one-offs
- Always: get permission first before deleting a test, before quarantining
  anything on a critical path, or before reverting a culprit commit —
  identifying it is this skill's job; reverting is a release decision
- Never: add a `sleep`, extend a timeout, or add a retry to make a test green.
  That converts a reproducible defect into an intermittent production incident,
  and it removes the evidence
- Never: loosen an assertion to match observed output. That rewrites the
  specification to match the bug
- Never: mark a test skipped without an owner and an expiry. An indefinitely
  skipped test reads as coverage on every dashboard that counts it
- Never: blame "flakiness" without a class. Unclassified flakiness is an
  unexamined race, and the race is usually in the product
- Never: edit production code to make the suite green. This skill holds `Edit`
  for tests, test infrastructure and `.agents/quality/`; the culprit commit's
  fix is a directive, and reverting it is the host project's call

## Verify with

The reproduction is the evidence (`E2`), and the guard is `E3` — observed
failing on the pre-fix state and passing after. A repair claimed without both
runs is `E0` wearing a fix's name.

- **Say how many times you ran it.** A flake that reproduces once in twenty is
  not fixed by one green run, and the count is the claim
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

The failure is reproduced and classified, the repair addresses the cause class
rather than the occurrence, a guard was seen failing on the pre-fix state, and
anything quarantined carries an owner and a date.
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
