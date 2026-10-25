# Buckets

Each bucket lists:
- **Find**: what the scripts already flag, and what only reading catches
- **Prove**: the evidence an item needs before it goes under Will do
- **Traps**: things that look stale and aren't
- **Fallback**: `git grep` commands for when Python isn't available

Run all commands from the repo root. On macOS, `git grep -E` ignores `\b`: use
`-w` or plain alternation instead.

## 1 Steering

Agent instructions, rules, commands, skills, subagents, hooks and MCP config. See
`steering-files.md` for paths.

**Find**
- Scripts:
  - dead paths, links and scripts (`steering_refs.txt`)
  - `section-gone`: "see CLAUDE.md 'Provider Parity'" where the section no longer
    exists, also in code comments
  - `import-stub`: pointers at an instruction file that is now only an `@import`
    line, so its old sections are gone
  - always-loaded bytes
  - LOADING warnings on the card
  - retired names inside instruction files (`retired_names.txt`, weighted first)
- Reading only:
  - wrong claims about commands, settings, labels, flags, versions and model IDs
  - pointers to a file that exists but no longer holds what's described
  - contradictions between tools' files
  - duplicated rules
  - linter rules restated as prose
  - directory trees and overviews
  - "recent changes" and incident history
  - rules for retired models or tools
  - hooks that fire on every tool call (`drag.txt` flags them)
  - per-machine files that teammates or cloud agents never get (`CLAUDE.local.md`,
    user-level rules)

**Prove**
- The path is absent from `git ls-files` at the base branch.
- Or the commit that removed the thing is named.
- Or the claim was checked against the code (a grep result).

**Traps**
- Paths in fenced examples or templates.
- Placeholders (`path/to`, `NNNN`, `vX.Y.Z`).
- Paths relative to a package root in a monorepo.
- Skills a repo ships to other projects (`payload` class), whose paths name the
  consumer's project.
- Files that are gitignored on purpose (`.env`, build output).
- A rule that looks redundant but is backed by an eval or incident: check
  `git log -S`.

**Fallback**
```bash
for f in AGENTS.md CLAUDE.md .github/copilot-instructions.md GEMINI.md .cursorrules; do
  [ -f "$f" ] || continue
  grep -o '`[^` ]*[/.][^` ]*`' "$f" | tr -d '`' | sort -u | while read -r p; do
    [ -e "$p" ] || echo "$f: missing $p"
  done
done
wc -c AGENTS.md CLAUDE.md GEMINI.md .github/copilot-instructions.md 2>/dev/null
```

### Runtime prompts (when the product ships an agent)

`prompt_surfaces.txt` runs the checks below, each with a confidence. About 75% of
flags on one large agent-shipping app were real when read.

System prompts, tool descriptions (MCP `description`, zod `.describe()`, JSON schema),
reminders and skill indexes built in code steer every user's agent, so they rank with
instruction files. Tested on one large agent-shipping app, these
checks caught 21 of 36 stale prompt items, with these precisions:

- **Settings breadcrumbs** ("Settings → Tools"): the first segment must be a label in
  the settings or navigation registry. 3 of 5; the misses were another app's
  settings (1Password, Xcode).
- **Tool names a prompt mentions** (`mcp__server__tool`, backticked snake_case):
  compare with the registered tools. 1 of 1. Host-owned tools (`update_plan`) are
  traps.
- **Paths in comments and prompts**: count only paths that `git log --diff-filter=DR`
  shows deleted or renamed. 11 of 11 that way, against 9 of 94 without the history
  filter.
- **Prompt builders only tests, evals or scripts import** (`build*Prompt/Block`): the
  claim "every harness gets this" is false. 2 of 4.
- **Model generations older than the repo's own catalog**, outside catalogs (files
  naming 5 or more IDs) and outside tests (124 test hits, 0 real).
- **Links in shipped skills that climb out of the skill folder**, and words like
  "unreleased" or "development checkout" in shipped text.

Behavioural wording (how often to call a tool, what to batch) needs session logs or a
live run, not a scan. Every prompt change is Suggests:
- tests pin the wording
- stable prompt sections are cache-keyed, so their order and bytes matter
- eval arms compare wording
- generated manifests hash it

If the repo already has a prompt-versus-registry test, run that instead.

## 2 Memory and agent setup

Agent memory for this project, and the person's global agent setup. Both load into
sessions like instructions, but most of it lives outside git.

**Find**
- `agent_home.txt`, per memory store:
  - file counts by kind: preference, incident, fact, reference, status
  - the index size, and whether it is over the load limit
  - candidates with reasons: a repo path git shows deleted or moved, a retired name,
    a status note older than 30 days, a file missing from the index, an index entry
    past the load limit
- `agent_home.txt`, global setup:
  - user-level instruction files: size, and local paths that are gone
  - skills with the same name but different content in different tool folders, so
    an agent's instructions depend on which tool it runs in
  - broken skill links, and descriptions over 1,024 characters
  - user MCP servers, which add tool definitions to every session
  - hooks whose script is missing
- Reading only: contradictions between memories and the current instructions or
  code, two memories on the same subject, and memories that restate an instruction
  file.

**Prove**
- A deletion or move in git.
- The commit, PR or archived plan showing that the status a note describes is over.
- For a contradiction, both sources, by file name.

**Fix shape**
- Plain files: archive (move into `archive/` beside the store, drop the index line).
  Never delete.
- In git: like docs.
- App stores: tell the person where to remove the item.
- Global setup is the person's whole machine, so every item there is Suggests.
  Name the file and the tool it affects.

**Traps**
- Memories naming scratch or build-output paths (`.context/`, `out/`): the script
  ignores them, since they were never meant to persist.
- Preferences look old but stay true.
- Incident notes look stale and are the rationale for a rule.
- Identical skill copies across tool folders are how skill installers work. Only
  diverged copies are a finding.
- A memory written in one clone may name paths that only exist in another clone.
  Check `--also` before calling them gone.

## 3 Authority

Docs that look current and aren't: plans, specs, audits and handoffs with no status
line; plans that are done but not archived; docs nothing links to; setup steps that
fail; docs copied from another project; links to files that exist on one machine
only; site and marketing claims for removed features.

**Find**
- Scripts:
  - doc, spec, plan and history findings in `steering_refs.txt`
  - `version-differs`: "Electron 39.8" in a doc while the manifest has 44
  - statuses for paths git doesn't have:
    - `untracked`: in this checkout only
    - `other-worktree`: only in another worktree's untracked files
    - `outside-repo`: a link that climbs out of the repository
  - `plan_status`: a header says unbuilt while code for the topic exists
  - `plan_checkboxes`: fully ticked task lists still in an active folder, plans marked
    done with tasks open, and open tasks naming files that already exist
  - `stale_plan_dirs`: plan folders, including tool-generated ones like
    `.tatastu/plans/` and `.claude/plans/`, untouched for 45 days or more
  - `authority_claims`: unmarked docs that call themselves the source of truth
  - `plan_sprawl`, `dated_piles` and `orphan_docs` in `cruft_scan.txt`
- **Specs that describe deleted features:** for every retired name with `spec` hits
  in `retired_names.txt`, read that spec. A whole spec for a removed feature is the
  most misleading doc an agent can find, because it reads as authority.
- Reading only: follow the README quick start literally, one command at a time, and
  stop at the first step that fails. Compare the plans' task checklists against the
  code that shipped. Check that docs the repo marks CURRENT agree with the code.
  Check counts ("22 browser checks", "23 files") against the list or folder they
  count, and look for state words (on/off, enabled, offline, deployed) where two
  current docs disagree.

**Prove**
- A doc is stale when it names something that's gone, or contradicts a current doc or
  the code.
- A plan is finished when every task has shipped, which you prove by grepping for
  what each task built.

**Fix shape**
- If the repo has a status convention, add a status line (ARCHIVED or SUPERSEDED by
  `<path>`) or move the doc to its archive.
- Delete a doc only when the repo has no history convention and nothing links to it.

**Traps**
- Dated records (retros, ADRs, changelogs, evidence) are history by design: leave
  them alone unless they say they're current.

**Fallback**
```bash
git ls-files '*.md' | while read -r f; do
  b=$(basename "$f"); git grep -qF "$b" -- ":!$f" || echo "unlinked: $f"
done
git ls-files | grep -iE '(^|/)(plan|todo|notes|handoff|summary|status|progress|wip)[^/]*\.md$'
```

### Public copy and legal

README, site, marketing, store listings and legal pages make claims to people, not
agents. Check them in this bucket, but report them separately in Health.

- **Retired names in public files.** Filter with `git blame`: keep a line only if it
  is older than the retirement commit.
- **The owner's vocabulary or copy test, run over the roots it skips.** One app's
  "never say workspace" test covered only the renderer; its logic found about 14
  user-visible strings elsewhere.
- **Vendors named in privacy or security pages, against the manifests and
  integration points.** For example, a privacy page still naming a crash-reporting
  vendor the code removed.
- **Sibling pages that lag each other.** One page was corrected; a sibling page
  still makes the old claim.
- **Version claims ("released v0.2.128") against `package.json` and tags.**
- **Claims a code comment contradicts.** For example, "crash reports if you opt in"
  against "sends no crash reports anywhere".

Legal pages are counsel-reviewed and versioned, often tied to a clickwrap record:
report the mismatch and stop, always Suggests. Publishing any fix needs its own yes.
Traps:
- deliberate history ("purchases made through <old vendor>")
- code identifiers (`Fleet.astro`, `icon("pencil")`)
- vendor terms ("Railway workspace")
- a deleted path that only moved

## 4 Retired names

Features, services, vendors, product terms, flags, env vars and model IDs the project
retired, still mentioned in files.

**Find**
- Scripts: `retired_names.txt`, from retire/remove/rename/replace commits, plus
  `model_ids` in `cruft_scan.txt`.
- The script misses names that commit subjects write in lowercase ("delete the
  orchestrator mode") and retirements no subject describes. To catch those, read
  `git log --since=6.months --format=%s | grep -iE 'retire|remove|rename|replace|drop|delete'`
  yourself, then run `git grep -n -i -w '<name>'` for each name you spot.
- **Model IDs:** compare every ID outside a catalog file with the provider's current
  lineup (search the web if unsure). Stale IDs in scripts, evals, defaults and
  instruction files are findings. A catalog or price table that lists old IDs on
  purpose is not.

- **After-removal mode** (`retired_names.py --commit=<sha>` or `--range=`): everything
  one removal took away, including exported definitions, package.json keys and env
  vars, with every surviving line. It skips names still defined or read elsewhere,
  and lines that describe the removal itself.

**Prove**
- Cite the retirement commit, plus a hit in a file that is current.

**Traps**
- Compatibility names kept on purpose (the repo usually says so).
- Migration markers.
- Changelogs and archives.
- Tests asserting that the old name is rejected.
- A word that is both a retired name and plain English: read the hit.

## 5 Ghost code and config

Dead files, exports and deps:
- parallel implementations (`foo` beside `foo-v2`, `foo-new`, `foo-old`)
- unwired subsystems
- scripts and entry points nothing calls
- flags that are always on or always off
- tests that only keep dead code alive
- compatibility shims past their window
- empty catches and commented-out code

**Find**
- `config_refs.txt`: config naming paths that are gone. Examples: package.json scripts
  running deleted files, CI `run:`/`uses:`/`paths:`/`working-directory`, Dockerfile
  COPY/ADD, tsconfig include/references/paths/extends, knip entry and ignore lists,
  CODEOWNERS, dependabot directories, wrangler `main`, biome scopes. Each comes with
  its consequence: a CI step or image build that fails is harm; a stale ignore entry
  is clutter.
- Stack tools from `ecosystems.md`.
- `parallel` and `commented_code` in `cruft_scan.txt`.
- Flags: grep the flag's name. If every read takes the same branch, or its default
  has been the same for 90 days or more (`git log -S'<FLAG>'`), it's a candidate.

**Prove**: the deletion gate in SKILL.md step 4.

**Traps**
- Dynamic imports and string-built paths.
- Reflection, DI containers and route tables.
- Framework files loaded by convention.
- Plugin entry points.
- Public library APIs.
- Code generators.
- Code used only on another platform or build tag.
- Jobs that run quarterly.
- An export unused on your branch but imported on `origin/<base>`.

**Fallback**
```bash
git ls-files | grep -E '[-_.](v[0-9]+|new|old|legacy|copy|backup)\.[a-z]+$'
f=src/some/module.ts; git grep -n -F "$(basename "${f%.*}")" -- ":!$f"
```

### Tests

`test_scan.txt` runs these. `kind: unreachable` means nothing imports the module at
all; `test-only` means only tests do. Both held up on replays of real cleanups:

- **Modules only tests import.** Build the import graph (tsconfig paths, workspace
  packages) from production roots: entry points, config, CI, HTML `<script>`,
  scripts, framework route folders. Flag modules reached only from tests. That found
  22 of the 23 modules one cleanup deleted, plus 12 removed a week later. Trap: URL
  strings (`"./sw.js"`). knip misses these when `tests/**` is a knip entry.
- **Tests that pin source text** (read a `src/` file as a string and assert on it):
  80% needed action. If the repo has its own gate and baseline for this, report its
  trend instead.

Also: fixtures no file names, env-gated tests whose switch no workflow, script or hook
sets, and test support living in `src/`. Trivial and mock-only tests had no reliable
signal (26% precision at best): use a shortlist to read, never findings. Deleting a
test is always Suggests.

## 6 Drag

Slow or flaky loops:
- for people: install, typecheck, build, lint, tests, dev-server start, CI, git hooks,
  repo size
- for agents: always-loaded tokens, skill index size, MCP servers and tools, hooks on
  every tool call, commands that keep failing, files agents keep re-reading

**Find**
- `drag.txt`: CI medians and failure rates, hooks, largest blobs, branches and
  worktrees, MCP servers.
- `transcripts.txt` (opt-in): commands not found, missing scripts and paths, edit
  misses, re-reads, tool overuse.
  - It reads Claude Code and Codex logs only. A COVERAGE warning means most agent
    work ran elsewhere (Tatastu, Cursor, a cloud agent): report the numbers as a
    sample.
  - Near-miss folders are logs for another clone of the project. Rerun with
    `--also=<that path>` if the person agrees.
- Timing: only with permission, via `drag.py --run="<cmd>"` or the commands
  `drag.txt` lists.

**Prove**
- A measured number: seconds, a failure rate, a count of sessions.
- Commands that keep failing in agent sessions point at something specific:
  - A missing tool (`timeout` on macOS, `rg`, `fd`): either the instructions should
    name the right one, or the environment should provide it.
  - A missing script or path: a stale instruction.

**Fix shape**
- Usually a decision: split a slow test, drop a hook from pre-commit, remove a hook
  that fires on every tool call.
- Clear wins are rare here. Pruning merged local branches or prunable worktrees is
  one, but only local, and only after checking nothing is uncommitted.

**Traps**
- Runs from deleted workflows (`drag.txt` labels them).
- Release-only and `workflow_dispatch` workflows that rarely run.
- `--merged` misses squash merges: check PR state.
- Big blobs in history need a history rewrite, which is outward-facing: always a
  Suggests.

## 7 Dependency rot

Unused or missing deps:
- deprecated or archived packages
- several libraries doing one job
- two package managers in one package
- runtime pins that disagree (`.nvmrc`, `engines`, CI, Docker)
- outdated majors
- known vulnerabilities
- env vars that are read but undocumented, or declared but never read

**Find**
- `deps.txt`: audit severities, packages a major or more behind, declared but not
  installed.
- `lockfiles`, `versions`, `env_vars` and `model_ids` in `cruft_scan.txt`.
- Stack tools in `ecosystems.md` for non-JS stacks.
- If the repo has its own audit gate with an exceptions file, check whether the
  exceptions have expired.

**Prove**
- An unused dep needs the tool's report and zero string hits, including config files,
  scripts and CLI use.

**Traps**
- Deps used only by config (eslint plugins, babel presets, postcss).
- CLI deps run from scripts.
- Peer deps.
- Type-only packages.
- Platform-specific optional deps.
- A second lockfile in a separate package that uses another manager on purpose.

## 8 Clutter

- tracked agent scratch and backups (`tmpclaude-*`, `.bak`, `.tmp-*`)
- tracked files the repo's own `.gitignore` excludes
- committed build output
- root-level PLAN/SUMMARY/HANDOFF sprawl
- piles of dated reports
- unreferenced screenshots and fixtures
- merged branches and prunable worktrees

**Find**
- `scratch`, `ignored`, `build_output`, `plan_sprawl` (including root files nothing
  names), `dated_piles`, `orphan_assets` and `large_files` in `cruft_scan.txt`.
- Branches in `drag.txt`:
  - local branches merged into base
  - local branches whose upstream is gone: the strongest evidence that a branch is
    safe to delete
  - remote branches merged into base: deleting them is outward-facing, so always a
    Suggests

**Prove**
- Nothing references it (`git grep -F <basename>`).
- It isn't loaded by convention.
- For ignored files: the rule comes from the repo's `.gitignore`, not
  `.git/info/exclude`.

**Clear win**: `git rm --cached` or delete, when no file references it.

**Traps**
- Fixtures loaded by glob.
- Assets referenced by computed paths.
- Design review artifacts kept on purpose (check the README or design doc).
- A tracked `.env` is a secret problem first: rotate, then remove. That's always a
  Suggests, and say it plainly.

## 9 Escape hatches

Skipped tests; `@ts-ignore`, `as any`, `eslint-disable`, `noqa`; empty catches;
TODO/FIXME older than 180 days; allowlists and baselines that only grow.

**Find**
- `escape_hatches` (count now and 90 days ago) and `todos` (age by blame) in
  `cruft_scan.txt`.
- Read check scripts for allowlists and baselines with entries older than 90 days.

**Report the trend, not the total.** A count that grew is the finding. Fixes are
Suggests unless one is a one-line removal that tests prove safe.
- Counts cover code files only, and skip sketches, prototypes and fixtures.
- Compare the growth with the growth in code files the card prints: 35→59 casts while
  code grew 4× is not a trend.
- In a repo younger than 90 days there's no baseline: say so.

**Traps**
- `@ts-expect-error` in tests that assert a type error.
- Suppressions with a written reason.
- Generated files.

## Beyond the repo: live accounts (opt-in, read-only)

With the person's yes, compare live state with the repo using read-only list commands
(`gh api` GET; `wrangler`/`cf` list; `railway list --json`). Things found this way on
real projects:

- Actions secrets and variables no workflow reads. `drag.txt` does this by default
  and cites the commit that removed the last reader.
- Workflows that are disabled or have never run.
- Deployed Workers, buckets and databases no config names, and QA leftovers with old
  dates in their names.
- Platform projects that outlived the app.
- Tables and columns no code reads.

Every change there is outward-facing or destroys data, so it is always Suggests:
deleting a secret or resource, dropping a table, editing a ruleset.

Before calling a deployed resource unused, check how it is reached, not only its name:
- routes and custom domains bind a Worker to a URL path. A Worker whose name
  appears nowhere in the repo can still serve the site's analytics path.
  Find a route with the zone routes API or the dashboard. A routed resource with no
  source in the repo is a different finding: it can't be redeployed.
- a resource named in any plan or change that isn't archived is in flight, however
  old its date looks. Dated QA environments behind an open change are its test bed.

Traps:
- one cloud account shared by several projects (compare against all their configs)
- statuses posted by a local script, not a workflow job
- services wired only through a secret
- tables mid-migration (`*_new`)
- backups that live in a "dead" project
- a 403 from a plan-gated API means `unchecked`, not clean
- a local `origin/<base>` that is behind GitHub
