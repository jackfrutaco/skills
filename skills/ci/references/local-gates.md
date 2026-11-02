# Local gates, landing queues and result reuse

For projects whose deciding check runs on a developer's or agent's machine: a pre-push
gate, a local landing queue, several agents sharing one machine. The hosted rules still
apply, but the waste hides in different places: the same change gated several times,
gates waiting on a machine lock, and every gate reinstalling dependencies. This file
covers measuring that and cutting it without passing anything unverified.

## Measure gate time per landed change

Count per change that reached the default branch, not per run. Each lane can look
reasonable while one change pays for four complete gates.

- Record every gate run: passes, early failures, kills and timeouts. Keep the candidate
  tree and commit, the profile (a lighter branch check or the complete gate), the caller
  (agent, hook, queue), queue wait, setup time, time per lane, outcome and the first
  failure's cause.
- Join the records with merges to the default branch. Report gate minutes per landing,
  complete gates per landing, queue share, and failure causes ranked by minutes lost.
- Flag every landing whose exact tree has no passing complete result, naming its commit
  and tree. That is a false green, and it ranks above every speed finding.
- A store that keeps only the latest N records covers a window, not the history. Say
  which window the numbers cover.

In one audited project (2026-11-02), 26 landings over five days cost 57.4 gate-minutes
and 4.1 complete gates each, and 7 landed trees had no complete result. Every lane
looked reasonable on its own.

## Where the time goes

Check these in order; the first few usually pay most:

1. **The same change gated repeatedly.** Agents rerun the gate after every small edit, a
   lighter gate and then the complete gate check the same tree, and a retry follows an
   unrelated failure. Run the complete gate once per landing, from whatever lands the
   change (a queue or the merge step). For early feedback, agents run a fast focused
   check.
2. **Lock waiting.** Queue wait is gate time. Report it next to run time; do not hide it
   by starting heavy work before the lock ([local-loop.md](local-loop.md)).
3. **Setup.** Key dependency installs by an install identity: the lockfile, package
   manager and runtime versions, platform, and the inputs of install scripts. Reuse a
   matching install by link, or by a copy-on-write clone when anything writes into it.
   Install only when nothing matches.
4. **A few whole-repo static checks.** These usually dominate static time; in the audited
   project five of them took 78%. Reuse the whole static lane on an exact key instead of
   caching each narrow check.
5. **The slow tail of tests.** There the slowest 100 files took 71% of test time. Make
   those cheaper (build shared fixtures once, spawn fewer processes, wait on events
   instead of sleeping) before adding shards or workers.

Failures under load are their own cause. A test that times out only under memory
pressure goes into an intermittent ledger (file, tree, date, first error line), and a
file that shows up repeatedly is flagged. Nothing is retried silently
([flaky.md](flaky.md)).

## Levers that did not pay, and what would reopen them

| Lever | Why not | Reopen when |
|---|---|---|
| Caching each static check separately | The narrow checks totalled about 3 s; the whole-repo ones change on most edits | Narrow checks dominate the measured static time |
| Pooled or pre-warmed checkouts | Setup cost was installs; a checkout took seconds | Measured checkout time dominates setup |
| Batching landings | At about four landings a day, 101 minutes apart (median), batches rarely form, and bisecting a failed batch costs more than it saves | p90 queue wait above about 20 min over a week |
| Merging first, reverting on red | The default branch would hold unverified trees | Never, for required evidence |
| `isolate: false`, more workers on a loaded machine | Coverage risk ([tests-in-ci.md](tests-in-ci.md)); a loaded machine has no spare cores | The isolation evidence in tests-in-ci.md, on an idle machine |
| Affected-only tests as the deciding check | Misses what the graph does not see ([tests-in-ci.md](tests-in-ci.md)) | Fine as early feedback, not as the gate |
| Reusing test results from traced file reads | Reads hide: a native recursive copy (Node's `fs.cp`) shows only the top-level `stat`, and child processes clear `NODE_OPTIONS` or are binaries that ignore it. Results also depend on the caller's environment | Every child reports its reads, a copy counts as reading its whole source tree, and an allowlisted environment is part of the key |

## Reusing a result: the key

A passing result may stand in for a rerun only when every part of its key matches:

| Part | Why it is in the key |
|---|---|
| Tree: a content hash of the candidate, not a branch name or message | The thing that was verified |
| Gate revision: a hash of every file the gate runs, helpers and config included | Fixing the gate must invalidate old passes |
| Toolchain: runtime, package manager and compiler versions | Same tree, different result |
| Install identity | A stale or different install changes what ran |
| Environment class: sandboxed or not, loopback sockets and network available or not | Tests that skip in a sandbox would otherwise satisfy an unsandboxed gate |
| Merge base with the default branch, for checks that compare against it (ratchets, size or coverage budgets) | The comparison changes when the base moves |
| Profile, where profiles run different checks | A lighter profile never satisfies the complete gate |

- Any unknown or unreadable part means no reuse. Old records missing a part miss once.
- A test file with any skipped test is not recorded as passed for reuse.
- A run that crashed or was killed without a report has failed. Rerunning only its
  failures cannot turn it green, because there is no list of failures to rerun.
- Report a reuse as a reuse, naming the record it came from; never as a fresh run.
- Test the gate-revision list itself: every file the gate imports or spawns must be in it.

## A landing queue

- The code that lands comes from the default branch (or a pinned trusted copy), never
  from the branch being landed. Otherwise a branch can rewrite the gate that admits it.
- Approval shows the exact command, arguments quoted.
- Just before pushing, read the state again: the pull request is still open, its base is
  the default branch, and its head is the commit that was verified.
- Push only with a passing complete result for that exact tree and profile.
- When the queue merges the default branch into the head, the verified tree is the
  merged one. Reuse applies only if that tree equals one already verified.
- One runner at a time. Identify a live runner by process id and start time; a process id
  alone gets reused.
- Cleanup deletes only paths the queue created and recorded, never by pattern.

## False greens to audit for

Each of these was found in a real local gate:

- An install marker left behind by a failed install made the next gate use the wrong
  packages. Clear the marker first, write it last.
- A crashed run with no report went green when the gate reran its failures.
- A cached install was accepted while another gate deleted it partway through the copy.
  Copy, then verify identity and completeness before use.
- A sandboxed run's skipped tests counted as passes for an unsandboxed gate.
- The queue ran the lighter branch profile instead of the complete gate.
- Helper files missing from the gate revision, so editing them left old passes valid.
- Landings with no complete result for their tree.

## Changing a gate

- Every fix gets a test that fails on the old code.
- Then run the change once through the real gate on a throwaway commit or branch before
  relying on it. In the audited project that run caught new tests that bypassed the
  project's test isolation, which the unit tests had passed.
- Changes to the reuse key, the queue or what counts as passed get an independent,
  adversarial review. There, review overturned four parts of the first plan and found
  two serious defects after the build.
- While testing, never write state into a shared install (for example a dependency
  folder symlinked from another checkout) or into the real gate ledger. Use a copy.
- Name the target metric and window before rollout (for example, gate minutes per landing
  over 14 days) and accept on the gate records, not the estimates. In the audited
  project setup was estimated at 15 s and measured at 86 s.
