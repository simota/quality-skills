<!-- quality:contract -->
# Report Surface (quality-* pack)

> **Tier:** `spine`. Precedence: `_quality/VALUES.md` § Rule precedence.

The other axes decide what must be true. This one decides **what reaches the reader**, and it is
binding on every `quality-*` skill. A run that grades every claim, classifies every residual, and
then returns forty lines has still failed at the last step: **a report that gets skimmed is a
report that did not happen** — the same failure `_quality/CONTRACT.md` §6 names for duplicate
findings, arriving by length instead of by count.

## Record and view are different objects

| Object | Holds | Read by |
|---|---|---|
| The payloads (`_quality/HANDOFF.md`, `_quality/OPERATIONAL.md` §3) | Every finding, its rung, its outcome, the whole `open` list | The next skill, and the person when they ask |
| The report | The verdict, the line of evidence under it, what is unresolved | The person, now |

The report is a **view over** the payload, never a second copy of it in prose. A payload rendered
field by field is how a two-word verdict arrives as a page, and it is the failure this file exists
to stop.

## The moments a run speaks

Four, and no others. Each owes something different, and **what is right at one moment is
noise at the next.**

| Moment | What it owes | Ceiling |
|---|---|---|
| **Start** | What will be done and what is excluded, with the tier if it is not obvious | one line |
| **A question** | The one decision that is blocked, and the default taken if nobody answers | one question, one line |
| **Mid-run** | A line whenever the reader must act now: a divergence from what was agreed, a path found blocked, work that would grow the scope, a finding that changes the verdict the reader is waiting for | one line each |
| **End** | The report below | the bound below |

**Say what the reader can act on.** A tool call is already visible; the mid-run line that earns
its place is the one that tells the reader something changed since the start line.

**A question is not a status update.** Ask when guessing wrong would be expensive to undo, ask one
thing, and say what happens if the answer never comes.

## At the end — this order, every time

1. **The verdict, one line.** The status and the answer — ship or not, how many findings at or
   above the floor, the number that matters. A reader who stops here has the result
2. **The evidence, one line.** The sweep (`_quality/CONTRACT.md`), which already carries the
   counts: `swept, 0 markers; 9 claims / 9 at floor`
3. **What is unresolved** — one line per residual needing a human decision. `BLOCKED` and
   `HYPOTHESIS` always; `DEFERRED` and `OUT-OF-SCOPE` sit in the payload and appear here only if
   the reader would act on them today
4. **What is next** — one line, or nothing if the answer is nothing

A run with nothing unresolved reports lines 1 and 2 and stops.

## Bound

The report is the four parts above and nothing else. A `T0` answer (`_quality/SIZING.md`) is the
verdict line alone; a `T2` report also names the findings file. Length follows the number of
residuals a human must decide, never the amount of work done — a report that reproduces the
payload is the failure this file exists to stop.

**Ten findings, two that matter: report the two and the count of the rest** (`_quality/VALUES.md`
§4). The other eight are in the payload with their rungs, which is where someone acting on them
would look. A diagram that meets a trigger in the review skill's `visualise` playbook is content
and does not count against the bound — it replaces the sentences a reader would have had to
reassemble. One that restates a sentence costs the reader twice and counts double.

## The deliverable is not the report

The findings file, the metrics snapshot, the gate verdict is an artifact with a location. The
report names it and says in one line what it decides; it does not reproduce it. **A report that
reproduces its artifact makes the reader choose which copy is current**, and they will pick wrong
later.

## Not bigger than it is

The requested scope is the deliverable. Neighbouring concerns, future possibilities and general
principles are not folded into the answer, and a small ask does not come back as a survey. **Being
thoughtful and diverging are not the same thing** — thought goes deeper into the one thing asked,
never wider. Option lists are given when they were asked for, or when the choice is the reader's
to make.

**A real problem is the exception.** If the request would break something, is unsafe, or rests on
a false premise, say what is wrong, why, and the options, at whatever length that takes. **Cut
noise, never risk.**

## Shape

A table or a heading earns its place when the reader scans it faster than the prose it replaces;
a heading per finding is the payload rendered again. Every sentence either states the verdict,
the evidence under it, a decision someone must make, or the next step.

## Asked for more

Bounding the default is not withholding. Every field lives in the payload, and "why", "which
files", "what else did you find" are answered from it at whatever length the question deserves.
**The long form is available on request; it is just not the default.**
