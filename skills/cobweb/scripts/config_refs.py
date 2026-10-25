#!/usr/bin/env python3
"""Config entries that name paths the repository no longer has.

These break builds and CI, or quietly do nothing: a package.json script
running a deleted file, a CI step calling a removed script, a Dockerfile
COPY of a moved folder, a tsconfig include that matches nothing, an ignore
list entry for code that's gone, a CODEOWNERS line that owns nothing.
Read-only, stdlib only.

Usage: config_refs.py [repo] [--json]
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import FILE_EXTS, Repo, deleted_in, emit_json, git, is_vendored, vendored_roots  # noqa: E402

GLOB_CHARS = set("*?[{")
# A token in a shell command that names a file: has a known extension or starts with ./
CMD_PATH = re.compile(r"(?:(?<=\s)|^|(?<=[=\"']))(\.{0,2}/?[\w@.+-]+(?:/[\w@.+-]+)*\.(\w{1,6}))(?=$|[\s\"';|&)])")
RUNNERS = re.compile(r"\b(node|bun|tsx|ts-node|deno|python3?|uv run|bash|sh|zsh|ruby|go run|npx|bunx|pnpm exec|"
                     r"vite-node|esno|jiti|zx)\b")


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments outside strings, and trailing commas."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        ch = text[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
            out.append(ch)
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(ch)
        i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def load_json(path: str):
    try:
        return json.loads(strip_jsonc(open(path, encoding="utf-8", errors="replace").read()))
    except (OSError, ValueError):
        return None


class Checker:
    def __init__(self, root: str):
        self.root = root
        self.repo = Repo(root)
        self.findings: list[dict] = []
        self._ignored: dict[str, bool] = {}

    def ignored(self, path: str) -> bool:
        """Generated or local paths are absent on purpose (dist/, .env, build output)."""
        if path not in self._ignored:
            out = git(self.root, "check-ignore", "--no-index", "--stdin", stdin=f"{path}\n{path.rstrip('/')}/")
            self._ignored[path] = bool(out.strip())
        return self._ignored[path]

    def exists(self, base: str, raw: str) -> tuple[bool, str]:
        """Whether a path or glob (relative to base) matches anything tracked or ignored-by-design."""
        p = raw.strip().strip("\"'").lstrip("!")
        if not p or p.startswith(("$", "http", "~", "<", "{{")) or "${" in p:
            return True, p
        if p.startswith("/") and not os.path.exists(os.path.join(self.root, p.lstrip("/"))):
            # Absolute container paths (/app, /usr/src) are not repo paths.
            return True, p
        rel = posixpath.normpath(posixpath.join(base, p.lstrip("/"))) if not p.startswith("/") else p.lstrip("/")
        if rel.startswith(".."):
            return True, rel  # outside the repo: not this check's business
        if GLOB_CHARS & set(rel):
            pat = re.sub(r"\{([^}]*)\}", lambda m: "[" + "".join({w[:1] for w in m.group(1).split(",")}) + "]*", rel)
            pat = pat.rstrip("/")
            hit = any(fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(f, pat + "/*") or f.startswith(pat.split("*")[0])
                      and fnmatch.fnmatch(f, pat.replace("**/", "*")) for f in self.repo.files)
            return hit or self.ignored(rel.split("*")[0].rstrip("/") or "."), rel
        if self.repo.exists(rel.rstrip("/")) or self.ignored(rel):
            return True, rel
        # The file on disk but untracked (generated on install, e.g. .husky/_) is not "gone".
        return os.path.exists(os.path.join(self.root, rel)), rel

    def named_elsewhere(self, rel: str, source: str) -> bool:
        """A folder that code still writes to (a publisher's output dir, a cache) is a
        target, not a leftover: if its path appears in any non-markdown file other
        than the config itself, the entry is deliberate."""
        stem = re.split(r"/?[*?\[{]", rel, 1)[0].rstrip("/")
        parts = stem.split("/")
        probe = "/".join(parts[-2:]) if len(parts) >= 2 else stem
        if len(probe) < 6:
            return False
        out = git(self.root, "grep", "-l", "-I", "-F", "-e", probe, "--", ".", ":(exclude)*.md", f":(exclude){source}")
        return bool(out.strip())

    def check(self, source: str, line: int, field: str, base: str, raw: str, harm: str) -> None:
        ok, rel = self.exists(base, raw)
        if ok or self.named_elsewhere(rel, source):
            return
        when = deleted_in(self.repo, re.split(r"/?[*?\[{]", rel, 1)[0].rstrip("/"))
        self.findings.append({"file": source, "line": line, "field": field, "ref": raw.strip(),
                              "resolved": rel, "harm": harm,
                              "status": f"deleted in {when}" if when else "missing"})


def line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return text.count("\n", 0, i) + 1 if i >= 0 else 0


def scan(root: str) -> dict:
    c = Checker(root)
    extra = vendored_roots(root)
    files = [f for f in c.repo.files if not is_vendored(f, extra)]
    for f in files:
        base_dir = posixpath.dirname(f)
        name = posixpath.basename(f)
        full = os.path.join(root, f)
        try:
            text = open(full, encoding="utf-8", errors="replace").read()
        except OSError:
            continue

        if name == "package.json":
            data = load_json(full) or {}
            for script, cmd in (data.get("scripts") or {}).items():
                if not isinstance(cmd, str) or not RUNNERS.search(cmd):
                    continue
                for m in CMD_PATH.finditer(cmd):
                    if m.group(2).lower() in FILE_EXTS and "/" in m.group(1):
                        c.check(f, line_of(text, f'"{script}"'), f"scripts.{script}", base_dir, m.group(1),
                                "the script fails when run")
            for key in ("main", "module", "types", "typings", "bin"):
                v = data.get(key)
                for target in ([v] if isinstance(v, str) else list(v.values()) if isinstance(v, dict) else []):
                    # Entry points usually name build output; only check source-looking ones.
                    # "expo-router/entry" is a package specifier, not a path: require ./ or an extension.
                    if isinstance(target, str) and not re.search(r"(^|/)(dist|build|out|lib|cjs|esm)/", target) \
                            and (target.startswith(".") or re.search(r"\.\w{1,5}$", target)):
                        c.check(f, line_of(text, f'"{key}"'), key, base_dir, target, "imports of the package fail")

        elif f.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
            for i, line in enumerate(text.splitlines(), 1):
                m = re.match(r"\s*-?\s*uses:\s*(\./[^\s@#]+)", line)
                if m:
                    c.check(f, i, "uses", "", m.group(1), "the workflow fails to start")
                m = re.match(r"\s*working-directory:\s*['\"]?([^'\"\s$]+)", line)
                if m:
                    c.check(f, i, "working-directory", "", m.group(1), "the step fails")
                if re.match(r"\s*-?\s*(run:|[\w-]+\s*$)", line) or line.strip().startswith(("node ", "bun ", "bash ")):
                    body = line.split("run:", 1)[-1]
                    if RUNNERS.search(body):
                        for m in CMD_PATH.finditer(body):
                            if m.group(2).lower() in FILE_EXTS and "/" in m.group(1):
                                c.check(f, i, "run", "", m.group(1), "the step fails")
            for m in re.finditer(r"^\s*paths(?:-ignore)?:\s*\n((?:\s*-\s*.+\n)+)", text, re.M):
                for pm in re.finditer(r"-\s*['\"]?([^'\"\n]+)", m.group(1)):
                    c.check(f, line_of(text, pm.group(1)), "on.paths", "", pm.group(1),
                            "the trigger never fires for this entry")

        elif name.startswith("Dockerfile") or name.endswith(".dockerfile"):
            for i, line in enumerate(text.splitlines(), 1):
                m = re.match(r"\s*(COPY|ADD)\s+(?!--from)(?:--\S+\s+)*(.+)", line, re.I)
                if not m:
                    continue
                parts = m.group(2).split()
                for src in parts[:-1]:
                    if src.startswith("--") or src in (".", "./") or src.startswith(("http", "[")):
                        continue
                    # The build context is usually the Dockerfile's folder or the repo root.
                    if not c.exists(base_dir, src)[0]:
                        c.check(f, i, m.group(1).upper(), "", src, "the image build fails")

        elif re.fullmatch(r"tsconfig.*\.json|jsconfig\.json", name):
            data = load_json(full) or {}
            for key in ("include", "files"):
                for v in data.get(key) or []:
                    c.check(f, line_of(text, v), key, base_dir, v, "type checking silently skips it")
            for ref in data.get("references") or []:
                if isinstance(ref, dict) and ref.get("path"):
                    c.check(f, line_of(text, ref["path"]), "references", base_dir, ref["path"], "tsc -b fails")
            ext = data.get("extends")
            for e in ([ext] if isinstance(ext, str) else ext or []):
                if e.startswith("."):
                    c.check(f, line_of(text, e), "extends", base_dir, e, "every type check fails")
            for alias, targets in ((data.get("compilerOptions") or {}).get("paths") or {}).items():
                for t in targets:
                    c.check(f, line_of(text, t), f"paths.{alias}", posixpath.join(base_dir,
                            (data.get("compilerOptions") or {}).get("baseUrl", ".")), t, "imports through the alias fail")

        elif re.fullmatch(r"knip\.jsonc?|\.knip\.jsonc?", name):
            data = load_json(full) or {}
            # Workspace entries are relative to the workspace folder; "x!" marks production entries.
            blocks = [(base_dir, data)] + [(posixpath.join(base_dir, ws), b) for ws, b in
                                           (data.get("workspaces") or {}).items() if isinstance(b, dict)]
            for b_dir, b in blocks:
                if GLOB_CHARS & set(b_dir):
                    continue
                for key in ("entry", "project", "ignore", "ignoreFiles"):
                    vals = b.get(key) or []
                    for v in [vals] if isinstance(vals, str) else vals:
                        if not isinstance(v, str):
                            continue
                        c.check(f, line_of(text, v), key, b_dir, v.rstrip("!"),
                                "the dead-code check analyses less than it claims" if key in ("entry", "project")
                                else "a stale exemption: it hides nothing now")

        elif name == "CODEOWNERS":
            for i, line in enumerate(text.splitlines(), 1):
                if line.strip() and not line.lstrip().startswith("#"):
                    pat = line.split()[0]
                    if pat == "*":
                        continue
                    probe = pat.lstrip("/")
                    probe = probe + "**" if probe.endswith("/") else probe
                    c.check(f, i, "owners", "", probe if "/" in pat or "*" in pat else "**/" + pat,
                            "nobody is asked to review it; the rule owns nothing")

        elif f == ".github/dependabot.yml" or f == ".github/dependabot.yaml":
            for i, line in enumerate(text.splitlines(), 1):
                m = re.match(r"\s*-?\s*directory:\s*['\"]?([^'\"\s#]+)", line)
                if m and m.group(1) != "/":
                    c.check(f, i, "directory", "", m.group(1).lstrip("/"), "dependency updates stop for it")

        elif re.fullmatch(r"wrangler\.(toml|jsonc?)", name):
            m = re.search(r'^\s*"?main"?\s*[=:]\s*"([^"]+)"', text, re.M)
            if m:
                c.check(f, line_of(text, m.group(0)), "main", base_dir, m.group(1), "deploys fail")

        elif re.search(r"(^|/)[\w.-]*\.config\.(m?[jt]s|c[jt]s)$", f) or name in ("eslint.config.js", "Gruntfile.js"):
            # vitest coverage lists, playwright test dirs, vite aliases: string literals
            # that name a file. Only report what git shows was deleted, since config
            # strings also hold globs, URLs and generated output.
            for i, line in enumerate(text.splitlines(), 1):
                if line.lstrip().startswith(("//", "*", "/*")):
                    continue
                for m in re.finditer(r"[\"'`](\.{0,2}/?[\w@.+-]+(?:/[\w@.+-]+)+\.(\w{1,6}))[\"'`]", line):
                    if m.group(2).lower() not in FILE_EXTS or GLOB_CHARS & set(m.group(1)):
                        continue
                    ok, rel = c.exists(base_dir, m.group(1))
                    if ok or c.exists("", m.group(1))[0]:
                        continue
                    when = deleted_in(c.repo, rel.rstrip("/"))
                    if when:
                        c.findings.append({"file": f, "line": i, "field": "string", "ref": m.group(1),
                                           "resolved": rel, "harm": "the config points at a deleted file",
                                           "status": f"deleted in {when}"})

        elif re.fullmatch(r"biome\.jsonc?", name):
            data = load_json(full) or {}
            fl = data.get("files") or {}
            for key in ("include", "ignore", "includes"):
                for v in fl.get(key) or []:
                    if isinstance(v, str) and not v.startswith("!") and "*" not in v:
                        c.check(f, line_of(text, v), f"files.{key}", base_dir, v, "a stale lint scope entry")

    by_file = Counter(x["file"] for x in c.findings)
    return {"repo": root, "findings": c.findings, "by_file": dict(by_file.most_common())}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    r = scan(root)
    if emit_json(r):
        return
    print(f"repo: {root}\nconfig entries naming paths that are gone: {len(r['findings'])}")
    order = {"the image build fails": 0, "the workflow fails to start": 0, "the step fails": 0,
             "the script fails when run": 1, "every type check fails": 1, "deploys fail": 1, "tsc -b fails": 1}
    for x in sorted(r["findings"], key=lambda x: (order.get(x["harm"], 5), x["file"], x["line"])):
        print(f"  {x['file']}:{x['line']}  {x['field']} `{x['ref']}`  {x['status']}  -> {x['harm']}")


if __name__ == "__main__":
    main()
