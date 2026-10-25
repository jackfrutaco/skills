#!/usr/bin/env python3
"""Describe a repository before sweeping it: stacks, agent tools, CI, age, and
the checks the owner already wrote. Stdlib only; read-only.

Usage: fingerprint.py [repo] [--json]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import emit_json, git, is_vendored, vendored_roots  # noqa: E402

# manifest basename -> (stack, package manager or build tool)
MANIFESTS = {
    "package.json": ("js", None), "package-lock.json": ("js", "npm"),
    "pnpm-lock.yaml": ("js", "pnpm"), "yarn.lock": ("js", "yarn"), "bun.lock": ("js", "bun"),
    "bun.lockb": ("js", "bun"), "deno.json": ("js", "deno"), "deno.jsonc": ("js", "deno"),
    "tsconfig.json": ("ts", None),
    "pyproject.toml": ("python", None), "uv.lock": ("python", "uv"), "poetry.lock": ("python", "poetry"),
    "Pipfile.lock": ("python", "pipenv"), "requirements.txt": ("python", "pip"),
    "setup.py": ("python", "setuptools"), "pdm.lock": ("python", "pdm"),
    "go.mod": ("go", "go"), "Cargo.toml": ("rust", "cargo"),
    "Gemfile": ("ruby", "bundler"), "composer.json": ("php", "composer"),
    "pom.xml": ("jvm", "maven"), "build.gradle": ("jvm", "gradle"), "build.gradle.kts": ("jvm", "gradle"),
    "build.sbt": ("jvm", "sbt"), "Package.swift": ("swift", "swiftpm"), "Podfile": ("swift", "cocoapods"),
    "pubspec.yaml": ("dart", "pub"), "mix.exs": ("elixir", "mix"),
    "Dockerfile": ("docker", None), "docker-compose.yml": ("docker", None), "compose.yaml": ("docker", None),
    "wrangler.toml": ("cloudflare", None), "wrangler.jsonc": ("cloudflare", None),
    "wrangler.json": ("cloudflare", None), "vercel.json": ("vercel", None), "netlify.toml": ("netlify", None),
    "fly.toml": ("fly", None), "railway.json": ("railway", None), "railway.toml": ("railway", None),
    "Procfile": ("heroku", None), "flake.nix": ("nix", None), "Makefile": ("make", None),
    "justfile": ("just", None), "Taskfile.yml": ("task", None), "turbo.json": ("monorepo", "turbo"),
    "nx.json": ("monorepo", "nx"), "pnpm-workspace.yaml": ("monorepo", "pnpm"),
    "lerna.json": ("monorepo", "lerna"), "go.work": ("monorepo", "go"),
}
SUFFIX_MANIFESTS = {".csproj": ("dotnet", "dotnet"), ".fsproj": ("dotnet", "dotnet"),
                    ".sln": ("dotnet", "dotnet"), ".slnx": ("dotnet", "dotnet"),
                    ".xcodeproj/project.pbxproj": ("swift", "xcode"), ".gemspec": ("ruby", "gem")}
PACKAGE_ROOT_FILES = {"package.json", "pyproject.toml", "go.mod", "Cargo.toml", "Gemfile", "composer.json",
                      "pom.xml", "build.gradle", "build.gradle.kts", "pubspec.yaml", "mix.exs", "Package.swift"}
# path -> agent tool that reads it
AGENT_TOOLS = [
    ("CLAUDE.md", "claude-code"), ("CLAUDE.local.md", "claude-code"), (".claude/", "claude-code"),
    (".mcp.json", "claude-code"), ("AGENTS.md", "agents-md (codex, cursor, copilot, amp, opencode, ...)"),
    ("AGENTS.override.md", "codex"), (".codex/", "codex"), (".agents/", "shared skills (.agents)"),
    (".cursorrules", "cursor (legacy file)"), (".cursor/", "cursor"),
    (".github/copilot-instructions.md", "copilot"), (".github/instructions/", "copilot"),
    (".github/prompts/", "copilot"), (".github/agents/", "copilot"), ("GEMINI.md", "gemini-cli"),
    (".gemini/", "gemini-cli"), (".windsurfrules", "windsurf (legacy file)"), (".windsurf/", "windsurf"),
    (".devin/", "devin"), (".clinerules", "cline"), (".cline/", "cline"),
    (".roo/", "roo-code (discontinued 2026-05)"), (".roomodes", "roo-code (discontinued 2026-05)"),
    (".continue/", "continue"), (".rules", "zed"), (".kiro/", "kiro"), (".junie/", "junie"),
    ("AGENT.md", "amp (legacy name)"), (".goosehints", "goose"), ("CONVENTIONS.md", "aider"),
    (".aider.conf.yml", "aider"), ("opencode.json", "opencode"), (".opencode/", "opencode"),
    (".amazonq/", "amazon-q"), (".augment/", "augment"),
]
CI = [(".github/workflows/", "github-actions"), (".gitlab-ci.yml", "gitlab"), (".circleci/", "circleci"),
      ("azure-pipelines.yml", "azure"), (".buildkite/", "buildkite"), ("Jenkinsfile", "jenkins"),
      ("bitbucket-pipelines.yml", "bitbucket"), (".woodpecker", "woodpecker")]
HOOKS = [(".husky/", "husky"), ("lefthook.yml", "lefthook"), (".lefthook.yml", "lefthook"),
         (".pre-commit-config.yaml", "pre-commit"), (".codex/hooks.json", "codex hooks"),
         (".cursor/hooks.json", "cursor hooks"), (".github/hooks/", "copilot hooks")]
# Script names that mean the owner already wrote a hygiene check. Run those first:
# they encode the owner's intent better than any generic tool.
OWN_CHECK = re.compile(r"(lint|check|knip|dead|unused|docs?|hygiene|validate|verify|audit|typecheck|tsc|"
                       r"format|fmt|spell|links?|drift|stale|deps?|test)", re.I)


def matches(path: str, prefix: str) -> bool:
    if prefix.endswith("/"):
        return path.startswith(prefix) or ("/" + prefix) in path
    return path == prefix or path.endswith("/" + prefix)


def detect(root: str) -> dict:
    files = [f for f in git(root, "ls-files").splitlines() if f]
    extra = vendored_roots(root)
    own = [f for f in files if not is_vendored(f, extra)]
    vendored = Counter("/".join(f.split("/")[:2]) for f in files if is_vendored(f, extra))

    stacks: dict[str, set[str]] = defaultdict(set)
    roots: dict[str, set[str]] = defaultdict(set)
    for f in own:
        base = os.path.basename(f)
        hit = MANIFESTS.get(base) or next((v for k, v in SUFFIX_MANIFESTS.items() if f.endswith(k)), None)
        if hit:
            stack, tool = hit
            stacks[stack].add(tool or "")
            if base in PACKAGE_ROOT_FILES:
                roots[stack].add(os.path.dirname(f) or ".")

    agent: dict[str, list[str]] = defaultdict(list)
    for f in own:
        for prefix, tool in AGENT_TOOLS:
            if matches(f, prefix):
                agent[tool].append(f)
                break
    ci = sorted({name for f in own for prefix, name in CI if matches(f, prefix)})
    hooks = sorted({name for f in own for prefix, name in HOOKS if matches(f, prefix)})
    if os.path.isfile(os.path.join(root, ".claude/settings.json")):
        try:
            if json.load(open(os.path.join(root, ".claude/settings.json"))).get("hooks"):
                hooks.append("claude-code hooks")
        except (OSError, ValueError):
            pass
    hooks_dir = git(root, "rev-parse", "--git-path", "hooks").strip()
    hooks_dir = hooks_dir if os.path.isabs(hooks_dir) else os.path.join(root, hooks_dir)
    if os.path.isdir(hooks_dir):
        hooks += [f"git:{h}" for h in sorted(os.listdir(hooks_dir)) if not h.endswith(".sample")]
    if hp := git(root, "config", "core.hooksPath").strip():
        hooks.append(f"core.hooksPath={hp}")

    own_checks: dict[str, list[str]] = {}
    for f in own:
        base = os.path.basename(f)
        try:
            if base == "package.json":
                scripts = json.load(open(os.path.join(root, f), encoding="utf-8")).get("scripts") or {}
                hits = [k for k in scripts if OWN_CHECK.search(k)]
            elif base in ("Makefile", "justfile"):
                text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                hits = [n for n in re.findall(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", text, re.M) if OWN_CHECK.search(n)]
            else:
                continue
        except (OSError, ValueError):
            continue
        if hits:
            own_checks[f] = hits
    authority = [f for f in own if re.search(
        r"(^|/)(docs/(README|INDEX|index)\.md|DISPOSITIONS\.md|adr/|decisions/|ARCHITECTURE\.md)", f)][:12]

    first = git(root, "log", "--reverse", "--format=%as", "--max-parents=0").split("\n", 1)[0]
    body = git(root, "log", "--since=180.days", "--format=%b")
    co_authored = len(re.findall(
        r"(?im)^co-authored-by:.*(claude|codex|copilot|cursor|devin|gemini|aider|anthropic|openai)", body))
    default_branch = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip().replace("origin/", "")
    # A sweep of a stale checkout reports problems the project already fixed.
    head_branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    base = f"origin/{default_branch}" if default_branch else ""
    behind = ahead = None
    if base and git(root, "rev-parse", "--verify", "-q", base).strip():
        counts = git(root, "rev-list", "--left-right", "--count", f"HEAD...{base}").split()
        if len(counts) == 2:
            ahead, behind = int(counts[0]), int(counts[1])
    last_fetch = ""
    common = git(root, "rev-parse", "--git-common-dir").strip()
    fetch_head = os.path.join(common if os.path.isabs(common) else os.path.join(root, common), "FETCH_HEAD")
    if os.path.exists(fetch_head):
        last_fetch = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(fetch_head)))
    # The local base ref can itself be old. ls-remote is read-only; skip quietly offline.
    remote_base = None
    if default_branch and "--offline" not in sys.argv:
        try:
            out = subprocess.run(["git", "-C", root, "ls-remote", "origin", f"refs/heads/{default_branch}"],
                                 capture_output=True, text=True, timeout=15).stdout.split()
            remote_base = out[0][:10] if out else None
        except (subprocess.TimeoutExpired, OSError):
            pass
    local_base = git(root, "rev-parse", "--short=10", base).strip() if base else ""
    dirty = len([l for l in git(root, "status", "--porcelain").splitlines() if l])
    claude_co = len(re.findall(r"(?im)^co-authored-by:.*(claude|anthropic)", body))
    return {
        "loading_warnings": loading_warnings(root, own, claude_co),
        "repo": root, "tracked_files": len(files), "own_files": len(own),
        "vendored": dict(vendored.most_common(8)),
        "stacks": {k: sorted(x for x in v if x) for k, v in sorted(stacks.items())},
        "package_roots": {k: sorted(v) for k, v in roots.items()},
        "agent_tools": dict(agent),
        "ci": ci, "hooks": hooks,
        "own_checks": own_checks, "authority_docs": authority,
        "history": {
            "first_commit": first,
            "commits": git(root, "rev-list", "--count", "HEAD").strip(),
            "commits_30d": git(root, "rev-list", "--count", "--since=30.days", "HEAD").strip(),
            "authors_180d": len(set(git(root, "log", "--since=180.days", "--format=%ae").split())),
            "agent_coauthored_commits_180d": co_authored,
            "default_branch": default_branch or None,
        },
        "checkout": {"branch": head_branch, "ahead_of_base": ahead, "behind_base": behind, "base": base or None,
                     "last_fetch": last_fetch or None, "uncommitted_paths": dirty,
                     "local_base": local_base or None, "remote_base": remote_base,
                     "base_ref_stale": bool(remote_base and local_base and not remote_base.startswith(local_base[:7]))},
    }


def loading_warnings(root: str, own: list[str], co_authored_claude: int) -> list[str]:
    """Instruction files some tool silently never reads, or reads only in part."""
    present = set(own)
    w = []
    agents = [f for f in own if os.path.basename(f) == "AGENTS.md"]
    uses_claude = any(f.startswith(".claude/") for f in own) or co_authored_claude > 0
    if "AGENTS.md" in present and "CLAUDE.md" not in present and ".claude/CLAUDE.md" not in present and uses_claude:
        w.append("Claude Code is in use (.claude/ or Claude co-authored commits) but there is no CLAUDE.md: "
                 "Claude Code reads AGENTS.md only through a CLAUDE.md (one line: @AGENTS.md)")
    if agents and any(f.startswith(".gemini/") for f in own) and "GEMINI.md" not in present:
        w.append("Gemini CLI is configured but reads AGENTS.md only if .gemini/settings.json sets context.fileName")
    plain = [f for f in own if f.startswith(".cursor/rules/") and f.endswith(".md")]
    if plain:
        w.append(f"Cursor ignores plain .md in .cursor/rules/ (needs .mdc): {', '.join(plain[:4])}")
    zed_order = [".rules", ".cursorrules", ".windsurfrules", ".clinerules", ".github/copilot-instructions.md",
                 "AGENT.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md"]
    found = [f for f in zed_order if f in present]
    if len(found) > 1 and found[0] != "AGENTS.md":
        w.append(f"Zed reads only the first of these it finds: {found[0]} hides {', '.join(found[1:])}")
    for f in own:
        if os.path.basename(f) == "AGENTS.override.md":
            w.append(f"{f} makes Codex skip the AGENTS.md beside it")
    chain = sum(os.path.getsize(os.path.join(root, f)) for f in agents if f.count("/") <= 2)
    if chain > 32 * 1024:
        w.append(f"AGENTS.md files total {chain:,} bytes: Codex stops reading at 32 KiB by default")
    for f in [".claude/CLAUDE.md", "CLAUDE.md"] + agents:
        if f in present and os.path.getsize(os.path.join(root, f)) > 40_000:
            w.append(f"{f} is over 40,000 characters: Claude Code truncates on-demand files around that size")
    if any(f.startswith(".roo/") or f == ".roomodes" for f in own):
        w.append("Roo Code was discontinued on 2026-05-15: .roo/ and .roomodes are cobwebs unless a fork uses them")
    if ".cursorrules" in present:
        w.append(".cursorrules is Cursor's legacy file (still read by Zed, Cline and Devin): move it to .cursor/rules/*.mdc or AGENTS.md")
    return w


def clip(items: list[str], n: int) -> str:
    return ", ".join(items[:n]) + (f" ... +{len(items) - n}" if len(items) > n else "")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    r = detect(root)
    if emit_json(r):
        return
    h = r["history"]
    print(f"repo: {r['repo']}  files: {r['tracked_files']} (own {r['own_files']})")
    print(f"history: since {h['first_commit']}, {h['commits']} commits, {h['commits_30d']} in 30 days, "
          f"{h['authors_180d']} authors in 180 days, {h['agent_coauthored_commits_180d']} agent "
          f"co-authored; default branch {h['default_branch']}")
    c = r["checkout"]
    print(f"checkout: {c['branch']}, {c['ahead_of_base']} ahead / {c['behind_base']} behind {c['base']}"
          f" (last fetch {c['last_fetch']}), {c['uncommitted_paths']} uncommitted paths")
    if c.get("base_ref_stale"):
        print(f"  WARNING: local {c['base']} is {c['local_base']} but origin has {c['remote_base']}: the base ref is "
              "itself out of date. Fetch (with permission) or say so in the report.")
    if c["behind_base"]:
        print(f"  WARNING: {c['behind_base']} commits behind {c['base']}. Sweep {c['base']} in a temporary"
              " worktree, or findings will include things already fixed.")
    if r["vendored"]:
        print("vendored (skipped): " + ", ".join(f"{k} ({v})" for k, v in r["vendored"].items()))
    print("stacks: " + "; ".join(f"{k} [{', '.join(v)}]" if v else k for k, v in r["stacks"].items()))
    for k, v in r["package_roots"].items():
        if len(v) > 1:
            print(f"  {k} package roots: {clip(v, 12)}")
    print("agent tools configured:")
    for k, v in r["agent_tools"].items():
        print(f"  {k}: {clip(v, 6)}")
    for warning in r["loading_warnings"]:
        print(f"  LOADING: {warning}")
    print(f"ci: {', '.join(r['ci']) or 'none'}   hooks: {clip(r['hooks'], 8) or 'none'}")
    print("owner's own checks (run these first):")
    for f, names in r["own_checks"].items():
        print(f"  {f}: {clip(names, 16)}")
    if r["authority_docs"]:
        print("authority docs: " + ", ".join(r["authority_docs"]))


if __name__ == "__main__":
    main()
