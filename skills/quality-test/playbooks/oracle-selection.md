<!-- quality:guidance -->
# Choosing the oracle

The single decision that determines whether a test is worth anything (`_quality/CONTRACT.md` §3).

| Oracle | Use when | Cost |
|--------|----------|------|
| **Specification** | An AC, ticket, RFC, or standard states the expected result | free, if it exists and is precise |
| **Property** | A relation must hold for all inputs (`roundtrip`, `idempotent`, `ordering`, `conservation`) | design effort; catches the most |
| **Metamorphic** | No known correct output, but a known relation between two runs (`sort(shuffle(x)) == sort(x)`) | design effort; the answer for ML, search, rendering |
| **Golden / snapshot** | Behaviour is complex and current output is trusted | cheap now, rots silently; must carry a review discipline |
| **Reference implementation** | A second implementation, library, or hand table exists | expensive; unbeatable for algorithms |
| **Production capture** | Real inputs are available and representative | best distribution; watch for PII |
| **The implementation** | — | **never.** This is `E0`. |
