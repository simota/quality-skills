<!-- quality:deferred -->
# Oracles — Where the Expected Value Comes From

Purpose: Property and relation shapes, and what each one fits.
Read when: the expected value is a rule rather than an example.
Verified: 2026-08-21 — no automated check.

The oracle problem: to test, you must already know the right answer. Where you get it decides
whether the test is evidence or ceremony.

---

## The disqualifying question

> Where did this expected value come from?

If the answer is *"I ran the code and copied the output"* or *"I read the implementation and
wrote down what it does"*, the test asserts that the code does what the code does. It will pass
forever, including while the behaviour is wrong. `_quality/CONTRACT.md` §3 grades this `E0`.

This is the dominant failure of AI-assisted testing and of tests written after a fix.

---

## 1. Specification oracle

Expected value quoted from an AC, ticket, RFC, API contract, or standard.

```
// AC-114: "orders over 10,000 JPY ship free"
expect(shippingFee({ subtotal: 10_000 })).toBe(0)   // boundary is IN, per AC wording
expect(shippingFee({ subtotal: 9_999 })).toBe(500)
```

Strongest and cheapest **when the spec is precise**. Quote it in a comment with its ID — that
comment is what makes the test auditable later, and it is what `quality-gate` traces.

When the spec is vague ("should be fast", "handle errors gracefully"), the spec is the defect.
Say so rather than inventing a threshold and presenting it as verified.

## 2. Property oracle

A relation that must hold for **all** inputs. Use when examples run out before the input space does.

| Property | Shape | Fits |
|----------|-------|------|
| Round-trip | `decode(encode(x)) == x` | serializers, parsers, codecs, migrations |
| Idempotence | `f(f(x)) == f(x)` | normalizers, upserts, retries, cleanup |
| Invariant | `sum(split(x)) == x` | money splitting, sharding, allocation |
| Ordering | `sorted(f(x))` is stable and total | ranking, pagination |
| Commutation | `f(g(x)) == g(f(x))` | filters, transforms |
| Oracle bound | `0 <= score(x) <= 1` | scoring, probability |

Property tests find the input you would never have written down. They are `E4`
(`_quality/CONTRACT.md` §1) because the expectation is derived from the requirement, not the code.

## 3. Metamorphic oracle

No known correct output, but a known **relation between two runs**.

- `search(q)` and `search(q + " ")` return the same results.
- `sort(shuffle(xs)) == sort(xs)`.
- Rendering at 2× scale produces the same layout relationships.
- A model's prediction should not change when an irrelevant field is permuted.

The answer for ML, search, ranking, rendering, and anything else where "correct" is not
computable but "consistent" is.

## 4. Golden / snapshot oracle

Current output captured and frozen.

Useful for complex structured output. Dangerous because **it approves whatever happened**. Rules
that make it safe:

- The initial capture must be reviewed by a human against intent, once, deliberately.
- A changed golden in a diff is a behaviour change and must be reviewed as one.
- `--update-snapshots` never runs in CI.
- Goldens are small and readable. A 4,000-line snapshot is never reviewed and therefore never an oracle.

## 5. Reference-implementation oracle

Compare against a second implementation: a library, the old version, a naive-but-obviously-correct
version, or a hand-computed table.

```
// naive O(n^2) version is obviously correct; the optimized one is what ships
expect(fastIntersect(a, b)).toEqual(naiveIntersect(a, b))
```

The strongest available oracle for algorithms and for optimizations, and the natural fit for
migrations: the old system is the reference for the new one.

## 6. Production-capture oracle

Real inputs, recorded, replayed. Best possible input distribution — production contains shapes
nobody would invent.

Constraints: strip or synthesize PII before committing; pin the capture so it does not drift;
keep the set small enough to stay reviewable.

---

## Choosing

```
Is there a precise spec?              → specification
Does a universal relation hold?       → property
Is there a relation between runs?     → metamorphic
Does a trusted second impl exist?     → reference
Is output complex but trusted today?  → golden (with review discipline)
Are real inputs available?            → production capture
None of the above                     → the behaviour is not specified.
                                        That is the finding. Report it; do not invent an oracle.
```

The last branch matters. Fabricating an expected value to close a coverage ticket produces a test
that locks in a guess and reports it as verified behaviour.
