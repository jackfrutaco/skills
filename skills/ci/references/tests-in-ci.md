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
without a report if it is missing (exit 7); Vitest and Playwright create it. `node --test
test/` (a bare directory) works on Node 26 but fails on Node 24 with "Cannot find module
.../test"; pass a quoted glob (`node --test 'test/*.test.ts'`) so the command works on
every version the project supports, and run CI on the oldest one `engines` allows.

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

Selection has its own costs:

- **Time it.** Walking every test's imports on each run cost up to 111 s in one audited
  project. Cache each test's dependency list, and drop the cache when anything that
  steers resolution changes: lockfile, package manager config, workspace manifests,
  path aliases, and the selector's own code. On a case-insensitive file system, compare
  paths case-insensitively, since a new `Foo.ts` can change what `./foo` resolves to.
- **Unbounded tests set the floor.** Tests that read the repository in ways the graph
  cannot see (whole-tree walks, spawned scripts, computed paths) must run on every
  change; there, 116 such tests were most of a small rerun. A test may declare the
  paths it reads, if: the declaration sits in a fixed place (the file's leading comment,
  never anywhere a fixture string could match); it adds to what the scanner finds
  rather than replacing it; a declared path that is not tracked cancels the declaration;
  and only early feedback honors it, while the deciding run treats the test as
  unbounded.

## Making slow tests cheaper

Time every file once, sort, and work down from the slowest; the top 100 files are
usually most of the time. In one audited project this cut total test time from 1,081 s
to 773 s and the slowest 100 files by 37%, with no assertion removed. What worked:

- **Build expensive fixtures once per file, copy per test.** A git repository, a
  migrated database, a generated contract. When the copy embeds absolute paths, rewrite
  them and fail loudly if an expected one is missing.
- **Start from a database snapshot** instead of replaying hundreds of migrations per
  test; keep at least one test that runs the real migrations.
- **Run independent cases concurrently** inside a file, only where each test owns its
  fixture, temp folder, ports and processes. Shared lists emptied "after each" become
  per-test fixtures; cleanup that would kill another test's processes moves to the end
  of the file.
- **Merge near-duplicate tests** that repeat the same expensive setup, keeping every
  assertion.
- **Wait on events, not timers,** and make production intervals and grace periods
  injectable so a test does not sit out a 3 s default.
- **Batch subprocess work.** One `git cat-file --batch` or `ls-tree` instead of one
  `git show` per file; remember results that cannot change within a run.
- **Find per-process costs on the platform.** Measured on macOS: `/usr/bin/git` is a
  wrapper costing about 10 ms per call against about 4 ms for the real binary (put the
  directory from `git --exec-path` first on `PATH`), and the first run of a newly
  written executable costs 0.15 to 0.5 s while it is checked (link to one that already
  ran, or run scripts through `sh`). Fixture repositories should turn off git's
  automatic maintenance and garbage collection.

Then check the rewrites for lost protection ([flaky.md](flaky.md#after-a-speedup)):
concurrency and shorter waits change timing, and a merged test can quietly drop a
byte-for-byte or exit-code check.

## Retention

Choose `retention-days` per artifact from how long failures are investigated and any
compliance need, within the storage budget. Release manifests and gate results are kept
longer than routine shard reports.
