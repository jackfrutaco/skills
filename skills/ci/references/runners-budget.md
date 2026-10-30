# Runners, caches and budget

## Keep the runner that works

Default to the project's existing compatible runner. For a new GitHub project, use
GitHub-hosted runners (`ubuntu-24.04`, `ubuntu-24.04-arm`, `windows-2025`, `macos-15`;
check current labels). Change runner only with evidence: current price, eligibility,
compatibility, trust boundary, queue time and the measured workload.

## Comparing a runner change (Blacksmith, Depot, Namespace, larger GitHub runners)

1. **Measure the current workload** with `scripts/ci_health.mjs`: queue p90, job
   duration per cohort, summed minutes by runner class, re-run share.
2. **Check eligibility and access now**, not from memory. Blacksmith's docs (read
   2026-10-30) describe labels such as `blacksmith-2vcpu-ubuntu-2404`,
   `blacksmith-2vcpu-ubuntu-2404-arm`, `blacksmith-2vcpu-windows-2025` (public beta) and
   `blacksmith-6vcpu-macos-15`; a GitHub App that must be installed on **every**
   repository using its labels (otherwise jobs queue); 3,000 free x64 2-vCPU minutes a
   month per organization, with ARM at 0.625×, Windows at 2× and macOS 6-vCPU at 20× the
   x64 2-vCPU rate; no concurrency limit. The docs also claim "exactly half the cost of
   GitHub's per minute"; its pricing page is client-rendered, so read the live price
   in a browser before any cost claim. Earlier reports say it supports organizations
   only, not personal repositories; confirm before recommending it to a personal repo.
3. **Compare on a comparable workload**: same commit, same jobs, cold and warm cache,
   at least 30 completed runs per cohort before claiming a p90 change. Vendor
   benchmarks and sponsored case studies are not your numbers.
4. **Check compatibility**: architecture changes (x64 → ARM) need native dependencies,
   Docker images and cache keys revalidated; Windows on Blacksmith lacks Linux Docker
   containers and the full Visual Studio IDE (per its docs).
5. **Report latency and total cost together.** Faster runners that cost more per
   minute can still save money; parallelism that cuts latency usually adds minutes.

An audit or a question never installs an app, changes labels, connects billing or
starts a trial. Those need authority naming that account and spend. For a migration,
put the label behind a repository variable (`runs-on: ${{ vars.CI_RUNNER ||
'ubuntu-24.04' }}`) so rollback is one setting, and keep a job on the old runner until
the comparison is done.

Persistent self-hosted runners must not run untrusted fork code (see
[security.md](security.md)).

## Caches

- Key dependency caches on OS, architecture, toolchain version and the lockfile hash:
  `${{ runner.os }}-${{ runner.arch }}-node22-${{ hashFiles('package-lock.json') }}`.
  Prefer the setup action's built-in cache (`actions/setup-node` `cache: npm`).
- Build caches (Turborepo, Nx, Bazel, compiler caches) also key on source and build
  configuration, and on trust: a cache written by an untrusted PR must not feed a
  release build. GitHub scopes caches by branch; restore-keys only fall back within
  that scope and the default branch.
- A cache hit is a speed fact, never release evidence. Release artifacts are immutable
  and bound to a gate result (see [delivery.md](delivery.md)).
- GitHub's cache limit is 10 GB per repository (read 2026-10-30); eviction is
  least-recently-used, so many large keys thrash.

## Cost

GitHub-hosted standard runner rates read 2026-10-30 from GitHub's billing docs:

| Runner | USD/min |
|---|---|
| Linux 1-core x64 (`ubuntu-slim`) | 0.002 |
| Linux 2-core x64 | 0.006 |
| Linux 2-core arm64 | 0.005 |
| Windows 2-core (x64 or arm64) | 0.010 |
| macOS 3/4-core | 0.062 |

Included compute each month: Free and Free-for-orgs $12, Pro and Team $18, Enterprise
Cloud $300. Standard runners are free in public repositories; larger runners are not.
Failed jobs and re-runs are billed. Re-read the page before quoting numbers.

An estimate names: source and date of rates, repository visibility and plan, runner
classes, matrix size, retries/re-runs, how many events run per change (PR + merge
group + push is three), setup minutes, artifact and cache storage. Pass a rates file to
the collector for a list-price estimate:

```json
{ "source": "https://docs.github.com/en/billing/concepts/product-billing/github-actions",
  "date": "2026-10-30", "currency": "USD",
  "perMinute": { "linux": 0.006, "windows": 0.010, "macos": 0.062 } }
```

The result is list price, not a bill: it excludes included allowance and anything the
rates file does not price.

## Budgets: advisory unless something enforces them

| Kind | What it is | Enforced by |
|---|---|---|
| Static limits | `timeout-minutes`, matrix size, attempt cap, retention days | the workflow itself; check in review |
| Runtime admission | concurrency groups, a local lock, max parallel | the CI provider or local gate |
| Spend limits and alerts | monthly cap, 80% alert | the provider's billing settings (GitHub budgets, vendor dashboard), with an owner |

A budget file in the repository is advisory. Say "monthly budget: advisory" unless a
provider budget or alert is configured, its owner named, and its settings read back.

When required work exceeds the allowance: cut waste first (cancel superseded PR runs,
avoid duplicate events, cache, right-size runners, move portable jobs off macOS), defer
optional work to nightly, then present the funding or authority choice. Never shrink
the required gate to fit the budget without a decision from whoever owns that risk.
