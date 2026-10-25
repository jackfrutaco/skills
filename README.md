# Cobweb

An agent skill that sweeps a long-running or AI-assisted project for **cobwebs**:
instructions, agent memory, plans and docs that send agents after things that are
gone, names the project retired, dead code and config, clutter, and slow loops.

It reports first. You get a health card across nine buckets, then a list of what it
will fix and what it suggests you decide. Nothing changes until you say yes.

```
1 Steering            instruction files, rules, skills, hooks, runtime prompts
2 Memory and setup    agent memory, your global agent setup
3 Authority           docs and plans that look current but aren't, public copy
4 Retired names       features, vendors and models the project removed
5 Ghost code/config   dead modules, test-only code, config naming deleted paths
6 Drag                slow CI, hooks, repo size, where agents stumble
7 Dependency rot      vulnerable, outdated, unused, mismatched pins
8 Clutter             scratch files, stale branches, unused secrets
9 Escape hatches      skipped tests, suppressions, old TODOs (as trends)
```

## Install

```bash
npx skills add jackfrutaco/cobweb
```

or copy `skills/cobweb/` into your agent's skills folder (`~/.agents/skills/`,
`~/.claude/skills/`, `~/.codex/skills/`, …). It follows the
[Agent Skills](https://agentskills.io) format and works with Claude Code, Codex,
Cursor, Gemini CLI, Copilot, OpenCode and any tool that reads `SKILL.md`.

## Use

Ask your agent: *"Check this project for cobwebs."* After removing a feature:
*"Find everything that still mentions what commit abc123 removed."*

The scripts run on their own too:

```bash
python3 -I skills/cobweb/scripts/sweep.py /path/to/repo
python3 -I skills/cobweb/scripts/retired_names.py /path/to/repo --commit=abc123
```

## Requirements and limits

- git and Python 3.9+, standard library only. No installs.
- Read-only. Session logs, live cloud accounts and test timing are opt-in.
- Deepest on JavaScript/TypeScript. Python, Go, Rust, Ruby and others get the
  language-neutral checks plus written guidance for their own tools.
- Tested on macOS; Linux should work; Windows is untested.

## Safety rules it follows

- Code is alive until two kinds of evidence say otherwise.
- Agent memory outside git is archived, never deleted. App-managed memory is only
  reported.
- Anything outward-facing (deleting a branch, secret or cloud resource, publishing,
  rewriting history) needs its own yes.

## Develop

```bash
python3 -I skills/cobweb/evals/test_scripts.py   # fixture test, seconds
```

See `skills/cobweb/evals/scenarios.md` for replaying real cleanups.
