<!-- quality:contract -->
# Handoff Contracts (quality-* pack)

> **Tier:** `spine`. Precedence: `_quality/VALUES.md` § Rule precedence.

How work crosses a skill edge without losing its warrant. Every payload below is plain Markdown or
JSONL committed under `.agents/quality/` — never chat-only state. **A payload is the record, not
the report**: what a person reads is a bounded view over it (`_quality/REPORT.md`), never a payload
rendered field by field.

## 0. Where each payload lives

A payload with no address cannot be handed anywhere. The paths, and who owns each, are the
state-file table in `_quality/OPERATIONAL.md` §3 — one table, not two that drift apart.

**Append, never rewrite** (`_quality/OPERATIONAL.md` §3). A payload whose state changes — a finding
closed, a debt item repaid, a quarantine expired — is superseded by appending a new record with
the same `ID` and a later date. Current state is the latest record per `ID`. The one exception is
`.agents/quality/gate.yml`, which is a mutable current definition, not an event log.

**Freshness.** Every payload records the `ref` (commit SHA) it was produced against. A consumer
that reads a payload whose `ref` is not the ref under decision must say so; `quality-gate` treats
stale evidence as absent evidence.

---

## 1. Finding (`quality-review`, `quality-regression` → anyone)

```
ID:         Q-<skill>-<nnn>
REF:        <commit sha the finding was produced against>
FILE:       path/to/file.ts:120
CLAIM:      <one falsifiable sentence>
SEVERITY:   CRITICAL | HIGH | MEDIUM | LOW | NIT
BLOCKING:   BLOCK | FOLLOW-UP | NIT
CONFIDENCE: CONFIRMED | LIKELY | HYPOTHESIS
EVIDENCE:   E<n> — <command / file:line / measurement>
FAILURE:    <input or state → wrong output>
IF WRONG:   <the observation that would refute this>
ROUTE:      fix-directive | quality-test | quality-debt | none
```

`ID` is stable across runs so a finding can be tracked to closure rather than rediscovered.

## 2. Fix Directive (any quality skill → the implementer)

Quality skills describe the fix; they do not apply it (`_quality/OPERATIONAL.md` §2).

```
FIX <ID>
WHERE:    file:line
WHAT:     <the behavioural change required, not the code>
WHY NOT:  <the tempting wrong fix, and why it is wrong>
PROOF:    <the test or measurement that must pass afterwards, named>
```

`WHY NOT` exists because most quality findings have an obvious cheap fix that suppresses the
symptom — a try/except, a retry, a widened type, a raised timeout. Naming it up front is what
stops it.

## 3. Coverage Gap (`quality-review` / `quality-regression` → `quality-test`)

```
GAP <ID>
BEHAVIOUR:  <what is unverified, stated as an observable>
ORACLE:     spec | golden | property | reference-impl | production-capture
WHY E3 FAILS: <why a same-context unit test would not catch this>
SUGGESTED:  <test level: unit | integration | contract | e2e> — <and why that level>
```

`ORACLE` is mandatory. A gap handed over without a named oracle produces a test that asserts the
current behaviour, which closes the ticket and catches nothing (`_quality/CONTRACT.md` §3).

## 4. Debt Entry (`quality-review` / `quality-regression` → `quality-debt`)

Appended to `.agents/quality/debt.md`:

```
| ID | Location | Type | Cost today | Interest | Confidence of fix | Deliberate? | Status | First seen |
```

This is the **only** ledger shape; `quality-debt`'s taxonomy describes how to fill
each column and does not redefine them.

`Cost today` is what it costs *now* — reading time, workaround count, incident count — not a
guess at future pain. Future pain is what `interest` in `_quality/SEVERITY.md` §4 computes.

`Status` is `open` · `repaid` · `wont-fix`. The ledger is append-only, so status changes by adding
a row with the same `ID`, a later date, and the new status; current state is the latest row per
`ID`. `First seen` is copied forward unchanged — its age is data.

## 5. Metric Snapshot (`quality-metrics`, `quality-test`, `quality-regression` → `quality-gate`, `quality-debt`)

`quality-metrics` owns the file and the trend reading; `quality-test` and `quality-regression` may
append snapshots for metrics they produce as a by-product (coverage, mutation score, pass rate,
quarantine count). Every producer supplies the same fields, `source` included.

Appended to `.agents/quality/metrics.jsonl`, one object per line:

```json
{"date":"YYYY-MM-DD","ref":"<sha>","metric":"<name>","value":0,"unit":"<unit>","source":"<exact command>","scope":"<paths>"}
```

`source` is the exact command that produced `value`. A snapshot whose command cannot be re-run is
not a snapshot; it is a memory.

## 6. Gate Verdict (`quality-gate` → the release process)

```
VERDICT:    GO | GO-WITH-CONDITIONS | NO-GO
SCOPE:      <what is being decided: PR, release tag, deploy>
BASIS:      <which of the five skills contributed, and their headline>
UNMET:      <gate criteria not satisfied, each with the finding ID>
CONDITIONS: <for GO-WITH-CONDITIONS: what must be true, by when, owned by whom>
NOT COVERED:<what this verdict says nothing about>
```

`NOT COVERED` is required. A verdict read as "everything is fine" when it only examined the diff
is how gates get blamed for the incident they were never looking at.

## 7. AUTORUN envelope

When a skill runs under AUTORUN (`_quality/OPERATIONAL.md` §7), the payload is returned inside a
fenced JSON block so the caller can parse it without reading prose:

```json
{
  "status": "_STEP_COMPLETE",
  "skill": "quality-review",
  "ref": "<commit sha>",
  "payload_type": "Finding | FixDirective | CoverageGap | DebtEntry | MetricSnapshot | GateVerdict",
  "payload": [ { } ],
  "persisted_to": ".agents/quality/findings.jsonl",
  "not_covered": "<what this run did not examine>"
}
```

`not_covered` is required on every envelope, not only on gate verdicts. A caller that cannot see
the scope of what it received will over-read it.

Failure is returned in the same shape with `"status": "_STEP_FAILED"` and a `reason` field. A
skill that cannot complete never returns `_STEP_COMPLETE` with an empty payload — that is
indistinguishable from "found nothing", which is a different and much more reassuring answer.

## 8. Ordering

The pack's default chain, when a full pass is requested:

```
quality-metrics (baseline)
      ↓
quality-review ─┬→ quality-test (gaps)      ─┐
                └→ quality-debt (pre-existing)│
quality-regression (observed failures) ───────┤
                                              ↓
                                        quality-gate (verdict)
```

Gate runs last and only last. Running the gate first produces a verdict with nothing under it.
