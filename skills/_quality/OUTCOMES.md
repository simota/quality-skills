<!-- quality:contract -->
# OUTCOMES — what each finding turned out to be

Binding on every `quality-*` skill that emits findings or consumes them. A
finding is a claim about a defect, and this set already refuses claims with no
evidence rung. **This contract closes the other end: every finding is
adjudicated once its fate is known, and the record is kept.**

## The failure this prevents

Review output is graded on the day it is written and never afterwards. The
findings that were wrong cost the author an argument, a re-read, and sometimes a
change that made the code worse — and none of that cost lands anywhere near the
review that produced them. So a reviewer that produces forty plausible remarks
looks more thorough than one that produces six real ones, and there is no number
anywhere that says otherwise.

**Precision is invisible by default, and what is invisible drifts.**

## The five outcomes

Each finding reaches exactly one, and the one it reaches is written next to it.

| Outcome | Means |
|---|---|
| `real` | The defect was there. Fixed, or accepted as a defect |
| `refuted` | Examined and shown not to be a defect — the cited line does not say what the finding said, the path is unreachable, or the precondition is already prevented |
| `accepted` | Real, and deliberately not fixed. Names who decided and on what grounds |
| `moot` | The code it concerned was removed or rewritten before it was settled |
| `open` | Never adjudicated. It is not a neutral state — it is the review's cost with nobody assigned to it |

`refuted` is settled by the same standard the set applies everywhere else:
checked evidence — somebody opened the cited line, ran the path, or traced the
precondition. **A finding waved away is `open`, not `refuted`** — disagreement
is not adjudication.

## The rate, and what it cannot say

Precision is `real / (real + refuted)`. Report it with **all five counts** and
the scope, source and method it was taken over, never alone: three out of four
is not a rate. With no `real` and no `refuted` the rate is undefined, not zero
and not one. A run that emitted no findings owes no precision report, and
**never manufactures findings to have something to adjudicate**.

The rate speaks only about the findings that were settled. It says nothing
about open work, about defects nobody found, or about quality overall.

- **A low rate** means many settled findings were wrong. Read it with the
  method: findings stated faster than they were checked look like this
- **A rate of one is not suspicious by itself — read it against `open`.** With
  most findings still `open`, or phrased so that nothing could refute them, it
  measures nothing: `open` was quietly read as agreement. **An unchallengeable
  review is worth less than an imprecise one**, because nothing it says can be
  checked

The same asymmetry applies to a gate: an override with no recorded outcome is a
decision that can never be shown to have been wrong.

## What the record is for, and what it is not for

It is read by the next review of the same area, and by anyone weighing a
finding against the cost of acting on it. A finding from a source with a
recorded precision is worth more than the same sentence from nowhere.

**It attaches to the review and its method, never to a person.** A record used
to grade an individual stops being honest within one cycle, and the one thing
worse than no precision number is a fabricated one.

## Boundary cases

- **A finding fixed without anyone checking it was real** is `real` only if the
  fix was shown to change behaviour. Otherwise it is `open`: the code moved,
  and nobody learned anything
- **A `refuted` finding that recurs in the next review** is the record working.
  Cite the earlier refutation rather than re-litigating from scratch
- **Severity is not an outcome.** A `LOW` finding that was genuinely there is
  `real`. Merging the two axes is how a set of trivia becomes a precision score
- **`accepted` requires a name and a reason**, or it is `open` with better
  manners
- **A finding produced and withdrawn inside the same run** is not recorded.
  The record covers what was handed to somebody else
