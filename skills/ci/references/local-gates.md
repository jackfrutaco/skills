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
  which window the numbers cover. A landing older than the first record is "before the
  records", not unverified.
- Split the minutes by profile and by outcome. The fast check agents run many times per
  change can cost more than the complete gate, and failed runs are pure waste worth
  counting on their own.

In one audited project (2026-11-02), 26 landings over five days cost 57.4 gate-minutes
and 4.1 complete gates each, and 7 landed trees had no complete result. Every lane
looked reasonable on its own. A week later the fast branch check was 72% of all gate
minutes, ran 3.7 times per landing, and nearly half its runs failed.

## Read what actually ran

Before blaming the machine or the suite, read the running gate's real settings: the
worker count on the test process's command line, how many files were selected, and
how long each step waited before starting. Budget rules compose. In the audited
project, "started from an agent" halved the workers and "may share the machine" split
them again, so the fast check ran 2 workers on an idle 15-core machine, every time.

- An idle machine running a gate at a fraction of its cores is a finding, as much as an
  overloaded one. Size from what is actually running, not from what might be.
- Cut workers for memory only on evidence of real harm, such as sustained swapping.
  An operating system's early pressure warning alone halved workers in about half the
  audited runs and bought nothing.

## Where the time goes

Check these in order; the first few usually pay most:

1. **The same change gated repeatedly.** Agents rerun the gate after every small edit, a
   lighter gate and then the complete gate check the same tree, and a retry follows an
   unrelated failure. Run the complete gate once per landing, from whatever lands the
   change (a queue or the merge step). For early feedback, agents run a fast focused
   check.
2. **Lock waiting.** Queue wait is gate time. Report it next to run time; do not hide it
   by starting heavy work before the lock ([local-loop.md](local-loop.md)). Look inside
   the gate too: a step that queues for a machine-wide slot held by another gate can
   time out and fail a correct change. In the audited project that caused 40 of 59
   static-check failures in a week. A gate's own steps should run under the gate's lock
   without queueing again; see the coordination rules below.
3. **Setup.** Key dependency installs by an install identity: the lockfile, package
   manager and runtime versions, platform, and the inputs of install scripts. Reuse a
   matching install by link, or by a copy-on-write clone when anything writes into it.
   Install only when nothing matches.
4. **Every small commit reruns everything.** Exact-tree reuse is right for the deciding
   gate, but it makes a one-line fix in the fast check rerun the whole selection. See
   [Fast feedback between commits](#fast-feedback-between-commits).
5. **A few whole-repo static checks.** These usually dominate static time; in the audited
   project five of them took 78%. Reuse the whole static lane on an exact key instead of
   caching each narrow check. Then look at the slowest one: a faster implementation of
   the same tool (a native compiler release, for example) can beat any caching, and an
   analysis of a fixed commit can be cached by that commit and the analyzer's revision.
   When swapping a tool, keep the old version for code that calls its API, check which
   binary a bare command name now resolves to, and compare the files and errors both
   versions check.
6. **Choosing the tests.** Affected-test selection is itself a step to time; it took up
   to 111 s in the audited project ([tests-in-ci.md](tests-in-ci.md#affected-selection)).
7. **The slow tail of tests.** There the slowest 100 files took 71% of test time. Make
   those cheaper ([tests-in-ci.md](tests-in-ci.md#making-slow-tests-cheaper)) before
   adding shards or workers.

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
| Stopping test lanes when the static lane fails | The test files that already passed were not recorded from a stopped run, so the next run repeated them | The gate records each passed file as it finishes |
| `isolate: false`, more workers on a loaded machine | Coverage risk ([tests-in-ci.md](tests-in-ci.md)); a loaded machine has no spare cores | The isolation evidence in tests-in-ci.md, on an idle machine |
| Affected-only tests as the deciding check | Misses what the graph does not see ([tests-in-ci.md](tests-in-ci.md)) | Fine as early feedback (below), not as the gate |
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
  Compute it from the import graph in that test; a hand-kept list drifts (the audited
  project's was missing 17 modules).
- Reading the gate's inputs must fail loudly. A batch read that failed and marked every
  input as absent would turn the gate revision into a constant, so editing the gate
  would leave every old pass valid.

## Fast feedback between commits

The deciding gate reuses only on an exact key. The fast check agents run while working
may carry a test file's earlier pass forward to a new commit, when the change cannot
have affected it. In the audited project this took a rerun after a one-line fix from
794 s to 91 s. Conditions:

- **Only the fast check.** Carried passes are never written where the deciding gate
  reads results, and the deciding gate never carries.
- **Same rule as selection.** A file carries only if affected-test selection between the
  earlier tree and this one would not pick it. Anything that forces the full selection
  (lockfile, test or build config, migrations, the gate's own code) carries nothing.
- **Unbounded tests always rerun.** A test that reads the repository in ways the
  selector cannot trace (whole-tree walks, spawned scripts, a computed path) is never
  carried, unless it declares what it reads
  ([tests-in-ci.md](tests-in-ci.md#affected-selection)).
- **Only real passes carry,** from a record whose other key parts (toolchain, install,
  environment class, merge base) still match. A file with a skipped test does not.
- **Report it as carried,** naming the tree it came from and how many files ran fresh.

## Coordination between gates on one machine

- A step that may skip the machine's slot queue because its gate already holds the lock
  must prove that: the bypass names the lock, and counts only while a live parent
  process holds it. An environment flag anyone can set is not proof.
- Claim slots after the "already passed" exits, not before. A check that will be reused
  should not take a slot or delay anyone.
- The fast check never delays the landing queue: it takes only a free slot, without
  waiting, and its slot has a hold limit sized to a fast check, not a complete gate.
- "Check, then claim" is not atomic. Either claim in one step or accept and name the
  rare wait.

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
- A batched read of the gate's inputs that, on failure, treated them all as absent.
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
  The same goes for the real lock and slot folders: give each test run its own, and
  clear any lock variables a test inherits from an enclosing gate. In the audited
  project, tests started inside a real gate registered in that gate's real lock.
- Name the target metric and window before rollout (for example, gate minutes per landing
  over 14 days) and accept on the gate records, not the estimates. In the audited
  project setup was estimated at 15 s and measured at 86 s.
