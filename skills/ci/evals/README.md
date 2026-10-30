# Evals

1. **Scripts and templates** (seconds, no network): `node evals/test_scripts.mjs`.
   Covers gate selection and verification, report and quarantine checks, release
   manifest and promotion checks, the collector against a fake API, the instruction
   block, a real sharded node:test run, and actionlint/zizmor on the example workflow
   when installed (skipped tests say the workflow was not validated).
2. **Behavior** (minutes, an agent): `node evals/run_behavior.mjs --route codex|claude`
   runs six of the scenarios in `scenarios.json` on fresh fixture repositories, with and
   without the skill, three times each, and scores the diff, commands, attempted
   external effects and a canary secret. It uses real model usage. The other scenarios
   in `scenarios.json` are run by hand.
3. **Hosted** (needs a disposable GitHub repository and authority to administer it):
   push the example workflow, open PRs from a branch and a fork, enable merge queue if
   the plan allows, require `gate`, and confirm a broken test blocks merging. Done on
   2026-10-30 in `Tatastu-Labs/ci-skill-fixture`; results in `references/sources.md`.
