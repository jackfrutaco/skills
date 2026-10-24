# Personal Security

Helps someone review and improve their personal digital security with the AI they already use. It asks about their setup one question at a time, explains what it sees, offers options (including changing nothing), and walks through any change they choose. It never asks for passwords and never touches accounts on its own.

## Two ways to use it

- **Any AI chat (Claude, ChatGPT and others):** attach [PERSONAL-SECURITY-GUIDE.md](PERSONAL-SECURITY-GUIDE.md) to a new chat and say "Use this guide to review my personal security." No install, terminal or API key.
- **Developer agents:** copy this folder to `.claude/skills/personal-security/` for Claude Code or `.agents/skills/personal-security/` for Codex, in a project or your home folder. Then run `/personal-security` in Claude Code, or ask Codex to use the personal-security skill.

## Files

| File | What it is |
| --- | --- |
| `SKILL.md` | The instructions: rules, session flow, how to ask questions, incidents, pausing |
| `references/questions.md` | The question bank, with answer choices and a reason for each question |
| `references/coverage.md` | The 21 areas a review can cover, plus official sources |
| `PERSONAL-SECURITY-GUIDE.md` | The three files above merged into one, for chats. Generated, so don't edit it by hand |
| `scripts/build-guide.mjs` | Rebuilds the guide |

After editing `SKILL.md` or a reference, rebuild the guide from the repository root:

```bash
node skills/personal-security/scripts/build-guide.mjs
```

Add `--check` to only confirm the guide is up to date.

## Status

Pilot draft, not yet tried with real people. Earlier, longer versions were tested with invented cases in Codex. This shorter rewrite has had a spot check only. Untested so far: the consumer Claude and ChatGPT apps, and Claude Code (blocked by an expired login). 1Password is the preferred paid option, but no sponsorship is agreed. This isn't professional incident response or a security guarantee.

The earlier research notes, test runs and rollout plan are in git history, in commit `806f27f`.
