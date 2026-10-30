# GitHub Actions

The adapter generates a workflow for this repository's own checks. Start from the
validated example in `evals/fixtures/workflows/ci.yml` and the templates in
`templates/ci/`; change commands, check names, branches and paths to fit the project.
Never ship a workflow you have not at least validated with `actionlint` and `zizmor`.

## Candidate identity per event

| Event | Candidate (`github.sha`) | Base for selection | Default selection |
|---|---|---|---|
| `pull_request` | the test merge commit GitHub checked out | its first parent (`HEAD^1`, checkout with `fetch-depth: 2`) | affected or no-op |
| fork PR, Dependabot | same, without secrets | same | same; never needs secrets |
| `merge_group` | the queue's merge commit, not a PR head | not needed | full |
| `push` to default/release | the pushed commit | not needed | full |
| `workflow_dispatch` | the ref chosen | none | full; no bypass path |

The gate's `verify` checks that the selection names this candidate and this exact
policy file revision. Comparing the merge commit with its first parent gives exactly the
PR's changes on top of the base it was merged with, and needs no later `git fetch`
(which fails in private repositories once checkout credentials are not persisted).

## A pull request runs its own CI code

On `pull_request`, GitHub runs the workflow, policy and gate scripts from the PR's merge
commit. So `gate.mjs select` always picks the full set when a PR changes `.github/`, the
policy file, the policy's folder or the gate scripts' folder, regardless of what the
policy says; a PR cannot narrow its own checks by editing them. A PR that rewrites the
gate scripts themselves can still change its own result, so protect these paths with
required code-owner review (`.github/CODEOWNERS` listing `/.github/` and `/ci/`).

## The expected-evidence gate

1. Copy `templates/ci/` into the repository (for example `ci/`), plus
   `ci-policy.json` written for the project and, if used, `quarantine.json`.
2. `ci-policy.json` lists each required check by job id:
   - no `paths`: always runs (static checks, anything global);
   - `paths`: runs when a changed file matches;
   - `follows`: runs exactly when another check does (shard report mergers);
   - `reports`: where `reports.mjs` finds JUnit files;
   - `fullOn.paths`: global inputs (lockfiles, CI files, build config) that force the
     full set; `fullOn.events` defaults to push, merge_group, workflow_dispatch, schedule;
   - `noop.paths` + `noop.rationale`: files proven irrelevant to every check. Markdown
     is not irrelevant by default; docs that feed a site build belong to a check;
   - `critical`: test-id globs that can never be quarantined;
   - `maxAttempts`: run attempts allowed to satisfy the gate (default 2);
   - `afterGate`: job ids that run after the gate (build, deploy), so the job inventory
     accepts them.
   A changed file that no scoped check claims and the no-op list does not cover makes
   the full set run. That is deliberate.
3. Jobs: `select` → checks (`if: needs.select.outputs.run_<id> == 'true' &&
   github.run_attempt <= fromJSON(needs.select.outputs.max_attempts)`; a sharded check
   uses `matrix.shard: ${{ fromJSON(needs.select.outputs.shards_<id>) }}` and
   `strategy.job-total`, so the policy is the only place the cap and shard count live) →
   `gate` with `if: always()` and `needs` listing `select` and every check. `gate` lists
   this run's jobs with `gh api .../attempts/$ATTEMPT/jobs` (needs `actions: read`) and
   runs `node ci/gate.mjs verify --jobs jobs.json` with `NEEDS_JSON: ${{ toJSON(needs) }}`.
   Any job that is not a policy check, `select`, `gate` or `afterGate` fails the gate, so
   a job added to the workflow but forgotten in the policy cannot slip through. Check
   jobs must not set `name:` (or must set it to their id); matrix jobs appear as
   `unit (1)` and are matched by the part before the parenthesis.
4. Require only `gate` (plus any independent security checks) in protection.

Why not `paths:` on the workflow, or a gate that only rejects `failure`: a workflow
skipped by `paths` never reports, so its required check stays pending forever; and a
job skipped by `if` reports as skipped, which protection treats as passing. The
expected-evidence gate closes both.

## Workflow hygiene

- `permissions: contents: read` at the top; grant more per job, only where needed.
- `persist-credentials: false` on checkout unless the job pushes.
- `timeout-minutes` on every job (the default is 360).
- Concurrency: `group: ci-${{ github.event_name }}-${{ github.event.pull_request.number
  || github.run_id }}`, `cancel-in-progress` only for `pull_request`. GitHub keeps one
  pending run per group and cancels the older pending one even when
  `cancel-in-progress` is false, so a shared group for pushes to `main` silently skips
  commits; `run_id` gives every non-PR run its own group (or use `queue: max`, up to
  100 pending). Order within a group is not guaranteed. Production promotion has its
  own group, where replacing an older waiting deploy is wanted and the release check
  refuses anything older than what is live.
- Pass expressions through `env:`, never inline `${{ }}` inside `run:` scripts.
- Use the repository's real default branch name in `on.push.branches`.
- Upload reports with `if: ${{ !cancelled() }}` and an explicit `retention-days`
  chosen for debugging and compliance needs within the storage budget.

## Changing protection (only with authority to administer the repository)

Inspect first, change in stages, read back after:

```bash
gh api repos/OWNER/REPO --jq '{default_branch, visibility, owner: .owner.type}'
gh api repos/OWNER/REPO/rules/branches/BRANCH          # effective rules on a branch
gh api repos/OWNER/REPO/rulesets --jq '.[] | {id, name, enforcement, target}'
gh api repos/OWNER/REPO/branches/BRANCH/protection     # classic protection (404 = none)
```

1. Add the `gate` job and let it run green on real PRs before requiring it.
2. Add `gate` as a required status check (ruleset `required_status_checks`), keeping
   existing security and compliance checks required.
3. Only then retire required checks that `gate` now covers, one change at a time,
   with the previous rule JSON saved for rollback.
4. Read back the effective rules and bypass actors. Prove protection in an authorized
   disposable branch or draft PR: a deliberately failing test must show `gate` failing
   and merge blocked.

If a change fails or the plan lacks a feature, report protection as not enforced.
Never loosen protection to get past an error.

Renaming or re-sharding jobs changes check names; requiring only the stable `gate`
avoids leaving PRs pending on a check that no longer exists.

## Merge queue

Merge queues are available for organization-owned public repositories and for
organization-owned private repositories on Enterprise Cloud (check current docs and the
actual plan). With a queue: add `merge_group: types: [checks_requested]`, keep required
checks identical for PR and queue, and expect each change to run twice. Without one,
"require branches to be up to date before merging" re-tests against the latest base at
the cost of more rebases. Do not claim a queue exists until the rules read back.

## Other hosted CI

GitLab CI, Buildkite, CircleCI, Jenkins and others keep their owner. Apply the same
rules (one stable required result, expected-evidence aggregation, conservative
selection, reports, scoped credentials) in that provider's terms and say the adapter is
guidance only: nothing here has been qualified on those providers.
