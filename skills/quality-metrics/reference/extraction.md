<!-- quality:deferred -->
# Extraction — The Actual Commands

Purpose: The commands that produce each metric, and their scoping flags.
Read when: producing a number rather than quoting one.
Verified: 2026-08-21 — the pickaxe and `--shortstat` claims are re-run by `make figures`; the per-ecosystem tables are not checked.

Read during `MEASURE`. Every snapshot records the command **as run**, including flags and scope,
so it can be re-run against a later commit (`_quality/HANDOFF.md` §5).

Verify the tool exists before reporting. A metric that could not be measured is reported as
not measured — never estimated.

---

## Repository-derived (no tooling required)

```sh
# churn: commits per file over 90 days
git log --since="90 days ago" --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40

# churn excluding a known formatting sweep
git log --since="90 days ago" --name-only --pretty=format: --invert-grep --grep="^style:" \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40

# PR size distribution — changed lines (insertions + deletions), p50/p95
gh pr list --state merged --limit 200 --json additions,deletions \
  --jq '.[] | (.additions + .deletions)' | sort -n \
  | awk '{a[NR]=$1} END{printf "p50=%d p95=%d n=%d\n", a[int(NR*0.5)], a[int(NR*0.95)], NR}'
# Do not derive this from merge commits: `--stat` field 4 is insertions only (it becomes
# deletions on a deletion-only diff), and merge commits miss every squashed or rebased PR.

# lead time to merge, per PR (requires gh)
gh pr list --state merged --limit 100 \
  --json number,createdAt,mergedAt --jq '.[] | [.number, .createdAt, .mergedAt] | @tsv'

# first-seen date of a failing test — oldest pickaxe match, not newest
git log --reverse --format=%cI -S"<test name>" -- <test file> | head -n 1
# `git log` is newest-first, so `-1` returns the most recent change to the string, not the first.
# Confirm the matching diff is an addition; `-S` also fires when the occurrence count drops.
```

## Coverage & mutation

| Ecosystem | Coverage | Mutation |
|-----------|----------|----------|
| JS/TS | `vitest run --coverage` · `jest --coverage --coverageReporters=json-summary` | `npx stryker run` |
| Python | `pytest --cov --cov-report=json` | `mutmut run` · `cosmic-ray init cfg.toml s.sqlite && cosmic-ray exec cfg.toml s.sqlite` |
| Go | `go test ./... -coverprofile=c.out && go tool cover -func=c.out` | `go-mutesting ./...` |
| Rust | `cargo llvm-cov --json` | `cargo mutants` |
| Java/Kotlin | `./gradlew jacocoTestReport` | `./gradlew pitest` |
| Ruby | `COVERAGE=1 bundle exec rspec` (simplecov) | `mutant run` |

Mutation runs are slow. Scope them and record the scope in the snapshot — an unscoped comparison
against a scoped baseline is not a trend. The selector is per-runner, not shared: Stryker takes
`--mutate 'src/billing/**'`, mutmut and Cosmic Ray take paths in their config file, `cargo mutants`
takes `--file`, PIT takes `targetClasses`. Record the selector you used verbatim.

## Complexity

| Ecosystem | Command |
|-----------|---------|
| JS/TS | `npx eslint --rule '{"complexity":["error",0]}' --format json src/` |
| Python | `radon cc -s -j src/` · `radon mi -j src/` |
| Go | `gocyclo -over 0 .` |
| Rust | `cargo clippy -- -W clippy::cognitive_complexity` |
| Java | `./gradlew pmdMain` (cyclomatic ruleset) |
| Any | `scc --by-file --format json` (also gives LoC per file) |

Record the tool **and its version**. Cross-tool complexity comparisons are invalid.

## Suite reliability

Pass rate requires repetition — a single run measures nothing about reliability:

```sh
# 20 runs, count failures
fails=0
for i in $(seq 1 20); do <test command> >/dev/null 2>&1 || fails=$((fails+1)); done
echo "pass_rate=$(echo "scale=3; (20-$fails)/20" | bc)"
```

Quarantine count is grep-able and should be:

```sh
grep -rn --include='*test*' -E '\.(skip|only)\(|@pytest.mark.skip|t.Skip\(|#\[ignore\]' . | wc -l
```

`.only` in the count is deliberate — a committed `.only` silently disables the rest of the file.

## Defect data

Requires an issue tracker. From GitHub:

```sh
# defects closed in a window, by label — `--limit` is a count cap, NOT a time window
gh issue list --label bug --state closed --search 'closed:<start>..<end>' --limit 1000 \
  --json number,createdAt,closedAt,labels --jq '.[] | [.number,.createdAt,.closedAt] | @tsv'

# escaped defects: bugs labelled as found in production — total, not a capped page
gh api -X GET search/issues \
  -f q='repo:<owner>/<repo> is:issue label:bug label:production' --jq '.total_count'
# `gh issue list ... --limit 200 | jq length` silently reports 200 once the real count exceeds it.
```

If the labels do not exist, the metric does not exist. Say so; do not approximate from titles.

## Snapshot format

One JSON object per line, appended to `.agents/quality/metrics.jsonl`:

```json
{"date":"2026-08-21","ref":"a1b2c3d","metric":"mutation_score","value":0.62,"unit":"ratio","source":"npx stryker run --mutate 'src/billing/**'","scope":"src/billing","tool":"stryker@8.2.0"}
```

`tool` is required for anything whose value is tool-dependent — complexity, mutation, coverage.
Without it, the next comparison is between two different definitions of the same word.
