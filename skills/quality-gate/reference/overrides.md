<!-- quality:deferred -->
# Overrides — Shipping Despite an Unmet Criterion

Purpose: How a gate is passed deliberately, and what that must leave behind.
Read when: someone needs past a gate.
Source: none — nothing outside this page can move what it states.
Verified: 2026-08-21 — no automated check.

Read for the `override` recipe. Overrides are legitimate and necessary. What is never legitimate
is an override that leaves no trace, because the trace is the only thing that distinguishes a
considered exception from a gate that does not work.

---

## The record

An override does not happen without this artifact. Producing it *is* the override process.

```
OVERRIDE <id>
DATE:        YYYY-MM-DD
SCOPE:       <what is shipping>
CRITERION:   <the unmet criterion, verbatim>
WHY UNMET:   <the actual reason — "no time" is an acceptable and common answer>
RISK:        <what could go wrong, concretely; the failure, not "some risk">
COMPENSATING CONTROL: <what reduces the risk in the meantime>
APPROVER:    <a named person who can accept this risk>
EXPIRES:     YYYY-MM-DD
ON EXPIRY:   <what happens: the criterion is met, or the change is reverted>
```

Every field is required. The two that people try to omit are the two that matter:

- **COMPENSATING CONTROL** — without it, this is not an override, it is a decision to accept the risk with nothing in place. That is sometimes correct, and it must then say so explicitly: `COMPENSATING CONTROL: none — risk accepted in full`.
- **APPROVER** — a person, not a team, not "the team agreed". Someone accepts this.

## Compensating controls that actually reduce risk

| Unmet criterion | Compensating control |
|-----------------|----------------------|
| no test for the new behaviour | ship behind a flag, off by default; manual verification recorded; test owed within N days |
| rollback unverified | deploy to one instance/region first; a monitored window with a named watcher |
| suite reliability below `floors.suite_pass_rate` | the specific affected suites run manually and recorded green before deploy |
| migration not reversible | a backup taken and its **restore exercised**, not merely taken |
| review not performed | post-merge review scheduled with a date, and the change is flagged off until then |

A control is compensating only if it addresses **the same failure** as the criterion. "We'll watch
the dashboard" compensates for a detection gap, not for a correctness gap.

## What may never be overridden

- A `T4` criterion (`risk-tiers.md`). If a `T4` requirement is unmet, the change waits.
- Anything protecting data that cannot be recovered.
- A criterion whose failure mode is silent — where nobody would notice being wrong. The whole value of the check is that nobody else will catch it.
- The record itself. There is no override of the override process.

## Expiry

Every override expires; the default is 14 days. At expiry, exactly two outcomes:

1. The criterion is now met — close the record with the evidence.
2. It is not — the change is reverted, or a **new** override is written with a new approver and a new date.

An override renewed three times is not an exception; it is a criterion the project has decided not
to meet. Say so plainly and take it to `design`: either the criterion is wrong, or the project has
a standing gap that deserves to be visible rather than renewed quietly.

## The rate is the diagnostic

Track overrides per release. The number is more informative than any individual record.

| Rate | Reading |
|------|---------|
| ~0 | either healthy, or the gate checks nothing — audit it (`ci-gates.md`) |
| under ~1 in 10 | working as intended |
| over ~1 in 10 | the criteria do not match how this project actually works |
| over ~1 in 3 | the gate is decorative; developers have routed around it and the records are now theatre |

When the rate is high, fix the criteria — not the people. A gate that is bypassed as a matter of
routine has already failed; the bypass rate is just how you find out.
