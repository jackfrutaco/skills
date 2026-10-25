#!/usr/bin/env python3
"""Count where agents stumble in this project, from local session logs.

Opt-in: run only after the person agrees. Reads Claude Code logs
(~/.claude/projects) and Codex logs (~/.codex/sessions, or $CODEX_HOME) whose
working directory is this repository or one of its worktrees. Prints counts,
tool names, repository paths and command names only: never prompts, outputs
or file contents. Stdlib only; read-only.

Usage: transcripts.py [repo] [--days=60] [--json]
"""

from __future__ import annotations

import glob
import json
import os
import re
import shlex
import sys
import time
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import emit_json, classify, git  # noqa: E402

MISSING_CMD = re.compile(r"(?:^|\n)(?:\S+: )?(?:line \d+: )?([\w.+-]+): command not found|command not found: ([\w.+-]+)")
MISSING_PATH = re.compile(r"(?:^|[\s'\"])((?:\.{0,2}/)?[\w@.+-]+(?:/[\w@.+-]+)+|[\w@+-]+\.[A-Za-z0-9]{1,6})['\"]?:? "
                          r"(?:No such file or directory|does not exist)|ENOENT[^'\"\n]*['\"]([\w@./+-]+)['\"]|"
                          r"File does not exist[^\n]*?(/[^\s'\"]+)?")
MISSING_SCRIPT = re.compile(r"Missing script: \"?([\w:.\-]+)\"?|Script not found \"([\w:.\-]+)\"|"
                            r"ERR_PNPM_NO_SCRIPT[^\"\n]*\"([\w:.\-]+)\"|Command \"([\w:.\-]+)\" not found|"
                            r"No rule to make target [`']([\w:.\-]+)'")
MISSING_MODULE = re.compile(r"Cannot find module '([^']+)'|No module named '([^']+)'|"
                            r"Cannot find package '([^']+)'|Module not found: Error: Can't resolve '([^']+)'")
EDIT_MISS = re.compile(r"String to replace not found|old_string not found|oldText must match|could not find the text",
                       re.I)
EXIT_CODE = re.compile(r"(?:Process exited with code|Exit code:?) ?(\d+)")
# Random-looking tokens (upper, lower and digits mixed) and key=value pairs.
SECRETISH = re.compile(r"\b(?=[\w-]*\d)(?=[\w-]*[A-Z])(?=[\w-]*[a-z])[\w-]{24,}\b|"
                       r"(?i:(?:key|token|secret|password|auth)[\w-]*=\S+)")
PATHISH = re.compile(r"^[\w@.~/+-]+$")
READ_TOOLS = {"Read", "read", "read_file", "view", "open_file"}
SHELL_TOOLS = {"Bash", "bash", "exec_command", "shell", "local_shell", "run_terminal_cmd"}
READ_CMD = re.compile(r"(?:^|[;&|]\s*)(?:cat|head|tail|sed|less|bat|nl)((?:\s+[^\s;&|>]+)+)")


def read_targets(cmd: str) -> list[str]:
    """Files a cat/head/sed/tail command reads: its non-flag, non-number words."""
    out = []
    for m in READ_CMD.finditer(cmd):
        words = m.group(1).split()
        skip_next = False
        for w in words:
            if skip_next:
                skip_next = False
                continue
            if w in ("-n", "-c", "-e"):
                skip_next = True
                continue
            if w.startswith("-") or not PATHISH.match(w) or not ("/" in w or "." in w):
                continue
            out.append(w)
    return out


def repo_paths(root: str) -> list[str]:
    paths = [line[9:] for line in git(root, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")]
    # Other clones of the same project (another path on this machine) via --also=PATH.
    paths += [a.split("=", 1)[1] for a in sys.argv if a.startswith("--also=")]
    return sorted({os.path.realpath(p) for p in paths + [root]}, key=len, reverse=True)


def owner(cwd: str, roots: list[str]) -> str | None:
    cwd = os.path.realpath(cwd) if cwd else ""
    return next((r for r in roots if cwd == r or cwd.startswith(r + os.sep)), None)


def command_name(cmd: str) -> str:
    """The first two words of a command, with env assignments and secrets removed."""
    try:
        words = shlex.split(cmd, posix=True)
    except ValueError:
        words = cmd.split()
    # "cd x && pnpm test" is a pnpm command.
    segments, current = [], []
    for w in words:
        if w in ("&&", ";", "||", "|"):
            segments.append(current)
            current = []
        else:
            current.append(w)
    segments.append(current)
    words = next((seg for seg in segments if seg and seg[0] not in ("cd", "export", "set")), words)
    words = [w for w in words if not re.match(r"^[A-Z_][A-Z0-9_]*=", w)]
    out = " ".join(words[:2])
    return SECRETISH.sub("…", out)[:60]


def rel(path: str, roots: list[str]) -> str | None:
    if not path:
        return None
    p = path.strip("'\"")
    if not PATHISH.match(p):
        return None
    for r in roots:
        if p.startswith(r + os.sep):
            return p[len(r) + 1:]
    if os.path.isabs(p):
        return None  # outside the repo: not this project's cobweb
    while p.startswith("./"):
        p = p[2:]  # keep the dot of ".github/" and ".tatastu-sketches/"
    return p or None


def claude_sessions(roots: list[str], since: float):
    base = os.path.expanduser("~/.claude/projects")
    encoded = {re.sub(r"[^A-Za-z0-9]", "-", r): r for r in roots}
    for d in glob.glob(os.path.join(base, "*")):
        name = os.path.basename(d)
        root = next((r for e, r in encoded.items() if name == e or name.startswith(e + "-")), None)
        if not root:
            continue
        for f in glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True):
            if os.path.getmtime(f) >= since:
                yield "claude-code", f


def codex_sessions(roots: list[str], since: float):
    home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    for f in glob.glob(os.path.join(home, "sessions", "**", "*.jsonl"), recursive=True):
        if os.path.getmtime(f) < since:
            continue
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                first = json.loads(fh.readline() or "{}")
        except (OSError, ValueError):
            continue
        cwd = (first.get("payload") or {}).get("cwd", "")
        if owner(cwd, roots):
            yield "codex", f


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(text_of(c.get("text") or c.get("content") or "") if isinstance(c, dict) else str(c)
                         for c in content)
    return str(content or "")


def parse(kind: str, path: str):
    """Yield (call_id, tool, input dict) and ("result", call_id, text, is_error)."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if kind == "claude-code":
                for b in (o.get("message") or {}).get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use":
                        yield ("call", b.get("id"), b.get("name", "?"), b.get("input") or {})
                    elif b.get("type") == "tool_result":
                        yield ("result", b.get("tool_use_id"), text_of(b.get("content")), bool(b.get("is_error")))
            else:
                p = o.get("payload") or {}
                t = p.get("type")
                if t in ("function_call", "custom_tool_call"):
                    args = p.get("arguments") or p.get("input") or ""
                    try:
                        args = json.loads(args) if isinstance(args, str) and args.startswith("{") else {"input": args}
                    except ValueError:
                        args = {"input": args}
                    yield ("call", p.get("call_id"), p.get("name", "?"), args)
                elif t in ("function_call_output", "custom_tool_call_output"):
                    out = text_of(p.get("output"))
                    m = EXIT_CODE.search(out[:400])
                    yield ("result", p.get("call_id"), out, bool(m and m.group(1) != "0"))


def analyze(root: str, days: int) -> dict:
    roots = repo_paths(root)
    since = time.time() - days * 86400
    sessions = list(claude_sessions(roots, since)) + list(codex_sessions(roots, since))
    base = os.path.basename(root).lower()
    claude_dir = os.path.expanduser("~/.claude/projects")
    encoded = {re.sub(r"[^A-Za-z0-9]", "-", r) for r in roots}
    near = sorted(d for d in (os.listdir(claude_dir) if os.path.isdir(claude_dir) else [])
                  if base in d.lower() and not any(d == e or d.startswith(e + "-") for e in encoded))
    commits = int(git(root, "rev-list", "--count", f"--since={days}.days", "HEAD").strip() or 0)
    tools = Counter()
    max_per_session = Counter()
    errors = Counter()
    signatures: dict[str, Counter] = defaultdict(Counter)
    sig_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    rereads = Counter()
    steering_reads = Counter()
    repeated_cmds = Counter()
    calls_total = 0
    for kind, path in sessions:
        pending: dict[str, tuple[str, dict]] = {}
        per_tool = Counter()
        reads = Counter()
        cmds = Counter()
        for ev in parse(kind, path):
            if ev[0] == "call":
                _, cid, name, args = ev
                calls_total += 1
                tools[name] += 1
                per_tool[name] += 1
                pending[cid] = (name, args)
                target = None
                if name in READ_TOOLS:
                    target = rel(str(args.get("file_path") or args.get("path") or ""), roots)
                elif name in SHELL_TOOLS or "cmd" in args or "command" in args:
                    cmd = str(args.get("cmd") or args.get("command") or args.get("input") or "")
                    if cmd:
                        cmds[command_name(cmd)] += 1
                        for word in read_targets(cmd):
                            t = rel(word, roots)
                            if t:
                                reads[t] += 1
                if target:
                    reads[target] += 1
                continue
            _, cid, text, is_error = ev
            name, args = pending.pop(cid, ("?", {}))
            found = []
            for m in MISSING_CMD.finditer(text[:4000]):
                found.append(("command not found", m.group(1) or m.group(2)))
            for m in MISSING_SCRIPT.finditer(text[:4000]):
                found.append(("missing script", next(g for g in m.groups() if g)))
            for m in MISSING_MODULE.finditer(text[:4000]):
                mod = next(g for g in m.groups() if g)
                if os.path.isabs(mod):
                    mod = rel(mod, roots)
                if mod:
                    found.append(("missing module", mod))
            if is_error or "No such file" in text[:4000] or "does not exist" in text[:4000] or "ENOENT" in text[:4000]:
                for m in MISSING_PATH.finditer(text[:4000]):
                    p = rel(next((g for g in m.groups() if g), ""), roots)
                    if not p and name in READ_TOOLS:
                        p = rel(str(args.get("file_path") or args.get("path") or ""), roots)
                    if p:
                        found.append(("missing path", p))
            if EDIT_MISS.search(text[:600]):
                found.append(("edit text not found", name))
            if is_error:
                errors[name] += 1
            for sig, token in found:
                token = SECRETISH.sub("…", token)[:80]
                signatures[sig][token] += 1
                sig_sessions[(sig, token)].add(path)
        for name, n in per_tool.items():
            max_per_session[name] = max(max_per_session[name], n)
        for f, n in reads.items():
            if n >= 3:
                rereads[f] += n - 1
            if classify(f) in ("always", "scoped", "on-demand", "doc", "plan", "history"):
                steering_reads[f] += n
        for c, n in cmds.items():
            if n >= 4:
                repeated_cmds[c] += n

    return {
        "repo": root, "days": days, "worktrees_matched": len(roots),
        "scanned": [claude_dir, os.path.join(os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"), "sessions")],
        "near_miss_dirs": near[:10], "commits_in_window": commits,
        "not_read": "logs of other hosts (Tatastu/Pi, Cursor, Copilot, Gemini) are not read",
        "sessions": Counter(k for k, _ in sessions), "tool_calls": calls_total,
        "tool_errors": dict(errors.most_common(12)),
        "top_tools": [{"tool": t, "calls": n, "max_in_one_session": max_per_session[t]} for t, n in tools.most_common(15)],
        "stumbles": {sig: [{"what": tok, "times": n, "sessions": len(sig_sessions[(sig, tok)])}
                           for tok, n in c.most_common(15)] for sig, c in signatures.items()},
        "reread_files": [{"file": f, "extra_reads": n} for f, n in rereads.most_common(15)],
        "most_read_docs": [{"file": f, "reads": n} for f, n in steering_reads.most_common(15)],
        "repeated_commands": [{"command": c, "runs_in_sessions_with_4plus": n} for c, n in repeated_cmds.most_common(12)],
    }


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    days = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--days=")), "60"))
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    r = analyze(root, days)
    if emit_json(r):
        return
    s = r["sessions"]
    print(f"repo: {root}  last {days} days, {r['worktrees_matched']} worktree paths")
    print(f"sessions: {dict(s) or 'none found'}  tool calls: {r['tool_calls']}  "
          f"failed calls: {sum(r['tool_errors'].values())} {r['tool_errors']}")
    print(f"scanned: {', '.join(r['scanned'])}; {r['not_read']}")
    total = sum(s.values())
    if r["commits_in_window"] and total < max(5, r["commits_in_window"] // 20):
        print(f"  COVERAGE: {total} sessions for {r['commits_in_window']} commits in {days} days. Most agent work "
              "happened somewhere these logs don't cover; treat the counts below as a sample, not the picture.")
    if r["near_miss_dirs"]:
        print("  near-miss Claude log folders (another clone of this project? rerun with --also=<path>): "
              + ", ".join(r["near_miss_dirs"]))
    if not s:
        return
    print("most used tools (calls, most in one session):")
    for t in r["top_tools"][:10]:
        print(f"    {t['tool'][:40]:40} {t['calls']:6}  max {t['max_in_one_session']}")
    for sig, rows in r["stumbles"].items():
        print(f"{sig}:")
        for x in rows[:10]:
            print(f"    {x['times']:4}x in {x['sessions']:3} sessions  {x['what']}")
    if r["reread_files"]:
        print("files re-read 3+ times in one session (extra reads):")
        for x in r["reread_files"][:10]:
            print(f"    {x['extra_reads']:5}  {x['file']}")
    if r["most_read_docs"]:
        print("docs and instructions agents read most:")
        for x in r["most_read_docs"][:10]:
            print(f"    {x['reads']:5}  {x['file']}")
    if r["repeated_commands"]:
        print("commands run 4+ times in one session:")
        for x in r["repeated_commands"][:10]:
            print(f"    {x['runs_in_sessions_with_4plus']:5}  {x['command']}")


if __name__ == "__main__":
    main()
