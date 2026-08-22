<!-- quality:guidance -->
# Traps — regressions

- **A "flaky" test is usually a real race in the product.** The test is the only thing exercising the concurrency; making it deterministic often means removing the only detector.
- **CI parallelism changes the defect surface.** Tests that share a database, a port, a temp directory, or a fixed filename pass at one worker and fail at eight. Reproduce at CI's worker count.
- **`git bisect` needs a scripted predicate.** Bisecting by hand on an intermittent failure produces a wrong answer confidently; script it with N repetitions and a failure-rate threshold, not a single run.
- **The first bad commit is not always the cause.** A commit can expose a latent defect — a reordering, a dependency bump, a timing change. Read the culprit diff before assigning blame to it.
- **Timezone failures cluster at UTC midnight and at DST boundaries.** A suite that goes red for 9 hours a day in JST is not flaky; it is a date-boundary defect with a schedule.
- **A test that started failing after a dependency upgrade may be reporting a real behaviour change**, and the upgrade's changelog is the fastest oracle available.
- **Pass rate, not pass/fail, is the metric.** A test at 97% looks green in any single run and costs an hour a week across the team.
