<!-- quality:guidance -->
# Traps — debt

- **The scariest file is often not the most expensive one.** Fear tracks unfamiliarity; cost tracks touch frequency. Measure before trusting the instinct.
- **Refactoring untested hot code is the highest-risk activity in this domain.** Hot means frequently changed, which means the incident lands quickly. Characterization tests first, always.
- **"We'll clean it up after launch" is not deliberate debt** unless it has a written condition and an owner. Without those it is accidental debt with better PR.
- **A rewrite is not debt repayment.** It replaces known debt with unknown debt and forfeits every bug fix embedded in the original. It can be right; it is never the default, and it needs its own justification.
- **Dependency debt compounds differently.** It grows with time regardless of whether you touch the code, and the repayment cost rises non-linearly across major versions. Age is the interest driver, not churn.
- **Deleting the ledger entry is not repaying the debt.** An entry closed without a change is `won't fix` and must carry its condition.
- **Repayment that nobody can see gets defunded.** Attach each repayment to the work it makes cheaper, in the same sentence.
