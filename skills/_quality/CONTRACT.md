<!-- quality:contract -->
# Evidence Discipline (quality-* pack)

> **Tier:** `spine`. Precedence: `_quality/VALUES.md` § Rule precedence.

Quality work fails in one specific way: **a confident claim with nothing behind it.** This file
defines what "behind it" means, so that every finding, metric, and verdict this pack emits carries
a legible warrant.

**Read when:** deciding whether a finding may be reported · choosing what to run before a gate
verdict · judging whether a green suite proves anything · grading a metric you did not measure.

---

## 1. The ladder

| Level | Evidence | Produced by | Independent of the author's assumptions? |
|-------|----------|-------------|------------------------------------------|
| `E0` | **Assertion** — "this looks wrong", reasoning alone | anyone | **No.** Never ships as a finding. |
| `E1` | **Static** — types, lint, SAST, dependency rules | tooling | Partially: an external rule, but only over syntax. |
| `E2` | **Execution** — build, run, reproduce, smoke | runtime | Partially: only over paths actually taken. |
| `E3` | **Automated test** — unit, integration, contract | test suite | **Only if the oracle is independent** (§3). |
| `E4` | **Independent test** — property, metamorphic, mutation, differential, fuzz | derived oracle | Yes, by construction. |
| `E5` | **Integration** — preview env, canary, policy check | real surface | Yes. |
| `E6` | **Production** — SLO, trace, incident, user outcome | reality | Yes; the only rung on real input distribution. |

Climbing is not about effort. What rises is **distance from the hypothesis that produced the
code**. E0 and E3 can share the same misunderstanding; E4 and above cannot.

## 2. Minimum rung per output

| Output | Floor | Rationale |
|--------|-------|-----------|
| A reported defect | `E2` | If you cannot show it happening, you are describing a worry. |
| A reported **absence** (missing guard, rollback, timeout, validation) | `E1` **plus a named reachable input** | There is no execution to show — the defect is that nothing runs. The reachability path is what replaces the execution: name the input that reaches the unguarded state, or the finding is `E0` and does not ship. |
| A blocking gate verdict | `E3` | Blocking a release on a hunch destroys the gate's credibility faster than any bug. |
| A performance or cost claim | `E2` with a number | "Feels slow" is not a finding; a measurement with units is. |
| A metric in a report | `E1` | Every number names its extraction command. Un-sourced numbers are deleted, not caveated. |
| A refactor-safety claim | `E4` | Behaviour-preservation is exactly the claim a same-author test cannot make. |
| A style / readability note | `E0` allowed | Labelled `nit`, never blocking, never counted in defect density. |

A finding that cannot reach its floor is **not** downgraded and shipped anyway. It is emitted as a
`HYPOTHESIS` with the one command that would settle it — that is the useful form.

## 3. Independence — the failure this pack exists to catch

A test written from the same context, by the same author, in the same sitting as the code under
test inherits its misunderstanding. It will pass. It proves the code does what the author *meant*,
which was never in doubt.

A test oracle is **independent** when its expectation comes from a source other than the
implementation:

- the specification, an AC, or a ticket quoted verbatim,
- a previous version's observed behaviour (differential / golden),
- a mathematical property that must hold regardless of implementation (`reverse(reverse(x)) == x`),
- a second implementation, a reference library, or a hand-computed table,
- a real captured production input.

"I read the code and wrote a test asserting what it does" is `E0` wearing a green check. Say so.

**One case looks like this and is not.** A characterization test also asserts what the code
currently does — but it is used to support a different claim. For *"this behaviour is correct"* it
is `E0`, exactly as above. For *"this refactor changed no behaviour"* it is `E4`: the pre-change
system is the reference implementation, and the comparison is differential. Always say **which
claim** a characterization suite is evidence for. It never carries the first one.

**AI-written code + AI-written test in one turn is a single observation, not two.** When both come
from the same generation, the pair sits at `E0`+. Break the loop by deriving the oracle from the
spec before reading the implementation, or by having a different pass author the test.

## 4. Reporting shape

Every finding this pack emits carries four fields. Missing fields are shown as missing.

```
CLAIM:    <one sentence, falsifiable>
EVIDENCE: <E-level> — <the command, file:line, or measurement>
FAILURE:  <concrete input/state → wrong output, crash, or cost>
IF WRONG: <what observation would refute this>
```

`IF WRONG` is not decoration. A claim with no refutation condition is an opinion, and opinions do
not block merges.

## 5. Absence is harder than presence, and matters more

Most real defects are **missing** code: no bounds check, no rollback, no timeout, no test for the
empty case. Scanning a diff surfaces what is there. Reaching absence requires asking, per changed
behaviour: *what must be true for this to be safe, and where is that enforced?* If the answer is
"nowhere", that is an `E1`-or-better finding, not a nitpick — subject to the absence row in §2:
name the input that reaches the unguarded state, or drop it.

## 6. Do not double-count

Three tools flagging one root cause is **one** finding with three sources, not three findings.
Tool agreement raises confidence; it never raises count. A report inflated by duplicates trains
readers to skim, and a skimmed report is a report that did not happen.

## 7. What counts as done

| Status | Condition |
|---|---|
| `DONE` | Every claim at or above its floor (§2), every residual classified, zero unclassified leftovers |
| `PARTIAL` | Everything else that produced work — a single unreachable floor lands here |
| `BLOCKED` | Could not proceed. Say what was tried and what stopped it |

Falling short is reported as falling short. **A report that reaches `DONE` by
lowering a floor is the exact failure this pack exists to catch**, arriving from
the inside.

## 8. Residuals

Anything left behind is classified and recorded in the handoff's `open` list
with the place a reader would next look.

| Class | Means |
|---|---|
| `BLOCKED` | Wanted, attempted, prevented |
| `OUT-OF-SCOPE` | Found during the work, outside what was agreed. Named, not pursued |
| `DEFERRED` | In scope, deliberately postponed, with the condition to resume named |
| `HYPOTHESIS` | Believed, could not reach its floor. Carries the one command that would settle it |

`HYPOTHESIS` is the useful form of a claim that did not make it (§2). It is not
a downgraded finding, and it never blocks.

A skill holding `Write` puts a `#TODO(agent): <class> — <action>` marker where a
reader would next look. A skill that does not writes the entry into `open`
alone and names where the marker belongs. **The report closes and is gone; the
marker stays.**

## 9. The completion sweep — never omitted

Before reporting, run both halves and state both results:

1. **Markers introduced by this run** — every one appears in `open` with a
   matching class
2. **Floors** — every claim made, against every claim that reached its floor

Report it in one line: `swept, 1 marker / 1 in open; 9 claims / 9 at floor`.
**While either pair fails to match, the status is not `DONE`.**

## 10. Comments — the code says what, a comment says why

A comment restating the line under it is a defect in the code, not a sentence
missing from it. **The test is mechanical: cover the comment and read the
code.** Nothing lost — delete it. Something lost — put it in the code, renaming
or extracting until the comment has become the name, then delete it anyway.

What survives is what code cannot carry: why this way and not the obvious way,
the constraint from outside, and in this pack above all **the oracle's
identifier** — the spec clause, ticket or recorded run an expected value came
from. **Deleting those is the opposite failure and costs more**: a `what` is
re-read off the code, where an unattributed expected value is a claim at no rung
at all. A `#TODO(agent):` marker and a licence header are never trimmed by this.

**Nothing checks this automatically**, §9 included: it is a reading pass over
the files this run wrote. Comments elsewhere are not this run's to strip.
