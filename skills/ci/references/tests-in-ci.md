# Tests in CI

## Reports: structured where qualified, process-level elsewhere

Every check reports its command, candidate, outcome, original failure and where the
diagnostics are kept. Test-level metrics need a structured report:

| Adapter | Report command (per shard `i` of `n`) | Test id in reports | Status |
|---|---|---|---|
| node:test | `mkdir -p reports && node --test --test-shard=i/n --test-reporter=junit --test-reporter-destination=reports/unit-i.xml <dir>` | `<file>::<classname>::<name>` where the reporter names the file (Node 26 does, Node 20 does not; there it is `classname::name` and top-level tests share classname `test`, so keep their names unique) | run by `evals/test_scripts.mjs` |
| Vitest | `vitest run --shard=i/n --reporter=default --reporter=junit --outputFile.junit=reports/unit-i.xml` | `<file path>::<name>` | run manually with Vitest 5.0.5 (2026-10-30) |
| Playwright | `PLAYWRIGHT_JUNIT_OUTPUT_NAME=reports/e2e-i.xml playwright test --shard=i/n --reporter=list,junit` | `<spec file>::<title>` | run manually with Playwright 1.64.1 (2026-10-30), browserless specs |
| Anything else | the project's command; `pytest --junitxml`, `go-junit-report`, `cargo nextest --profile ci` (JUnit), `gotestsum --junitfile` | tool-specific | process-level until qualified: say test-level metrics are unavailable |

Notes from those runs: node:test does not create the destination directory and crashes
without a report if it is missing (exit 7); Vitest and Playwright create it.

Rules:

- The test step records its exit code and does not fail the job by itself
  (`set +e; <cmd>; echo "code=$?" >> "$GITHUB_OUTPUT"`); the next step runs
  `node ci/reports.mjs --shard i --exit-code "$CODE"`, which fails on missing, corrupt or
  empty reports, unquarantined failures, and a failing command with no reported failure
  (setup or infrastructure).
- A merge job (`if: ${{ !cancelled() }}`, `follows` the check in the policy) downloads all
  shard reports and runs `reports.mjs` without `--shard`. Every expected shard must
  be present; a shard that died before reporting is named.
- Upload reports with `if: ${{ !cancelled() }}` so failures keep their evidence. Add the
  reproducing command (with shard and filter) to the job summary.
- For Vitest's or Playwright's HTML reports across shards, add their blob reporter and
  `--merge-reports` / `merge-reports` in the merge job; JUnit stays the gate's input.

## Sharding: measure first, native partitioning first

Shard when the measured test phase dominates the job and the runner has headroom; not
because a job crossed a fixed number of minutes. Each shard repeats checkout, install
and cache restore, so compare both:

- **Latency:** slowest shard's wall time vs. the unsharded job.
- **Total work:** sum of all shard minutes (that is what is billed and what competes for
  the machine) vs. the unsharded job.

Report both. Adopt a change that cuts latency only if the extra compute fits the budget.
Vitest and Jest shard by file count, Playwright balances by test with
`fullyParallel: true`. A custom timing-based balancer needs a measured imbalance and its
own correctness tests; keep an existing one that works.

Bound matrix × in-job workers × simultaneous runs. Setting workers to all cores on every
shard of a large matrix overloads small runners.

## Isolation changes

Reducing isolation (`isolate: false`, threads instead of forks, shared databases) is a
coverage risk. Before adopting it, run the suite shuffled and concurrently several times
on the target runner (`vitest --sequence.shuffle`, `pytest -p random_order`, `go test
-shuffle=on`) and keep the previous setting on any order-dependent failure. Tools such
as `vitest doctor` provide evidence for the installed version; they are not a guarantee.

## Affected selection

Selecting only affected tests is a speed optimization with a correctness cost. Use it
on PRs only when:

- the tool's dependency graph covers the change (`vitest --changed <ref>`,
  `nx affected -t test`, `turbo run test --affected`, Bazel/Pants/Buck queries);
- global inputs (lockfiles, build and test config, CI files, toolchain versions) force
  the full set;
- base history is available (otherwise the full set runs);
- reverse dependants and supported platforms are included;
- it has been compared against full runs on real history and missed nothing that the
  full run caught.

Push to the default branch, merge queue and release always run the full set. The gate's
path selection is coarser: it decides which jobs run, never which tests inside a job.

## Retention

Choose `retention-days` per artifact from how long failures are investigated and any
compliance need, within the storage budget. Release manifests and gate results are kept
longer than routine shard reports.
