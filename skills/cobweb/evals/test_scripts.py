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
    failures += cruft_precision_failures()
    failures += steering_precision_failures()

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


def cruft_precision_failures() -> list[str]:
    """Precision of cruft_scan, test_scan and prompt_surfaces outside the JS stack: planted
    look-alikes that earlier produced false findings on flask, django, cobra, ripgrep and sinatra."""
    failures: list[str] = []

    def check(cond: bool, what: str) -> None:
        if not cond:
            failures.append("precision: " + what)

    def repo(files: dict[str, str]) -> str:
        root = tempfile.mkdtemp(prefix="cobweb-precision-")
        sh(root, "git", "init", "-q", "-b", "main")
        sh(root, "git", "config", "user.email", "t@example.com")
        sh(root, "git", "config", "user.name", "t")
        for path, text in files.items():
            write(root, path, text)
        sh(root, "git", "add", "-A")
        sh(root, "git", "commit", "-q", "-m", "init")
        return root

    def script(name: str, root: str, *extra: str) -> dict:
        out = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, name), root, "--json", *extra],
                             capture_output=True, text=True, check=True).stdout
        return json.loads(out)

    roots: list[str] = []
    try:
        # 1. escape hatches: scoped to their languages, no \b (Apple's git grep -E ignores it)
        sys.path.insert(0, SCRIPTS)
        try:
            import cruft_scan
            patterns = [p for parts in cruft_scan.ESCAPES.values() for p, _ in parts]
        finally:
            sys.path.remove(SCRIPTS)
        check(patterns and not any("\\b" in p or "\\s" in p for p in patterns),
              "escape patterns use no \\b or \\s (they differ between Apple's git grep and GNU's)")
        r = repo({
            "src/a.ts": "const x = y as any\nfunction f(v: any) {}\n// takes values as any of the following\n"
                        "// @ts-ignore\ntry { go() } catch {}\n",
            "src/doc.py": '"""Accepts values as any thing; the word noqa is prose here."""\n'
                          "x = 1  # noqa\ntry:\n    pass\nexcept ValueError: pass\n",
            "src/b.ts": "// # noqa and //nolint are not TypeScript escapes\n",
            "main.go": "package main\n\nfunc a() {} //nolint:errcheck\n",
        })
        roots.append(r)
        rows = {x["kind"]: x for x in script("cruft_scan.py", r, "--only=escape_hatches")["escape_hatches"]["rows"]}
        check(rows.get("as-any", {}).get("now") == 2, "as any counts code in .ts only, not prose in comments or .py docstrings")
        check(rows.get("ts-ignore", {}).get("now") == 1, "@ts-ignore counts in .ts")
        check(rows.get("noqa/type-ignore", {}).get("now") == 1 and
              rows["noqa/type-ignore"]["top_files"] == ["src/doc.py (1)"], "noqa counts in .py only")
        check(rows.get("nolint", {}).get("now") == 1, "//nolint counts in .go only")
        check(rows.get("empty-catch", {}).get("now") == 2, "empty catch is found in .ts and .py with POSIX classes")

        # 2. parallel implementations: a version series is not a copy; release notes are history
        r = repo({
            "docs/releases/1.0.txt": "a\n", "docs/releases/1.0.2.txt": "b\n",
            "notes/2.0.txt": "a\n", "notes/2.0.1.txt": "b\n",
            "src/util.ts": "export {}\n", "src/util.old.ts": "export {}\n",
            "src/handler.ts": "export {}\n", "src/handler-v2.ts": "export {}\n",
        })
        roots.append(r)
        par = script("cruft_scan.py", r, "--only=parallel")["parallel"]
        check({p["file"] for p in par} == {"src/util.old.ts", "src/handler-v2.ts"},
              "parallel: only real copies, not 1.0.2.txt beside 1.0.txt")

        # 3. orphan docs: toctree entries, :doc:, :ref: labels, :orphan:, tests and community files
        r = repo({
            "docs/index.rst": "Welcome\n=======\n\n.. toctree::\n   :maxdepth: 2\n\n   utils\n   Tutorial <tutorial/index>\n\n"
                              "See :doc:`api` too.\n",
            "docs/utils.rst": "Utils\n=====\n\nThe :ref:`the-label` page.\n",
            "docs/api.rst": "API\n===\n",
            "docs/tutorial/index.rst": "Tutorial\n========\n\n.. toctree::\n\n   layout\n",
            "docs/tutorial/layout.rst": "Layout\n======\n",
            "docs/labelled.rst": ".. _the-label:\n\nLabelled\n========\n",
            "docs/deliberate.rst": ":orphan:\n\nNot in a toctree\n================\n",
            "docs/lonely.rst": "Lonely\n======\n\nNothing links here.\n",
            "tests/docs/sample.md": "# fixture\n",
            "CODE_OF_CONDUCT.rst": "Conduct\n",
            "docs/CONDUCT.md": "Conduct\n",
        })
        roots.append(r)
        orphans = {x["file"] for x in script("cruft_scan.py", r, "--only=orphan_docs")["orphan_docs"]}
        check(orphans == {"docs/lonely.rst"},
              f"orphan docs: toctree, :doc:, :ref:, :orphan:, tests and community files are not orphans (got {sorted(orphans)})")

        # 6. test_scan: honest coverage, skip guards in every language the repo's tests use
        r = repo({
            "pkg/__init__.py": "", "pkg/core.py": "def run():\n    return 1\n",
            "tests/test_core.py": "import pytest\nneeds_db = pytest.mark.skipif(True, reason='x')\n\n"
                                  "@pytest.mark.skip\ndef test_a():\n    pass\n",
            "calc/calc.go": "package calc\n", "calc/calc_test.go": 'package calc\n\nfunc TestA(t *testing.T) {\n\tt.Skip("x")\n'
                                                                  '\tt.Skipf("y")\n}\n',
            "tests/it.rs": "#[test]\n#[ignore]\nfn slow() {}\n",
            "src/lib.rs": "pub fn a() {}\n#[cfg(test)]\nmod t {\n    #[test]\n    #[ignore]\n    fn b() {}\n}\n",
        })
        roots.append(r)
        ts = script("test_scan.py", r)
        sg = ts["skip_guards"]
        check(sg["counts"].get("pytest.skipif") == 1 and sg["counts"].get("pytest.skip") == 1,
              "skip guards: pytest.mark.skipif without an @, and @pytest.mark.skip")
        check(sg["counts"].get("go.Skip") == 2 and sg["counts"].get("rust.ignore") == 2, "skip guards: Go t.Skip and Rust #[ignore]")
        check(sg["test_files"] == 4 and sg["test_files_by_language"] == {"Rust": 2, "Python": 1, "Go": 1},
              f"skip guards: Go _test.go, Rust tests/*.rs and #[cfg(test)] files are test files (got {sg['test_files_by_language']})")
        check(ts["analysed_languages"] == [] and ts["mostly_unchecked"] and "Python" in ts["code_files_by_language"]
              and ts["main_language"] in ("Python", "Rust"), "test_scan says the import graph did not read a non-JS repo")
        sys.path.insert(0, SCRIPTS)
        try:
            import sweep
            line = sweep.test_lines(ts)[0]
        finally:
            sys.path.remove(SCRIPTS)
        check(line.startswith("UNCHECKED for ") and "(the import graph reads JS/TS only)" in line,
              "health card prints UNCHECKED, not 0, for a repo in a language the graph skips")

        # 7. prompt_surfaces: silent without agent signals; docstrings and shell templates are not prompts
        shell = "`# bash completion for %[1]s\n" + "".join(
            f"__%[1]s_step{i}()\n{{\n    local file=\"$FILE\"\n    if [[ -n ${{file}} ]]; then\n        echo \"$*\" >> \"${{file}}\"\n    fi\n}}\n"
            for i in range(3)) + "`"
        docstring = ('"""You MUST never call `update_things` before `sync_all`. Never mind: the tool `sync_all` is described '
                     'here as prose for people who read the source of this module and nobody else at all."""\n')
        plain = {"app/main.py": docstring + "def go():\n    return 1\n",
                 "cmd/completion.go": "package cmd\n\nconst tpl = " + shell + "\n"}
        r = repo(plain)
        roots.append(r)
        res = script("prompt_surfaces.py", r)
        check(res.get("agent_code") is False and not res["findings"], "no agent signal: prompt_surfaces reports agent_code false and nothing else")
        r = repo({**plain, "pyproject.toml": '[project]\nname = "x"\nkeywords = ["ai", "mcp"]\ndependencies = [\n  "anthropic>=0.30",\n]\n',
                  "app/prompts.py": 'PROMPT = """You are the helper. You MUST call `fetch_ledger` first and never guess a balance."""\n'})
        roots.append(r)
        res = script("prompt_surfaces.py", r)
        tokens = {f["token"] for f in res["findings"] if f["check"] == "orphan_tool"}
        check(res.get("agent_code") is True, "an LLM SDK dependency opens the scan")
        check("fetch_ledger" in tokens and not tokens & {"update_things", "sync_all"},
              f"a prompt literal is read, a docstring in the same repo is not (orphan tools {sorted(tokens)})")
        check(all(f["file"] != "cmd/completion.go" for f in res["prompt_surfaces"]["largest_files"]),
              "a shell completion template is not a prompt")
        r = repo({"package.json": '{"name": "x", "keywords": ["ai"], "dependencies": {"left-pad": "1"}}\n', "a.js": "export const a = 1\n"})
        roots.append(r)
        check(script("prompt_surfaces.py", r).get("agent_code") is False, "the keyword 'ai' is not the ai package")
        r = repo({"package.json": '{"name": "x", "dependencies": {"ai": "^4"}}\n'})
        roots.append(r)
        check(script("prompt_surfaces.py", r).get("agent_code") is True, "the ai package opens the scan")
        r = repo({"skills/helper/SKILL.md": "# Helper\n\nDo the thing.\n"})
        roots.append(r)
        check(script("prompt_surfaces.py", r).get("agent_code") is True, "a shipped SKILL.md opens the scan")
    finally:
        for d in roots:
            shutil.rmtree(d, ignore_errors=True)
    return failures



def steering_precision_failures() -> list[str]:
    """Docs that describe the reader's project, prose that sounds like a command,
    release notes, HTML anchors and common words: planted look-alikes beside real cobwebs."""
    root = tempfile.mkdtemp(prefix="cobweb-precision-")
    failures: list[str] = []

    def check(cond: bool, what: str) -> None:
        if not cond:
            failures.append("steering_precision: " + what)

    try:
        sh(root, "git", "init", "-q", "-b", "main")
        sh(root, "git", "config", "user.email", "t@example.com")
        sh(root, "git", "config", "user.name", "t")
        write(root, "docs/Makefile", "html:\n\t@echo html\n\ncheck:\n\t@echo check\n")
        write(root, "scripts/run.sh", "echo run\n")
        write(root, "tools/scripts/moved.sh", "echo moved\n")
        write(root, "src/gone.ts", "export const gone = 1\n")
        write(root, "old-name.md", "# old\n")
        write(root, "pkg/other/helper.html", "<p>x</p>\n")
        write(root, "examples/proj/tests/sample.py", "x = 1\n")
        write(root, "tests/fixtures/app/Procfile", "web: run\n")
        write(root, "package.json", '{"name": "p", "scripts": {"build": "echo build"}}\n')
        write(root, "FAQ.md", '# FAQ\n\n<h3 name="complete">\n\n<a name="other"></a>\n\n<div id="byid">x</div>\n\n## Real heading\n')
        write(root, "docs/links.md", "[a](../FAQ.md#complete) [b](../FAQ.md#other) [c](../FAQ.md#byid) "
                                     "[d](../FAQ.md#real-heading) [e](../FAQ.md#nothere)\n")
        # Fix 1: RST text between two literals is not a span; commands count only as code.
        write(root, "docs/howto.rst",
              "Setup\n=====\n\n"
              "Run ``pip`` and make sure ``tox`` passes, then make sure the docs build.\n"
              "You can make nothing here, and a ` make sure ` pair is stray ticks.\n\n"
              "Use ``make html`` for docs and ``make bogus`` for nothing.\n\n"
              "Heading\n~~~~~~~\n\n"
              "Build::\n\n    make check\n    make gone_target\n    make sure it works\n\n"
              ".. code-block:: console\n    :linenos:\n\n    $ make gone_console\n\n"
              "After the block, make sure_prose_not_code again.\n")
        write(root, "docs/howto.md", "Please make sure `a` and make sure `b` exist, then `make html`.\n\n"
                                     "    make gone_indented\n")
        # Fix 2: a tutorial that walks through the reader's project.
        write(root, "docs/tutorial.md",
              "Create `polls/models.py` and `mysite/settings.py`, serve `./public`, add `favicon.ico`.\n"
              "Edit `scripts/missing.sh`, `src/gone.ts`, `old-name.md`, `helper.html`.\n"
              "Copy `tests/sample.py` and run `scripts/moved.sh`.\n")
        write(root, "AGENTS.md", "# Rules\n\nSee `polls/models.py` and `favicon.ico` before editing.\n"
                                  "The widget is `OldWidget`. Check the Site, homepage, Sphinx and True setup.\n")
        # Fix 3: release notes and changelogs are records.
        for rel in ("docs/releases/1.0.txt", "docs/release-notes/2.md", "NEWS.md", "docs/changelog/x.md", "CHANGES.rst",
                    "docs/whatsnew/3.rst"):
            write(root, rel, "Fixed `scripts/missing_history.sh` and removed `OldGadget` and `scripts/gone_history.sh`.\n")
        write(root, "docs/notes.md", "The site has a site map; each site has a homepage, a homepage again, a homepage third. "
                                     "Build sphinx with sphinx and sphinx. Keep true as true, true.\n")
        write(root, "legacy/a.txt", "OldWidget\nOldWidget\nOldGadget\nOldGadget\nhomepage\nhomepage\nSite\nSite\nSphinx\nSphinx\nTrue\nTrue\n")
        sh(root, "git", "add", "-A")
        sh(root, "git", "commit", "-q", "-m", "init")
        sh(root, "git", "rm", "-q", "src/gone.ts", "old-name.md", "pkg/other/helper.html", "legacy/a.txt")
        sh(root, "git", "commit", "-q", "-m",
           'chore: remove the "homepage" and "Site" setup, the (Sphinx) shim, the True flag, `OldWidget` and `OldGadget`')

        st = run("steering_refs.py", root)
        found = {(f["doc"], f["ref"]) for f in st["findings"]}
        refs = lambda doc: {r for d, r in found if d == doc}  # noqa: E731
        scripts = {r for d, r in found if d.startswith("docs/howto") and r in ("sure", "the", "nothing", "html")}
        check(not scripts, f"prose 'make sure', 'make nothing' and a real target are not flagged ({sorted(scripts)})")
        rst = refs("docs/howto.rst")
        check({"bogus", "gone_target", "gone_console"} <= rst, f"a bad make target in a span or code block is flagged ({sorted(rst)})")
        check("check" not in rst and "html" not in rst and "sure_prose_not_code" not in rst and "linenos" not in rst,
              f"a real target and prose after a block are fine ({sorted(rst)})")
        check("gone_indented" in refs("docs/howto.md"), "an indented Markdown code block counts")
        check(not refs("docs/howto.md") - {"gone_indented"}, f"Markdown prose around two spans is fine ({sorted(refs('docs/howto.md'))})")
        tut = refs("docs/tutorial.md")
        check("polls/models.py" not in tut and "mysite/settings.py" not in tut and "./public" not in tut,
              f"a doc about the reader's project is not drift ({sorted(tut)})")
        check("favicon.ico" not in tut and "helper.html" not in tut, "a bare filename is not drift unless it was deleted near the doc")
        check("tests/sample.py" not in tut, "a path found only inside a sample project did not move")
        check({"scripts/missing.sh", "src/gone.ts", "old-name.md", "scripts/moved.sh"} <= tut,
              f"a path under the repo's own folder, a deleted path, a deleted root file and a moved path stay flagged ({sorted(tut)})")
        agents = refs("AGENTS.md")
        check("polls/models.py" in agents and "favicon.ico" in agents, "an always-loaded file keeps every missing path")
        for rel in ("docs/releases/1.0.txt", "docs/release-notes/2.md", "NEWS.md", "docs/changelog/x.md", "CHANGES.rst",
                    "docs/whatsnew/3.rst"):
            kinds = {f["kind"] for f in st["findings"] if f["doc"] == rel}
            check(kinds <= {"history"}, f"{rel} is a record, not a live doc (kinds {sorted(kinds)})")
        anchors = {r for d, r in found if d == "docs/links.md"}
        check(anchors == {'../FAQ.md "nothere"'} or anchors == {'FAQ.md "nothere"'},
              f"HTML name/id anchors and heading slugs resolve; only the missing one is flagged ({sorted(anchors)})")

        names = run("retired_names.py", root)
        terms = {r["term"] for r in names}
        check(not terms & {"Site", "homepage", "Sphinx", "True"}, f"common words and keywords are not retired names ({sorted(terms)})")
        check("OldWidget" in terms, "a distinctive retired name that survives in AGENTS.md is reported")
        check("OldGadget" not in terms, "a retired name that survives only in release notes is not reported")

        fp = run("fingerprint.py", root)
        check("heroku" not in fp["stacks"], "a Procfile in a test fixture is not a stack")
        check("make" not in fp["stacks"], "docs/Makefile is not a make stack")

        dr = run("drag.py", root)
        check(not any("vitest" in s or "jest" in s for s in dr["timing_suggestions"]), "no vitest or jest suggestion without the dependency")
        check(dr["branches"].get("remote_refs") == "local refs, never fetched", "remote branch count says the refs were never fetched")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return failures


if __name__ == "__main__":
    main()
