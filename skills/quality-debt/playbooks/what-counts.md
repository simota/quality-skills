<!-- quality:guidance -->
# What counts as debt

## What counts as debt

| Is debt | Is not debt |
|---------|-------------|
| a change that must be made in six places | duplication nobody has had to change |
| a module nobody can modify without an incident | old code that works and is never touched |
| a workaround that new code must also work around | a style the team no longer uses |
| missing tests on code that changes weekly | missing tests on code frozen for three years |
| an abstraction that leaks into every caller | an abstraction you would design differently now |
| a dependency blocking a required upgrade | a dependency that is merely not the newest |

The distinguishing question is always: **does this cost anything, to anyone, in work that is
actually happening?** If not, it is a preference, and preferences do not get sprint capacity.

## Deliberate vs accidental

| | Deliberate | Accidental |
|---|-----------|------------|
| Origin | a decision, with a reason | erosion, turnover, no decision |
| Documented | usually, at the time | never |
| Repayment condition | often already stated ("until we have >1k users") | must be constructed now |
| Ranking | check the condition first — it may already be met | rank by interest |
| Risk of repaying | low; the shape was intentional | higher; nobody knows what depends on it |

Deliberate debt whose condition has been met is the highest-value entry in most ledgers: it was
designed to be repaid, and someone once knew how.

## Boy Scout scope

What may ride along with unrelated feature work, without its own change:

| Allowed | Not allowed |
|---------|-------------|
| renaming a local variable in a function you are already editing | renaming across files |
| extracting a helper used only by the code you are changing | introducing a new abstraction |
| adding a missing test for the behaviour you touched | restructuring the test suite |
| deleting code proven dead by the change itself | deleting code that merely looks dead |

The line is **reviewability**: if it makes the diff harder to review, it belongs in its own change,
however small it is. A feature PR that also refactors is a PR where neither gets reviewed.
