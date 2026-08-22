---
name: quality-test
description: "Writing tests that can actually fail: naming an independent oracle, boundary and edge cases, choosing the test level, closing a coverage gap, and auditing whether a suite proves anything."
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---
<!-- quality:contract -->

## Owns

Tests whose expected value comes from somewhere other than the code under test.
It delivers the test, the reason it can fail, and the defect class it guards.
Scope per run: one behaviour, one gap, or one suite audit. It writes tests and
test infrastructure only — never production code.

Phases: `GAP → ORACLE → LEVEL → CASES → RED → GREEN → PRUNE`.

## Before starting

- **Name the oracle before writing anything.** No named oracle means no test —
  ask for one. Where the spec permits, derive the expectation **before** reading
  the implementation: reading first contaminates the oracle and cannot be undone
- **State the behaviour as something observable**, not as a function name. A gap
  that cannot be phrased as a falsifiable claim is not yet a gap
- **Find the suite's existing style.** A second convention costs every future
  reader more than one imperfect consistent one
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
| Deciding where the expected value comes from | [oracle-selection](playbooks/oracle-selection.md) — the single decision that determines whether the test is worth anything |
| Needing a property or relation rather than an example | [oracles](reference/oracles.md) |
| Choosing unit, integration, contract, or e2e | [test-levels](reference/test-levels.md) — by what must be falsified, not by convention |
| Enumerating partitions, boundaries, and error paths | [case-design](reference/case-design.md) |
| Auditing whether an existing suite proves anything | [test-smells](reference/test-smells.md) |
| Someone quotes a coverage number | [coverage](playbooks/coverage.md) — it measures what executed, never what was verified |
| About to write the test | [traps](playbooks/traps.md) |
| The behaviour is already correct, so there is no pre-fix state | Break the code on purpose, watch the test fail, put it back. That injected defect is the control, and it is the cheapest mutation test there is |
| The code cannot be tested without restructuring | That is a debt entry with a named seam, not a testing problem |
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

- Always: observe every new test **failing against a negative control** — the
  pre-fix state for a bug guard, or a deliberately injected defect otherwise —
  and name the control in the deliverable. A test never seen red is unproven
- Always: cover empty, one, maximum, and one past the maximum per input.
  Production data contains all four; hand-written test data contains "a few"
- Always: one test, one reason to fail. A test asserting six things reports one
  bit and hides five
- Always: keep test data explicit and local. A shared mutable fixture is a
  future order-dependent flake
- Always: get permission first before introducing a test framework or runner,
  before changing a production seam to enable testing, or before deleting any
  existing test
- Never: write a test whose expected value was copied from a failing run's
  actual output. That converts a bug into a specification
- Never: assert on internals — private state, call counts of internal helpers —
  to reach coverage. Such tests fail on every refactor and catch no defect
- Never: add a `sleep` to stabilise a test. Inject the clock or await the condition
- Never: report a coverage number as the answer to "is this tested?"
- Never: edit production code to make a test pass. This skill holds `Edit` for
  tests and test infrastructure; a source change the tests demand leaves as a
  fix directive under `.agents/quality/`, not as an edit made here

## Verify with

`RED` is the evidence and it is not a formality (`E3`, or `E4` where the oracle
is a property, metamorphic relation, or mutation). **A test that goes straight
to green has not been shown to be connected to the behaviour at all** — the
commonest cause is asserting something that was already true.

- **Name the defect class each test guards**, in one line. A test whose failure
  mode cannot be stated is covering nothing, whatever the line count says
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

Each test names an independent oracle, was observed failing against a named
control for the intended reason, then passes; the defect class of each is
stated; and what remains unverified is written down rather than implied.
