<!-- quality:guidance -->
# The core metrics and their counterweights

## The four core metrics

Start here. Adding a fifth requires naming the decision it changes.

| Metric | Measures | Counterweight |
|--------|----------|---------------|
| **Mutation score** | whether the suite can detect defects | runtime cost — report it |
| **Change failure rate** | how often shipped changes need remediation | deploy frequency — a low rate from shipping nothing is not quality |
| **Defect escape rate** | defects found after release ÷ total found | detection capacity — an escape rate that falls because nobody is reporting bugs is not an improvement |
| **Suite pass rate** | reliability of the signal everything else depends on | quarantine count — pass rate rises trivially by skipping tests |

Coverage is deliberately **not** in the core four. It is worth measuring as an input to mutation
testing and as a map of unexecuted code, but as a headline number it is the most gameable metric
in the domain.

## Counterweights

Every metric that can be optimized directly gets published with the metric that detects the
optimization being fake:

| Metric | Gamed by | Counterweight |
|--------|----------|---------------|
| line coverage | assertion-free tests | mutation score |
| defect count (down) | not reporting defects | escape rate + detection channel volume |
| velocity | smaller stories | change failure rate |
| MTTR | closing incidents early | reopen rate |
| suite pass rate | skipping and quarantining | quarantine count + expiry breaches |
| complexity (down) | splitting into many trivial units | cross-file coupling / call depth |
| PR review time | rubber-stamping | escaped defects per reviewed PR |

Publishing one without the other is not a shortcut; it is an instruction to game it.
