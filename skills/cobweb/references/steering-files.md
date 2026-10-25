# Steering files by tool

What each agent tool loads, as of October 2026. **Always** means loaded at session
start, so every byte costs tokens on every turn. **Scoped** means loaded by glob,
directory or description. **On-demand** means loaded when invoked. Re-check a
tool's docs if a version matters: these paths moved several times in 2026.

| Tool | Repo paths | Loads | Fails silently when |
|---|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` (gitignored), nested `CLAUDE.md`; `.claude/rules/**/*.md` (`paths:` frontmatter scopes them); `.claude/skills/*/SKILL.md`; `.claude/commands/` (merged into skills); `.claude/agents/`; `.claude/settings.json` (hooks, permissions); `.mcp.json`; `@path` imports (max 4 hops) | `CLAUDE.md` in cwd and every parent, rules without `paths:`, and the first 200 lines or 25 KB of auto-memory: always. Subdirectory `CLAUDE.md` and scoped rules: when a matching file is touched. Skills: by description. | AGENTS.md is read only if no `CLAUDE.md` or `CLAUDE.local.md` exists in or above cwd, so a one-line `@AGENTS.md` import is the usual bridge. On-demand files over about 40k chars are cut. Conflicting files: Claude "may pick one arbitrarily". Skill description + `when_to_use` over 1,536 chars is cut. |
| Codex | `AGENTS.md`, `AGENTS.override.md` per directory; `.codex/config.toml`, `.codex/hooks.json`, `.codex/agents/*.toml`, `.codex/rules/*.rules`; `.agents/skills/` from cwd up to repo root | The instruction chain from root to cwd, concatenated: always. Skills: names and descriptions up front, body on use. | Total cap 32 KiB (`project_doc_max_bytes`): files past it are dropped without warning. `AGENTS.override.md` hides the sibling AGENTS.md. Untrusted projects skip every `.codex/` layer. |
| Cursor | `.cursor/rules/**/*.mdc` (frontmatter `alwaysApply`, `globs`, `description`); `AGENTS.md` (root and nested); `.cursor/mcp.json`; `.cursor/hooks.json`; skills in `.cursor/skills/` and `.agents/skills/` | `alwaysApply: true`: always. `globs`: when a matching file is in context. `description` only: when the agent decides. None of these: only on `@` mention. | Plain `.md` files in `.cursor/rules/` are ignored. `.cursorrules` is legacy and no longer in Cursor's docs. A rule's `@file` is a pointer and isn't inlined. |
| GitHub Copilot | `.github/copilot-instructions.md`; `.github/instructions/*.instructions.md` (`applyTo`); `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`; `.github/prompts/*.prompt.md`; `.github/agents/`; `.github/skills/`; `.github/hooks/` | The repo-wide file and AGENTS.md: always. Path-specific files: when a match is touched. Support differs across CLI, VS Code, JetBrains, the cloud agent and code review. | VS Code and the CLI combine files with no precedence order. Code review reads the PR head branch. A running CLI session doesn't see edits until resumed. |
| Gemini CLI | `GEMINI.md` (and in parents up to `.git`); `.gemini/settings.json`; `.gemini/skills/`, `.agents/skills/`; `.gemini/commands/*.toml` | Always. Nested `GEMINI.md` files load just in time. `@file` imports. | AGENTS.md is **not** read unless `context.fileName` names it. |
| Windsurf / Devin | `.devin/rules/*.md` (preferred), `.windsurf/rules/*.md`, legacy `.windsurfrules`; AGENTS.md; Devin CLI also reads `CLAUDE.md`, `AGENT.md`, `.cursor/rules` | `trigger:` is `always_on`, `model_decision`, `glob` or `manual`. Root AGENTS.md: always. | Each rule is capped at 12,000 chars; the global rules file at 6,000. |
| Cline | `.clinerules/` (or the legacy single file), `.cline/rules/`, AGENTS.md, `.cursorrules`, `.windsurfrules` | Always, unless `paths:` frontmatter scopes the rule. | Invalid YAML frontmatter fails open, so the rule is always active. |
| Roo Code | `.roo/rules*/`, `.roorules`, `.roomodes` | Always, in alphabetical order. | **Discontinued on 2026-05-15.** These files are cobwebs unless the team uses a fork (Kilo, Zoo). |
| Aider | `CONVENTIONS.md` or any file named in `read:` in `.aider.conf.yml` | Only files listed via `--read` or the config. | Nothing is auto-discovered, so an AGENTS.md is ignored unless it's listed. |
| Continue | `.continue/rules/*.md` (`globs`, `regex`, `alwaysApply`) | Joined in filename order. | Legacy YAML rules. |
| Zed | The **first** match of `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`; skills in `.agents/skills/` | Always: one file only. | A stray `.rules` or `.cursorrules` hides AGENTS.md completely. |
| Kiro | `.kiro/steering/**/*.md` (`inclusion:` `always`, `fileMatch`, `manual`, `auto`); AGENTS.md | `always` is the default. | Unresolved `#[[file:...]]` references leave a visible marker. |
| JetBrains Junie | `.junie/AGENTS.md`, AGENTS.md, `.junie/rules/`, legacy `.junie/guidelines.md` | Always, in that order. | Legacy file names. |
| Amp | `AGENTS.md` in cwd, parents and subtrees; falls back to `AGENT.md` or `CLAUDE.md` | cwd and parents: always. Subtrees: on read. | — |
| OpenCode | `AGENTS.md` (falls back to `CLAUDE.md`); `opencode.json` `instructions`; `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | Always. | First match wins per category. |
| Goose | `AGENTS.md`, `.goosehints` | Always; nested files when touched. | — |
| Jules | Root `AGENTS.md` | Always. | Root only. |
| Agent Skills (shared) | `<skill>/SKILL.md` + `scripts/`, `references/`, `assets/` | Name and description (≤1,024 chars): always. Body: on activation. References: when read. | A vague description means the skill never fires: one eval found skills uninvoked in 56% of cases. |

## What to check across tools

1. **Which tools are actually in use?** The fingerprint lists configured tools. Files
   for a tool nobody uses (Roo, legacy `.cursorrules`) are clutter that other tools
   may still read (Zed, Cline).
2. **One source of truth.** When several tools' files exist, the healthy shape is one
   canonical file plus thin pointers or imports (`CLAUDE.md` holding just
   `@AGENTS.md`). Copies drift: diff them, and report each disagreement as a
   Steering item.
3. **Size.** Report always-loaded bytes ÷ 4 as approximate tokens a turn. Above about
   200 lines or 8 KB per file, ask of each line: "Would removing this cause an agent
   to make a mistake?" (Anthropic's test). Lines that fail it are Suggests unless
   they're stale, which makes them Will do.
4. **What evidence says helps.** Non-obvious commands, tools and conventions the
   agent can't infer from the code. What doesn't help: repo overviews and directory
   trees (no faster discovery, +20% cost in the ETH Zurich study), style rules a
   linter enforces, history.
5. **Hooks.** A `PreToolUse`/`PostToolUse` hook with matcher `*` runs on every tool
   call. Check what it runs, how long it takes, and whether its log grows without
   bound.
6. **User-level files** (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, global rules)
   steer every project, but they're outside the repo. Audit them only if the person
   asks.

## Memory stores

Memory loads like an instruction file but usually lives outside git. Ownership
decides what the skill may change (SKILL.md step 4, "Memory").

| Tool | Where | Loads | Owner, and how to change it |
|---|---|---|---|
| Claude Code auto-memory | `~/.claude/projects/<repo path with non-alphanumerics as ->/memory/`: `MEMORY.md` index plus one topic file per memory. Frontmatter `name`, `description`, `metadata.{type, modified, originSessionId}`; types user, feedback, project, reference. | The first 200 lines or 25 KB of `MEMORY.md` at session start; later lines never load, and Claude is told to rewrite the index. Topic files load when read. Subagents don't get it. | Plain files with no history, outside git. Worktrees of one repository share a store; a separate clone has its own (`--also=<path>`). Encode candidate paths to find it; folder names can't be decoded. Archive, never delete. |
| Memory tracked in the repo | `memory/`, `.memory/`, notes folders | Like docs | Git: treat like docs |
| Codex | `~/.codex/memories/` (generated) with state in `~/.codex/memories_1.sqlite`. Off by default (`[features] memories = true`). | Injected into later sessions when on | The docs call it generated state: change it only through Codex (Settings > Delete Codex memories, or `/memories`). Open the database only with `mode=ro&immutable=1`. |
| Gemini CLI | `save_memory` appends to `~/.gemini/GEMINI.md` under "Gemini Added Memories" | Every Gemini session | Plain file, the person's global instructions: Suggests only |
| Windsurf / Devin | `~/.codeium/windsurf/memories/` (Cascade memories); `global_rules.md` | Memories: retrieved by the app. Global rules: always. | Memories through the app. `global_rules.md` is the person's file. |
| Cursor | In-app (Settings > Rules), if the feature still exists | App-managed | Only through the app |
| GitHub Copilot memory | Server-side, scoped to the repository; checked against the current branch; unused facts expire after 28 days | Cloud agent, code review, CLI | Repo Settings > Copilot > Memory |
| Host app project memory (for example Tatastu: a `project_memories` table, up to 8 facts / 2,600 chars injected into a session's first turn, edited in the chat toolbar's memory panel) | The app's private state | Injected into prompts by the app | Never touch. Report stale facts and say where in the app to remove them. |
