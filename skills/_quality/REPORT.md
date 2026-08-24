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
| **Mid-run** | Nothing — unless the reader must act now: a divergence from what was agreed, a path found blocked, work that would grow the scope, a finding that changes the verdict the reader is waiting for | one line each, or silence |
| **End** | The report below | the ceiling below |

**Progress is not information.** "running the suite", "now reading the diff", "nothing so far"
tell the reader nothing they can act on, and they cost the same attention as the line that
matters. A tool call is already visible; narrating it a second time is the commonest way a run
fills a screen while saying nothing.

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

## Ceiling

| Tier (`_quality/SIZING.md`) | The whole report |
|---|---|
| `T0` | one line |
| `T1` | six lines |
| `T2` | ten lines, plus the findings file itself |

**Over the ceiling means cutting content, not reformatting it.** A table, a nested list, and a
heading per finding are the three ways a report grows while appearing to have been tightened.

**Ten findings, two that matter: report the two and the count of the rest** (`_quality/VALUES.md`
§4). The other eight are in the payload with their rungs, which is where someone acting on them
would look. A diagram that meets a trigger in the review skill's `visualise` playbook is content
and does not count against the ceiling — it replaces the sentences a reader would have had to
reassemble. One that restates a sentence costs the reader twice and counts double.

## The deliverable is not the report

The findings file, the metrics snapshot, the gate verdict is an artifact with a location. The
report names it and says in one line what it decides; it does not reproduce it. **A report that
reproduces its artifact makes the reader choose which copy is current**, and they will pick wrong
later.

## Never in a report

- A restatement of the request, or of what the run was about to check
- A closing summary of what was just said
- Findings the payload already lists in full, or a walk through every rung awarded
- Narration of process: what was read, which tool ran, what was tried first
- Confidence about a claim nobody doubted, or hedging that changes no decision

## Asked for more

Bounding the default is not withholding. Every field lives in the payload, and "why", "which
files", "what else did you find" are answered from it at whatever length the question deserves.
**The long form is available on request; it is just not the default.**
