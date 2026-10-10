<!-- quality:deferred -->
# Extraction — The Actual Commands

Purpose: The commands that produce each metric, and their scoping flags.
Read when: producing a number rather than quoting one.
Source: git, gh, pytest, jest, vitest, cargo, go test — every command below is one of theirs, run against whatever is installed.
Verified: 2026-10-10 — the pickaxe and `--shortstat` claims are re-run by `make figures`; the per-ecosystem tables are not checked.

Read during `EXTRACT`. Every snapshot records the command **as run**, including flags and scope,
so it can be re-run against a later commit (`_quality/HANDOFF.md` §5).

Verify the tool exists before reporting. A metric that could not be measured is reported as
not measured — never estimated.

---

## Repository-derived (no tooling required)

```sh
# churn: commits per file over 90 days
git log --since="90 days ago" --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40

# churn excluding a known formatting sweep — by message, so the sweep must follow a convention
git log --since="90 days ago" --name-only --pretty=format: --invert-grep --grep="^style:" \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40
# ...and the hashes that pattern excluded, recorded in the snapshot
git log --since="90 days ago" --grep="^style:" --format='%h %s'
# Counts are per path: a rename starts the new path from zero. `git log --follow -- <file>`
# recovers one file's history; there is no whole-repo equivalent.

# PR size distribution — changed lines (insertions + deletions), p50/p95 by nearest rank
# `--limit` is a count cap, not a window: the window is the `merged:` search
gh pr list --state merged --search 'merged:<start>..<end>' --limit 1000 --json additions,deletions \
  --jq '.[] | (.additions + .deletions)' | sort -n \
  | awk 'function rank(p,  i) { i = int(NR*p); if (i < NR*p) i++; return a[i] }
         {a[NR]=$1} END{printf "p50=%d p95=%d n=%d\n", rank(0.5), rank(0.95), NR}'
# If n equals the limit, the window held more PRs than were fetched; raise it or narrow the window.
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
| JS/TS | `vitest run --coverage` · `jest --coverage --coverageReporters=json-summary` | `npx --no-install stryker run` |
| Python | `pytest --cov --cov-report=json` | `mutmut run` · `cosmic-ray init cfg.toml s.sqlite && cosmic-ray exec cfg.toml s.sqlite && cr-report s.sqlite` (`exec` prints no score) |
| Go | `go test ./... -coverprofile=c.out && go tool cover -func=c.out` | `go-mutesting ./...` |
| Rust | `cargo llvm-cov --json` | `cargo mutants` |
| Java/Kotlin | `./gradlew jacocoTestReport` | `./gradlew pitest` |
| Ruby | `bundle exec rspec` with SimpleCov started at the top of `spec_helper.rb` — `COVERAGE=1` works only where that file gates on it | `bundle exec mutant run --integration rspec -I lib -r <lib> '<Namespace>*'`, or the same in `.mutant.yml` |

`npx` without `--no-install` (or `npm exec --no --`) downloads a package that is not installed —
installing a tool, which needs permission first. Not a local dependency → report the metric as not
measured.

Mutation runs are slow. Scope them and record the scope in the snapshot — an unscoped comparison
against a scoped baseline is not a trend. The selector is per-runner, not shared: Stryker takes
`--mutate 'src/billing/**'`, mutmut and Cosmic Ray take paths in their config file, `cargo mutants`
takes `--file`, PIT takes `targetClasses`. Record the selector you used verbatim.

## Complexity

| Ecosystem | Command |
|-----------|---------|
| JS/TS | `npx --no-install eslint --rule '{"complexity":["error",0]}' --format json src/` |
| Python | `radon cc -s -j src/` · `radon mi -j src/` |
| Go | `gocyclo -over 0 .` |
| Rust | `cognitive-complexity-threshold = 0` in `clippy.toml`, then `cargo clippy --message-format=json -- -W clippy::cognitive_complexity` and keep the messages whose `code.code` is that lint — it only warns above the threshold (default 25), so without the `0` every function under it is missing |
| Java | `./gradlew pmdMain` (cyclomatic ruleset) |
| Any | `scc --by-file --format json` (also gives LoC per file) |

Record the tool **and its version**. Cross-tool complexity comparisons are invalid.

## Suite reliability

Pass rate requires repetition — a single run measures nothing about reliability:

```sh
# N runs, count test failures — any other status is infrastructure, and stops the measurement
N=20 fails=0
for i in $(seq 1 "$N"); do
  <test command> >/dev/null 2>&1
  status=$?
  case $status in
    0) ;;
    <runner's failure status>) fails=$((fails+1)) ;;
    *) echo "not a test result: status $status" >&2; exit 1 ;;
  esac
done
awk -v n="$N" -v f="$fails" 'BEGIN { printf "pass_rate=%.3f n=%d\n", (n-f)/n, n }'
```

State the resolution with the rate. 20 runs cannot tell 97% from 100%: a suite passing 97% of runs
goes 20 for 20 54% of the time. Zero failures in N runs bounds the failure rate below ~3/N at 95%
confidence — 100 clean runs to claim 97%.

Skip markers are grep-able, and the count is a **lower bound**: it sees markers in test sources,
not skips decided at runtime, in config, or by a CI filter.

```sh
tgrep() {   # test sources only: dependencies and build output carry their own skips
  grep -rnE --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=target \
    --exclude-dir=.git --exclude-dir=dist --exclude-dir=build --exclude-dir=.venv \
    --include='*test*' --include='*spec*' --include='*Test*' --include='*.rs' "$@" .
}
# skipped — the count a quarantine list should match
tgrep -e '\b(it|test|describe)\.skip\(|\bx(it|test|describe)\(' \
      -e '@pytest\.mark\.skip|pytest\.skip\(|@unittest\.skip' \
      -e '\bt\.Skip(f|Now)?\(' -e '#\[ignore' -e '@(Disabled|Ignore)\b' | wc -l
# focused — reported separately: not a skip, a filter on everything else
tgrep -e '\b(it|test|describe)\.only\(|\bf(it|describe)\(' | wc -l
```

A committed `.only` is a defect of its own. jest scopes it to its file; Mocha narrows the **whole
run** to the focused tests, and the rest of the suite stops running without a single skip marker.

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
