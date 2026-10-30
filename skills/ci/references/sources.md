# Sources and tested versions

Claims in this skill and where they come from. Dates are when they were read. Vendor
claims about their own products are marked (vendor). Re-read live pages before quoting
prices, labels or plan availability; they change.

## Practice

| Claim | Source | Read |
|---|---|---|
| ~10 min build/test feedback; fix or revert a red mainline first | [DORA: continuous integration](https://dora.dev/capabilities/continuous-integration/); [Fowler: Continuous Integration](https://martinfowler.com/articles/continuousIntegration.html) | 2026-10-29 |
| Presubmit runs fast, reliable, project-scoped tests; larger tests post-submit with owners; release candidates are not rebuilt | [Software Engineering at Google ch. 23](https://abseil.io/resources/swe-book/html/ch23.html), [ch. 14](https://abseil.io/resources/swe-book/html/ch14.html) | 2026-10-29 |
| Test sizes by constraint (small/medium/large) | [Google Testing Blog: test sizes](https://testing.googleblog.com/2010/12/test-sizes.html) | 2026-10-29, summary |
| Flaky = fails then passes an identical retry; ticketed states; critical tests still block | [Uber: flaky tests overhaul](https://www.uber.com/blog/flaky-tests-overhaul/) | 2026-10-29 |
| Quarantined tests keep running; failures don't block; broken tests not auto-quarantined | [Trunk: quarantining](https://docs.trunk.io/flaky-tests/quarantining) (vendor) | 2026-10-29 |
| AI raises throughput and instability together | DORA 2025 State of AI-assisted Software Development, via summaries | 2026-10-29, summary only |
| Google flakiness: 1.5% of runs, ~16% of tests (2016 data, Google scale) | Google Testing Blog 2016/2017 | historical; not a present benchmark |

## GitHub Actions

| Claim | Source | Read |
|---|---|---|
| A job skipped by a conditional reports "Success"; a workflow skipped by path/branch filtering leaves its required check "Pending" | [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks) | 2026-10-30 |
| `needs`, `always()`, job skipping | [Using jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-jobs) | 2026-10-29 |
| One pending run per concurrency group (older pending run cancelled); `queue: max`; ordering not guaranteed | [Workflow syntax: concurrency](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) | 2026-10-30 |
| Events, `workflow_run`, `merge_group` | [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows) | 2026-10-29 |
| Privileged events, persistent runners, pinning | [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) | 2026-10-29 |
| Fork and Dependabot runs get no secrets | [Using secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) | 2026-10-29 |
| Merge queue availability | [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) | 2026-10-29 |
| Runner rates, included compute, storage, re-runs billed | [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) | 2026-10-30 |
| Runner labels | [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) | 2026-10-29 |
| Run-usage endpoint is closing down; do not build billing on it | [Workflow run usage](https://docs.github.com/en/rest/actions/workflow-runs#get-workflow-run-usage) | 2026-10-29 |
| tj-actions tag repointing (CVE-2025-30066): pin by SHA | GitHub advisory and incident reports | 2026-10-29, summaries |

## Runners and frameworks

| Claim | Source | Read |
|---|---|---|
| Blacksmith labels, app-per-repo requirement, free minutes and ratios, no concurrency limit, Windows limits (vendor) | [Blacksmith instance types](https://docs.blacksmith.sh/blacksmith-runners/overview.md) | 2026-10-30 |
| Blacksmith per-minute prices | [pricing page](https://www.blacksmith.sh/pricing) | not readable without a browser; unverified |
| Blacksmith organizations only, not personal repos (vendor) | Blacksmith docs, 2026-10-29 research pass | not reconfirmed 2026-10-30 |
| Vitest shards by file; blob reports and merge; isolation trade-offs | [Vitest: improving performance](https://vitest.dev/guide/improving-performance) | 2026-10-29 |
| Playwright sharding, `fullyParallel`, merge-reports | [Playwright: sharding](https://playwright.dev/docs/test-sharding) | 2026-10-29 |
| Workers rollback limits; Pages rollback eligibility | [Workers rollbacks](https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/), [Pages rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/) | 2026-10-29 |
| Wrangler flags used in delivery.md | `wrangler <cmd> --help`, Wrangler 4.119.0 | 2026-10-30 |

## Tested versions

| Item | Version | How |
|---|---|---|
| Node (scripts, tests) | 20.20.2 and 26.10.0; standard library only. Node 20 is past end of life: run on a supported LTS | `node evals/test_scripts.mjs` on both |
| node:test JUnit reporter and `--test-shard` | Node 26.10.0 | automated in `evals/tests/local-adapter.test.mjs` |
| Vitest JUnit + `--shard` | 5.0.5 | manual run, 2026-10-30; red shard detected by `reports.mjs` |
| Playwright JUnit + `--shard` | 1.64.1 | manual run, browserless specs, 2026-10-30 |
| actionlint | 1.7.12 | example workflow clean |
| zizmor | 1.31.1 | example workflow clean, online (impostor-commit and known-vulnerable-action audits included); only `anonymous-definition` infos in auditor mode |
| Wrangler | 4.119.0 | `deploy --dry-run --outdir`, `versions upload --no-bundle --assets --dry-run` on a Worker with assets and a dynamic import; no real account |
| actions/checkout, setup-node, upload-artifact, download-artifact | v7.0.1, v7.1.0, v7.0.2, v8.0.2 (SHAs in the example) | pinned 2026-10-30 |
| `ci_health.mjs` live read | one public organization repository, 14 days | 2026-10-30, read-only |

## Not yet qualified

- The example workflow has not run on GitHub. Hosted event behavior (fork, Dependabot,
  merge queue, manual dispatch) and protection read-back are unverified until a
  disposable fixture repository exercises them.
- The Cloudflare deploy leg has not run against a staging target.
- Blacksmith migration has not been measured on a comparable workload.
- Other CI providers and other test frameworks: guidance only.
