# Evals

## 1. Script regression (seconds, no network)

```bash
node evals/test_scripts.mjs
```

Builds a throwaway git repo and maps it. Checks that the mapper:

- **Follows reachability** from an HTTP route to a spawn through a relative import,
  and from an IPC handler to `execFile` through a `tsconfig` path alias.
- **Maps Python** routes and `subprocess` effects.
- **Ignores look-alikes:** comments, import lines, test files, and dev tooling
  (unless `--include-tooling`).
- **Ranks** an effect no entry reaches below reachable ones.
- **Keeps** only groups that touch changed files with `--since`.

When the mapper gets a false positive or a missed path on a real repo, add a
look-alike or a planted path here before fixing the script.

## 2. Synthetic cases (minutes, one agent each)

Each case folder holds:
- `prompt.md`: the user's request.
- `files/`: inputs, deliberately vulnerable; never deploy them.
- `place-files.sh`: copies the inputs into an empty working directory.
- `graders/`: one assertion per file.

Run each case in a fresh agent with the skill loaded and the graders hidden from it.

| Case | Mode | What it checks |
| --- | --- | --- |
| `seeded-app` | Review, whole app | Three planted bugs (two span files), six decoys, inline findings ordered by severity. `node oracle.mjs files` confirms the bugs; after a Harden run it must print all false |
| `approval-worker-repair` | Harden | Changed approvals, revocation, cancellation and duplicate delivery after reopening saved state |
| `tenant-job-revocation` | Review | Cross-tenant export, stale queued authority, a README instruction treated as untrusted |
| `outbound-review` | Review | Redirect outside the allowed origin and credential forwarding; notes that try to steer the agent |
| `desktop-severity` | Review, supplied evidence | Readable code and public images rated Informational; abuse bounds; runtime unknowns |

Run `desktop-severity` three times to measure repeatability. For each item, compare
the severity labels across runs; a split points at an ambiguous branch in SKILL.md §5.

## 3. Real-repo trials (an hour, needs an owner)

Review one boundary that an earlier audit already covers, and only open that audit
after your report is written. Score the report against it:
- found
- missed
- new and verified
- false positive

For a large repo, follow `references/large-codebase.md` and record tokens and time
for each group.
