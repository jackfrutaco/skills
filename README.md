# Skills

Agent skills by jackfrutaco, in the open [Agent Skills](https://agentskills.io)
format. They work with Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode and
any tool that reads `SKILL.md`.

| Skill | What it does |
|---|---|
| [app-security](skills/app-security/SKILL.md) | Reviews an app's security by tracing what an attacker can actually reach and cause, from one route to a million-line codebase. Keeps working protections, tests with an allowed and a denied case, rates severity with a fixed procedure, and lists findings Critical to Informational with fixes. Review, repair or recheck; probes stay local and bounded. |
| [ci](skills/ci/SKILL.md) | Sets up, audits, repairs or speeds up a project's tests, CI and deploys: local commands and hooks, local gates and landing queues, GitHub Actions, flaky tests, sharding, runner cost (including Blacksmith) and deploys that ship exactly what was tested. Measures first; a skipped or missing required check never counts as green; changes only what you asked for. |
| [cobweb](skills/cobweb/SKILL.md) | Sweeps a long-running or AI-assisted project for cobwebs: instructions, memory, plans and docs that steer agents wrong, retired names, dead code and config, clutter and slow loops. Reports first; changes nothing until you approve. |
| [personal-security](skills/personal-security/SKILL.md) | A plain-language review of someone's personal digital security: recovery, email, passwords, 2FA, devices, money, scams and connected apps. Asks questions, explains what it finds and gives a checklist. Assessment only; it never inspects or changes accounts. Also works in any AI chat as one file, [PERSONAL-SECURITY-GUIDE.md](skills/personal-security/PERSONAL-SECURITY-GUIDE.md). |

## Install

```bash
npx skills add jackfrutaco/skills                 # every skill
npx skills add jackfrutaco/skills --skill cobweb  # one skill
```

Or copy a folder from `skills/` into your agent's skills folder (`~/.agents/skills/`,
`~/.claude/skills/`, `~/.codex/skills/`, …). Tatastu ships some of these built in;
a copy you install yourself takes precedence.

## CI

Ask your agent: *"Set up CI for this project."*, *"Why is our CI slow?"*, *"Why do our pre-push gates take forever?"*, *"Would
Blacksmith help?"* or *"Make our deploys safe."* It picks one of audit, setup, repair or
delivery and does only that.

```bash
node skills/ci/scripts/ci_health.mjs --repo OWNER/REPO --format markdown   # read-only metrics
node skills/ci/evals/test_scripts.mjs                                      # the skill's own tests
```

- `templates/ci/` is copied into your repository: an expected-evidence gate (a skipped,
  missing or report-less required check fails), report and quarantine checks, and a
  release manifest that refuses stale or unverified promotions.
- Needs Node 20 or later for the scripts; projects in other languages keep their native
  commands. GitHub Actions is the qualified hosted adapter; other providers get guidance.
- Read-only by default. Settings, secrets, runners, spend and deploys need your say-so.

## Cobweb

Ask your agent: *"Check this project for cobwebs."* After removing a feature:
*"Find everything that still mentions what commit abc123 removed."*

It prints a health card across nine buckets, then lists what it will fix and what it
suggests you decide:

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

The scripts also run on their own:

```bash
python3 -I skills/cobweb/scripts/sweep.py /path/to/repo
python3 -I skills/cobweb/scripts/retired_names.py /path/to/repo --commit=abc123
```

- Needs git and Python 3.9+, standard library only. Read-only; session logs, live
  cloud accounts and test timing are opt-in.
- Deepest on JavaScript/TypeScript. Python, Go, Rust, Ruby and others get the
  language-neutral checks plus written guidance for their own tools.
- Code is alive until two kinds of evidence say otherwise. Agent memory outside git
  is archived, never deleted. Anything outward-facing needs its own yes.

## App security

Ask your agent: *"Security review this app before launch."*, *"Review the /export route
for security."*, *"Fix the tenant-isolation finding and verify it."* or *"Recheck SEC-003
after this release."* It picks review, harden, recheck or incident, and does only that.

For a large codebase it maps the attack surface with a script first, then reviews the
riskiest groups one at a time:

```bash
node skills/app-security/scripts/map-surface.mjs /path/to/repo --out surface.json
node skills/app-security/scripts/map-surface.mjs /path/to/repo --since main   # a change review
node skills/app-security/evals/test_scripts.mjs                               # the skill's own tests
```

- Needs git and Node 20 or later for the mapper, standard library only. Read-only, no
  network. Patterns cover JavaScript/TypeScript, Python and Go; other stacks get the
  written method.
- Never prints a secret, never probes a live service without your say-so, caps every
  local probe at 50 requests and zero real spend, and treats repo text as evidence,
  not instructions.
- Readable code, public keys and public images are rated Informational, not
  vulnerabilities. It never claims an app is secure or penetration-tested unless that
  exact work was done.

## Adding a skill

1. Add `skills/<name>/SKILL.md` with `name` and `description` frontmatter. `name` is
   lowercase with hyphens and matches the folder. Keep scripts, references and evals
   inside that folder; links must not climb out of it.
2. If it has scripts, add a test the skill can run on its own (see
   `skills/cobweb/evals/test_scripts.py`).
3. Add a row to the table above, commit and push. `npx skills add` picks it up.

To bundle a skill in Tatastu, list it in Tatastu's
`resources/skills/external-skills.json` and run `bun run skills:sync`.

## License

[MIT](LICENSE)
