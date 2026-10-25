#!/usr/bin/env python3
"""Regression test for the cobweb scripts: plant cobwebs and look-alikes in a
throwaway repo and check the scripts report the first and not the second.

Every false-positive class found on real repos gets a look-alike here.
Usage: python3 -I evals/test_scripts.py   (exit 0 = pass)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")


def sh(cwd: str, *cmd: str) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_DATE": "2026-01-01T00:00:00", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00"})


def write(root: str, path: str, text: str) -> None:
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)


def run(script: str, root: str, *extra: str, home: str | None = None) -> dict:
    env = {**os.environ, "HOME": home} if home else None
    out = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, script), root, "--json", "--no-ci", *extra],
                         capture_output=True, text=True, check=True, env=env).stdout
    return json.loads(out)


def build_home(home: str, root: str) -> None:
    """A fake home with Claude Code memory for the fixture repo, so the test never
    reads the real one."""
    mem = os.path.join(home, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(root)), "memory")
    os.makedirs(mem)
    files = {
        "deploy-status-2026-01-02.md": ("project", "Where the deploy stands", "Waiting on `src/gone.ts` review."),
        "router-lives-in-legacy.md": ("project", "Router location", "Routing lives in `src/legacy-router.ts`."),
        "no-em-dashes.md": ("feedback", "Never use em dashes", "A hook blocks them."),
        "build-command.md": ("reference", "How to build", "Run `npm run build` from the root."),
        "orphan-note.md": ("project", "Unindexed note", "Nothing points here."),
    }
    index = ["# Memory index", ""]
    for name, (kind, desc, body) in files.items():
        with open(os.path.join(mem, name), "w") as fh:
            fh.write(f"---\nname: {name[:-3]}\ndescription: {desc}\nmetadata:\n  type: {kind}\n"
                     f"  modified: 2026-01-02T00:00:00.000Z\n---\n\n{body}\n")
        if name != "orphan-note.md":
            index.append(f"- [{desc}]({name}): {desc}")
    index.append("- [Gone](missing-file.md): points nowhere")
    with open(os.path.join(mem, "MEMORY.md"), "w") as fh:
        fh.write("\n".join(index) + "\n")


def build(root: str) -> None:
    sh(root, "git", "init", "-q", "-b", "main")
    sh(root, "git", "config", "user.email", "t@example.com")
    sh(root, "git", "config", "user.name", "t")
    write(root, "src/gone.ts", "export const gone = 1\n")
    write(root, "src/fleet-dashboard.ts", "// Fleet dashboard\nexport const fleet = 1\nexport const fleetRuns = []\n")
    write(root, "src/atlas-view.ts", "export const atlas = 1\n")
    write(root, "src/app.ts", "export const app = process.env.APP_SECRET_URL\n")
    write(root, "src/lib/index.ts", "export {}\n")
    write(root, "src/foo.ts", "export const foo = 1\n")
    write(root, "src/foo-v2.ts", "export const foo = 2\n")
    write(root, "src/notes.ts.bak", "old\n")
    write(root, ".gitignore", ".env\ndist/\n")
    write(root, "package.json", json.dumps({"name": "fixture", "scripts": {"build": "tsc", "test": "vitest"},
                                            "dependencies": {"electron": "^44.1.0"},
                                            "devDependencies": {"vitest": "1"}, "engines": {"node": ">=20"}}))
    write(root, "docs/GUIDE.md", "# Guide\n\n## Setup\n\nRun it.\n")
    write(root, "src/escrow.ts", "export const escrow = 1\n")
    write(root, ".node-version", "22\n")
    write(root, ".env.example", "APP_SECRET_URL=\nUNUSED_FLAG=\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "init")
    sh(root, "git", "rm", "-q", "src/gone.ts")
    sh(root, "git", "commit", "-q", "-m", "chore: remove the gone module")
    write(root, "src/legacy-router.ts", "export function routeLegacyRequest() {}\n"
                                        "export function formatDateLabel() {}\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "feat: add the legacy router")
    sh(root, "git", "rm", "-q", "src/legacy-router.ts")
    write(root, "src/app.ts", "export const app = process.env.APP_SECRET_URL\nexport function formatDateLabel() {}\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "chore: remove the legacy router")
    sh(root, "git", "rm", "-q", "src/fleet-dashboard.ts")
    sh(root, "git", "commit", "-q", "-m", "feat: retire the Fleet dashboard")
    sh(root, "git", "mv", "src/atlas-view.ts", "src/compass-view.ts")
    sh(root, "git", "commit", "-q", "-m", "refactor: rename Atlas to Compass")
    # Mentions a name without retiring it: the diff adds Ledger lines, removes none.
    write(root, "docs/LEDGER.md", "Ledger notes.\nLedger owns the record.\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "docs: note the removed billing flow in Ledger")
    write(root, "CLAUDE.md", "# Old rules\n\n## Provider Parity\n\nKeep providers equal.\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "docs: claude rules")
    write(root, "AGENTS.md", "\n".join([
        "# Fixture",
        "- Build with `npm run build`; test with `pnpm vitest`.",          # real script, dependency bin
        "- Release with `npm run publish-site`.",                            # COBWEB: missing script
        "- Entry point is `src/app.ts`; helpers in `src/lib`.",              # real; extensionless module
        "- The old module lives in `src/gone.ts`.",                          # COBWEB: deleted
        "- Secrets go in `.env`; output lands in `dist/app.js`.",            # gitignored on purpose
        "- Colors come from `bg.canvas` and `ink.primary` tokens.",          # dotted identifiers
        "- There is no `legacy.ts` file any more.",                          # negated claim
        "- Put new files at `path/to/file.ts`.",                             # placeholder
        "- Open the Fleet panel to see runs.",                               # COBWEB: retired name
        "- Compass replaced the old view.",                                  # replacement name: fine
        "", "```bash", "cat src/never-existed.ts", "```",                    # fenced example
    ]) + "\n")
    write(root, "CLAUDE.md", "@AGENTS.md\n")  # collapsed to an import: its sections are gone
    write(root, "src/provider.ts", "// Provider rules: see CLAUDE.md \"Provider Parity\".\n"     # COBWEB x2
                                   "const s = 'CLAUDE.md \"not a claim\"'\n"                       # string, not comment
                                   "// Setup lives in docs/GUIDE.md \"Setup\".\nexport {}\n")    # real section
    write(root, "docs/ARCH.md", "# Arch\n\nBuilt on Electron 39.8 and Node 20.\n"            # COBWEB: version
                                "Notes: jotai 289 imports.\n")                                  # usage count
    write(root, "docs/ESCROW-PLAN.md", "# Escrow\n\nStatus: planning proposal, not implemented.\n")  # COBWEB
    write(root, "docs/DESIGN.md", "See [study](../local-only/study.html).\n")                  # COBWEB: local-only
    write(root, ".git/info/exclude", "local-only/\n")
    write(root, "local-only/study.html", "<p>study</p>\n")
    write(root, "vendor/lib/AGENTS.md", "See `src/vendored-missing.ts`.\n")  # vendored: skipped
    write(root, "docs/ROUTING.md", "# Routing\n\nCall `routeLegacyRequest` for old URLs and `formatDateLabel` for dates.\n")
    # Config naming gone paths, and look-alikes that must pass.
    write(root, "package.json", json.dumps({
        "name": "fixture", "dependencies": {"electron": "^44.1.0"},
        "devDependencies": {"vitest": "1"}, "engines": {"node": ">=20"},
        "scripts": {"build": "tsc", "test": "vitest", "release": "node scripts/publish-site.mjs",  # COBWEB
                    "lint": "node scripts/lint.mjs"}}))
    write(root, "scripts/lint.mjs", "export {}\n")
    write(root, "vitest.config.ts", "export default { coverage: { include: [\n"
                                    "  'src/legacy-router.ts',\n"          # COBWEB: deleted
                                    "  'src/app.ts',\n"                     # exists
                                    "  'src/**/*.ts',\n"                    # glob
                                    "  'dist/never-tracked.js',\n"          # never in git: not reported
                                    "] } }\n")
    write(root, "tsconfig.json", '{\n  // comment\n  "include": ["src/**/*.ts", "types/*.d.ts"]\n}\n')  # types/ COBWEB
    write(root, ".github/workflows/ci.yml", "on:\n  push:\n    paths:\n      - 'src/**'\n      - 'site/blog/**'\n"
                                             "jobs:\n  t:\n    steps:\n      - run: node scripts/lint.mjs\n")
    # Plans: done but active, parked on purpose, and a doc claiming authority.
    write(root, "docs/plans/ship-router.md", "# Ship router\n\n- [x] build it\n- [x] test it\n- [x] ship it\n")
    write(root, "docs/plans/parked-idea.md", "> **PARKED (2026-01-01).** Not available work.\n\n- [ ] a\n- [ ] b\n- [ ] c\n")
    write(root, "docs/notes/routing-guide.md", "# Routing guide\n\nThis doc is the source of truth for routing.\n")
    write(root, "docs/notes/old-guide.md", "> **ARCHIVED.** Kept for history.\n\nThis doc is the source of truth.\n")
    write(root, "docs/archive/2025-01-01-plan.md", "Uses `src/also-gone.ts`.\n")  # history class
    write(root, "skills/helper/SKILL.md", "Edit `app/routes.ts` in your project.\n")  # payload class
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "docs: agent instructions")


def build_tests(root: str) -> None:
    """Tests that prop up code, and look-alikes that must not be reported."""
    write(root, "src/only-tested.ts", "export const onlyTested = 1\n")                       # COBWEB: only a test imports it
    write(root, "src/shared-mod.ts", "export const shared = 1\n")                            # prod imports it too: fine
    write(root, "src/sw.js", "self.addEventListener('fetch', () => {})\n")                   # loaded by URL string: fine
    write(root, "src/fake-clock.ts", "export const fakeClock = () => 0\n")                   # test support in src/
    write(root, "src/dead-end.ts", "export const deadEnd = 1\n")                             # nothing imports it
    write(root, "src/boot.ts", "import { shared } from './shared-mod'\n"
                               "navigator.serviceWorker.register('/sw.js')\nexport const boot = shared\n")
    write(root, "src/app.ts", "import { boot } from './boot'\n"
                              "export const app = process.env.APP_SECRET_URL ?? boot\n"
                              "export function formatDateLabel() {}\n")
    write(root, "tests/only-tested.test.ts", "import { onlyTested } from '../src/only-tested'\n"
                                              "import { shared } from '../src/shared-mod'\n"
                                              "import { fakeClock } from '../src/fake-clock'\n"
                                              "it('works', () => { onlyTested; shared; fakeClock })\n")
    write(root, "tests/sw.test.ts", "import '../src/sw.js'\nit.skip('registers', () => {})\n")
    write(root, "tests/pin.test.ts", "import { readFileSync } from 'node:fs'\n"
                                     "const text = readFileSync('src/app.ts', 'utf8')\n"            # COBWEB: pins source text
                                     "it('pins', () => { expect(text).toContain('boot') })\n")
    write(root, "tests/fixture-reader.test.ts", "import { readFileSync } from 'node:fs'\n"
                                                 "const data = readFileSync('tests/fixtures/used.json', 'utf8')\n"  # not source
                                                 "const gone = 'src/never-existed.ts'\n"                           # no such path
                                                 "it('reads', () => { data; gone })\n")
    write(root, "tests/fixtures/used.json", "{}\n")
    write(root, "tests/fixtures/orphan-sample.json", "{}\n")                                  # COBWEB: nothing names it
    write(root, "tests/live.test.ts", "describe.skipIf(!process.env.LIVE_API_FLAG)('live', () => {})\n")   # COBWEB: never set
    write(root, "tests/switch.test.ts", "describe.skipIf(!process.env.GATED_SWITCH)('switch', () => {})\n")  # CI sets it: fine
    write(root, "tests/manual.test.ts", "// Never run in CI: needs a developer machine.\n"
                                         "describe.skipIf(process.env.MANUAL_ONLY !== '1')('manual', () => {})\n")  # deliberate
    write(root, ".github/workflows/switch.yml", "on: push\njobs:\n  t:\n    env:\n      GATED_SWITCH: '1'\n    steps:\n      - run: npx vitest\n")
    sh(root, "git", "add", "-A")
    sh(root, "git", "commit", "-q", "-m", "test: tests that prop up code")


def main() -> None:
    root = tempfile.mkdtemp(prefix="cobweb-fixture-")
    failures = []

    def check(cond: bool, what: str) -> None:
        if not cond:
            failures.append(what)

    try:
        build(root)
        build_tests(root)
        st = run("steering_refs.py", root)
        always = {(x["ref"], x["status"]) for x in st["findings"] if x["kind"] == "always"}
        refs = {r for r, _ in always}
        check(("src/gone.ts", "deleted") in always, "deleted path in AGENTS.md is reported as deleted")
        check(("publish-site", "missing-script") in always, "missing npm script is reported")
        for fp in ("build", "vitest", "src/app.ts", "src/lib", ".env", "dist/app.js", "bg.canvas",
                   "ink.primary", "legacy.ts", "path/to/file.ts", "src/never-existed.ts"):
            check(fp not in refs, f"false positive: {fp}")
        check(st["vendored_files_skipped"] == 1, "vendored AGENTS.md is skipped")
        kinds = {x["doc"]: x["kind"] for x in st["findings"]}
        check(kinds.get("docs/archive/2025-01-01-plan.md") == "history", "archived plan is classed as history")
        check(kinds.get("skills/helper/SKILL.md") in ("payload", None), "shipped skill is not this repo's steering")
        check(st["always_loaded_bytes"] > 0, "always-loaded bytes measured")

        cites = {(x["doc"], x["status"]) for x in st["findings"] if x["status"] in ("section-gone", "import-stub")}
        check(("src/provider.ts", "section-gone") in cites, "section citation to a gone CLAUDE.md section")
        check(("src/provider.ts", "import-stub") in cites, "pointer at an import-only CLAUDE.md")
        check(not any(x["doc"] == "src/provider.ts" and "Setup" in x["ref"] for x in st["findings"]),
              "citation of a section that exists is fine")
        check(sum(1 for x in st["findings"] if x["doc"] == "src/provider.ts" and x["status"] == "section-gone") == 1,
              "string literals are not citations")
        versions = [x["ref"] for x in st["findings"] if x["status"] == "version-differs"]
        check(any("Electron 39" in v for v in versions), "stale Electron version claim")
        check(not any("jotai" in v or "Node 20" in v for v in versions), "usage counts and satisfied ranges are fine")
        check(any(x["doc"] == "docs/DESIGN.md" and x["status"] == "untracked" for x in st["findings"]),
              "link into a folder only this machine excludes is reported")

        rn = run("retired_names.py", root)
        terms = {r["term"] for r in rn}
        check("Fleet" in terms, "retired name Fleet found in AGENTS.md")
        check("Compass" not in terms, "the replacement in a rename is not retired")
        check("Ledger" not in terms, "a name the retiring commit adds, not removes, is not retired")

        cr = run("cruft_scan.py", root)
        check(any(p["file"] == "src/foo-v2.ts" and p["sibling"] == "src/foo.ts" for p in cr["parallel"]),
              "parallel implementation found")
        check(any(x["file"] == "src/notes.ts.bak" for x in cr["scratch"]), "tracked backup found")
        check(cr["versions"] == [], "node 22 against engines >=20 is not a conflict")
        env = cr["env_vars"]
        check(any(x["name"] == "UNUSED_FLAG" for x in env["declared_but_unused"]), "declared-but-unused env var")
        check(not any(x["name"] == "APP_SECRET_URL" for x in env["used_but_undocumented"]), "documented env var")

        check(any(p["doc"] == "docs/ESCROW-PLAN.md" and "src/escrow.ts" in p["code_for_topic"]
                  for p in cr["plan_status"]), "plan says unbuilt while its code exists")

        cfg = {(x["file"], x["ref"]) for x in run("config_refs.py", root)["findings"]}
        check(("package.json", "scripts/publish-site.mjs") in cfg, "package.json script running a missing file")
        check(("tsconfig.json", "types/*.d.ts") in cfg, "tsconfig include matching nothing")
        check((".github/workflows/ci.yml", "site/blog/**") in cfg, "CI paths filter matching nothing")
        check(("vitest.config.ts", "src/legacy-router.ts") in cfg, "config literal naming a deleted file")
        check(not any(r in ("src/app.ts", "dist/never-tracked.js") for _, r in cfg),
              "config literals that exist or were never in git are not reported")
        check(not any(r in ("scripts/lint.mjs", "src/**/*.ts", "src/**") for _, r in cfg),
              "existing paths and globs (also inside JSONC) are fine")

        plans = {x["doc"] for x in cr["plan_checkboxes"]}
        check("docs/plans/ship-router.md" in plans, "fully ticked plan in an active folder")
        check("docs/plans/parked-idea.md" not in plans, "a parked plan is left alone")
        claims = {x["doc"] for x in cr["authority_claims"]}
        check("docs/notes/routing-guide.md" in claims, "unmarked old doc claiming to be the source of truth")
        check("docs/notes/old-guide.md" not in claims, "an archived doc's claim is fine")

        sha = subprocess.run(["git", "-C", root, "log", "--format=%h", "--grep", "remove the legacy router"],
                             capture_output=True, text=True).stdout.split()[0]
        after = {r["term"] for r in run("retired_names.py", root, f"--commit={sha}")}
        check("routeLegacyRequest" in after, "after-removal mode finds a removed function still named in docs")
        check("formatDateLabel" not in after, "a function still defined elsewhere is not retired")

        home = tempfile.mkdtemp(prefix="cobweb-home-")
        try:
            build_home(home, root)
            ah = run("agent_home.py", root, "--no-global", home=home)
            store = ah["claude_memory"][0] if ah["claude_memory"] else {}
            cands = {c["file"]: c for c in store.get("candidates", [])}
            check("deploy-status-2026-01-02.md" in cands and cands["deploy-status-2026-01-02.md"]["kind"] == "status",
                  "old status note naming a deleted path is a candidate")
            check("router-lives-in-legacy.md" in cands, "fact naming a deleted file is a candidate")
            check("build-command.md" not in cands, "a reference with live paths is fine")
            check("orphan-note.md" in cands, "a memory no index lists is a candidate")
            check(store.get("index_missing_targets") == ["missing-file.md"], "index line pointing at a missing file")
            check(cands.get("no-em-dashes.md") is None, "a preference with no evidence is never a candidate")
            # Global setup, in the fake home only.
            for rel, body in ((".claude/CLAUDE.md", "\n".join(f"- Shared rule number {i} that both tools carry" for i in range(4))),
                              (".codex/AGENTS.md", "\n".join(f"- Shared rule number {i} that both tools carry" for i in range(4))),
                              (".claude/hooks/old_guard.py", "print('x')\n"),
                              (".claude/settings.json", "{\"hooks\": {}}\n"),
                              (".codex/config.toml", '[projects."/nonexistent/cobweb/project"]\ntrust_level = "trusted"\n')):
                write(home, rel, body)
            g = run("agent_home.py", root, home=home)["global"]
            check(any("share 4 lines" in c for c in g["copied_instruction_lines"]), "rules copied between tools' user files")
            check(g["unwired_hook_scripts"] == ["~/.claude/hooks/old_guard.py"], "hook script nothing runs")
            check(g["stale_trusted_projects"].get("~/.codex/config.toml") == [1, 1], "trusted project path that is gone")
        finally:
            shutil.rmtree(home, ignore_errors=True)

        ts = run("test_scan.py", root)
        only = {x["file"]: x for x in ts["test_only_modules"]}
        check(only.get("src/only-tested.ts", {}).get("kind") == "test-only"
              and only["src/only-tested.ts"]["test_importers"] == ["tests/only-tested.test.ts"],
              "module only a test imports is reported with its test importer")
        check("src/shared-mod.ts" not in only, "module prod code also imports is fine")
        check("src/sw.js" not in only and ts["graph"]["candidates_dropped"].get("named as a string elsewhere", 0) >= 1,
              "file loaded by a URL string is dropped, not reported")
        check("src/fake-clock.ts" not in only and any(x["file"] == "src/fake-clock.ts" for x in ts["test_support_in_src"]),
              "fake in src/ goes to test support, not test-only")
        check(only.get("src/dead-end.ts", {}).get("kind") == "unreachable", "module nothing imports is labelled unreachable")
        check(not any(f in only for f in ("src/app.ts", "src/boot.ts")), "modules on the production path are fine")
        pins = {x["file"] for x in ts["source_text_pins"]["files"]}
        check("tests/pin.test.ts" in pins, "test that reads a source file and names it is a pin")
        check("tests/fixture-reader.test.ts" not in pins, "reading a fixture or a nonexistent src path is not a pin")
        orphans = {x["file"] for x in ts["orphan_fixtures"]}
        check("tests/fixtures/orphan-sample.json" in orphans, "fixture no file names is an orphan")
        check("tests/fixtures/used.json" not in orphans, "fixture a test names is fine")
        gates = ts["dormant_env_gates"]
        check({x["env"] for x in gates["dormant"]} == {"LIVE_API_FLAG"}, "env gate nothing sets is dormant; one a workflow sets is not")
        check({x["env"] for x in gates["deliberate_opt_in"]} == {"MANUAL_ONLY"}, "'Never run in CI' gate is deliberate")
        check(ts["skip_guards"]["counts"].get("skipIf") == 3 and ts["skip_guards"]["counts"].get("skip") == 1,
              "skip guards are counted by kind")

        fp = run("fingerprint.py", root)
        check("js" in fp["stacks"], "js stack detected")
        check("claude-code" in fp["agent_tools"], "claude-code configured")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    failures += prompt_surfaces_failures()

    if failures:
        print("FAIL")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("PASS: all fixture checks")


def prompt_surfaces_failures() -> list[str]:
    """Stale text in agent-steering strings: planted cobwebs and look-alikes in a throwaway repo."""
    root = tempfile.mkdtemp(prefix="cobweb-prompts-")
    failures: list[str] = []

    def check(cond: bool, what: str) -> None:
        if not cond:
            failures.append("prompt_surfaces: " + what)

    try:
        sh(root, "git", "init", "-q", "-b", "main")
        sh(root, "git", "config", "user.email", "t@example.com")
        sh(root, "git", "config", "user.name", "t")
        labels = ["General", "Appearance", "Phone access", "Cloud", "Connected tools", "Skills", "Account", "Advanced"]
        write(root, "src/legacy/old-router.ts", "export const route = 1\n")
        write(root, "src/settings/settings-pages.ts",
              "export const PAGES = [\n" + "".join(f'  {{ id: "p{i}", label: "{l}" }},\n' for i, l in enumerate(labels)) + "]\n")
        write(root, "src/tools.ts",
              "server.tool('lookup_order', 'Look up an order by its number and return its status', {}, async () => ({}))\n"
              "export const REAL_PATH = 'src/settings/settings-pages.ts'\n")
        write(root, "src/model-a.ts", "export const MODEL_A = 'claude-sonnet-5-5'\n")
        write(root, "src/model-b.ts", "export const MODEL_B = 'claude-sonnet-5-5'\n")
        write(root, "src/prompts.ts", "\n".join([
            "export const SYSTEM_PROMPT = `You are the support agent. You MUST never guess an order status.",
            "Read the routing rules in src/legacy/old-router.ts before answering and keep src/settings/settings-pages.ts in mind.",  # COBWEB + live path
            "To pair a device open Settings → Phone, or open Settings → General to change the language.",              # COBWEB + live label
            "In 1Password Settings → Security turn on the vault. Never edit \\`update_plan\\` yourself.",              # other app; host tool
            "Call \\`lookup_order\\` first, then \\`fetch_ledger\\` when the person asks about refunds.",                  # live tool + COBWEB
            "Delegate cheap work with claude-sonnet-4-5 when it is a trivial lookup.`",                                # COBWEB: older model
            "export function buildMainPrompt() { return SYSTEM_PROMPT }",
            "export function buildReportPrompt() { return 'x' }",                                                      # COBWEB: only tests
            ""]))
        write(root, "src/app.ts", "import { buildMainPrompt } from './prompts'\nexport const p = buildMainPrompt()\n")
        write(root, "tests/prompt.test.ts", "\n".join([
            "import { buildReportPrompt } from '../src/prompts'",
            "const SAMPLE = `You are a test agent. You MUST read src/legacy/old-router.ts, use claude-sonnet-4-5 and open Settings → Phone. Never mind.`",
            "export const r = buildReportPrompt()", ""]))
        write(root, "src/catalog.ts", "export const IDS = ['claude-sonnet-4-5', 'claude-opus-4-1', 'claude-haiku-4-5', 'claude-sonnet-4', 'claude-opus-4']\n")
        write(root, "skills/helper/SKILL.md", "# Helper\n\nSee [guide](../../docs/guide.md) and [more](references/more.md).\n"
                                              "This describes the development checkout.\n")
        write(root, "skills/helper/references/more.md", "# More\n")
        write(root, "docs/guide.md", "# Guide\n")
        sh(root, "git", "add", "-A")
        sh(root, "git", "commit", "-q", "-m", "init")
        sh(root, "git", "rm", "-q", "src/legacy/old-router.ts")
        sh(root, "git", "commit", "-q", "-m", "chore: remove the old router")

        out = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "prompt_surfaces.py"), root, "--json"],
                             capture_output=True, text=True, check=True).stdout
        res = json.loads(out)
        found = {(f["check"], f["file"], f["token"]) for f in res["findings"]}
        in_src = lambda check_name: {t for c, f, t in found if c == check_name and f == "src/prompts.ts"}  # noqa: E731
        check("src/legacy/old-router.ts" in in_src("dead_pointer"), "prompt naming a deleted path is flagged")
        check("src/settings/settings-pages.ts" not in in_src("dead_pointer"), "prompt naming a live path is fine")
        crumbs = in_src("settings_breadcrumb")
        check(any(t.startswith("Settings → Phone") for t in crumbs), "breadcrumb to a missing settings label is flagged")
        check(not any("General" in t for t in crumbs), "breadcrumb to an existing settings label is fine")
        check(not any("Security" in t for t in crumbs), "another app's Settings breadcrumb is fine")
        tools = in_src("orphan_tool")
        check("fetch_ledger" in tools, "tool name nothing registers is flagged")
        check("lookup_order" not in tools and "update_plan" not in tools, "registered and host-owned tool names are fine")
        check("buildReportPrompt" in {t for c, f, t in found if c == "builder_unwired"}, "builder only tests import is flagged")
        check("buildMainPrompt" not in {t for c, f, t in found if c == "builder_unwired"}, "builder the app imports is fine")
        check("claude-sonnet-4-5" in in_src("model_drift"), "old model ID in a prompt is flagged")
        check(not any(f.startswith("tests/") for c, f, t in found), "test files are never flagged")
        check(not any(f == "src/catalog.ts" for c, f, t in found), "a catalog of model IDs is never flagged")
        skill = {t for c, f, t in found if c == "skill_hygiene" and f == "skills/helper/SKILL.md"}
        check("../../docs/guide.md" in skill and "development checkout" in skill, "shipped skill link out of its folder and dev wording")
        check("references/more.md" not in skill, "shipped skill link inside its folder is fine")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return failures


if __name__ == "__main__":
    main()
