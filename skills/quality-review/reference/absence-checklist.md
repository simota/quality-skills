<!-- quality:deferred -->
# Absence Checklist

Purpose: The guards whose absence is the defect, per changed behaviour.
Read when: asking what is missing rather than what is wrong.
Verified: 2026-08-21 — no automated check.

Read during `PROBE-ABSENCE`. This phase exists because reading a diff shows what was written;
most real defects are what was not.

**The method:** for each behaviour the change introduces or alters, ask *what must be true for
this to be safe* — then find where that is enforced. If the answer is "nowhere", it is a finding.

---

## Per-behaviour probes

| The change… | Must-hold question | Common answer that is a finding |
|-------------|--------------------|---------------------------------|
| accepts input from outside | Where is it validated, and what happens to the rejected case? | validated for shape, not for range or authority |
| writes to a store | If step 2 fails after step 1 succeeded, what state remains? | a half-written record with no rollback and no repair |
| calls a network dependency | What is the timeout, the retry policy, and the behaviour when it is down? | no timeout; the caller hangs and the queue backs up |
| adds a field | What do existing rows/messages/payloads have here? | `undefined`, handled nowhere |
| removes a field | Who still reads it? | a consumer the diff cannot see |
| adds a loop | What bounds it? | the size of an external input |
| caches | What invalidates it, and what is the blast radius of a stale entry? | nothing invalidates it |
| adds concurrency | What is shared, and what serializes access to it? | a module-level variable |
| changes auth or scope | Which existing callers gain or lose access? | a broadened check nobody enumerated |
| adds a feature flag | What is the behaviour with the flag off, and who cleans it up? | the off path is untested |
| changes a schema | Is there a migration, is it reversible, and is it safe mid-deploy? | forward-only, run during rollout |
| touches money or counts | Where is the idempotency guarantee? | retries double the charge |

## Things that should exist and usually don't

- **A test for the failure path.** Coverage tends to prove the success path twice.
- **An error message a user could act on.** "An error occurred" is a `LOW` finding, always present, rarely written down.
- **A metric or log at the failure point.** A silent failure is an incident with no start time.
- **A limit.** Page size, batch size, payload size, retry count, queue depth. Unbounded is the default and is almost never intended.
- **The rollback.** If this change is wrong in production, what is the undo? If the answer requires a code deploy, say so.

## How to grade an absence finding

Absence findings are easy to over-emit — every system is missing something. Grade by
**reachability**, not by principle:

| Reachable by | Severity |
|--------------|----------|
| ordinary user input, today | `HIGH`+ |
| unusual but legitimate input, or a dependency being slow | `MEDIUM` |
| only under a state the system prevents elsewhere (show where) | `LOW` |
| only in a scenario you cannot construct | not a finding — drop it |

"There is no validation here" with no reachable bad input is `E0` and does not ship
(`_quality/CONTRACT.md` §2). Find the input, or drop the finding.
