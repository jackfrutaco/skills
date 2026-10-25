#!/usr/bin/env python3
"""Measure what slows work on a repository down, for people and agents.
Stdlib only. Read-only unless --run is given, which runs the named commands.

Usage: drag.py [repo] [--json] [--no-ci] [--no-live] [--run="pnpm typecheck"] [--run=...] [--timeout=600]
  --no-live  skip CI and branch state (for sweeping a historical snapshot)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections import defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import emit_json, git  # noqa: E402


def run(cmd: list[str], cwd: str, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout
    except (subprocess.TimeoutExpired, OSError):
        return -1, ""


def repo_size(root: str) -> dict:
    stats = dict(line.split(": ", 1) for line in git(root, "count-objects", "-vH").splitlines() if ": " in line)
    return {"pack": stats.get("size-pack"), "loose": stats.get("size"), "objects": stats.get("in-pack")}


def largest_blobs(root: str, n: int = 10, timeout: int = 90) -> list[dict]:
    try:
        objs = subprocess.run(["git", "-C", root, "rev-list", "--objects", "--all"], capture_output=True,
                              text=True, timeout=timeout, check=False).stdout
        batch = subprocess.run(
            ["git", "-C", root, "cat-file", "--batch-check=%(objecttype) %(objectname) %(objectsize) %(rest)"],
            input=objs, capture_output=True, text=True, timeout=timeout, check=False).stdout
    except subprocess.TimeoutExpired:
        return [{"error": "timed out"}]
    blobs = []
    for line in batch.splitlines():
        parts = line.split(" ", 3)
        if len(parts) == 4 and parts[0] == "blob":
            blobs.append((int(parts[2]), parts[3]))
    blobs.sort(reverse=True)
    tracked = set(git(root, "ls-files").splitlines())
    out, seen = [], set()
    for size, path in blobs:
        if path in seen:
            continue
        seen.add(path)
        out.append({"path": path, "mb": round(size / 1e6, 1), "in_head": path in tracked})
        if len(out) >= n:
            break
    return out


def branches(root: str, base: str | None) -> dict:
    now = time.time()
    rows = git(root, "for-each-ref", "--format=%(refname:short)\t%(committerdate:unix)", "refs/heads").splitlines()
    local = [(r.split("\t")[0], int(r.split("\t")[1])) for r in rows if "\t" in r]
    merged = set()
    if base:
        merged = {b.strip().lstrip("*+ ").strip() for b in git(root, "branch", "--merged", base).splitlines()}
    stale = [b for b, t in local if now - t > 90 * 86400]
    gone = [l.split()[0].lstrip("*+ ") for l in git(root, "branch", "-vv").splitlines() if ": gone]" in l]
    remote_merged = []
    if base:
        remote_merged = [b.strip() for b in git(root, "branch", "-r", "--merged", base).splitlines()
                         if b.strip() and "->" not in b and b.strip() != base]
    wt = git(root, "worktree", "list", "--porcelain")
    worktrees = wt.count("\nworktree ") + (1 if wt.startswith("worktree ") else 0)
    prunable = wt.count("\nprunable")
    return {"local": len(local), "merged_into_base": len(merged - {base.split("/")[-1] if base else ""}),
            "no_commits_90d": len(stale), "worktrees": worktrees, "prunable_worktrees": prunable,
            "upstream_gone": gone, "remote_merged_into_base": len(remote_merged),
            "note": "--merged misses squash merges; check PR state before deleting"}


def ci(root: str, limit: int = 100) -> dict:
    if not shutil.which("gh"):
        return {"skipped": "gh not installed"}
    if "github.com" not in git(root, "remote", "get-url", "origin"):
        return {"skipped": "origin is not GitHub"}
    code, out = run(["gh", "run", "list", "--limit", str(limit), "--json",
                     "workflowName,conclusion,startedAt,updatedAt,event"], root, 60)
    if code != 0:
        return {"skipped": "gh run list failed (not signed in, or no access)"}
    runs = json.loads(out or "[]")
    per: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for r in runs:
        try:
            start = time.mktime(time.strptime(r["startedAt"][:19], "%Y-%m-%dT%H:%M:%S"))
            end = time.mktime(time.strptime(r["updatedAt"][:19], "%Y-%m-%dT%H:%M:%S"))
        except (KeyError, ValueError):
            continue
        per[r["workflowName"]].append((end - start, r.get("conclusion") or ""))
    code, out = run(["gh", "workflow", "list", "--all", "--json", "name,state,path"], root, 30)
    states = json.loads(out) if code == 0 and out else []
    # GitHub keeps listing a workflow as "active" after its file is deleted;
    # the tracked file is what decides whether it can still run.
    tracked_wf = set(git(root, "ls-files", ".github/workflows").splitlines())
    states = [w for w in states if w.get("path") in tracked_wf]
    disabled = [w["name"] for w in states if w.get("state") != "active"]
    workflows = []
    for name, vals in per.items():
        durations = [d for d, _ in vals if d > 0]
        fails = sum(1 for _, c in vals if c in ("failure", "timed_out", "startup_failure"))
        # Fewer than 3 runs has no meaningful median.
        workflows.append({"workflow": name, "runs": len(vals), "current": name in {w["name"] for w in states},
                          "median_min": round(statistics.median(durations) / 60, 1) if len(durations) >= 3 else None,
                          "max_min": round(max(durations) / 60, 1) if durations else None,
                          "fail_rate": round(fails / len(vals), 2)})
    never = sorted(w["name"] for w in states if w.get("state") == "active" and w["name"] not in per)
    workflows.sort(key=lambda w: (not w["current"], w["median_min"] is None, -(w["median_min"] or 0)))
    return {"recent_runs": len(runs), "workflows": workflows,
            "disabled": disabled, "no_recent_runs": never, "workflow_files": len(tracked_wf)}


BUILTIN_SECRETS = {"GITHUB_TOKEN"}


def actions_secrets(root: str) -> dict:
    """Repository and environment secret/variable NAMES (never values) against the
    names workflows and composite actions read."""
    if not shutil.which("gh") or "github.com" not in git(root, "remote", "get-url", "origin"):
        return {"skipped": "gh or a GitHub origin is missing"}
    code, slug = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], root, 30)
    slug = slug.strip()
    if code != 0 or not slug:
        return {"skipped": "gh repo view failed"}
    defined: dict[str, str] = {}
    for kind in ("secrets", "variables"):
        code, out = run(["gh", "api", f"repos/{slug}/actions/{kind}?per_page=100", "-q", f".{kind}[].name"], root, 30)
        if code != 0:
            return {"skipped": f"listing {kind} failed (no admin access, or the plan hides it): unchecked"}
        for name in out.split():
            defined[name] = "secret" if kind == "secrets" else "variable"
    code, out = run(["gh", "api", f"repos/{slug}/environments", "-q", ".environments[].name"], root, 30)
    for env in (out.split() if code == 0 else []):
        for kind in ("secrets", "variables"):
            c2, o2 = run(["gh", "api", f"repos/{slug}/environments/{env}/{kind}?per_page=100", "-q",
                          f".{kind}[].name"], root, 30)
            for name in (o2.split() if c2 == 0 else []):
                defined.setdefault(name, f"{'secret' if kind == 'secrets' else 'variable'} in environment {env}")
    text = ""
    for f in git(root, "ls-files", ".github").splitlines():
        if f.endswith((".yml", ".yaml")):
            text += open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
    read = {m.group(2) for m in re.finditer(r"\b(secrets|vars)\.([A-Za-z_][A-Za-z0-9_]*)", text)}
    inherit = bool(re.search(r"secrets:\s*inherit", text))
    unused = []
    for name, kind in sorted(defined.items()):
        if name in read or name in BUILTIN_SECRETS:
            continue
        # The commit that removed the last reader is the evidence.
        last = git(root, "log", "-1", "--format=%h %as %s", f"-S{name}", "--", ".github").strip()
        unused.append({"name": name, "kind": kind, "last_reader_removed_in": last or None})
    unset = sorted(n for n in read - set(defined) - BUILTIN_SECRETS)
    return {"repo": slug, "defined": len(defined), "unused": unused, "read_but_not_defined": unset,
            "note": "a workflow passes secrets with `secrets: inherit`: a called workflow elsewhere may read them"
                    if inherit else None}


def hooks(root: str) -> list[dict]:
    """What runs on commit and push, and on every agent tool call."""
    out = []
    hp = git(root, "config", "core.hooksPath").strip()
    hooks_dir = os.path.join(root, hp) if hp else os.path.join(root, git(root, "rev-parse", "--git-path", "hooks").strip())
    for name in ("pre-commit", "commit-msg", "pre-push", "post-checkout", "post-merge"):
        path = os.path.join(hooks_dir, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            body = open(path, encoding="utf-8", errors="replace").read()
            manager = next((m for m in ("lefthook", "husky", "pre-commit", "simple-git-hooks") if m in body), None)
            if manager:  # a generated shim: the real commands are in the manager's config, listed below
                out.append({"hook": f"git {name}", "runs": [f"(runs {manager})"]})
                continue
            cmds = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#")
                    and not l.startswith(("set ", "#!/", ". ", "if ", "fi", "then", "else", "exit"))][:4]
            out.append({"hook": f"git {name}", "runs": cmds})
    for f in (".husky/pre-commit", ".husky/pre-push", "lefthook.yml", ".lefthook.yml", ".pre-commit-config.yaml"):
        p = os.path.join(root, f)
        if os.path.isfile(p):
            body = open(p, encoding="utf-8", errors="replace").read()
            cmds = [c for c in re.findall(r"(?:run|entry):\s*[|>]?-?\s*\n?\s*(.+)", body) if c.strip() not in "|>"] or [l for l in body.splitlines() if l.strip()
                                                                and not l.startswith("#")][:4]
            out.append({"hook": f, "runs": [c.strip() for c in cmds][:6]})
    settings = os.path.join(root, ".claude", "settings.json")
    if os.path.isfile(settings):
        try:
            data = json.load(open(settings))
        except ValueError:
            data = {}
        for event, entries in (data.get("hooks") or {}).items():
            for e in entries if isinstance(entries, list) else []:
                matcher = e.get("matcher", "*") or "*"
                for h in e.get("hooks", []):
                    out.append({"hook": f"claude-code {event} [{matcher}]", "runs": [h.get("command", "")[:120]],
                                "every_tool_call": event in ("PreToolUse", "PostToolUse") and matcher in ("*", "")})
    return out


def agent_load(root: str) -> dict:
    mcp = {}
    for f in (".mcp.json", ".cursor/mcp.json", ".vscode/mcp.json", ".gemini/settings.json"):
        p = os.path.join(root, f)
        if os.path.isfile(p):
            try:
                data = json.load(open(p))
                servers = data.get("mcpServers") or data.get("servers") or {}
                mcp[f] = sorted(servers)
            except ValueError:
                mcp[f] = ["(unparseable)"]
    toml = os.path.join(root, ".codex", "config.toml")
    if os.path.isfile(toml):
        mcp[".codex/config.toml"] = re.findall(r"^\[mcp_servers\.([\w-]+)\]", open(toml).read(), re.M)
    skills = [f for f in git(root, "ls-files").splitlines() if f.endswith("SKILL.md")]
    return {"mcp_servers": mcp, "repo_skills": len(skills)}


def timing_suggestions(root: str) -> list[str]:
    files = set(git(root, "ls-files").splitlines())
    s = []
    if "package.json" in files:
        try:
            scripts = json.load(open(os.path.join(root, "package.json"))).get("scripts") or {}
        except ValueError:
            scripts = {}
        pm = "pnpm" if "pnpm-lock.yaml" in files else "bun" if {"bun.lock", "bun.lockb"} & files else \
             "yarn" if "yarn.lock" in files else "npm"
        for name in ("typecheck", "lint", "test", "build"):
            if name in scripts:
                s.append(f"{pm} run {name}")
        if "tsconfig.json" in files:
            s.append("npx tsc --noEmit --extendedDiagnostics   # check time per phase")
        s.append("vitest run --reporter=json --outputFile=/tmp/vitest.json   # then sort by duration")
    if "pyproject.toml" in files or any(f.endswith("requirements.txt") for f in files):
        s.append("pytest --durations=20 -q")
    if "go.mod" in files:
        s.append("go test -json ./... | gotestsum tool slowest   # or: go test ./... -v and sort")
    if "Cargo.toml" in files:
        s.append("cargo build --timings   # writes target/cargo-timings/")
    if any(f.endswith(("build.gradle", "build.gradle.kts")) for f in files):
        s.append("./gradlew build --profile")
    if "mix.exs" in files:
        s.append("mix test --slowest 10")
    return s


def time_commands(root: str, commands: list[str], timeout: int) -> list[dict]:
    out = []
    for cmd in commands:
        start = time.time()
        try:
            p = subprocess.run(cmd, cwd=root, shell=True, capture_output=True, text=True, timeout=timeout)
            code = p.returncode
            tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
        except subprocess.TimeoutExpired:
            code, tail = "timeout", []
        out.append({"command": cmd, "seconds": round(time.time() - start, 1), "exit": code, "tail": tail})
    return out


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    default = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip() or None
    commands = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--run=")]
    timeout = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--timeout=")), "600"))
    r = {
        "repo": root, "size": repo_size(root), "largest_blobs": largest_blobs(root),
        "branches": {} if "--no-live" in sys.argv else branches(root, default), "hooks": hooks(root), "agent_load": agent_load(root),
        "ci": {"skipped": "--no-ci"} if "--no-ci" in sys.argv or "--no-live" in sys.argv else ci(root),
        "actions_secrets": {"skipped": "--no-ci"} if "--no-ci" in sys.argv or "--no-live" in sys.argv
        else actions_secrets(root),
        "timing_suggestions": timing_suggestions(root),
    }
    if commands:
        r["timed"] = time_commands(root, commands, timeout)
    if emit_json(r):
        return
    s = r["size"]
    print(f"repo: {root}\nsize: pack {s['pack']}, loose {s['loose']}, {s['objects']} packed objects"
          + ("  (never packed: loose size overstates a clone; `git gc` would shrink it)"
             if str(s.get('objects')) == "0" else ""))
    print("largest blobs in history:")
    for b in r["largest_blobs"]:
        print(f"    {b.get('mb')} MB  {b.get('path')}{'' if b.get('in_head') else '  (deleted, still in history)'}")
    b = r["branches"]
    if b:
        print(f"branches: {b['local']} local, {b['merged_into_base']} merged into {default}, "
              f"{b['no_commits_90d']} untouched 90+ days, {len(b['upstream_gone'])} with upstream gone; "
              f"remote branches merged into base {b['remote_merged_into_base']}; "
              f"worktrees {b['worktrees']} ({b['prunable_worktrees']} prunable)")
    print("hooks:")
    for h in r["hooks"] or [{"hook": "none", "runs": []}]:
        flag = "  <- fires on every agent tool call" if h.get("every_tool_call") else ""
        print(f"    {h['hook']}: {' ; '.join(h['runs'])[:160]}{flag}")
    a = r["agent_load"]
    print(f"agent load: {a['repo_skills']} skills in repo; MCP servers: "
          + (", ".join(f"{f} {len(v)} ({', '.join(v[:6])})" for f, v in a["mcp_servers"].items()) or "none"))
    c = r["ci"]
    if "skipped" in c:
        print(f"ci: skipped ({c['skipped']})")
    else:
        print(f"ci: {c['recent_runs']} recent runs across {len(c['workflows'])} workflows")
        for w in c["workflows"][:10]:
            gone = "" if w["current"] else "  (workflow file no longer exists: past runs only)"
            print(f"    {w['workflow'][:40]:40} runs {w['runs']:3}  median {w['median_min'] if w['median_min'] is not None else '-'} min  "
                  f"max {w['max_min']} min  fail {int(w['fail_rate'] * 100)}%{gone}")
        if c["disabled"]:
            print(f"    disabled: {', '.join(c['disabled'])}")
        if c["no_recent_runs"]:
            print(f"    active but no run in the last {c['recent_runs']}: {', '.join(c['no_recent_runs'][:10])}")
    sec = r["actions_secrets"]
    if "skipped" in sec:
        print(f"actions secrets: skipped ({sec['skipped']})")
    else:
        print(f"actions secrets and variables (names only): {sec['defined']} defined, {len(sec['unused'])} no workflow reads, "
              f"{len(sec['read_but_not_defined'])} read but not defined in the repo")
        for u in sec["unused"][:10]:
            print(f"    unused {u['kind']}: {u['name']}"
                  + (f"  (last reader removed in {u['last_reader_removed_in'][:80]})" if u["last_reader_removed_in"] else ""))
        for n in sec["read_but_not_defined"][:10]:
            print(f"    read but not defined: {n} (or set at organization level)")
        if sec["note"]:
            print(f"    note: {sec['note']}")
    print("time these (ask first; they run the project's code):")
    for t in r["timing_suggestions"]:
        print(f"    {t}")
    for t in r.get("timed", []):
        print(f"timed: {t['command']}  {t['seconds']} s  exit {t['exit']}")


if __name__ == "__main__":
    main()
