---
name: cobweb
description: "Sweep a long-running or AI-assisted ('vibecoded') project for cobwebs: instructions, agent memory, plans and docs that steer agents wrong, names the project retired, dead code and config, clutter, and slow loops. Gives a health report first, then a sectioned list of what it will do and what it suggests, and changes nothing until the person approves. Use when someone asks what is stale, crufty, outdated or slowing a repo down, wants a cleanup or tech-debt sweep, wants AGENTS.md, CLAUDE.md, rules, skills, memories or docs checked for drift, or has just removed a feature and wants every leftover mention found. Works on any language and any agent tool."
---

# Cobweb

A project that agents have worked on for months collects guidance that points at
things that are gone, names it retired, code nobody runs, and loops that make every
change slow. Agents follow written instructions literally, so a stale line produces
wrong work, not just noise. This skill finds those cobwebs, proves each one, reports
on project health, and removes the clear wins once the person says yes.

## Rules

1. **Report before acting.** Nothing in the repo changes until the person has read
   the health report and approved items. The report is the product; a fix the
   person didn't approve is a surprise.
2. **Rank by harm to the next agent: misleading > dead > slow.** A wrong instruction
   makes an agent run a missing command or edit a dead copy. Dead code misleads
   passively. Slowness taxes every loop but doesn't send it the wrong way.
3. **Scripts find candidates; you decide.** Read every candidate line in context
   before it goes in the report. A script hit is a lead, never a verdict.
4. **Steering is stale on evidence; code is alive until proven dead.** An
   instruction that names a missing path, script or retired name is wrong. Code is
   used until two independent kinds of evidence agree it isn't (step 4).
5. **Delete, don't add.** The fix for a stale rule is removing it or pointing at the
   file that holds the truth. Instruction files only grow unless someone cuts them.
   Before cutting a rule, find why it was added (`git log -S'<phrase>'`) and say so.
6. **Sweep the current code.** If the checkout is behind its base branch, sweep the
   base in a temporary worktree. A stale checkout reports problems already fixed.
7. **The owner's map beats your guess.** If the repo says which docs are current (a
   docs index, status banners, CURRENT/ARCHIVED markers, ADR status) or ships its
   own hygiene checks, use those first and judge against them.
8. **Never quote session logs or secrets.** Session-log findings are counts and
   names. Secret-scan output stays redacted.
9. **Memory belongs to whoever stores it.** Agent memory outside git has no history
   to undo a mistake, and an app's memory store is the app's. Report on all of it;
   change only plain files, only with a yes, and only by archiving (step 4,
   "Memory").

## Process

### 0. Frame: one message at most

Ask only what the request didn't answer, in one message, then start:
- Scope: whole repo (default) or an area.
- May I read this project's local agent session logs (Claude Code, Codex)? Default
  no. They show where agents actually stumble, which no static check can.
- May I run the test, typecheck and build commands to time them? Default no.
- May I compare your live accounts with the repo, using read-only list commands
  (Cloudflare, Railway, Vercel)? Default no. See "Beyond the repo" in
  [references/buckets.md](references/buckets.md).

Also say, without asking: "I'll read this project's agent memory and your global
agent setup (names and counts only in the report). Say if you'd rather I didn't."
Memory loads into every session, so it steers like an instruction file. If they
object, pass `--no-memory --no-global`.

A "no" to tests and builds still allows read-only checks: package audits, outdated
reports, secret scans, and owner checks that only read (open the script first to
confirm it writes nothing).

### 1. Sweep

```bash
S=<this skill's directory>/scripts
python3 -I "$S/sweep.py" <repo> --out=<new temp dir> [--transcripts]
```

Read the health card it prints, then the `<check>.txt` files it names. Each script
also runs alone (`fingerprint`, `steering_refs`, `config_refs`, `retired_names`,
`cruft_scan`, `drag`, `deps`, `agent_home`, `test_scan`, `prompt_surfaces`,
`transcripts`); `sweep.py --help` lists
every option. Keep the output folder: the next sweep's `--compare=<this folder>` shows
what is new and what got fixed.

- **If the sweep says STOP** (the checkout is behind its base), run the worktree
  commands it prints, with a unique folder from `mktemp -d` (several agents may be
  sweeping at once; never delete temp folders by pattern), sweep the worktree with `--also=<original repo>` so session
  logs still match, and remove the worktree at the end. Confirm it's gone with
  `git -C <repo> worktree list`.
- **If it warns that the local base ref is older than origin**, don't fetch without
  permission. Say in the report's first line that findings may already be fixed
  upstream.
- **If the session-log line says LOW COVERAGE or lists near-miss folders**, say so in
  Drag. A few sessions are a sample, not proof that agents are fine.
- **If `python3` is missing**, use the `git grep` fallbacks in
  [references/buckets.md](references/buckets.md).
- **On macOS there is no `timeout` command.** Use a tool's own timeout flag or the
  scripts, which time out internally.
- The sweep takes from 5 s to about a minute. Don't re-run a check to re-read its
  results; read the saved files.

### 2. Stack tools

For each stack the fingerprint lists, run the dead-code, dependency and vulnerability
tools in [references/ecosystems.md](references/ecosystems.md):
- Owner's checks first (the fingerprint lists them). Run only read-only forms: no
  `--fix`, `--write` or `-u`. An owner gate that already fails (a security audit, a
  drift check) is a finding in its own right.
- `deps.txt` already holds the JS audit and outdated results. Run the stack's
  dead-code tool yourself. Until it runs, Ghost code is `unchecked`.
- Dead-code tools over-report. Before trusting any "unused file", run
  `git grep -F <basename>`. Browser `<script>` tags, scripts named in other scripts,
  and config hints are the usual misses.
- Zero-install runners (`npx`, `uvx`, `go run`) are fine. A tool that needs
  `node_modules` or a virtualenv that isn't there goes in "Not checked". Don't
  install to make it run.
- Write down every check you couldn't run and why. It goes in "Not checked".

### 3. Read the steering by hand

Read every always-loaded and scoped instruction file in full. Use
[references/steering-files.md](references/steering-files.md) for which tool loads what.
Scripts only check paths and script names. You check everything else:

- **Claims:** every command, setting location, UI label, tool name, flag, version,
  count and model ID it states. For "X lives in Y", grep Y for X: the file can exist
  after the content moved out of it. Check claims about CI, required checks, branch
  protection and deploys against the live settings with read-only `gh api` calls
  (`repos/{o}/{r}/rulesets`, `branches/<base>/protection`).
- **Silent non-loading:** the card's LOADING lines, plus anything else in the
  reference.
- **Contradictions** between tools' files: package manager, test command, versions.
- **Rules a linter, formatter, type checker or hook already enforces.**
- **Overviews, directory trees, "recent changes" and incident-history sections.**
- **Rules written for older models or retired tools.**

If the product ships an agent, read its runtime prompts and tool descriptions the same
way: `prompt_surfaces.txt` lists dead pointers, settings breadcrumbs with no matching
label, tool names nothing registers, prompt builders only tests use, old model IDs,
shipped-skill hygiene and banned words, each with a confidence ("Runtime prompts" in
[references/buckets.md](references/buckets.md)). They reach every user's agent; every
change is Suggests unless it only fixes a path or label. If it has a public site, legal pages or store listing, check those
claims too ("Public copy and legal"). Report them as their own line in Health, because
they mislead people, not the next agent.

Then read the docs agents read most, to the same depth:
- With session logs, that's `transcripts.txt` "docs agents read most".
- Without them, take the README and the docs the always-loaded files link to.

The biggest cobwebs often sit there, not in the always-loaded file. For a linked doc
over 20 KB, read its headings and check every command, path, version and count it
states. Report its size as a cost, since every agent sent there pays it.

Also check plans against the code:
- `plan_status` lists docs whose header says "not started" while code for the topic
  exists.
- `plan_checkboxes` lists task lists that are fully ticked but still in an active
  folder, marked done with tasks open, or open with tasks naming files that already
  exist.
- `stale_plan_dirs` lists folders of plans untouched for 45 days or more.
- `authority_claims` lists unmarked docs that call themselves "source of truth" or
  "read this first". Search finds them by meaning and drops the folder name that
  says they're old.

Compare them with any plans index, and with docs that disagree about the same state
("email is off" vs "email is on"). An open plan nobody marked parked is still intent:
report it, never archive it unless the code shows it shipped.

Then read `agent_home.txt`: memory candidates, then your global setup. Open each
memory candidate and judge it the same way as an instruction line. If the
conversation shows project memory from the host app (for example a "Project memory"
section), check those facts against the code too. That store is the app's, so only
report them.

### 4. Triage every candidate

```
Is the evidence deterministic? (path gone, name retired in a commit, tool output,
zero references found)
├── No → "Suggests", with the question that would settle it, or drop it
└── Yes → read the line in context. Still wrong?
    ├── No → "Looks stale, is fine", with the reason
    └── Yes → check origin/<base> and the commit that retired it. For a path marked
        `missing` (never deleted here), `git log --all --oneline -- <path>` shows
        whether it lives on another branch or never existed. Fixed, or deliberate?
        ├── Yes → drop it, or "Looks stale, is fine"
        └── No → clear win only if ALL hold:
            • a text or file change, or tests prove behaviour is unchanged
            • one commit reverts it
            • no product, owner or pricing call
            • nothing outward-facing (push, publish, remote branch, history rewrite)
            otherwise → "Suggests"
```

**Before deleting code, require all of:**
- a static tool reports it unused;
- zero hits for its file and symbol names as plain strings across code, config, CI,
  scripts, docs and `origin/<base>`;
- no dynamic loading, registry or route table names it;
- an observation window longer than its longest schedule (cron, quarterly or release
  jobs).

Delete a module together with the tests that only keep it alive.

**Traps that look stale and aren't:**
- compatibility names and migration markers
- public library APIs and plugin entry points
- framework conventions (routes, decorators, DI)
- duplicates that a test keeps identical
- workflows that a local script publishes
- generated and vendored code
- skills or templates the repo ships to other projects
- archived docs that are clearly marked
- tracked files ignored only by this machine's excludes (but links *into* such
  folders are broken for every other clone)

[references/buckets.md](references/buckets.md) lists traps per bucket.

**Will do or Suggests, for the common cases:**
- **Unreferenced files:** Will do for agent scratch, backups, temp folders, and files
  the repo's own `.gitignore` excludes. Suggests for everything else (mockups, root
  HTML, screenshots), because they may be kept on purpose.
- **A status line on a plan:** Will do when the code shows it shipped and the doc
  already records that (a "Built" section, an index entry). Suggests when marking it
  done would be your call on what counts as done.
- **Correcting a doc claim the code disproves** (a wrong command, count or path):
  always Will do.

**Memory: who owns it decides what you may do.**

| Store | What you may do |
|---|---|
| Plain files you own, outside git (Claude Code auto-memory, Windsurf global rules, `~/.gemini/GEMINI.md`) | Report. With a yes, archive: move the file to `~/.claude/cobweb-archive/<date>/<store folder name>/`, outside the memory folder so no tool finds it there, remove its index line, and write a `MANIFEST.md` listing what moved and the index lines removed. Never delete and never rewrite a memory's body: nothing outside git can undo it. |
| Memory tracked in the repo (`memory/`, `.memory/`) | Treat like docs; git can undo it. |
| App-managed stores (Tatastu project memory, Codex's database, Cursor, Copilot) | Never touch the storage. List the stale facts and tell the person where in the app to remove them. |
| Opaque or vector stores | Skip. List under Not checked. |

And by kind (`agent_home.txt` labels each file):
- **preference** (how the person likes things done): never Will do. Code can't prove a
  preference wrong. Duplicates or contradictions go under Suggests, with both quoted
  by file name.
- **incident**: keep. It records why a rule exists, the rationale that stops someone
  deleting the rule later. Suggests at most: fix a dead path inside it.
- **fact** and **reference** (paths, commands, where things live): judge like an
  instruction. A path that git shows deleted makes it Will do: correct it, or archive
  the file if nothing else in it holds.
- **status** (handoffs, "verified", "dispatch status"): the strongest candidates.
  Archive is Will do once the work it describes merged, was archived, or was retired.
  Cite the commit or plan that shows it.

Also Will do: index lines pointing at missing files, and memory files no index lists
when the person wants them found (add the line) or not (archive). An index over its
load limit is a finding in itself, because later entries never load; so is one that
`agent_home.txt` projects will reach the limit within a month.

Global setup is the person's machine, not this project: every item there is
Suggests, with the file and the tool it affects. Claude Code's own `/doctor` already
audits `~/.claude` instruction files and skills, so point to it rather than repeating
it. What cobweb adds: rules copied between tools' user files, skills that say
different things in different tools' folders, skill lists past what the tools list,
remembered project paths that are gone, and hook scripts nothing runs.

**Order within a list:**
1. **Harm:** makes an agent or person do the wrong thing, then wastes time or
   tokens, then cosmetic.
2. **Reach:** always-loaded, then scoped or on-demand, then the README and docs they
   link to, then searched-only.
3. **Cost:** cheapest first.

### 5. Report

Use exactly this structure. The health section comes first because the person
decides from it. Every item is one line: it starts with a verb and cites its evidence
(`path:line`, commit, tool output, a count). Leave out buckets with no findings from
the action sections; they show as `clean` (or `unchecked`) under Health.

```markdown
# Cobweb report: <project>, <date>, <branch>@<short sha>

## Health
| Bucket | Status | Key numbers |
|---|---|---|
| 1 Steering | heavy | 21 KB always loaded (~5.3k tokens a turn); 4 dead paths in CLAUDE.md |
| 2 Memory and agent setup | light | MEMORY.md ~4.4k tokens a session; 4 status notes about merged work |
| ... all 9 buckets ... |
Biggest cobweb: <one sentence>.

## 1 Steering
**Will do** (on your OK)
- [ ] Remove `.github/pr-assets/` from AGENTS.md:121; deleted in 9f12eab (#7762)
**Suggests** (your call)
- Cut the 60-line directory tree in CLAUDE.md:80-140. Agents read the code instead,
  and it costs ~900 tokens a turn. Keep it if humans use it for onboarding.

## 2 Memory and agent setup … ## 9 Escape hatches   (same two lists, in bucket order)

## Looks stale, is fine
- `~/.2code` paths: kept on purpose for compatibility (AGENTS.md:9).

## Not checked
- Go dead code: `go` isn't installed.

## Guard
- <one cheap check that would have caught the top finding, with a baseline that can only shrink>

Reply "do it" to apply every Will do item, or name the ones you want.
```

**Status words:**
- `clean`: no confirmed findings.
- `light`: findings that cost minutes or tokens.
- `heavy`: at least one finding that makes an agent do wrong work, a failing
  security gate or a high or critical advisory in a deployed dependency, or measured
  drag of hours a week.
- `unchecked`: the main tool for the bucket couldn't run. Say why under Not checked.

Use numbers, not adjectives. Put at most 10 items under Will do per bucket; say how
many more there are. Group similar items under "Looks stale, is fine" and keep that
list to about 10 lines.

### 6. Fix, only what was approved

- Steering first. One commit per bucket, and the message cites the evidence.
- In a shared checkout, commit only the files you changed.
- After each batch, re-run the scripts that cover it and show the before/after
  numbers. Run the owner's checks for the files you touched. A code deletion needs
  the build and tests passing.
- Anything outward-facing needs its own yes, even after "do it": push, remote branch
  deletion, history rewrite, secret rotation, publishing.
- Memory: archive, never delete. Don't touch a store that `agent_home.txt` says was
  written in the last 15 minutes: a session may be writing it. Move each approved file
  to `~/.claude/cobweb-archive/<date>/<store folder name>/`, remove its index line,
  and write `MANIFEST.md` there (file, reason, the index line removed), so moving it
  back is one step.
  Before moving one, list the other memories that link to it (`[[name]]`): their links
  will dangle. Name them in the manifest and in your reply.

## Other modes

**After a removal.** When the person has just removed something, or names a commit,
PR or feature they retired, skip the full sweep:

```bash
python3 -I "$S/retired_names.py" <repo> --commit=<sha> [--commit=<sha>]   # or --range=<base>..HEAD
```

It takes everything those commits removed (deleted files, exported definitions,
package.json scripts and dependencies, env vars, names in the subject) and lists
every line that still mentions one. Most hits are Will do: the removal is already
decided. Run it at the end of any removal task, before calling the task done.

**Since the last sweep.** `sweep.py --compare=<previous output folder>` lists, per
check, how many findings are new and how many got fixed. Use it for a monthly
check-up, before handing a repo to someone, or before setting up a new agent tool.

### 7. Guard

Offer one check that would have caught the biggest finding, with a baseline that can
only shrink, so it can't fail on old debt the day it lands.
- Put it in the owner's existing hygiene check if there is one, which the
  fingerprint lists.
- Otherwise, add a small script with a JSON baseline beside it, run from the
  project's lint or CI.

Add it only if the person agrees.

## References

- [references/buckets.md](references/buckets.md): what each bucket covers, the
  evidence it needs, `git grep` fallbacks, and traps.
- [references/steering-files.md](references/steering-files.md): every agent tool's
  instruction files and memory stores, how each loads, and how they fail silently.
- [references/ecosystems.md](references/ecosystems.md): dead-code, dependency, outdated,
  vulnerability and timing tools per stack.
