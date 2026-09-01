<!-- quality:guidance -->
# The three axes, and what weights them

## The Three Axes

| Axis | Question | Typical finding |
|------|----------|-----------------|
| **Correct** | Does it produce the right result on the paths it will actually take? | off-by-one, inverted condition, wrong operator precedence, lost update, wrong unit |
| **Robust** | What happens on the paths nobody intended? | unhandled empty/null, unbounded growth, missing timeout, partial write with no rollback, swallowed error |
| **Clear** | Can the next person change this without re-deriving it? | a name that lies, a function doing three things, an invariant enforced nowhere and documented nowhere |

Clear is **third on purpose**. It is real — most defects enter through code nobody understood —
but it never outranks a correctness defect, and it is `LOW`/`NIT` unless the unclarity is *itself*
causing wrong behaviour.

## Risk Weighting

| Surface | Depth | Why |
|---------|-------|-----|
| auth, permissions, tenancy | maximum | failure is silent and total |
| money, billing, inventory | maximum | wrong results are irreversible in the real world |
| data mutation, migrations | maximum | no undo |
| concurrency, async, retries | maximum | defects are invisible in single-threaded reading and in tests |
| public API / contract change | high | breaks callers you cannot see |
| business logic | standard | the default |
| internal refactor with tests | light | the suite is the evidence — verify it actually covers the change |
| docs, formatting, config comments | skim | do not manufacture findings here — a comment restating the line under it is the exception, and it is a finding wherever it appears |
