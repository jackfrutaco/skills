# Evals

## 1. Script regression (seconds, no network)

```bash
python3 -I evals/test_scripts.py
```

Builds a throwaway repo with planted cobwebs and planted look-alikes, one for each
false-positive class found on real repos:
- dotted identifiers
- gitignored files
- placeholders
- negated claims
- fenced examples
- extensionless modules
- dependency binaries
- vendored trees
- archived docs
- shipped skills
- the replacement name in a rename
- version ranges
- memory, config, plan, test and prompt look-alikes

It also builds a fake home folder for the memory and global-setup checks, so it never
reads the real one.

When a new false positive turns up, add a look-alike here before fixing the script.

## 2. Known-answer replays (minutes, real repos)

Sweep a snapshot taken just before someone cleaned the repo by hand, then compare the
report with what they actually changed. Any repo with a cleanup commit works: look for
subjects like "remove dead", "stale", "retire", "clean up docs".

Setup:
1. Run `d=$(mktemp -d)` and `git -C <repo> worktree add --detach "$d/wt" <cleanup>^`.
2. Sweep with `sweep.py "$d/wt" --no-live`. That skips CI, branches, deps, memory,
   remote checks and other worktrees, which would leak today's state into the past.
3. Tell the agent not to read newer commits.
4. Remove the worktree (`git -C <repo> worktree remove --force "$d/wt"`) and `$d`.

What to score:
- **Recall**: the share of files the cleanup changed that the report flags.
- **Clear-win precision**: every Will do item must be correct. One wrong deletion is a
  failed run.
- **Time and tokens.**
- **Skill feedback**: steps the agent found unclear.

Baseline from the first large replay (an agent-built Electron app, 200 files changed
by a three-commit manual cleanup): the scripts alone flagged 34 files and the full
agent report 56 (28%). Instruction files and docs did best (5 of 6 root files, 15 of
27 docs). Dead code needed an installed dead-code tool. Prompt wording that changed
agent behaviour was found from session logs, not files. The test-only-module
detector found all 23 modules a separate cleanup deleted.

Script-level counts mean the file had a finding, not that the finding was the exact
fix. Rerun a replay after any change to the scripts or SKILL.md.

## 3. With and without the skill

Same model, same repo, same prompt ("What's stale here and slowing things down?"),
once with the skill and once without. Compare: number of confirmed findings, false
Will do items, and whether a health report came before any change.
