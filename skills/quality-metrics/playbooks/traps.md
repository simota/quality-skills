<!-- quality:guidance -->
# Traps — metrics

- **Coverage is measured on executed lines, not verified behaviour.** A suite with zero assertions can reach 90%. Mutation score is the honest version and costs more to run — say what it cost.
- **Complexity is tool-defined, not a property of the code.** Each tool counts different constructs, so values are not comparable across tools or across versions of one tool. Pin the tool and record its version in the snapshot; compare only within that pin.
- **Git churn is commits per path, not blame.** A formatting sweep adds a commit to every file it touched and inflates churn for a quarter; a rename starts the new path from zero and splits its history. Exclude sweeps by message pattern, record the hashes the pattern matched (`reference/extraction.md`), and name renamed hotspots rather than ranking them on half a history.
- **DORA metrics require deploy data.** A repository alone yields lead-time-to-merge, not lead-time-to-production. Report the one you have under its real name, not the one the audience expects.
- **Defect density depends entirely on how hard anyone looked.** It falls when a QA engineer leaves. Read it alongside detection channel volume or not at all.
- **Percentage changes on small denominators are noise.** 2 → 3 escaped defects is not "+50%"; report the counts.
- **A trend across a scope change is not a trend.** A new directory, a monorepo merge, or an excluded path invalidates the comparison. Comparability is checked before, not after.
