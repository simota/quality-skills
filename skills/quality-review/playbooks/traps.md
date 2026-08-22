<!-- quality:guidance -->
# Traps — review

- **Line numbers in a diff are not line numbers in the file.** Cite the post-change file position and open it. A finding at the wrong line is read as a finding that isn't there.
- **A green test suite is not evidence the change is correct** — it is evidence the change did not break what was already asserted. Ask what the suite would have to assert to catch this defect, and whether it does.
- **Deleted code is part of the diff.** Removed guards, removed error handling, and removed tests are the highest-yield thing in most diffs and the easiest to scroll past.
- **"It's the same pattern as the file next door"** is not a defence if the neighbour is also wrong, and not a defect if the neighbour is right. Check which, rather than treating consistency as either.
- **Config and constant changes carry production severity.** A timeout, a retry count, a feature flag default, or a pool size is a one-line diff with `CRITICAL` reach; review depth must follow blast radius, not line count.
- **A `try/except` added in the same commit as the bug fix usually hides the second bug.** Ask what exception was actually being thrown, and whether it is now invisible.
- **Renames hide edits.** A file shown as renamed may carry logic changes the diff view collapses; re-diff with rename detection off when the change touches a risky surface.
