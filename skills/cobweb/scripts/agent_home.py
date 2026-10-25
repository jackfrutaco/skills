#!/usr/bin/env python3
"""Agent memory and global agent setup that live OUTSIDE the repository.

Read-only. Prints names, counts, sizes and reasons; never memory contents,
instruction text or config values. Stdlib only.

1. Memory for this project:
   - Claude Code auto-memory: ~/.claude/projects/<path>/memory, with the MEMORY.md index.
     Each file is checked for paths and names that are gone, for status notes that have
     gone stale, and for problems with the index.
   - memory folders tracked in the repo: listed, and treated like docs
   - other stores (Codex, Windsurf, Gemini): presence and size only
2. Global setup: user-level instruction files, skills (duplicates, broken links, long
   descriptions, index size), user MCP servers, and hooks that fire on every tool call.

Usage: agent_home.py [repo] [--json] [--days=30] [--also=PATH] [--retired=retired_names.json] [--no-global]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import (DATED, Repo, deleted_in, emit_json, extract, git,  # noqa: E402
                           is_path_claim, resolve)

HOME = os.path.expanduser("~")
# Claude Code loads the first 200 lines or 25 KB of MEMORY.md at session start;
# topic files load only when the agent reads them. Index lines past the limit never load.
CLAUDE_INDEX_LINES = 200
CLAUDE_INDEX_BYTES = 25_000
STATUS = re.compile(r"(status|hand-?off|progress|dispatch|next[-_ ]steps?|\bwip\b|in[-_ ]flight|remaining|"
                    r"outstanding|\btodo\b|verified|verification|checkpoint|resume|current[-_ ]state|stands|"
                    r"open[-_ ]items|stranded|in[-_ ]progress|pending)", re.I)
INCIDENT = re.compile(r"(incident|postmortem|post-mortem|outage|lesson|regression|root[-_ ]cause|broke|"
                      r"mistake|never again|caused|failure)", re.I)
SKILL_DIRS = [".agents/skills", ".claude/skills", ".codex/skills", ".pi/agent/skills", ".cursor/skills",
              ".gemini/skills", ".config/opencode/skills"]
USER_INSTRUCTIONS = [".claude/CLAUDE.md", ".codex/AGENTS.md", ".codex/AGENTS.override.md", ".gemini/GEMINI.md",
                     ".config/opencode/AGENTS.md", ".config/amp/AGENTS.md", ".config/AGENTS.md",
                     ".codeium/windsurf/memories/global_rules.md", ".junie/AGENTS.md", ".kiro/steering",
                     ".config/goose/.goosehints", ".copilot/copilot-instructions.md"]


def flag(name: str, default: str | None = None) -> str | None:
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{name}=")), default)


def encode(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line:
            k, _, v = line.strip().partition(":")
            out.setdefault(k.strip(), v.strip().strip('"'))
    return out


def ignored_anywhere(root: str, path: str) -> bool:
    out = git(root, "check-ignore", "--no-index", "--stdin", stdin=f"{path}\n{path}/")
    return bool(out.strip())


def kind_of(fm: dict[str, str], name: str, desc: str) -> str:
    """preference | incident | status | reference | fact"""
    t = fm.get("type", "").lower()
    words = f"{name} {desc}"
    if t in ("user", "feedback"):
        return "preference"
    if INCIDENT.search(words):
        return "incident"
    if STATUS.search(words):
        return "status"
    if t == "reference":
        return "reference"
    return "fact"


def age_days(fm: dict[str, str], path: str) -> int:
    stamp = fm.get("modified", "")
    try:
        t = time.mktime(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S")) if stamp else os.path.getmtime(path)
    except ValueError:
        t = os.path.getmtime(path)
    return int((time.time() - t) / 86400)


def claude_memory(repo: Repo, roots: list[str], days: int, retired: dict[str, str]) -> list[dict]:
    base = os.path.join(HOME, ".claude", "projects")
    if not os.path.isdir(base):
        return []
    wanted = {encode(r) for r in roots} | {encode(os.path.realpath(r)) for r in roots}
    stores = []
    for d in sorted(os.listdir(base)):
        mem = os.path.join(base, d, "memory")
        if d not in wanted or not os.path.isdir(mem):
            continue
        files = sorted(f for f in os.listdir(mem) if f.endswith(".md"))
        if not files:
            continue
        index_path = os.path.join(mem, "MEMORY.md")
        index = open(index_path, encoding="utf-8", errors="replace").read() if os.path.exists(index_path) else ""
        index_lines = index.splitlines()
        linked = re.findall(r"\]\(([^)]+\.md)\)", index)
        # Entries past the load limit never reach a session.
        loaded, size = [], 0
        for i, line in enumerate(index_lines):
            size += len(line.encode()) + 1
            if i >= CLAUDE_INDEX_LINES or size > CLAUDE_INDEX_BYTES:
                break
            loaded.append(line)
        loaded_links = set(re.findall(r"\]\(([^)]+\.md)\)", "\n".join(loaded)))
        topic = [f for f in files if f != "MEMORY.md"]
        kinds = Counter()
        candidates = []
        for f in topic:
            full = os.path.join(mem, f)
            text = open(full, encoding="utf-8", errors="replace").read()
            fm = frontmatter(text)
            name = fm.get("name") or f[:-3]
            kind = kind_of(fm, name, fm.get("description", ""))
            kinds[kind] += 1
            age = age_days(fm, full)
            reasons = []
            gone = []
            for _, rtype, tok in extract(text, "doc"):
                if rtype not in ("path", "link") or tok in files or not is_path_claim(tok, repo):
                    continue
                status, hint = resolve(tok, "MEMORY.md", repo)
                if status == "ok":
                    continue
                # Memory is written from many checkouts and often names scratch, build
                # output or app-bundle paths. Count only what git proves is gone: a
                # deletion in history, a move, or a path under a real top-level
                # folder that no ignore rule (on this machine either) explains.
                clean = tok.rstrip("/")
                when = deleted_in(repo, clean)
                if when:
                    gone.append(f"{tok} (deleted {when.split(' ')[0]})")
                elif status == "moved":
                    gone.append(f"{tok} (moved to {hint})")
                elif status == "missing" and clean.split("/", 1)[0] in repo.top and not ignored_anywhere(repo.root, clean):
                    gone.append(f"{tok} (missing)")
            if gone:
                reasons.append(f"names {len(gone)} repo path(s) that are gone: {', '.join(sorted(set(gone))[:3])}")
            names = [t for t in retired if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text)]
            if names:
                reasons.append(f"mentions retired name(s): {', '.join(names[:4])}")
            if kind == "status" and age > days:
                reasons.append(f"status or handoff note, {age} days old")
            dangling = sorted({w for w in re.findall(r"\[\[([^\]|#]+)", text)
                               if f"{w.strip()}.md" not in files and w.strip() not in files})
            if dangling:
                reasons.append(f"links to memories that are gone: {', '.join(dangling[:3])}")
            if f not in linked:
                reasons.append("not in MEMORY.md, so no session finds it")
            elif f not in loaded_links:
                reasons.append("indexed past the load limit, so it never loads")
            if reasons:
                candidates.append({"file": f, "kind": kind, "age_days": age, "bytes": len(text.encode()),
                                   "reasons": reasons})
        # Same subject twice: identical normalised names.
        stems = defaultdict(list)
        for f in topic:
            stems[re.sub(r"[-_]?(19|20)\d\d-?\d\d-?\d\d", "", f[:-3]).lower()].append(f)
        dupes = [v for v in stems.values() if len(v) > 1]
        # Pace: topic files created in the last 30 days (birth time where the OS keeps it).
        def born(f: str) -> float:
            st = os.stat(os.path.join(mem, f))
            return getattr(st, "st_birthtime", st.st_mtime)
        new_30d = sum(1 for f in topic if time.time() - born(f) < 30 * 86400)
        lines_left = max(0, CLAUDE_INDEX_LINES - len(index_lines))
        bytes_left = max(0, CLAUDE_INDEX_BYTES - len(index.encode()))
        per_line = (len(index.encode()) / max(1, len(index_lines))) or 140
        room = int(min(lines_left, bytes_left / per_line))
        days_to_limit = int(room / (new_30d / 30)) if new_30d else None
        newest_write = max(os.path.getmtime(os.path.join(mem, f)) for f in files)
        order = {"status": 0, "fact": 1, "reference": 2, "incident": 3, "preference": 4}
        candidates.sort(key=lambda c: (order.get(c["kind"], 9), -len(c["reasons"]), -c["age_days"]))
        stores.append({
            "tool": "claude-code", "path": mem, "owner": "plain files outside git (no history)",
            "files": len(topic), "kinds": dict(kinds),
            "index_bytes": len(index.encode()), "index_lines": len(index_lines),
            "index_over_limit": len(index_lines) > CLAUDE_INDEX_LINES or len(index.encode()) > CLAUDE_INDEX_BYTES,
            "index_missing_targets": sorted(set(linked) - set(files)),
            "duplicate_subjects": dupes[:10], "candidates": candidates,
            "new_files_30d": new_30d, "entries_left": room, "days_to_limit": days_to_limit,
            "minutes_since_last_write": int((time.time() - newest_write) / 60),
        })
    return stores


def other_stores() -> list[dict]:
    out = []
    codex = os.path.join(os.environ.get("CODEX_HOME") or os.path.join(HOME, ".codex"), "memories_1.sqlite")
    if os.path.exists(codex):
        rows = {}
        try:
            # immutable: a WAL database can't be opened read-only without write access to -shm.
            con = sqlite3.connect(f"file:{codex}?mode=ro&immutable=1", uri=True, timeout=2)
            for (t,) in con.execute("select name from sqlite_master where type='table'"):
                rows[t] = con.execute(f'select count(*) from "{t}"').fetchone()[0]
            con.close()
        except sqlite3.Error as e:
            rows = {"error": str(e)[:80]}
        out.append({"tool": "codex", "path": codex, "owner": "app-managed database: change it only through Codex",
                    "kb": round(os.path.getsize(codex) / 1e3), "tables": rows})
    ws = os.path.join(HOME, ".codeium", "windsurf", "memories")
    if os.path.isdir(ws):
        files = os.listdir(ws)
        out.append({"tool": "windsurf", "path": ws, "owner": "app-managed (Cascade memories); global_rules.md is yours",
                    "files": len(files)})
    gem = os.path.join(HOME, ".gemini", "GEMINI.md")
    if os.path.exists(gem):
        text = open(gem, encoding="utf-8", errors="replace").read()
        m = re.search(r"^## Gemini Added Memories\n(.*?)(?=^## |\Z)", text, re.S | re.M)
        out.append({"tool": "gemini-cli", "path": gem, "owner": "plain file, loaded in every Gemini session",
                    "memory_lines": len([l for l in (m.group(1).splitlines() if m else []) if l.strip()])})
    return out


def dead_local_paths(text: str, here: str) -> list[str]:
    """~/x, /abs/x and relative links that point at nothing on this machine."""
    out = []
    for m in re.finditer(r"(?<![\w.])((?:~|/Users|/home|\.\.?)/[\w@.+~/-]+)", text):
        p = m.group(1).rstrip(".,):")
        if p.count("/") < 2 or re.search(r"[<>*{}]", p) or "<" in text[max(0, m.start() - 1):m.start()]:
            continue
        full = os.path.expanduser(p) if p.startswith("~") else (p if p.startswith("/") else os.path.join(here, p))
        if not os.path.exists(full):
            out.append(p)
    return sorted(set(out))


def global_setup() -> dict:
    instr = []
    for rel in USER_INSTRUCTIONS:
        p = os.path.join(HOME, rel)
        if os.path.isfile(p):
            text = open(p, encoding="utf-8", errors="replace").read()
            instr.append({"file": "~/" + rel, "bytes": len(text.encode()),
                          "imports": len(re.findall(r"^@\S+", text, re.M)),
                          "dead_paths": dead_local_paths(text, os.path.dirname(p))[:6]})
        elif os.path.isdir(p):
            size = sum(os.path.getsize(os.path.join(p, f)) for f in os.listdir(p) if os.path.isfile(os.path.join(p, f)))
            instr.append({"file": "~/" + rel + "/", "bytes": size, "imports": 0, "dead_paths": []})

    skills: dict[str, list[dict]] = defaultdict(list)
    broken, no_skill_md, long_desc = [], [], []
    per_dir = {}
    for rel in SKILL_DIRS:
        root = os.path.join(HOME, rel)
        if not os.path.isdir(root):
            continue
        desc_total = count = 0
        for name in sorted(os.listdir(root)):
            if name.startswith("."):
                continue
            entry = os.path.join(root, name)
            if os.path.islink(entry) and not os.path.exists(entry):
                broken.append(f"~/{rel}/{name} -> {os.readlink(entry)}")
                continue
            if not os.path.isdir(entry):
                continue
            md = os.path.join(entry, "SKILL.md")
            if not os.path.isfile(md):
                # A container of skills (a sync folder) is not a broken skill.
                depth = entry.count(os.sep)
                nested = any("SKILL.md" in fs for d, _, fs in os.walk(entry) if d.count(os.sep) - depth <= 3)
                if not nested:
                    no_skill_md.append(f"~/{rel}/{name}")
                continue
            text = open(md, encoding="utf-8", errors="replace").read()
            fm = frontmatter(text)
            desc = fm.get("description", "")
            count += 1
            desc_total += len(fm.get("name", name)) + len(desc)
            if len(desc) > 1024 and not any(x.startswith(f"{name} (") for x in long_desc):
                long_desc.append(f"{name} ({len(desc)} chars, over the 1,024 the Agent Skills spec allows)")
            skills[fm.get("name") or name].append({"dir": "~/" + rel, "real": os.path.realpath(entry),
                                                   "hash": hashlib.sha1(text.encode()).hexdigest()[:10]})
        per_dir["~/" + rel] = {"skills": count, "name_and_description_chars": desc_total}
    copies, diverged = [], []
    for name, places in skills.items():
        reals = {p["real"] for p in places}
        if len(reals) < 2:
            continue  # one folder, reached through symlinks
        if len({p["hash"] for p in places}) == 1:
            copies.append(name)
        else:
            diverged.append(f"{name}: different SKILL.md in {', '.join(p['dir'] for p in places)}")

    mcp: dict[str, list[str]] = {}
    try:
        cj = json.load(open(os.path.join(HOME, ".claude.json"), encoding="utf-8"))
        mcp["~/.claude.json (user)"] = sorted(cj.get("mcpServers") or {})
    except (OSError, ValueError):
        pass
    for rel in (".cursor/mcp.json", ".gemini/settings.json"):
        try:
            mcp["~/" + rel] = sorted(json.load(open(os.path.join(HOME, rel), encoding="utf-8")).get("mcpServers") or {})
        except (OSError, ValueError):
            pass
    toml = os.path.join(HOME, ".codex", "config.toml")
    if os.path.exists(toml):
        mcp["~/.codex/config.toml"] = re.findall(r"^\[mcp_servers\.([\w-]+)\]", open(toml).read(), re.M)

    hooks = []
    settings = os.path.join(HOME, ".claude", "settings.json")
    try:
        data = json.load(open(settings, encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    for event, entries in (data.get("hooks") or {}).items():
        for e in entries if isinstance(entries, list) else []:
            matcher = e.get("matcher") or "*"
            for h in e.get("hooks", []):
                cmd = h.get("command", "")
                script = next((w for w in re.findall(r"[\"']?((?:~|\$HOME|/)[^\s\"']+\.\w+)", cmd)), None)
                missing = bool(script) and not os.path.exists(os.path.expanduser(script.replace("$HOME", "~")))
                hooks.append({"event": event, "matcher": matcher,
                              "every_call": event in ("PreToolUse", "PostToolUse") and matcher in ("*", ""),
                              "script_missing": missing, "script": os.path.basename(script) if script else None})
    # The same rule copied into several tools' user files drifts: an edit reaches one tool.
    bodies = {}
    for rel in USER_INSTRUCTIONS:
        p = os.path.join(HOME, rel)
        if os.path.isfile(p):
            bodies["~/" + rel] = {l.strip() for l in open(p, encoding="utf-8", errors="replace")
                                  if len(l.strip()) > 30 and not l.startswith("#")}
    copied = []
    names = sorted(bodies)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(bodies[a] & bodies[b])
            if shared >= 3:
                copied.append(f"{a} and {b} share {shared} lines")

    # Projects the tools still trust or remember whose folders are gone.
    stale_projects = {}
    toml = os.path.join(HOME, ".codex", "config.toml")
    if os.path.exists(toml):
        paths = re.findall(r'^\[projects\."([^"]+)"\]', open(toml, encoding="utf-8", errors="replace").read(), re.M)
        stale_projects["~/.codex/config.toml"] = (sum(1 for p in paths if not os.path.exists(p)), len(paths))
    try:
        cj = json.load(open(os.path.join(HOME, ".claude.json"), encoding="utf-8"))
        paths = list((cj.get("projects") or {}).keys())
        stale_projects["~/.claude.json projects"] = (sum(1 for p in paths if not os.path.exists(p)), len(paths))
    except (OSError, ValueError):
        pass

    # Hook scripts nothing runs.
    hook_dir = os.path.join(HOME, ".claude", "hooks")
    settings_text = open(settings, encoding="utf-8", errors="replace").read() if os.path.exists(settings) else ""
    unwired = []
    if os.path.isdir(hook_dir):
        scripts = [f for f in os.listdir(hook_dir) if os.path.isfile(os.path.join(hook_dir, f))]
        others = "".join(open(os.path.join(hook_dir, f), encoding="utf-8", errors="replace").read() for f in scripts)
        for f in scripts:
            stem = os.path.splitext(f)[0]
            if f not in settings_text and stem not in others.replace(open(os.path.join(hook_dir, f), encoding="utf-8",
                                                                            errors="replace").read(), ""):
                unwired.append(f"~/.claude/hooks/{f}")

    # Skills an installer's lock file lists that are not on disk.
    lock_missing = []
    lock = os.path.join(HOME, ".agents", ".skill-lock.json")
    try:
        locked = (json.load(open(lock, encoding="utf-8")).get("skills") or {})
        lock_missing = sorted(k for k in locked if not os.path.isdir(os.path.join(HOME, ".agents", "skills", k)))
    except (OSError, ValueError, AttributeError):
        pass

    return {"instructions": instr, "skills_per_dir": per_dir, "broken_skill_links": broken,
            "copied_instruction_lines": copied, "stale_trusted_projects": stale_projects,
            "unwired_hook_scripts": unwired, "skill_lock_missing": lock_missing,
            "skills_without_skill_md": no_skill_md, "long_descriptions": long_desc,
            "identical_copies": copies, "diverged_copies": diverged, "mcp_servers": mcp, "hooks": hooks}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    days = int(flag("days", "30"))
    roots = [l[9:] for l in git(root, "worktree", "list", "--porcelain").splitlines() if l.startswith("worktree ")]
    roots += [root] + [a.split("=", 1)[1] for a in sys.argv if a.startswith("--also=")]
    retired = {}
    if flag("retired"):
        try:
            retired = {r["term"]: r["retired_in"] for r in json.load(open(flag("retired"), encoding="utf-8"))}
        except (OSError, ValueError):
            pass
    repo = Repo(root)
    tracked_memory = [f for f in repo.files if re.search(r"(^|/)(\.?memory|memories)/", f)]
    r = {"repo": root, "claude_memory": claude_memory(repo, roots, days, retired),
         "tracked_memory_files": len(tracked_memory),
         "tracked_memory_dirs": sorted({re.match(r"(.*?(?:\.?memory|memories))/", f).group(1) for f in tracked_memory}),
         "other_stores": other_stores(),
         "global": {} if "--no-global" in sys.argv else global_setup()}
    if emit_json(r):
        return
    print(f"repo: {root}")
    if not r["claude_memory"]:
        print("claude-code memory: none for this repo's paths")
    for s in r["claude_memory"]:
        print(f"\n[claude-code memory] {s['path']}")
        print(f"  {s['files']} files {s['kinds']}; MEMORY.md {s['index_lines']} lines, {s['index_bytes']:,} bytes "
              f"(~{s['index_bytes'] // 4:,} tokens loaded every session)"
              + ("  OVER THE LOAD LIMIT: later entries never load" if s["index_over_limit"] else ""))
        if s["days_to_limit"] is not None:
            print(f"  {s['new_files_30d']} new memories in 30 days; about {s['entries_left']} more index entries fit, "
                  f"so the index reaches its load limit in about {s['days_to_limit']} days at this pace")
        if s["minutes_since_last_write"] < 15:
            print(f"  written {s['minutes_since_last_write']} minutes ago: a session may be writing it; don't move files now")
        if s["index_missing_targets"]:
            print(f"  index links to missing files: {', '.join(s['index_missing_targets'][:6])}")
        if s["duplicate_subjects"]:
            print(f"  same subject in several files: {'; '.join(', '.join(d) for d in s['duplicate_subjects'][:4])}")
        print(f"  candidates: {len(s['candidates'])} (status first; preferences listed last and never auto-removed)")
        for c in s["candidates"][:25]:
            print(f"    [{c['kind']}] {c['file']}  {c['age_days']}d: {'; '.join(c['reasons'])}")
        if len(s["candidates"]) > 25:
            print(f"    ... +{len(s['candidates']) - 25} more")
    if r["tracked_memory_files"]:
        print(f"\nmemory tracked in git: {r['tracked_memory_files']} files in {', '.join(r['tracked_memory_dirs'])} "
              "(treated like docs by the other checks)")
    for o in r["other_stores"]:
        detail = {k: v for k, v in o.items() if k not in ("tool", "path", "owner")}
        print(f"\n[{o['tool']} memory] {o['path']}: {detail}; {o['owner']}")
    g = r["global"]
    if g:
        print("\n[global setup]")
        for i in g["instructions"]:
            dead = f"; dead paths: {', '.join(i['dead_paths'])}" if i["dead_paths"] else ""
            print(f"  {i['file']}: {i['bytes']:,} bytes (~{i['bytes'] // 4:,} tokens every session){dead}")
        for c in g["copied_instruction_lines"]:
            print(f"  copied rules: {c}; an edit to one won't reach the other tool")
        for d, v in g["skills_per_dir"].items():
            over = v["name_and_description_chars"] > 8_000
            print(f"  {d}: {v['skills']} skills, {v['name_and_description_chars']:,} chars of names and descriptions"
                  + ("  (over the ~8,000 chars Codex lists; Claude Code lists about 1% of the context window,"
                     " so the least-used descriptions get dropped)" if over else ""))
        for f, (gone, total) in g["stale_trusted_projects"].items():
            if gone:
                print(f"  {f}: {gone} of {total} remembered project paths no longer exist")
        if g["unwired_hook_scripts"]:
            print(f"  hook scripts no setting or other hook runs: {', '.join(g['unwired_hook_scripts'])}")
        if g["skill_lock_missing"]:
            print(f"  skills in ~/.agents/.skill-lock.json but not installed: {len(g['skill_lock_missing'])} "
                  f"({', '.join(g['skill_lock_missing'][:8])})")
        if g["identical_copies"]:
            print(f"  skills installed as identical copies in several tool folders: {len(g['identical_copies'])} "
                  "(normal for skill installers; not a finding)")
        for label in ("broken_skill_links", "skills_without_skill_md", "long_descriptions", "diverged_copies"):
            if g[label]:
                note = {"diverged_copies": " (one name, different instructions depending on the tool)"}.get(label, "")
                print(f"  {label.replace('_', ' ')}: {len(g[label])}{note}")
                for x in g[label][:8]:
                    print(f"    {x}")
        for f, names in g["mcp_servers"].items():
            if names:
                print(f"  MCP servers in {f}: {len(names)} ({', '.join(names[:10])})")
        for h in g["hooks"]:
            flags = [x for x, on in (("fires on every tool call", h["every_call"]),
                                      ("SCRIPT MISSING", h["script_missing"])) if on]
            if flags:
                print(f"  hook {h['event']} [{h['matcher']}] {h['script'] or ''}: {', '.join(flags)}")


if __name__ == "__main__":
    main()
