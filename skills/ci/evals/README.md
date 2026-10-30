# Evals

1. **Scripts and templates** (seconds, no network): `node evals/test_scripts.mjs`.
   Covers gate selection and verification, report and quarantine checks, release
   manifest and promotion checks, the collector against a fake API, the instruction
   block, a real sharded node:test run, and actionlint/zizmor on the example workflow
   when installed (skipped tests say the workflow was not validated).
2. **Behavior** (minutes, an agent): `scenarios.json`. Run each scenario with and
   without the skill, three or more times per model route, and assert on diffs,
   commands and attempted external effects.
3. **Hosted** (needs a disposable GitHub repository and authority to administer it):
   push the example workflow, open PRs from a branch and a fork, enable merge queue if
   the plan allows, require `gate`, and confirm a broken test blocks merging. Until this
   runs, the GitHub adapter is statically validated, not qualified.
