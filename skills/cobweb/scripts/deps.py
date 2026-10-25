#!/usr/bin/env python3
"""Vulnerable and outdated dependencies, from each package manager's own
read-only commands. Needs network; never installs, fixes or writes a lockfile.
Stdlib only.

Usage: deps.py [repo] [--json] [--timeout=120]
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import emit_json, git, is_vendored, vendored_roots  # noqa: E402

TIMEOUT = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--timeout=")), "120"))


def run(cmd: list[str], cwd: str) -> tuple[int | str, str]:
    # Python's timeout, not `timeout(1)`: macOS has no `timeout` binary.
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT, check=False)
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired:
        return "timeout", ""
    except OSError as e:
        return "missing", str(e)


def js_audit(pm: str, cwd: str) -> dict:
    cmd = {"npm": ["npm", "audit", "--json"], "pnpm": ["pnpm", "audit", "--json"],
           "bun": ["bun", "audit", "--json"], "yarn": ["yarn", "npm", "audit", "--json", "--all"]}[pm]
    code, out = run(cmd, cwd)
    if code in ("timeout", "missing"):
        return {"skipped": f"{pm} audit {code}"}
    try:
        data = json.loads(out or "{}")
    except ValueError:
        # yarn berry prints one JSON object per line
        data = {}
    meta = (data.get("metadata") or {}).get("vulnerabilities")
    if meta:  # npm and pnpm
        if data.get("advisories"):  # pnpm: keyed by advisory id
            names = sorted({a.get("module_name", "?") for a in data["advisories"].values()})
        else:  # npm: keyed by package
            names = sorted(data.get("vulnerabilities") or {})
        return {"counts": {k: v for k, v in meta.items() if v and k != "total"}, "packages": names[:15]}
    if isinstance(data, dict) and data and pm == "bun":
        sev = {}
        for pkg, advisories in data.items():
            for a in advisories if isinstance(advisories, list) else []:
                sev[a.get("severity", "?")] = sev.get(a.get("severity", "?"), 0) + 1
        return {"counts": sev, "packages": sorted(data)[:15]}
    return {"counts": {}, "packages": [], "note": f"exit {code}; read `{' '.join(cmd)}` yourself"}


def js_outdated(pm: str, cwd: str) -> dict:
    cmd = {"npm": ["npm", "outdated", "--json"], "pnpm": ["pnpm", "outdated", "--format", "json"],
           "bun": None, "yarn": None}[pm]
    if not cmd:
        return {"skipped": f"{pm} has no JSON outdated report; run `{pm} outdated`"}
    code, out = run(cmd, cwd)
    if code in ("timeout", "missing"):
        return {"skipped": f"{pm} outdated {code}"}
    try:
        data = json.loads(out or "{}")
    except ValueError:
        return {"skipped": "unparseable output"}
    majors, not_installed = [], []
    for name, info in data.items():
        info = info[0] if isinstance(info, list) else info
        cur, latest = str(info.get("current") or ""), str(info.get("latest") or "")
        if not cur or cur == "none":
            not_installed.append(name)
            continue
        a, b = re.match(r"\d+", cur), re.match(r"\d+", latest)
        if a and b and int(b.group(0)) > int(a.group(0)):
            majors.append({"package": name, "current": cur, "latest": latest,
                           "behind": int(b.group(0)) - int(a.group(0))})
    majors.sort(key=lambda m: -m["behind"])
    return {"outdated": len(data), "major_behind": majors[:20], "major_behind_total": len(majors),
            "declared_not_installed": not_installed[:10]}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    extra = vendored_roots(root)
    files = [f for f in git(root, "ls-files").splitlines() if f and not is_vendored(f, extra)]
    locks = {"package-lock.json": "npm", "pnpm-lock.yaml": "pnpm", "bun.lock": "bun", "bun.lockb": "bun",
             "yarn.lock": "yarn"}
    results = []
    # Workspace roots only: a monorepo's root lockfile covers its packages.
    for f in sorted(files, key=lambda x: x.count("/")):
        pm = locks.get(os.path.basename(f))
        d = os.path.dirname(f) or "."
        if not pm or any(r["dir"] != "." and d.startswith(r["dir"] + "/") or r["dir"] == "." and d != "."
                         and r["pm"] == pm for r in results):
            continue
        if not shutil.which(pm):
            results.append({"dir": d, "pm": pm, "skipped": f"{pm} not installed"})
            continue
        cwd = os.path.join(root, d)
        installed = os.path.isdir(os.path.join(cwd, "node_modules"))
        results.append({"dir": d, "pm": pm, "audit": js_audit(pm, cwd),
                        "outdated": js_outdated(pm, cwd) if installed else
                        {"skipped": "no node_modules: installed versions unknown"}})
    if "requirements.txt" in files and shutil.which("uvx"):
        code, out = run(["uvx", "pip-audit", "-r", "requirements.txt", "-f", "json", "--progress-spinner", "off"], root)
        try:
            deps = json.loads(out).get("dependencies", [])
            vulns = [d["name"] for d in deps if d.get("vulns")]
            results.append({"dir": ".", "pm": "pip", "audit": {"counts": {"vulnerable_packages": len(vulns)},
                                                              "packages": vulns[:15]}})
        except (ValueError, AttributeError):
            results.append({"dir": ".", "pm": "pip", "skipped": f"pip-audit exit {code}"})
    for manifest, tool, cmd in (("go.mod", "go", ["go", "run", "golang.org/x/vuln/cmd/govulncheck@latest", "./..."]),
                                ("Cargo.toml", "cargo-audit", ["cargo", "audit", "--json"])):
        if manifest in files:
            if not shutil.which(tool):
                results.append({"dir": ".", "pm": tool, "skipped": f"{tool} not installed"})
            else:
                code, out = run(cmd, root)
                results.append({"dir": ".", "pm": tool, "audit": {"exit": code, "note": "read the output yourself"}})
    r = {"repo": root, "results": results}
    if emit_json(r):
        return
    print(f"repo: {root}")
    if not results:
        print("no lockfile or manifest this script knows; see references/ecosystems.md")
    for x in results:
        print(f"\n[{x['pm']}] {x['dir']}")
        if "skipped" in x:
            print(f"  skipped: {x['skipped']}")
            continue
        a = x.get("audit", {})
        if "skipped" in a:
            print(f"  audit skipped: {a['skipped']}")
        else:
            print(f"  vulnerabilities: {a.get('counts') or 'none'}  {', '.join(a.get('packages', [])[:10])}"
                  + (f"  ({a['note']})" if a.get("note") else ""))
        o = x.get("outdated")
        if o and "skipped" in o:
            print(f"  outdated skipped: {o['skipped']}")
        elif o:
            print(f"  outdated {o['outdated']}, a major or more behind {o['major_behind_total']}")
            for m in o["major_behind"][:10]:
                print(f"    {m['package']:40} {m['current']} -> {m['latest']}")
            if o["declared_not_installed"]:
                print(f"  declared but not installed: {', '.join(o['declared_not_installed'])}")


if __name__ == "__main__":
    main()
