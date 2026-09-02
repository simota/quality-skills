<!-- quality:guidance -->
# Traps — gates

- **A gate that has never blocked is not evidence of quality.** It is an unmeasured check. Audit by asking, per criterion: when did this last block something, and was that block correct?
- **Skipped tests count as failures for gating purposes.** A suite reporting "0 failed, 47 skipped" has 47 unknowns, and every dashboard renders it green.
- **Coverage thresholds as gate criteria produce assertion-free tests within one sprint.** Gate on mutation score for critical modules, or on "the new behaviour has a test with a named oracle" — both resist the obvious gaming.
- **The rollback is part of the change.** An `R3`+ approval without a verified undo is an approval to find out whether one exists during the incident.
- **A gate everyone bypasses is worse than no gate**, because it makes the bypass routine and the record meaningless. If overrides exceed roughly one in ten, the criteria are wrong; fix them rather than the people.
- **Green CI proves the checks passed, not that the change is correct.** The gate's authority comes entirely from what the criteria actually check — audit that, not the colour.
- **A conditional GO with no date is a GO.** Every condition gets an owner and a date, or it is not a condition.
