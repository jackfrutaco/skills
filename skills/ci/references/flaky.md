# Flaky tests

A flaky test passes and fails on the same code and inputs. Treat every claim of
flakiness as a hypothesis until evidence identifies the same test, inputs and
environment.

## Diagnose

1. Start from the **first** failing attempt: its log, report, runner, image, seed and
   timing. A workflow re-run that passed hides it; collect it before anything else.
2. Classify: product regression, test defect (timing, order, shared state, real
   network), infrastructure (runner, network, service, disk), cancellation/timeout, or
   unknown.
3. Reproduce under controlled variation: same commit, repeated
   (`--repeat-each`, `--count`, `vitest --retry=0` in a loop), shuffled order, the
   runner's CPU count, with and without parallelism. Two failures do not prove the
   test deterministic; two passes do not prove it fixed.
4. Fix the cause: wait on events, inject clocks, isolate state, use OS-assigned ports,
   replace live third-party calls with fakes or recordings. Raising a timeout is valid
   only with a measured reason and review; lowering one invites flakiness.

## Retries

- **Diagnostic retries** (re-running to learn) keep every attempt and never change the
  first result.
- **Gate retries** (a framework retry that can turn a check green) have an explicit cap,
  report every attempt, and are not used for unit tests. A retry pass is recorded as a
  flaky signal for that test.
- Workflow re-runs count against `maxAttempts` in the gate policy; beyond it the gate
  reports incomplete verification.

## Quarantine: the test keeps running, its failure stops blocking

The file is optional: without `ci/quarantine.json` nothing is quarantined and every
failure blocks. Entry requires, in that file:

| Field | Meaning |
|---|---|
| `test` | the exact report id (`classname::name`) |
| `check` | the policy check it belongs to |
| `owner` | who fixes it |
| `issue` | the tracking issue |
| `reason` | evidence summary: rate, conditions |
| `riskApproval` | who accepted the coverage risk |
| `entered`, `review` | dates; the review date is a deadline, not a renewal |

`reports.mjs` enforces it:

- Only listed test assertions become nonblocking. Setup, discovery, missing reports and
  a failing command without a reported failure still fail.
- Tests matching the policy's `critical` patterns (auth, billing, data loss, security)
  cannot be quarantined; a consistently failing test is broken, not flaky, and is
  fixed or reverted.
- After the review date the check fails with the entry named. The owner restores the
  test to blocking or renews the entry through review. Nothing deletes the test;
  removing obsolete coverage is a separate reviewed change.
- In the merge step, entries that match no reported test are listed so they can be
  removed in a reviewed change.

Keep the list short. Include its size and the oldest entry date in audits; a growing
list is a finding.
