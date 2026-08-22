<!-- quality:guidance -->
# Traps — metrics

- **Coverage is measured on executed lines, not verified behaviour.** A suite with zero assertions can reach 90%. Mutation score is the honest version and costs more to run — say what it cost.
- **Complexity is tool-defined, not a property of the code.** Each tool counts different constructs, so values are not comparable across tools or across versions of one tool. Pin the tool and record its version in the snapshot; compare only within that pin.
- **Git churn attributes to whoever last touched a line.** A formatting sweep or a rename destroys blame and inflates churn for a quarter. Exclude such commits by hash and say which you excluded.
- **DORA metrics require deploy data.** A repository alone yields lead-time-to-merge, not lead-time-to-production. Report the one you have under its real name, not the one the audience expects.
- **Defect density depends entirely on how hard anyone looked.** It falls when a QA engineer leaves. Read it alongside detection channel volume or not at all.
- **Percentage changes on small denominators are noise.** 2 → 3 escaped defects is not "+50%"; report the counts.
- **A trend across a scope change is not a trend.** A new directory, a monorepo merge, or an excluded path invalidates the comparison. Comparability is checked before, not after.
