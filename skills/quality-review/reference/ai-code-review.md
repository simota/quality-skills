<!-- quality:deferred -->
# Reviewing Machine-Authored Code

Purpose: The failure modes specific to generated code.
Read when: the change was machine-generated.
Verified: 2026-08-21 — no automated check.

Read for the `ai` recipe. Generated code fails differently from hand-written code, and the
difference is exploitable: the defects cluster in known places.

---

## What generation gets right, and why that is the problem

Generated code is fluent, idiomatic, well-named, consistently formatted, and confidently
structured. Every surface signal a reviewer uses to allocate attention is maximised. The result
is that reviewers skim it — which is precisely inverted from what its defect profile deserves.

**Rule: read generated code more slowly than hand-written code, not less.**

## The five characteristic failures

### 1. Hallucinated surface

An import, method, option, or field that does not exist — or exists with different semantics in a
different version.

Check: for every unfamiliar API call in the diff, confirm it exists in the pinned version. Not
"seems plausible" — grep the dependency or the docs. This is `E1` work and takes seconds.

### 2. Plausible-but-wrong logic

The shape of the algorithm is right and one step is wrong: a boundary, an ordering, a sign, an
early return. It survives reading because the surrounding structure is correct and the eye
completes the pattern.

Check: hand-execute one non-trivial case, on paper, with real values. One case. This catches more
generated defects than any other single technique.

### 3. Tests that assert the implementation

The same generation that wrote the code wrote the test, from the same misunderstanding. It passes.
It is `E0` (`_quality/CONTRACT.md` §3).

Check: read the test **without** the implementation and ask *where did this expected value come
from?* If the answer is "from what the code does", the test is not evidence. Route to
`quality-test` as a Coverage Gap with a real oracle named.

### 4. Silently dropped requirements

Multi-requirement prompts lose one. Usually the least glamorous: the error case, the empty case,
the cleanup, the migration, the flag-off path.

Check: enumerate the requirements from the issue or prompt; tick each against the diff. The
missing one is rarely mentioned in the PR description either.

### 5. Defensive noise

Null checks, try/catch, and validation added at internal boundaries where the value cannot be
null and the exception cannot be thrown. Harmless-looking, and it hides the real failure: the
one place that genuinely needed a check now looks identical to twenty places that didn't.

Check: for each new guard, ask what call path produces the condition it guards. No path → `LOW`
finding, route to `quality-debt` if pervasive.

## Additional probes

- **Copy-paste at scale.** Generation duplicates rather than extracts. Three near-identical blocks with one differing constant is a generated signature — check whether all three were updated together.
- **Comments describing intent that the code does not implement.** Generated comments are written from the prompt; the code is written from the model's plan. When they disagree, the comment often reflects what was actually asked for.
- **Over-broad types.** `any`, `interface{}`, `Object`, `dict` appearing where the surrounding code is precisely typed usually marks the spot where generation could not resolve the real type — which is where the defect is.
- **Version drift.** Generated code targets the most common version in its training distribution, which is rarely the pinned one. Config formats, framework APIs, and CLI flags are the usual casualties.

## Grading

Do not add a severity penalty for being machine-authored — a defect is a defect. But **do** lower
the confidence you assign to unverified claims about generated code, and **do** raise the evidence
floor for the tests that accompany it: a generated test does not satisfy `E3` for generated code
until its oracle is shown to be independent.
