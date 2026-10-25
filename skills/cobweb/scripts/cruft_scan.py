#!/usr/bin/env python3
"""Find the clutter long AI-assisted projects accumulate. Stdlib only; read-only.

Every result is a candidate. Read it before calling it stale.

Usage: cruft_scan.py [repo] [--json] [--only=section,section]
Sections: parallel, scratch, ignored, build_output, lockfiles, versions, plan_sprawl,
          dated_piles, escape_hatches, todos, commented_code, model_ids, env_vars,
          orphan_docs, orphan_assets, large_files
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import sys
import time
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import (Repo, emit_json, classify, extract, git, is_path_claim,  # noqa: E402
                           is_vendored, resolve, vendored_roots)

CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".py", ".go", ".rs", ".rb",
            ".php", ".java", ".kt", ".kts", ".scala", ".swift", ".m", ".mm", ".c", ".cc", ".cpp", ".h",
            ".hpp", ".cs", ".fs", ".dart", ".ex", ".exs", ".vue", ".svelte", ".astro", ".lua", ".sh"}
DOC_EXT = {".md", ".mdx", ".mdc", ".rst", ".txt"}
ASSET_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mov", ".webm", ".pdf", ".avif"}
TESTISH = re.compile(r"(^|/)(tests?|__tests__|spec|specs|e2e|fixtures?|__mocks__|testdata)/|"
                     r"[._-](test|spec|stories)\.[a-z]+$")

PARALLEL = re.compile(
    r"^(?P<stem>.+?)(?P<tag>[-_. ](v\d{1,2}|new|old|legacy|deprecated|backup|bak|orig|copy|final|tmp|temp|"
    r"wip|alt|2|3)| \d| copy( \d+)?)(?P<ext>\.[A-Za-z0-9]+)$", re.I)
SCRATCH = re.compile(
    r"(\.(bak|orig|rej|swp|swo|tmp|temp|old|log)$|~$|(^|/)\.DS_Store$|(^|/)Thumbs\.db$|"
    r"(^|/)tmpclaude[^/]*|(^|/)\.tmp[^/]*/|(^|/)(scratch|tmp|temp)/|(^|/)untitled[^/]*$|"
    r"(^|/)nohup\.out$|\.(pyc|pyo)$|(^|/)__pycache__/)", re.I)
TRACKED_ENV = re.compile(r"(^|/)\.env(\.(local|development|production|staging|test))?$")
BUILD_OUTPUT = re.compile(r"(^|/)(dist|\.next|\.nuxt|\.svelte-kit|\.turbo|coverage|\.nyc_output|"
                          r"node_modules|\.parcel-cache|\.vite|storybook-static|out|target/(debug|release))/")
LOCKFILES = {"package-lock.json": "npm", "npm-shrinkwrap.json": "npm", "yarn.lock": "yarn",
             "pnpm-lock.yaml": "pnpm", "bun.lock": "bun", "bun.lockb": "bun",
             "poetry.lock": "poetry", "uv.lock": "uv", "Pipfile.lock": "pipenv", "pdm.lock": "pdm"}
STANDARD_ROOT_MD = {"readme", "changelog", "license", "licence", "contributing", "security", "code_of_conduct",
                    "agents", "claude", "gemini", "architecture", "support", "governance", "authors",
                    "notice", "conventions", "codeowners", "history", "releasing", "maintainers"}
SESSION_DOC = re.compile(
    r"(^|/)([^/]*[-_ ])?(plan|todo|notes?|handoff|summary|status|progress|wip|scratch|brainstorm|"
    r"implementation|fix|fixes|report|findings|analysis|next[-_ ]steps|session|tasks?|checklist|"
    r"audit|review|retro|postmortem)([-_ ][^/]*)?\.(md|txt)$", re.I)
ROOT_LOOSE_EXT = {".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".mov", ".mp4",
                  ".log", ".csv", ".txt", ".bak", ".tmp", ".patch", ".diff"}
DATED = re.compile(r"(19|20)\d\d[-_]?[01]\d[-_]?[0-3]\d")

ESCAPES = {
    "ts-ignore": r"@ts-ignore|@ts-nocheck",
    "ts-expect-error": r"@ts-expect-error",
    "as-any": r"as any\b|: any\b|<any>",
    "eslint-disable": r"eslint-disable",
    "biome/oxlint-ignore": r"biome-ignore|oxlint-disable",
    "noqa/type-ignore": r"# ?noqa|# ?type: ?ignore|# ?pyright: ?ignore|# ?pragma: no cover",
    "nolint": r"//nolint|//lint:ignore",
    "rust-allow": r"#\[allow\(",
    "suppress-warnings": r"@SuppressWarnings|@Suppress\(|swiftlint:disable|rubocop:disable|phpcs:ignore",
    "skipped-tests": r"\b(it|test|describe)\.(skip|todo)\(|\bx(it|describe)\(|@pytest\.mark\.skip|"
                     r"\bt\.Skip\(|#\[ignore\]|@Disabled|@Ignore\b|\bskip\(\s*['\"]",
    "empty-catch": r"catch\s*(\([^)]*\))?\s*\{\s*\}|\.catch\(\s*\(\s*\)\s*=>\s*\{?\s*\}?\s*\)|except[^:]*:\s*pass\b",
}
MODEL_ID = re.compile(
    r"(?<![\w.-])("
    r"claude-(?:\d(?:[-.]\d)?-)?(?:opus|sonnet|haiku|fable|instant)(?:-\d+(?:[-.]\d+)*)?(?:-\d{8})?(?:-latest)?"
    r"|claude-\d(?:\.\d)?(?:-\d{8})?"
    r"|gpt-\d(?:\.\d+)?(?:o)?(?:-[a-z]+)*(?:-\d{4}-\d{2}-\d{2})?"
    r"|o[1-9](?:-(?:mini|pro|preview))+"
    r"|gemini-\d(?:\.\d+)?-(?:pro|flash|ultra|nano)(?:-[a-z0-9]+)*"
    r"|grok-\d(?:\.\d)?(?:-[a-z]+)*|(?:mistral|codestral|devstral)-[a-z0-9.-]+|llama-?\d(?:\.\d)?[a-z0-9.-]*"
    r"|deepseek-[a-z0-9.-]+|qwen\d(?:\.\d)?[a-z0-9.-]*"
    r")(?![\w])", re.I)
ENV_USE = re.compile(
    r"process\.env\.([A-Z][A-Z0-9_]{2,})|process\.env\[['\"]([A-Z][A-Z0-9_]{2,})['\"]\]|"
    r"import\.meta\.env\.([A-Z][A-Z0-9_]{2,})|Bun\.env\.([A-Z][A-Z0-9_]{2,})|Deno\.env\.get\(['\"]([A-Z][A-Z0-9_]{2,})|"
    r"os\.environ(?:\.get)?[\[(]['\"]([A-Z][A-Z0-9_]{2,})|os\.getenv\(['\"]([A-Z][A-Z0-9_]{2,})|"
    r"os\.Getenv\(\"([A-Z][A-Z0-9_]{2,})|env::var\(\"([A-Z][A-Z0-9_]{2,})|ENV\[['\"]([A-Z][A-Z0-9_]{2,})|"
    r"getenv\(['\"]([A-Z][A-Z0-9_]{2,})|env\(['\"]([A-Z][A-Z0-9_]{2,})")
ENV_DECL = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})\s*=", re.M)
# Variables every platform sets; never "undocumented".
PLATFORM_ENV = re.compile(r"^(NODE_ENV|CI|HOME|PATH|PWD|USER|SHELL|TERM|TMPDIR|LANG|TZ|PORT|HOST|DEBUG|"
                          r"GITHUB_\w+|RUNNER_\w+|VERCEL\w*|NETLIFY\w*|RAILWAY_\w+|CF_\w+|npm_\w+|"
                          r"XDG_\w+|APPDATA|LOCALAPPDATA|USERPROFILE|NEXT_RUNTIME|VITE_USER_NODE_ENV|"
                          r"MODE|DEV|PROD|SSR|BASE_URL|JEST_WORKER_ID|VITEST\w*|PYTEST_\w+|FORCE_COLOR|"
                          r"NO_COLOR|EDITOR|VISUAL|PAGER|LOGNAME|HOSTNAME|SystemRoot|ComSpec|COMSPEC|LC_\w+|GIT_\w+|SSH_\w+|"
                          r"TERM_PROGRAM\w*|COLORTERM|SHLVL|ProgramFiles\w*|WINDIR|SYSTEMROOT|TEMP|TMP)$")


def own_files(root: str) -> list[str]:
    extra = vendored_roots(root)
    return [f for f in git(root, "ls-files").splitlines() if f and not is_vendored(f, extra)]


def is_history(path: str) -> bool:
    """Archived or dated records: expected to be old and unlinked."""
    return classify(path) == "history"


GENERATED = re.compile(r"(\.patch|\.diff|\.min\.js|\.generated\.\w+|worker-configuration\.d\.ts|\.snap)$|"
                       r"(^|/)(generated|__generated__|gen)/")


def ext(path: str) -> str:
    return os.path.splitext(path)[1].lower()


_TOUCHED: dict[str, dict[str, str]] = {}


def last_touch(root: str, paths: list[str]) -> dict[str, str]:
    """Last commit date per path. One full log walk per repo, cached: git log with
    hundreds of pathspecs is far slower than reading the whole history once."""
    if root not in _TOUCHED:
        table: dict[str, str] = {}
        date = ""
        for line in git(root, "log", "--format=@%as", "--name-only", "--no-renames").splitlines():
            if line.startswith("@"):
                date = line[1:]
            elif line and line not in table:
                table[line] = date
        _TOUCHED[root] = table
    table = _TOUCHED[root]
    return {p: table[p] for p in paths if p in table}
    date = ""
    args = ["log", "--format=@%as", "--name-only", "--no-renames"]
    if len(paths) <= 300:
        args += ["--", *paths]
    for line in git(root, *args).splitlines():
        if len(out) == len(want):
            break
        if line.startswith("@"):
            date = line[1:]
        elif line in want and line not in out:
            out[line] = date
    return out


def section_parallel(root: str, files: list[str]) -> list[dict]:
    present = set(files)
    hits = []
    for f in files:
        if ext(f) not in CODE_EXT | DOC_EXT | {".json", ".yaml", ".yml", ".css", ".scss", ".html", ".sql"}:
            continue
        d, base = os.path.split(f)
        m = PARALLEL.match(base)
        if not m or DATED.search(base) or is_history(f):
            continue  # "2026-08-11-2.md" is a second record, not a second implementation
        sibling = os.path.join(d, m.group("stem") + m.group("ext"))
        if sibling in present:
            hits.append({"file": f, "sibling": sibling})
    # Who imports or names each side: both referenced means two live copies;
    # one side unreferenced means a leftover.
    stems = {os.path.splitext(os.path.basename(x))[0] for h in hits for x in (h["file"], h["sibling"])}
    seen = mentions(root, stems)
    for h in hits:
        for key in ("file", "sibling"):
            stem = os.path.splitext(os.path.basename(h[key]))[0]
            h[f"{key}_refs"] = len(seen.get(stem, set()) - {h["file"], h["sibling"]})
    return hits


def section_scratch(root: str, files: list[str]) -> list[dict]:
    hits = [{"file": f, "why": "scratch/backup"} for f in files if SCRATCH.search(f)]
    hits += [{"file": f, "why": "tracked env file: may hold secrets"} for f in files if TRACKED_ENV.search(f)]
    return hits


def section_ignored(root: str, files: list[str]) -> dict:
    """Tracked files an ignore rule matches. Only the repo's own .gitignore
    states the project's intent; .git/info/exclude and global excludes are
    this machine's."""
    paths = [f for f in git(root, "ls-files", "-ci", "--exclude-standard").splitlines() if f]
    repo_rule: list[str] = []
    local = Counter()
    if paths:
        out = git(root, "check-ignore", "-v", "--no-index", "--stdin", stdin="\n".join(paths))
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            source = meta.split(":", 1)[0]
            if source.endswith(".gitignore") and not os.path.isabs(source):
                added = git(root, "log", "--diff-filter=A", "-1", "--format=%h %as %s", "--", path).strip()
                repo_rule.append(f"{path}  ({meta}; added {added[:80] or '?'})")
            else:
                local[source] += 1
    return {"by_repo_gitignore": repo_rule, "by_local_excludes": dict(local)}


def section_build_output(root: str, files: list[str]) -> list[dict]:
    groups = Counter()
    for f in files:
        m = BUILD_OUTPUT.search(f)
        if m:
            groups[f[:m.end()]] += 1
    maps = Counter(os.path.dirname(f) for f in files if f.endswith((".js.map", ".css.map", ".min.js")))
    out = [{"dir": d, "files": n} for d, n in groups.most_common(20)]
    out += [{"dir": d, "files": n, "why": "source maps or minified files"} for d, n in maps.most_common(5) if n >= 3]
    return out


def section_lockfiles(root: str, files: list[str]) -> list[dict]:
    by_dir: dict[str, set[str]] = defaultdict(set)
    for f in files:
        pm = LOCKFILES.get(os.path.basename(f))
        if pm:
            by_dir[os.path.dirname(f) or "."].add(pm)
    out = []
    for d, pms in sorted(by_dir.items()):
        js = {p for p in pms if p in ("npm", "yarn", "pnpm", "bun")}
        py = pms - js
        if len(js) > 1 or len(py) > 1:
            out.append({"dir": d, "managers": sorted(pms), "why": "two package managers in one directory"})
    # packageManager field disagreeing with the lockfile next to it
    for f in files:
        if os.path.basename(f) != "package.json":
            continue
        try:
            pm_field = json.load(open(os.path.join(root, f), encoding="utf-8")).get("packageManager", "")
        except (OSError, ValueError):
            continue
        d = os.path.dirname(f) or "."
        name = pm_field.split("@", 1)[0] if pm_field else ""
        locks = {p for p in by_dir.get(d, set()) if p in ("npm", "yarn", "pnpm", "bun")}
        if name and locks and name not in locks:
            out.append({"dir": d, "managers": sorted(locks), "why": f"packageManager says {pm_field}"})
    all_js = sorted({p for v in by_dir.values() for p in v if p in ("npm", "yarn", "pnpm", "bun")})
    if len(all_js) > 1:
        out.append({"dir": "(repo)", "managers": all_js,
                    "why": "several JS package managers across the repo; check each is intended"})
    return out


def section_versions(root: str, files: list[str]) -> list[dict]:
    """Runtime pins that disagree: .nvmrc, .node-version, .tool-versions, engines, CI, Docker."""
    pins: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add(runtime: str, value: str, where: str) -> None:
        major = re.search(r"\d+", value or "")
        if major:
            # ">=24" or "^24 || ^26" is a range: it agrees with any pin it admits.
            op = "min" if re.match(r"\s*(>=|>|\^|~)", value or "") or "||" in (value or "") else "pin"
            pins[runtime].append((major.group(0), where, op))

    for f in files:
        base = os.path.basename(f)
        full = os.path.join(root, f)
        try:
            if base in (".nvmrc", ".node-version"):
                add("node", open(full).read().strip(), f)
            elif base == ".python-version":
                add("python", open(full).read().strip(), f)
            elif base in (".tool-versions", "mise.toml", ".mise.toml"):
                for line in open(full):
                    m = re.match(r"\s*(nodejs|node|python|ruby|golang|go|bun)\s*[= ]\s*\"?([\d.]+)", line)
                    if m:
                        add({"nodejs": "node", "golang": "go"}.get(m.group(1), m.group(1)), m.group(2), f)
            elif base == "package.json" and f.count("/") <= 1:
                eng = (json.load(open(full, encoding="utf-8")).get("engines") or {})
                if eng.get("node"):
                    add("node", eng["node"], f + " engines")
            elif f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml")):
                for m in re.finditer(r"(node|python|go|bun)-version:\s*['\"]?([\d.x]+)", open(full).read()):
                    add(m.group(1), m.group(2), f)
            elif base.startswith("Dockerfile"):
                for m in re.finditer(r"^FROM\s+(node|python|golang|oven/bun):(\d+)", open(full).read(), re.M):
                    add({"golang": "go", "oven/bun": "bun"}.get(m.group(1), m.group(1)), m.group(2), f)
        except (OSError, ValueError):
            continue
    out = []
    for runtime, vals in pins.items():
        exact = {int(v) for v, _, op in vals if op == "pin"}
        floors = [int(v) for v, _, op in vals if op == "min"]
        conflict = len(exact) > 1 or any(e < f for e in exact for f in floors)
        if conflict:
            out.append({"runtime": runtime, "pins": [f"{v}{'+' if op == 'min' else ''} ({w})" for v, w, op in vals]})
    return out


def section_plan_sprawl(root: str, files: list[str]) -> dict:
    root_md = [f for f in files if "/" not in f and ext(f) in DOC_EXT
               and os.path.splitext(f)[0].lower() not in STANDARD_ROOT_MD]
    session = [f for f in files if SESSION_DOC.search(f) and not is_history(f)]
    # Loose files at the root that nothing names: mockups, screenshots, exports.
    loose = [f for f in files if "/" not in f and ext(f) in ROOT_LOOSE_EXT]
    seen = mentions(root, set(loose))
    root_loose = [f for f in loose if not seen.get(f, set()) - {f}]
    touched = last_touch(root, sorted(set(root_md + session + root_loose)))
    fmt = lambda fs: [{"file": f, "last_commit": touched.get(f, "?")} for f in sorted(fs, key=lambda x: touched.get(x, ""))]
    return {"root_markdown": fmt(root_md), "root_unreferenced_files": fmt(root_loose),
            "session_docs": fmt(session)[:60], "session_docs_total": len(session)}


UNBUILT = re.compile(r"(?i)\b(not (yet )?(started|implemented|built)|planning proposal|status:\s*\**\s*"
                     r"(plan|draft|proposed|proposal|open|todo|wip|in progress)\b|this (is a|plan) (proposal|plan))")
BANNER = re.compile(r"(?i)\b(archived|superseded|shipped|built|implemented|done|complete[d]?|historical|retired)\b")


CHECKBOX = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+(.*)$")
BACKTICK = re.compile(r"`([^`\s]+)`")
_REPO: dict[str, Repo] = {}


def repo_for(root: str) -> Repo:
    if root not in _REPO:
        _REPO[root] = Repo(root)
    return _REPO[root]


def days_since(date: str) -> int:
    try:
        return int((time.time() - time.mktime(time.strptime(date, "%Y-%m-%d"))) / 86400)
    except (ValueError, TypeError):
        return -1


def section_plan_checkboxes(root: str, files: list[str]) -> list[dict]:
    """Task lists that say done but stay in the active folder, and open tasks
    whose named files already exist (probably shipped and never ticked)."""
    repo = repo_for(root)
    rows = []
    for f in files:
        if ext(f) not in DOC_EXT or is_history(f):
            continue
        try:
            lines = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        if not (classify(f) == "plan" or SESSION_DOC.search(f) or TOOL_PLAN_DIRS.search(f)):
            continue  # templates and standing checklists are not task lists
        word = banner_word(lines)
        if word and word not in DONE_WORDS:
            continue  # parked, iceboxed or archived on purpose
        done = open_ = open_shipped = 0
        for line in lines:
            m = CHECKBOX.match(line)
            if not m:
                continue
            if m.group(1) in "xX":
                done += 1
                continue
            open_ += 1
            paths = [t for t in BACKTICK.findall(m.group(2)) if is_path_claim(t, repo)]
            if paths and all(resolve(t, f, repo)[0] == "ok" for t in paths):
                open_shipped += 1
        if done + open_ < 3:
            continue
        rows.append({"doc": f, "done": done, "open": open_, "open_naming_existing_files": open_shipped,
                     "marked_done": word in DONE_WORDS})
    touched = last_touch(root, [r["doc"] for r in rows])
    out = []
    for r in rows:
        r["last_commit"] = touched.get(r["doc"], "?")
        age = days_since(r["last_commit"])
        if r["open"] == 0 or r["marked_done"]:
            if age >= 0 and age < 14:
                continue  # just finished; give the archive step a chance
            r["finding"] = ("every task done, still in an active folder" if r["open"] == 0 else
                            f"marked done with {r['open']} tasks still open, in an active folder")
        elif r["open_naming_existing_files"] >= max(2, r["open"] // 3):
            r["finding"] = "open tasks name files that already exist: shipped and never ticked?"
        elif age > 60:
            r["finding"] = f"open tasks, untouched {age} days: stalled or shipped untracked?"
        else:
            continue
        out.append(r)
    rank = {"e": 0, "o": 1}
    return sorted(out, key=lambda r: (rank.get(r["finding"][0], 2), -r["open_naming_existing_files"], r["last_commit"]))


# A doc claiming authority over the reader, not a technical "the server is authoritative".
CLAIM = re.compile(r"(?i)\b(source of truth|single source|authoritative (?:doc|document|source|reference|spec|plan|"
                   r"version|guide)|canonical (?:doc|reference|spec|source|plan)|read (?:this|me) first|start here|"
                   r"this (?:doc|document|file|plan|spec) is the (?:current|canonical|plan|spec|reference|working)|"
                   r"working spec|must be followed)\b")
STATUS_BANNER = re.compile(r"(?i)\b(archived?|superseded|historical|deprecated|obsolete|outdated|stale|retired|"
                           r"no longer (?:current|accurate|maintained)|replaced by|frozen|snapshot|parked|iceboxed|"
                           r"dormant|not available work)\b")
DONE_STATUS = re.compile(r"(?i)^\W*(?:status|state)\W*:\W*(done|shipped|complete|completed|implemented)\b")


DONE_WORDS = {"done", "shipped", "complete", "completed", "implemented"}


def banner_word(lines: list[str]) -> str | None:
    """The status a doc declares near the top (frontmatter, a status line, or a
    bold blockquote banner like > **ICEBOXED**), lowercased; None if it declares none."""
    head = [l for l in lines if l.strip()][:10]
    for l in head:
        d = DONE_STATUS.match(l)
        if d:
            return d.group(1).lower()
        if re.match(r"^>\s*\*\*[A-Z][A-Z ]{3,}", l):
            return "banner"
        m = STATUS_BANNER.search(l)
        if m:
            return m.group(1).lower()
    return None


def has_status_banner(lines: list[str]) -> bool:
    return banner_word(lines) is not None
ORIENTATION = re.compile(r"(?i)^(readme|contributing|architecture)\.md$|(^|/)docs/(readme|index)\.md$")


def orientation_reachable(root: str, files: list[str]) -> set[str]:
    """Docs an agent reaches by following links from the always-loaded files and
    the README, two hops deep. Everything else is found only by search."""
    repo = repo_for(root)
    start = [f for f in files if classify(f) in ("always", "scoped") or ORIENTATION.search(f)]
    seen, frontier = set(start), list(start)
    for _ in range(2):
        nxt = []
        for f in frontier:
            try:
                text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for _, rtype, tok in extract(text, "doc"):
                if rtype not in ("link", "path", "import"):
                    continue
                for base in (posixpath.dirname(f), ""):
                    target = posixpath.normpath(posixpath.join(base, tok.split("#", 1)[0]))
                    if target in repo.tracked and target not in seen:
                        seen.add(target)
                        nxt.append(target)
                        break
        frontier = nxt
    return seen


def section_authority_claims(root: str, files: list[str]) -> list[dict]:
    """Docs that call themselves the source of truth while nothing marks them
    current: retrieval finds them by meaning and strips the folder that says old."""
    reach = orientation_reachable(root, files)
    hits = []
    for f in files:
        kind = classify(f)
        if kind not in ("doc", "plan", "history", "spec") or ORIENTATION.search(f):
            continue
        try:
            head = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()[:60]
        except OSError:
            continue
        # A record mentions "the source of truth" in passing; a claim sits in its opening lines.
        window = head[:15] if kind == "history" else head
        claim = next(((i + 1, m.group(0)) for i, line in enumerate(window) if (m := CLAIM.search(line))), None)
        if not claim:
            continue
        banner = has_status_banner(head)
        hits.append({"doc": f, "line": claim[0], "claims": claim[1], "class": kind, "banner": banner,
                     "linked_from_orientation": f in reach})
    touched = last_touch(root, [h["doc"] for h in hits])
    out = []
    for h in hits:
        h["last_commit"] = touched.get(h["doc"], "?")
        age = days_since(h["last_commit"])
        if h["banner"] or kind == "spec" and h["linked_from_orientation"]:
            continue
        if h["class"] == "history" or (not h["linked_from_orientation"] and age > 60) or (h["class"] == "plan" and age > 60):
            out.append(h)
    return sorted(out, key=lambda h: (h["class"] != "history", h["last_commit"]))


TOOL_PLAN_DIRS = re.compile(r"(^|/)(\.tatastu/plans|\.claude/plans|\.cursor/plans|\.codex/plans|\.kiro/specs|"
                            r"\.windsurf/plans|plans|\.plans)(/|$)")


def section_stale_plan_dirs(root: str, files: list[str]) -> list[dict]:
    """Folders of plans, mostly untouched for 45+ days and not marked as history."""
    groups: dict[str, list[str]] = defaultdict(list)
    for f in files:
        if ext(f) not in DOC_EXT or is_history(f):
            continue
        if classify(f) == "plan" or SESSION_DOC.search(f) or TOOL_PLAN_DIRS.search(f):
            try:
                head = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()[:8]
            except OSError:
                continue
            word = banner_word(head)
            if not word or word in DONE_WORDS:
                groups[os.path.dirname(f) or "."].append(f)
    groups = {d: fs for d, fs in groups.items() if len(fs) >= 3}
    touched = last_touch(root, [f for fs in groups.values() for f in fs])
    out = []
    for d, fs in groups.items():
        ages = [days_since(touched.get(f, "")) for f in fs]
        old = sum(1 for a in ages if a > 45)
        if old >= 0.75 * len(fs):
            out.append({"dir": d, "files": len(fs), "untouched_45d": old,
                        "newest": max((touched.get(f, "") for f in fs), default="?"),
                        "tool_folder": bool(TOOL_PLAN_DIRS.search(d + "/"))})
    return sorted(out, key=lambda x: (not x["tool_folder"], -x["files"]))[:25]


def section_plan_status(root: str, files: list[str]) -> list[dict]:
    """Plans whose header still says unbuilt while code for their topic exists.
    The person or agent decides; this only lines the two up."""
    code_by_stem: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for f in files:
        if ext(f) in CODE_EXT and not TESTISH.search(f):
            for word in re.split(r"[-_.]", os.path.splitext(os.path.basename(f))[0].lower()):
                if len(word) >= 5:
                    code_by_stem[word].append(f)
    out = []
    for f in files:
        if ext(f) not in DOC_EXT or is_history(f):
            continue
        try:
            head = "\n".join(open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()[:15])
        except OSError:
            continue
        m = UNBUILT.search(head)
        if not m or BANNER.search(head[:m.start()].splitlines()[-1] if head[:m.start()] else ""):
            continue
        words = [w for w in re.split(r"[-_.\s]", os.path.splitext(os.path.basename(f))[0].lower()) if len(w) >= 5
                 and w not in {"phase", "plan", "plans", "design", "proposal", "notes", "draft", "research"}]
        def size(c: str) -> int:
            try:
                return os.path.getsize(os.path.join(root, c))
            except OSError:
                return 0
        code = sorted({c for w in words for c in code_by_stem.get(w, [])}, key=size, reverse=True)[:5]
        out.append({"doc": f, "says": m.group(0)[:40], "code_for_topic": code})
    return sorted(out, key=lambda x: -len(x["code_for_topic"]))[:30]


def section_dated_piles(root: str, files: list[str]) -> list[dict]:
    piles: dict[str, list[str]] = defaultdict(list)
    for f in files:
        if DATED.search(os.path.basename(f)):
            piles[os.path.dirname(f) or "."].append(f)
    out = []
    for d, fs in piles.items():
        if len(fs) >= 4:
            dates = sorted(re.sub(r"[-_]", "", DATED.search(os.path.basename(x)).group(0)) for x in fs)
            out.append({"dir": d, "files": len(fs), "oldest": dates[0], "newest": dates[-1]})
    return sorted(out, key=lambda x: -x["files"])[:20]


def grep_count(root: str, pattern: str, rev: str | None = None) -> tuple[int, Counter]:
    args = ["grep", "-I", "-E", "-c", "-e", pattern]
    if rev:
        args.append(rev)
    args += ["--", *[f"*{e}" for e in sorted(CODE_EXT - {".sh"})], ":(exclude)*.md", ":(exclude)*.lock", ":(exclude)*lock.json", ":(exclude)*lock.yaml",
             ":(exclude)vendor/**", ":(exclude).repos/**", ":(exclude)third_party/**", ":(exclude)*.patch",
             ":(exclude)*.diff", ":(exclude)*.min.js", ":(exclude)*worker-configuration.d.ts", ":(exclude)*.snap"]
    out = git(root, *args)
    per_file = Counter()
    for line in out.splitlines():
        path, _, n = line.rpartition(":")
        if rev and path.startswith(rev + ":"):
            path = path[len(rev) + 1:]
        if n.isdigit() and not GENERATED.search(path) and not is_history(path) and not ARTIFACT.search(path):
            per_file[path] = int(n)
    return sum(per_file.values()), per_file


ARTIFACT = re.compile(r"(^|/)(\.tatastu-sketches|\.tatastu-captures|sketches|prototypes?|design-explorations|"
                      r"mockups?|demos?|examples?|fixtures?|\.tmp[^/]*|tmp|scratch)/", re.I)


def section_escape_hatches(root: str, files: list[str]) -> dict:
    first = git(root, "log", "--reverse", "--format=%ct", "--max-parents=0").split("\n", 1)[0].strip()
    young = first.isdigit() and time.time() - int(first) < 90 * 86400
    then = "" if young else git(root, "rev-list", "-1", "--before=90.days", "HEAD").strip()
    code_then = len([f for f in git(root, "ls-tree", "-r", "--name-only", then).splitlines()
                     if ext(f) in CODE_EXT]) if then else None
    code_now = len([f for f in files if ext(f) in CODE_EXT])
    rows = []
    for name, pattern in ESCAPES.items():
        total, per_file = grep_count(root, pattern)
        if not total:
            continue
        prior = grep_count(root, pattern, then)[0] if then else None
        rows.append({"kind": name, "now": total, "90_days_ago": prior,
                     "top_files": [f"{f} ({n})" for f, n in per_file.most_common(4)]})
    return {"rows": rows, "code_files_now": code_now, "code_files_90_days_ago": code_then,
            "note": "repo is younger than 90 days: no trend" if young else None}


def section_todos(root: str, files: list[str], limit: int = 250) -> dict:
    out = git(root, "grep", "-I", "-n", "-E", "-e", r"(TODO|FIXME|HACK|XXX)[:( ]", "--", ".",
              ":(exclude)*.md", ":(exclude)*lock*", ":(exclude)vendor/**", ":(exclude).repos/**",
              ":(exclude)third_party/**", ":(exclude)node_modules/**")
    hits = []
    for line in out.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[1].isdigit() and ext(parts[0]) in CODE_EXT:
            hits.append((parts[0], int(parts[1])))
    now = time.time()
    aged = []
    started = time.time()
    for path, lineno in hits[:limit]:
        if time.time() - started > 40:
            break
        blame = git(root, "blame", "-w", "-M", "-C", "--porcelain", "-L", f"{lineno},{lineno}", "--", path)
        m = re.search(r"^author-time (\d+)", blame, re.M)
        if m:
            aged.append({"at": f"{path}:{lineno}", "days": int((now - int(m.group(1))) / 86400)})
    aged.sort(key=lambda x: -x["days"])
    return {"total": len(hits), "aged": len(aged), "over_180_days": sum(1 for a in aged if a["days"] > 180),
            "oldest": aged[:12]}


COMMENT_CODE = re.compile(
    r"^\s*(//|#)\s*(const|let|var|import|export|function|def|class|if|for|while|return|await|async|"
    r"console\.|print\(|from \S+ import|\}|\{|<\w+[ >/])")


def section_commented_code(root: str, files: list[str]) -> list[dict]:
    out = []
    for f in files:
        if ext(f) not in CODE_EXT or TESTISH.search(f):
            continue
        try:
            lines = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        run = blocks = longest = 0
        start = 0
        first = None
        for i, line in enumerate(lines, 1):
            if COMMENT_CODE.match(line):
                if run == 0:
                    start = i
                run += 1
            else:
                if run >= 3:
                    blocks += 1
                    longest = max(longest, run)
                    first = first or start
                run = 0
        if run >= 3:
            blocks += 1
            longest = max(longest, run)
            first = first or start
        if blocks:
            out.append({"file": f, "blocks": blocks, "longest": longest, "first_line": first})
    return sorted(out, key=lambda x: -x["longest"])[:20]


def section_model_ids(root: str, files: list[str]) -> list[dict]:
    pattern = MODEL_ID.pattern
    out = git(root, "grep", "-I", "-o", "-i", "-P", "-e", pattern, "--", ".", ":(exclude)*lock*",
              ":(exclude)vendor/**", ":(exclude).repos/**", ":(exclude)node_modules/**", ":(exclude)CHANGELOG*")
    if not out.strip():  # git without PCRE: fall back to Python over text files
        found = []
        for f in files:
            if ext(f) in CODE_EXT | DOC_EXT | {".json", ".yaml", ".yml", ".toml", ".env", ".example"}:
                try:
                    text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                found += [f"{f}:{m.group(1)}" for m in MODEL_ID.finditer(text)]
        out = "\n".join(found)
    per_file: dict[str, set[str]] = defaultdict(set)
    for line in out.splitlines():
        path, _, model = line.rpartition(":")
        if path and model and not is_history(path) and not GENERATED.search(path):
            per_file[path].add(model.lower())
    # A file naming many models is a catalog or price table: one row for it,
    # and its IDs don't count as references elsewhere.
    catalogs = {f: len(m) for f, m in per_file.items() if len(m) >= 10}
    ids: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"code": set(), "test": set(), "doc": set()})
    for f, models in per_file.items():
        if f in catalogs:
            continue
        kind = "doc" if ext(f) in DOC_EXT or classify(f) == "plan" else "test" if TESTISH.search(f) else "code"
        for model in models:
            ids[model][kind].add(f)
    rows = [{"id": m, "code_files": len(v["code"]), "test_files": len(v["test"]), "doc_files": len(v["doc"]),
             "example": sorted(v["code"] or v["doc"] or v["test"])[0]} for m, v in ids.items()]
    rows.sort(key=lambda r: (r["id"].split("-")[0], r["id"]))
    return {"ids": rows, "catalogs": dict(sorted(catalogs.items(), key=lambda kv: -kv[1]))}


def section_env_vars(root: str, files: list[str]) -> dict:
    used: dict[str, set[str]] = defaultdict(set)
    for f in files:
        if ext(f) not in CODE_EXT or TESTISH.search(f):
            continue
        try:
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in ENV_USE.finditer(text):
            name = next(g for g in m.groups() if g)
            used[name].add(f)
    declared: dict[str, set[str]] = defaultdict(set)
    for f in files:
        base = os.path.basename(f)
        if re.match(r"\.env\.(example|sample|template|defaults)$|env\.example$|\.dev\.vars\.example$", base) or \
                base in ("wrangler.toml", "docker-compose.yml", "compose.yaml", "railway.json", "fly.toml"):
            try:
                for m in ENV_DECL.finditer(open(os.path.join(root, f), encoding="utf-8", errors="replace").read()):
                    declared[m.group(1)].add(f)
            except OSError:
                continue
    # Every UPPER_CASE token in docs, CI and config files, read once.
    documented: set[str] = set()
    for f in files:
        if ext(f) in DOC_EXT | {".json", ".jsonc", ".yaml", ".yml", ".toml"} or os.path.basename(f).startswith(".env") \
                or f.startswith(".github/"):
            try:
                if os.path.getsize(os.path.join(root, f)) > 1_000_000:
                    continue
                documented.update(re.findall(r"[A-Z][A-Z0-9_]{2,}",
                                             open(os.path.join(root, f), encoding="utf-8", errors="replace").read()))
            except OSError:
                pass
    undocumented = sorted(n for n in used if n not in declared and not PLATFORM_ENV.match(n) and n not in documented)
    # Declared but never read: no file mentions the name except where it is
    # declared and prose docs.
    really_unused = []
    for n in sorted(declared):
        if PLATFORM_ENV.match(n) or n in used:
            continue
        hits = git(root, "grep", "-I", "-l", "-w", "-F", "-e", n, "--", ".").split()
        if all(h in declared[n] or ext(h) in DOC_EXT for h in hits):
            really_unused.append(n)
    return {"used": len(used), "declared": len(declared),
            "used_but_undocumented": sorted(
                [{"name": n, "example": sorted(used[n])[0],
                  "area": "tooling" if all(re.search(r"(^|/)(scripts|tools|bin|\.claude|\.github|ci)/", f) or TESTISH.search(f) for f in used[n]) else "app"}
                 for n in undocumented], key=lambda x: (x["area"] != "app", x["name"]))[:60],
            "declared_but_unused": [{"name": n, "declared_in": sorted(declared[n])} for n in really_unused[:40]]}


def mentions(root: str, names: set[str]) -> dict[str, set[str]]:
    """Files that mention each name, from one git grep."""
    import tempfile
    if not names:
        return {}
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as tf:
        tf.write("\n".join(sorted(names)))
        path = tf.name
    try:
        out = git(root, "grep", "-I", "-o", "-F", "-f", path, "--", ".", ":(exclude)*lock*")
    finally:
        os.unlink(path)
    seen: dict[str, set[str]] = defaultdict(set)
    for line in out.splitlines():
        f, _, name = line.rpartition(":")
        if name in names:
            seen[name].add(f)
    return seen


def section_orphans(root: str, files: list[str], exts: set[str], skip: re.Pattern) -> list[dict]:
    candidates = [f for f in files if ext(f) in exts and not skip.search(f) and not is_history(f)]
    by_name: dict[str, list[str]] = defaultdict(list)
    for f in candidates:
        by_name[os.path.basename(f)].append(f)
    seen = mentions(root, set(by_name))
    orphans = []
    for name, fs in by_name.items():
        if not seen.get(name, set()) - set(fs):
            orphans.extend(fs)
    # A doc that names the folder ("evidence is in .tatastu-sketches/quality-fixes/")
    # references every file in it.
    # Only a specific folder path counts ("docs" alone appears everywhere).
    dirs = {os.path.dirname(f) + "/" for f in orphans if "/" in os.path.dirname(f)}
    dir_seen = mentions(root, dirs)
    orphans = [f for f in orphans
               if not (dir_seen.get(os.path.dirname(f) + "/", set())
                       - {x for x in orphans if os.path.dirname(x) == os.path.dirname(f)})]
    touched = last_touch(root, orphans[:400])
    return [{"file": f, "last_commit": touched.get(f, "?")} for f in sorted(orphans, key=lambda x: touched.get(x, ""))]


DOC_SKIP = re.compile(r"(^|/)(README|CHANGELOG|LICENSE|LICENCE|CONTRIBUTING|SECURITY|CODE_OF_CONDUCT|AGENTS|"
                      r"CLAUDE|GEMINI|SKILL)\.md$|(^|/)\.(github|claude|cursor|agents|codex)/|(^|/)(content|posts|blog|"
                      r"pages|src/content)/", re.I)
ASSET_SKIP = re.compile(r"(^|/)(favicon|apple-touch-icon|icon|logo|og|opengraph|twitter|manifest|robots)[^/]*$|"
                        r"(^|/)(public/icons|\.github|fastlane|ios/|android/|assets/fonts|Assets\.xcassets)/", re.I)


def group_by_dir(rows: list[dict]) -> list[dict]:
    dirs: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        dirs[os.path.dirname(r["file"]) or "."].append(r["last_commit"])
    return sorted(({"dir": d, "files": len(v), "last_commit": max(v)} for d, v in dirs.items()),
                  key=lambda x: -x["files"])


def section_large_files(root: str, files: list[str]) -> list[dict]:
    out = []
    for f in files:
        try:
            size = os.path.getsize(os.path.join(root, f))
        except OSError:
            continue
        if size >= 1_000_000:
            out.append({"file": f, "mb": round(size / 1_000_000, 1)})
    return sorted(out, key=lambda x: -x["mb"])[:20]


SECTIONS = {
    "parallel": section_parallel, "scratch": section_scratch, "ignored": section_ignored,
    "build_output": section_build_output, "lockfiles": section_lockfiles, "versions": section_versions,
    "plan_sprawl": section_plan_sprawl, "plan_status": section_plan_status,
    "plan_checkboxes": section_plan_checkboxes, "stale_plan_dirs": section_stale_plan_dirs,
    "authority_claims": section_authority_claims, "dated_piles": section_dated_piles,
    "escape_hatches": section_escape_hatches, "todos": section_todos,
    "commented_code": section_commented_code, "model_ids": section_model_ids, "env_vars": section_env_vars,
    "orphan_docs": lambda r, f: section_orphans(r, f, DOC_EXT, DOC_SKIP),
    "orphan_assets": lambda r, f: group_by_dir(section_orphans(r, f, ASSET_EXT, ASSET_SKIP)),
    "large_files": section_large_files,
}


def scan(root: str, only: list[str] | None = None) -> dict:
    files = own_files(root)
    result = {"repo": root, "own_files": len(files)}
    timings = {}
    for name, fn in SECTIONS.items():
        if only and name not in only:
            continue
        t = time.time()
        try:
            result[name] = fn(root, files)
        except Exception as e:  # one broken check must not hide the rest
            result[name] = {"error": f"{type(e).__name__}: {e}"}
        timings[name] = round(time.time() - t, 1)
    result["timings_s"] = timings
    return result


def show(items, n=12, key=None) -> None:
    for x in items[:n]:
        print("    " + (key(x) if key else (x if isinstance(x, str) else json.dumps(x))))
    if len(items) > n:
        print(f"    ... +{len(items) - n} more")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    r = scan(root, only)
    if emit_json(r):
        return
    print(f"repo: {r['repo']}  own files: {r['own_files']}")
    for name in SECTIONS:
        if name not in r:
            continue
        v = r[name]
        if isinstance(v, dict) and "error" in v:
            print(f"\n[{name}] check failed: {v['error']}")
            continue
        if name == "plan_sprawl":
            print(f"\n[plan_sprawl] root markdown {len(v['root_markdown'])}, session-style docs {v['session_docs_total']}"
                  " (oldest first)")
            show(v["root_markdown"], 10, lambda x: f"{x['file']}  last {x['last_commit']}")
            if v["root_unreferenced_files"]:
                print(f"  root files nothing names: {len(v['root_unreferenced_files'])}")
                show(v["root_unreferenced_files"], 10, lambda x: f"{x['file']}  last {x['last_commit']}")
            show(v["session_docs"], 14, lambda x: f"{x['file']}  last {x['last_commit']}")
        elif name == "plan_checkboxes":
            print(f"\n[plan_checkboxes] {len(v)} task lists that look done, shipped or stalled")
            show(v, 14, lambda x: f"{x['doc']}  {x['done']} done / {x['open']} open"
                                  f" ({x['open_naming_existing_files']} open naming existing files), last {x['last_commit']}: {x['finding']}")
        elif name == "stale_plan_dirs":
            print(f"\n[stale_plan_dirs] {len(v)} plan folders mostly untouched for 45+ days")
            show(v, 12, lambda x: f"{x['dir']}  {x['untouched_45d']}/{x['files']} untouched, newest {x['newest']}"
                                  + ("  (a tool's plan folder)" if x["tool_folder"] else ""))
        elif name == "authority_claims":
            print(f"\n[authority_claims] {len(v)} unmarked docs claiming authority (no status banner)")
            show(v, 14, lambda x: f"{x['doc']}:{x['line']}  '{x['claims']}'  [{x['class']}]"
                                  f"{'' if x['linked_from_orientation'] else ' not linked from README/instructions'}, last {x['last_commit']}")
        elif name == "plan_status":
            print(f"\n[plan_status] {len(v)} docs whose header says unbuilt; code for the topic listed when found")
            show(v, 12, lambda x: f"{x['doc']}  says '{x['says']}'  code: {', '.join(x['code_for_topic'][:3]) or '-'}")
        elif name == "todos":
            print(f"\n[todos] {v['total']} in code; aged {v['aged']}, over 180 days {v['over_180_days']}")
            show(v["oldest"], 8, lambda x: f"{x['days']}d  {x['at']}")
        elif name == "env_vars":
            print(f"\n[env_vars] read in code {v['used']}, declared in examples/config {v['declared']}")
            print(f"  read but not in any example, config or doc: {len(v['used_but_undocumented'])}")
            show(v["used_but_undocumented"], 14, lambda x: f"{x['name']:32} [{x['area']}]  e.g. {x['example']}")
            print(f"  declared but never read: {len(v['declared_but_unused'])}")
            show(v["declared_but_unused"], 10, lambda x: f"{x['name']}  in {', '.join(x['declared_in'])}")
        elif name == "ignored":
            print(f"\n[tracked but gitignored] by the repo's .gitignore: {len(v['by_repo_gitignore'])}")
            show(v["by_repo_gitignore"], 12)
            if v["by_local_excludes"]:
                print(f"  ignored only by this machine's excludes (not a repo problem): {v['by_local_excludes']}")
        elif name == "orphan_assets":
            print(f"\n[orphan_assets] {sum(x['files'] for x in v)} files no tracked text names, by directory")
            show(v, 12, lambda x: f"{x['files']:4}  {x['dir']}  (last commit {x['last_commit']})")
        elif name == "escape_hatches":
            print(f"\n[escape_hatches] code only; now vs 90 days ago (code files {v['code_files_now']} vs "
                  f"{v['code_files_90_days_ago']}){'  ' + v['note'] if v['note'] else ''}")
            show(v["rows"], 12, lambda x: f"{x['kind']:20} {x['now']:5}  (was {x['90_days_ago']})  {', '.join(x['top_files'][:3])}")
        elif name == "model_ids":
            print(f"\n[model_ids] {len(v['ids'])} distinct outside catalogs; judge each against the current lineup")
            show(v["ids"], 60, lambda x: f"{x['id']:30} code {x['code_files']:3} test {x['test_files']:3} doc {x['doc_files']:3}  e.g. {x['example']}")
            if v["catalogs"]:
                print("  catalog files (10+ model IDs each): " + ", ".join(f"{f} ({n})" for f, n in list(v["catalogs"].items())[:8]))
        else:
            label = name
            print(f"\n[{label}] {len(v)}")
            show(v, 12, lambda x: x if isinstance(x, str) else "  ".join(f"{k}={val}" for k, val in x.items()))
    print("\ntimings (s): " + ", ".join(f"{k} {t}" for k, t in r["timings_s"].items() if t >= 0.5))


if __name__ == "__main__":
    main()
