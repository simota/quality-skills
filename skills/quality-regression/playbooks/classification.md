<!-- quality:guidance -->
# Classification and quarantine

## Classification is the whole job

| Observation | Likely class | The tell |
|-------------|--------------|----------|
| Fails alone and in suite, every time | `REGRESSION` or `STALE` | deterministic — bisect it |
| Passes alone, fails in suite | `FLAKY-ORDER` | shared state; random-order run confirms |
| Fails at 09:00 JST, passes at 14:00 | `FLAKY-TIME` | timezone or date boundary |
| Fails on CI, passes locally | `FLAKY-ENV` | CPU count, parallelism, container clock, missing fixture |
| Fails ~1 in 20, no pattern | `FLAKY-TIME` (race) | a real race — in the product, usually |
| Fails right after an intentional behaviour change | `STALE` | the diff says so |
| Passes but asserts something nobody wanted | `WRONG-ORACLE` | found during audit — no red to observe |
| Fails deterministically, and the assertion was never valid | `WRONG-ORACLE` | the spec never said this; check before concluding `REGRESSION` |

**Do not skip to a fix from the symptom.** "Intermittent, so add a retry" is the single most
expensive shortcut in this domain: it converts a signal about a product race condition into a
green pipeline and a future incident.

## Quarantine

A quarantined test is a **loan**:

```
QUARANTINE <test id>
CLASS:   <from _quality/SEVERITY.md §5>
OWNER:   <a person, not a team>
EXPIRES: YYYY-MM-DD   (default: 14 days)
BLIND SPOT: <the behaviour now unverified, in one sentence>
```

At expiry: fixed, or deleted with the blind spot filed as a `quality-debt` entry. There is no
third option and no extension without a new owner. `BLIND SPOT` is what makes the deletion
honest — a deleted quarantined test that leaves no debt entry is coverage that silently vanished.
