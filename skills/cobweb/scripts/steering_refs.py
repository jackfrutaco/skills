#!/usr/bin/env python3
"""Find claims in agent instructions and docs that no longer match the repo.

Stdlib only. Reads tracked files through git, so it honours .gitignore and
works in any language's repository. It never edits anything.

Reports:
  - every steering file (agent instructions, rules, commands, skills, hooks,
    MCP config, plans, human docs) and how it reaches an agent
  - the always-loaded instruction bytes an agent pays on every turn
  - local paths, links and runnable scripts those files name that do not
    exist, with the commit that deleted the path when git still remembers it

Usage: steering_refs.py [repo] [--json] [--all] [--include-vendored]
  --all               list every finding in plans and history docs, not only counts
  --include-vendored  also scan vendor/, third_party/, .repos/ and similar
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import re
import subprocess
import sys
from collections import Counter, defaultdict

# How each kind of steering file reaches an agent. "always" files cost tokens
# on every turn; "scoped" load by directory, glob or description; "on-demand"
# load when invoked. Plans and history are retrieved by search, and search
# strips the folder name that says they are old.
ALWAYS = {
    "AGENTS.md", "AGENTS.override.md", "AGENT.md", "CLAUDE.md", "CLAUDE.local.md",
    "GEMINI.md", ".cursorrules", ".windsurfrules", ".clinerules", ".goosehints",
    ".rules", "CONVENTIONS.md", ".github/copilot-instructions.md",
    ".junie/guidelines.md",
}
SCOPED = [
    "**/AGENTS.md", "**/CLAUDE.md", "**/GEMINI.md", ".cursor/rules/**",
    ".windsurf/rules/**", ".clinerules/**", ".roo/**", ".continue/rules/**",
    ".kiro/steering/**", ".github/instructions/**", ".claude/rules/**",
    ".amazonq/rules/**", ".augment/rules/**",
]
ON_DEMAND = [
    ".claude/commands/**", ".claude/agents/**", ".claude/skills/**", ".agents/skills/**",
    ".github/prompts/**", ".github/agents/**", ".github/skills/**", ".gemini/commands/**",
    ".codex/**", ".opencode/**", ".cursor/commands/**", ".roomodes",
]
# Skills and prompts this repo ships to other projects: their paths name the
# consuming project, so a miss here is not drift.
PAYLOAD = ["**/SKILL.md", "**/skills/**", "**/prompts/**", "**/templates/**"]
DATED = re.compile(r"(19|20)\d\d-[01]\d-[0-3]\d")
NEGATED = re.compile(
    r"\b(there is no|no longer|removed|deleted|retired|renamed|formerly|replaced|used to|"
    r"was|were|instead of|legacy|deprecated)\b", re.I)
CONFIG = [
    ".claude/settings.json", ".claude/settings.local.json", ".mcp.json",
    ".cursor/mcp.json", ".vscode/mcp.json", ".gemini/settings.json",
    ".aider.conf.yml", "opencode.json", ".codex/config.toml",
]
PLAN = [
    "**/icebox/**", "**/parked/**", "**/backlog/**",
    "**/plans/**", "**/plan/**", "PLAN*.md", "TODO*.md", "ROADMAP*.md", "NOTES*.md",
    "TASKS*.md", "**/specs/**", "**/proposals/**", "**/changes/**", "**/rfcs/**",
    "*-plan.md", "*_plan.md", "*-spec.md",
]
HISTORY = [
    "**/archive/**", "**/archived/**", "**/audits/**", "**/postmortems/**",
    "**/adr/**", "**/decisions/**", "CHANGELOG*", "**/CHANGELOG*", "HISTORY*",
    "**/reports/**",
    # What shipped in each release is a record, however many docs-folder files hold it.
    "**/releases/**", "**/release-notes/**", "**/release_notes/**", "**/changelog/**",
    "**/changelogs/**", "**/whatsnew/**", "NEWS*", "**/NEWS*", "RELEASE*NOTES*",
    "**/RELEASE*NOTES*", "CHANGES*", "**/CHANGES*",
]
DOC_EXT = (".md", ".mdc", ".mdx", ".txt", ".rst")

# Extensions that mark a token as a file claim. A whitelist, because dotted
# identifiers (`ink.primary`, `c.var.user`, bundle ids, domains) are far more
# common in docs than unknown file types.
FILE_EXTS = set("""
ts tsx js jsx mjs cjs mts cts json jsonc json5 md mdx mdc rst txt py pyi ipynb rb go rs
java kt kts scala swift m mm h hpp c cc cpp cs fs vb php ex exs erl hs ml clj dart lua
r jl pl sh bash zsh fish ps1 bat cmd yml yaml toml ini cfg conf lock sql prisma
graphql gql proto css scss sass less html htm vue svelte astro hbs ejs njk liquid xml
plist gradle properties tf tfvars hcl nix csv tsv svg png jpg jpeg gif webp ico pdf
wasm mk cmake gemspec podspec storyboard xib entitlements xcconfig
""".split())
PLACEHOLDER = re.compile(
    r"X\.Y|\bvX\b|YYYY|\bfoo\b|\bbar\b|\bbaz\b|your[-_]|example|path/to|my[-_]", re.I
)
NOT_PATH = re.compile(r"[\s<>{}$*?|\\\"'`,;()\[\]@=!^%]|^[~/]|^[a-z][a-z0-9+.-]*:|\.\.\.|^-|^\.[A-Za-z0-9]+$")
# Docs name modules without extensions and build output by its compiled name.
MODULE_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".go", ".rs", ".rb")
COMPILED = {".js": (".ts", ".tsx", ".mts"), ".mjs": (".mts", ".ts"), ".cjs": (".cts", ".ts"),
            ".css": (".scss", ".sass", ".less"), ".pyc": (".py",)}
LINE_SUFFIX = re.compile(r"(#.*|:L?\d+(:\d+)?([-–]L?\d+)?)$")
LINK = re.compile(r"!?\[[^\]]*\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
TICKS = re.compile(r"`+")
FENCE = re.compile(r"^\s*(```|~~~)")
# reStructuredText: a line ending in "::" opens a literal block, and a code
# directive opens one too; both hold the indented lines that follow.
RST_EXTS = (".rst", ".txt")
RST_LITERAL = re.compile(r"^(?!\s*\.\.\s).*::\s*$|^\s*\.\.\s+(code-block|code|sourcecode|parsed-literal|console)::")
RST_OPTION = re.compile(r"^\s*:[\w-]+:(\s|$)")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s")
IMPORT = re.compile(r"^@([\w./-]+)\s*$")
RUNNER = re.compile(
    r"(?:^|[\s;&|(])(?:(npm)\s+run\s+([\w:.\-]+)"
    r"|(pnpm|yarn|bun)\s+(?:--filter\s+\S+\s+|-F\s+\S+\s+)?(?:run\s+)?([\w:.\-]+)"
    r"|(make|just|task)\s+([\w:.\-]+))"
)
# Prose words that follow make/just/task in a sentence, never a target.
NOT_TARGET = {"sure", "the", "a", "an", "it", "that", "this", "any", "your", "sense", "use", "of", "in",
              "to", "sure,", "certain", "clear", "up", "sure."}
# Package-manager builtins, not package.json scripts.
PM_BUILTINS = set("""
install i add remove rm uninstall ci init create exec x dlx link unlink publish pack
update up upgrade outdated audit why info view list ls version help login logout config
cache pm run workspace workspaces global set patch rebuild dedupe prune import store
upgrade-interactive bunx npx node test start t
""".split())


def code_spans(line: str) -> list[tuple[int, int, str]]:
    """Inline code as (start, end, text). A run of N backticks closes at the next
    run of exactly N, so RST ``a`` make sure ``b`` is two spans and the words
    between them are prose. A single-backtick span that starts or ends with
    whitespace is two stray ticks, not code."""
    runs = list(TICKS.finditer(line))
    spans, i = [], 0
    while i < len(runs):
        n = len(runs[i].group())
        j = next((k for k in range(i + 1, len(runs)) if len(runs[k].group()) == n), None)
        if j is None:
            i += 1
            continue
        body = line[runs[i].end():runs[j].start()]
        if n > 1:
            body = body.strip()  # Markdown pads ``  ` ``; RST does not
        if 2 <= len(body) <= 200 and (n > 1 or body == body.strip()):
            spans.append((runs[i].start(), runs[j].end(), body))
            i = j + 1
        else:
            i = j
    return spans


def git(repo: str, *args: str, stdin: str | None = None) -> str:
    out = subprocess.run(
        ["git", "-C", repo, *args], input=stdin, capture_output=True, text=True,
        check=False,
    )
    return out.stdout


def match_any(path: str, globs: list[str]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(path, g) or (g.startswith("**/") and fnmatch.fnmatch(path, g[3:])):
            return True
    return False


# Code another project owns. Its docs describe that project, not this one.
VENDORED_DIRS = {
    "vendor", "vendors", "third_party", "third-party", "thirdparty", "external", "extern",
    ".repos", "node_modules", "bower_components", "Pods", "Carthage", "deps", "_vendor",
}


def vendored_roots(root: str) -> set[str]:
    """Directories .gitattributes marks linguist-vendored or linguist-generated."""
    roots = set()
    try:
        for line in open(os.path.join(root, ".gitattributes"), encoding="utf-8", errors="replace"):
            if re.search(r"linguist-(vendored|generated)(?!=false)", line) and not line.startswith("#"):
                pat = line.split()[0].rstrip("*").rstrip("/")
                if pat and not any(c in pat for c in "*?["):
                    roots.add(pat.lstrip("/"))
    except OSError:
        pass
    return roots


def is_vendored(path: str, extra: set[str] = frozenset()) -> bool:
    parts = path.split("/")
    if any(p in VENDORED_DIRS for p in parts[:-1]):
        return True
    return any(path == r or path.startswith(r + "/") for r in extra)


def classify(path: str) -> str | None:
    if path in ALWAYS:
        return "always"
    if match_any(path, SCOPED):
        return "scoped"
    if match_any(path, ON_DEMAND):
        return "history" if DATED.search(posixpath.basename(path)) else "on-demand"
    if match_any(path, CONFIG):
        return "config"
    if not path.lower().endswith(DOC_EXT) or "node_modules/" in path:
        return None
    if match_any(path, HISTORY) or DATED.search(path):
        return "history"  # a date in the name or any folder marks a record
    # Current specs are authority; proposals and their spec deltas are plans.
    if match_any(path, ["**/specs/**"]) and not re.search(r"(^|/)(changes|proposals|rfcs|icebox|parked|backlog)/", path):
        return "spec"
    if match_any(path, PLAN):
        return "plan"
    if match_any(path, PAYLOAD):
        return "payload"
    return "doc"


def runnable_names(repo: str, files: list[str]) -> dict[str, set[str]]:
    names: dict[str, set[str]] = defaultdict(set)
    for f in files:
        base = os.path.basename(f)
        full = os.path.join(repo, f)
        try:
            if base == "package.json" and "node_modules/" not in f:
                data = json.load(open(full, encoding="utf-8"))
                names["pkg"].update((data.get("scripts") or {}).keys())
                # `pnpm vitest`, `bunx tsc`: a dependency's binary, not a script.
                for field in ("dependencies", "devDependencies", "optionalDependencies"):
                    for dep in (data.get(field) or {}):
                        names["bin"].update({dep, dep.rsplit("/", 1)[-1]})
                bins = data.get("bin")
                names["bin"].update(bins.keys() if isinstance(bins, dict) else [data.get("name", "")])
            elif base in ("Makefile", "makefile", "GNUmakefile") or f.endswith(".mk"):
                for line in open(full, encoding="utf-8", errors="replace"):
                    m = re.match(r"^([A-Za-z0-9_.\-/]+)\s*:(?!=)", line)
                    if m:
                        names["make"].add(m.group(1))
            elif base.lower() in ("justfile", ".justfile"):
                for line in open(full, encoding="utf-8", errors="replace"):
                    m = re.match(r"^@?([A-Za-z0-9_\-]+)[^:=]*:(?!=)", line)
                    if m:
                        names["just"].add(m.group(1))
            elif base in ("Taskfile.yml", "Taskfile.yaml"):
                for line in open(full, encoding="utf-8", errors="replace"):
                    m = re.match(r"^  ([A-Za-z0-9_:\-]+):\s*$", line)
                    if m:
                        names["task"].add(m.group(1))
        except (OSError, ValueError):
            continue
    return names


class Repo:
    def __init__(self, root: str):
        self.root = root
        self.files = [l for l in git(root, "ls-files").splitlines() if l]
        self.tracked = set(self.files)
        self.dirs: set[str] = set()
        self.by_tail: dict[str, list[str]] = defaultdict(list)
        for t in self.files:
            parts = t.split("/")
            for i in range(1, len(parts)):
                self.dirs.add("/".join(parts[:i]))
            for i in range(len(parts)):
                self.by_tail["/".join(parts[i:])].append(t)
        self.top = {t.split("/", 1)[0] for t in self.files}

    def exists(self, p: str) -> bool:
        if p in self.tracked or p in self.dirs or p == ".":
            return True
        if not posixpath.splitext(p)[1]:
            return any(p + e in self.tracked or f"{p}/index{e}" in self.tracked for e in MODULE_EXTS)
        return False

    def has_tail(self, tail: str) -> list[str]:
        hits = self.by_tail.get(tail, [])
        if hits:
            return hits
        stem, ext = posixpath.splitext(tail)
        for source in COMPILED.get(ext, ()):
            if self.by_tail.get(stem + source):
                return self.by_tail[stem + source]
        if not ext:
            for e in MODULE_EXTS:
                if self.by_tail.get(tail + e):
                    return self.by_tail[tail + e]
        return []

    def ignored(self, paths: list[str]) -> set[str]:
        if not paths:
            return set()
        paths = [p for p in paths if p and not p.startswith("../")]
        # "dir/" patterns only match a path that ends in a slash. Only the repo's
        # own .gitignore files say "absent on purpose"; .git/info/exclude and
        # global excludes are one machine's, so links into them still break
        # for every other clone.
        probe = paths + [p.rstrip("/") + "/" for p in paths]
        out = git(self.root, "check-ignore", "-v", "--no-index", "--stdin", stdin="\n".join(probe))
        keep = set()
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            source = meta.split(":", 1)[0]
            if source.endswith(".gitignore") and not os.path.isabs(source):
                keep.add(path.rstrip("/"))
        return keep


def is_path_claim(tok: str, repo: Repo) -> bool:
    if NOT_PATH.search(tok) or PLACEHOLDER.search(tok):
        return False
    stem = tok.rstrip("/")
    ext = stem.rsplit(".", 1)[-1].lower() if "." in posixpath.basename(stem) else ""
    if tok.startswith(("./", "../")):
        return True
    if "/" in stem:
        # A slash alone is weak evidence (and/or, read/write): require a real
        # top-level entry or a file extension.
        return stem.split("/", 1)[0] in repo.top or ext in FILE_EXTS
    return ext in FILE_EXTS and not stem[0].isdigit()


def resolve(tok: str, doc: str, repo: Repo) -> tuple[str, str | None]:
    """Return (status, hint). status: ok | moved | missing."""
    clean = LINE_SUFFIX.sub("", tok).rstrip("/")
    if not clean:
        return "ok", None
    # The doc's own directory, then each ancestor: monorepo packages and
    # vendored projects write paths relative to their own root.
    base = posixpath.dirname(doc)
    while True:
        p = posixpath.normpath(posixpath.join(base, clean)) if base else posixpath.normpath(clean)
        if repo.exists(p):
            return "ok", None
        if not base:
            break
        base = posixpath.dirname(base)
    tail = posixpath.normpath(clean)
    while tail.startswith("../"):
        tail = tail[3:]
    hits = repo.has_tail(tail)
    anchored = clean.startswith(("./", "../")) or clean.split("/", 1)[0] in repo.top
    if hits and not anchored:
        return "ok", None  # abbreviated reference that still finds its file
    if hits:
        return "moved", hits[0] if len(hits) == 1 else f"{len(hits)} candidates"
    if "/" not in clean:
        return "missing-name", None
    return "missing", None


# Top-level folders every project has: a miss under one proves nothing about
# whether a doc about the reader's own project is describing this repo.
GENERIC_TOPS = {"src", "tests", "test", "docs", "app", "lib"}


# Folders that hold a sample project, fixtures or scaffolding rather than the
# project itself: a path found there did not "move" from the repo's own tree.
SAMPLE_PATH = re.compile(r"(^|/)(tests?|fixtures?|testdata|examples?|samples?|templates?|[^/]*_template)/")


def belongs_here(r: dict, repo: Repo) -> bool:
    """Prose in a human doc often walks the reader through THEIR project
    (`polls/models.py`, `./public`). A missing path counts against the repo only
    when git remembers it, it moved, or it sits under one of this repo's own
    non-generic top-level folders."""
    if r["status"] == "missing-name":
        return False
    if r["status"] == "moved":
        hint = r.get("hint") or ""
        tail = posixpath.normpath(LINE_SUFFIX.sub("", r["ref"])).lstrip("./")
        return not (hint in repo.tracked and hint.endswith(tail) and SAMPLE_PATH.search(hint[:-len(tail)]))
    if r["status"] != "missing":
        return True  # deleted, untracked, other-worktree, outside-repo: evidence enough
    first = re.sub(r"^(\.\./)+", "", posixpath.normpath(LINE_SUFFIX.sub("", r["ref"]))).split("/", 1)[0]
    return first in repo.top and first in repo.dirs and first not in GENERIC_TOPS


_DELETIONS: dict[str, dict[str, str]] = {}


def deleted_in(repo: Repo, path: str) -> str | None:
    """The newest commit that deleted this path (or a file with this name),
    from one walk over history instead of one `git log` per path."""
    if repo.root not in _DELETIONS:
        by_path: dict[str, str] = {}
        commit = ""
        for line in git(repo.root, "log", "--diff-filter=D", "--name-only", "--no-renames",
                        "--format=@%h %as %s").splitlines():
            if line.startswith("@"):
                commit = line[1:]
            elif line:
                by_path.setdefault(line, commit)
                by_path.setdefault("name:" + posixpath.basename(line), commit)
                # Directories that held a deleted file count as deleted with it.
                d = posixpath.dirname(line)
                while d:
                    by_path.setdefault(d, commit)
                    d = posixpath.dirname(d)
        _DELETIONS[repo.root] = by_path
    table = _DELETIONS[repo.root]
    clean = re.sub(r"^(\.{1,2}/)+", "", posixpath.normpath(path)) if path not in (".", "./") else path
    return table.get(clean) or (table.get("name:" + clean) if "/" not in clean else None)


def block_lines(lines: list[str], rst: bool) -> list[bool]:
    """Per line: is it inside a fenced block, an RST literal block, or a
    Markdown indented code block?"""
    flags: list[bool] = []
    fence = False
    opener: int | None = None   # RST: indent of the line that opened a literal block
    started = False             # RST: saw the block's first indented line
    in_list = md_block = False
    prev_blank = True
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" \t"))
        if not rst and FENCE.match(line):
            fence = not fence
            flags.append(False)
        elif fence:
            flags.append(True)
        elif rst:
            flag = False
            if opener is not None:
                if not stripped:
                    flag = started
                elif indent > opener:
                    # Directive options (":caption: ``x``") come before the code.
                    if started or not RST_OPTION.match(line):
                        started = flag = True
                else:
                    opener = None
            if opener is None and RST_LITERAL.search(line):
                opener, started = indent, False
            flags.append(flag)
        else:
            if not stripped:
                flags.append(md_block)
            elif indent >= 4:
                md_block = md_block or (prev_blank and not in_list)
                flags.append(md_block)
            else:
                md_block = False
                in_list = bool(LIST_ITEM.match(line))
                flags.append(False)
        prev_blank = not stripped
    return flags


def command_starts_here(code: str, start: int) -> bool:
    """In a code block a command begins the line (after a prompt) or follows a shell joiner."""
    before = code[:start]
    return bool(re.fullmatch(r"\s*(?:[$%>]\s+)?", before) or re.search(r"(?:&&|\|\||[;|(])\s*$", before))


# A bare filename like BunPtyAdapter.ts or build-cli.ts names one file; layout.html, root.go do not.
DISTINCT_NAME = re.compile(r"[a-z][A-Z]|[a-z0-9][-_][a-z0-9]")


def deleted_near(repo: Repo, clean: str, doc: str) -> str | None:
    """A bare filename counts as deleted only where this doc would have looked
    for it (its folder or an ancestor), not any file anywhere that shared the name."""
    deleted_in(repo, "")  # build the table
    table = _DELETIONS[repo.root]
    base = posixpath.dirname(doc)
    while True:
        if hit := table.get(posixpath.normpath(posixpath.join(base, clean))):
            return hit
        if not base:
            return None
        base = posixpath.dirname(base)


def extract(text: str, kind: str, path: str = "") -> list[tuple[int, str, str]]:
    refs = []
    lines = text.splitlines()
    rst = path.lower().endswith(RST_EXTS)  # "~~~~" under a heading is not a fence there
    blocks = block_lines(lines, rst)
    for lineno, line in enumerate(lines, 1):
        if not rst and FENCE.match(line):
            continue
        in_block = blocks[lineno - 1]
        spans = code_spans(line)
        prose = line
        for a, b, _ in reversed(spans):
            prose = prose[:a] + " " + prose[b:]
        prose = LINK.sub(" ", prose)
        if NEGATED.search(prose):
            continue  # "there is no changes.ts", "replaced foo.ts": absence is the claim
        if kind in ("always", "scoped") and (m := IMPORT.match(line.strip())):
            refs.append((lineno, "import", m.group(1)))
        for m in LINK.finditer(line):
            target = m.group(1)
            if not re.match(r"^[a-z][a-z0-9+.\-]*:|^#|^/", target, re.I):
                refs.append((lineno, "link", target))
        # A command is a claim only where it is code: an inline span or a code
        # block. "make sure" in a sentence is English.
        for span in [line] if in_block else [t for _, _, t in spans]:
            # Code blocks are examples as often as claims: keep runnable
            # scripts there, drop bare path guesses.
            if not in_block:
                for tok in span.split():
                    refs.append((lineno, "path", tok.rstrip(".:,")))
            for m in RUNNER.finditer(span):
                word = m.start() + len(m.group(0)) - len(m.group(0).lstrip(" \t;&|("))
                if in_block and not command_starts_here(span, word):
                    continue
                g = m.groups()
                if g[0]:
                    refs.append((lineno, "script:pkg", g[1]))
                elif g[2] and g[3] not in PM_BUILTINS and g[3][0].isalpha():
                    refs.append((lineno, "script:pkg-or-bin", g[3]))
                elif g[4] and g[5].lower() not in NOT_TARGET:
                    refs.append((lineno, f"script:{g[4]}", g[5]))
    return refs


CITE_AFTER = re.compile(  # CLAUDE.md's "Provider Parity", AGENTS.md "Verification", README.md → Setup
    r"([\w./-]*[A-Za-z0-9_-]\.md)`?(?:'s)?\s*(?:§\s*|→\s*|>\s*|section\s+|,\s*)?[\"“]([^\"”\n]{3,60})[\"”]")
CITE_BEFORE = re.compile(  # "Versioning Convention" in ../CLAUDE.md
    r"[\"“]([^\"”\n]{3,60})[\"”]\s+(?:section\s+)?(?:in|of|from)\s+`?([\w./-]*[A-Za-z0-9_-]\.md)\b")
HTML_ANCHOR = re.compile(r"""<[A-Za-z][\w-]*\b[^>]*?\b(?:name|id)\s*=\s*["']([^"']+)["']""")
ANCHOR_LINK = re.compile(r"\]\(([^)\s#]+\.md)#([^)\s]+)\)")
MENTION = re.compile(r"(?<![\w./-])((?:\.\./|\./)*(?:[\w.-]+/)*(?:CLAUDE|AGENTS|GEMINI|CONVENTIONS|AGENT)\.md)\b")
COMMENT_LINE = re.compile(r"^\s*(//|#|\*|/\*|<!--|--|;)")
SECTION_NAME = re.compile(r"[A-Za-z][\w &/'’.-]*[\w)]")
POINTER = re.compile(r"(?:\b(?:see|per|described in|lives? in|defined in|documented in|explained in|rules? in|"
                     r"according to|follow|read)\s+(?:the\s+)?[`'\"]?(?:\.\./|\./)*(?:[\w.-]+/)*"
                     r"(?:CLAUDE|AGENTS|GEMINI|CONVENTIONS|AGENT)\.md|(?:CLAUDE|AGENTS|GEMINI|CONVENTIONS|AGENT)\.md['’]s)",
                     re.I)
TEXT_EXT = DOC_EXT + (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".rb", ".sh",
                      ".swift", ".kt", ".java", ".yml", ".yaml", ".toml", ".json")


def slug(heading: str) -> str:
    h = re.sub(r"[`*_]", "", heading.strip().lower())
    h = re.sub(r"[^\w\- ]", "", h)
    return h.replace(" ", "-")


def is_import_stub(text: str) -> bool:
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("<!--")]
    return bool(lines) and all(l.startswith("@") for l in lines)


def section_citations(repo: "Repo", root: str, include_vendored: bool, extra: set[str]) -> list[dict]:
    """Citations of a section or anchor that the cited file no longer has, and
    pointers at an instruction file that is now only an import line."""
    cache: dict[str, str | None] = {}

    def target_text(cited: str, src: str) -> tuple[str | None, str | None]:
        """The cited file, trying the citing file's directory, then the root,
        then a unique tail match. Returns the first path and every candidate's
        text joined, so a phrase in any plausible target counts."""
        cands = []
        for base in (posixpath.dirname(src), ""):
            p = posixpath.normpath(posixpath.join(base, cited))
            if p in repo.tracked and p not in cands:
                cands.append(p)
        if not cands:
            hits = repo.by_tail.get(cited.lstrip("./"), [])
            if len(hits) != 1:
                return None, None
            cands = hits
        texts = []
        for p in cands:
            if p not in cache:
                try:
                    cache[p] = open(os.path.join(root, p), encoding="utf-8", errors="replace").read()
                except OSError:
                    cache[p] = None
            if cache[p] is not None:
                texts.append(cache[p])
        return (cands[0], "\n".join(texts)) if texts else (None, None)

    out = []
    for f in repo.files:
        if (not include_vendored and is_vendored(f, extra)) or not f.endswith(TEXT_EXT):
            continue
        kind = classify(f) or "code"
        if kind in ("history", "payload", "config"):
            continue
        try:
            if os.path.getsize(os.path.join(root, f)) > 400_000:
                continue
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if ".md" not in text:
            continue
        seen = set()
        is_prose = f.lower().endswith(DOC_EXT)
        for lineno, line in enumerate(text.splitlines(), 1):
            if ".md" not in line or NEGATED.search(line):
                continue
            # In code, only comments make claims; string literals are data.
            if not is_prose and not COMMENT_LINE.match(line):
                continue
            cites = [(m.group(1), m.group(2), "section") for m in CITE_AFTER.finditer(line)]
            cites += [(m.group(2), m.group(1), "section") for m in CITE_BEFORE.finditer(line)]
            cites += [(m.group(1), m.group(2), "anchor") for m in ANCHOR_LINK.finditer(line)]
            for cited, section, how in cites:
                if (cited, section) in seen or (how == "section" and not SECTION_NAME.fullmatch(section.strip())):
                    continue
                seen.add((cited, section))
                p, body = target_text(cited, f)
                if body is None or p == f:
                    continue
                if how == "anchor":
                    heads = {slug(h) for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", body, re.M)}
                    # <a name="x">, <h3 name="x">, id="x": hand-written anchors count too.
                    heads |= {a.lower() for a in HTML_ANCHOR.findall(body)}
                    ok = section.lower() in heads or not re.search(r"[a-z]", section)
                else:
                    norm = lambda t: re.sub(r"\s+", " ", t).lower()
                    ok = norm(section) in norm(body)
                if not ok:
                    out.append({"doc": f, "line": lineno, "kind": kind, "type": how,
                                "ref": f"{cited} \"{section}\"", "status": "section-gone", "hint": p})
            if re.search(r"\bimport", line, re.I):
                continue  # describes the stub itself
            if not POINTER.search(line):
                continue
            for m in MENTION.finditer(line):
                p, body = target_text(m.group(1), f)
                if body is not None and p != f and is_import_stub(cache.get(p) or "") and not line.lstrip().startswith("@"):
                    key = ("stub", p)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"doc": f, "line": lineno, "kind": kind, "type": "pointer",
                                "ref": m.group(1), "status": "import-stub",
                                "hint": f"{p} only imports {body.strip()[:40]}"})
    return out


def version_claims(repo: "Repo", root: str, steering: dict) -> list[dict]:
    """'Electron ~39', 'TypeScript 5.4' in prose when package.json says otherwise."""
    majors: dict[str, set[int]] = defaultdict(set)
    for f in repo.files:
        if os.path.basename(f) != "package.json" or "node_modules/" in f or is_vendored(f):
            continue
        try:
            data = json.load(open(os.path.join(root, f), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for field in ("dependencies", "devDependencies", "peerDependencies"):
            for dep, rng in (data.get(field) or {}).items():
                m = re.match(r"\s*(?:npm:[^@]+@)?[\^~>=< ]*(\d+)", str(rng))
                if m and len(dep) >= 3:
                    majors[dep.lower()].add(int(m.group(1)))
        if eng := (data.get("engines") or {}).get("node"):
            if m := re.search(r"(\d+)", eng):
                majors["node"].add(int(m.group(1)))
    for pin in (".nvmrc", ".node-version"):
        if pin in repo.tracked:
            if m := re.search(r"(\d+)", open(os.path.join(root, pin)).read()):
                majors["node"].add(int(m.group(1)))
    if not majors:
        return []
    # A dependency name followed by a version: "Electron ~39.8", "typescript@5.4", "Node 22".
    names = sorted((d for d in majors if re.fullmatch(r"[a-z][a-z0-9.-]+", d)), key=len, reverse=True)
    pattern = re.compile(r"(?<![\w@/.-])(" + "|".join(re.escape(n) for n in names) +
                         r")(?:\.js)?(?:\s+v?|@|\s*~|\s*\^|\s*>=\s*|\s+version\s+)(\d+)(?:\.\d+){0,2}\b", re.I)
    out = []
    for kind in ("always", "scoped", "on-demand", "doc", "spec"):
        for e in steering.get(kind, []):
            f = e["path"]
            if not f.lower().endswith(DOC_EXT):
                continue
            try:
                lines = open(os.path.join(root, f), encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for lineno, line in enumerate(lines, 1):
                for m in pattern.finditer(line):
                    name, claimed = m.group(1), int(m.group(2))
                    text_ = m.group(0)
                    sep_is_space = not re.search(r"[@~^]|>=|\sv\d|version", text_)
                    # "jotai 289" is a usage count; "Electron 39" and "TypeScript 5.4" are versions.
                    if sep_is_space and not (name[0].isupper() or re.search(r"\d\.\d", text_)):
                        continue
                    if name.islower() and name.lower() in ENGLISH_WORDS and "@" not in text_:
                        continue
                    have = majors[name.lower()]
                    if claimed not in have and claimed < 1000:
                        out.append({"doc": f, "line": lineno, "kind": kind, "type": "version",
                                    "ref": m.group(0).strip(), "status": "version-differs",
                                    "hint": f"package.json has {name.lower()} {'/'.join(map(str, sorted(have)))}"})
    return out


ENGLISH_WORDS = {"next", "react", "vite", "node", "express", "commander", "ink", "chalk", "zod", "ws", "glob",
                 "debug", "ms", "open", "execa", "got", "sharp", "marked", "yaml", "dotenv"}


def scan(root: str, include_vendored: bool = False) -> dict:
    root = git(root, "rev-parse", "--show-toplevel").strip() or root
    repo = Repo(root)
    scripts = runnable_names(root, repo.files)
    steering: dict[str, list[dict]] = defaultdict(list)
    raw = []

    extra_vendored = vendored_roots(root)
    vendored_files = 0
    for f in repo.files:
        if not include_vendored and is_vendored(f, extra_vendored):
            vendored_files += 1
            continue
        kind = classify(f)
        if not kind:
            continue
        full = os.path.join(root, f)
        try:
            size = os.path.getsize(full)
            text = open(full, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        steering[kind].append({"path": f, "bytes": size})
        # Config is JSON/TOML and skills may ship code; only prose carries claims.
        if kind == "config" or (kind != "always" and not f.lower().endswith(DOC_EXT)):
            continue
        seen = set()
        for lineno, rtype, tok in extract(text, kind, f):
            if (rtype, tok) in seen:
                continue
            seen.add((rtype, tok))
            if rtype.startswith("script:"):
                family = rtype.split(":", 1)[1]
                if family == "pkg-or-bin":
                    if scripts.get("pkg") and tok not in scripts["pkg"] | scripts.get("bin", set()):
                        raw.append({"doc": f, "line": lineno, "kind": kind, "type": "script:pkg",
                                    "ref": tok, "status": "missing-script"})
                    continue
                if scripts.get(family) and tok not in scripts[family]:
                    raw.append({"doc": f, "line": lineno, "kind": kind, "type": rtype,
                                "ref": tok, "status": "missing-script"})
                continue
            if rtype == "path" and not is_path_claim(tok, repo):
                continue
            status, hint = resolve(tok, f, repo)
            if status == "ok":
                continue
            raw.append({"doc": f, "line": lineno, "kind": kind, "type": rtype,
                        "ref": tok, "status": status, "hint": hint})

    # Local-only files (.env, build output) are absent by design.
    def forms(r: dict) -> tuple[str, str]:
        clean = LINE_SUFFIX.sub("", r["ref"]).rstrip("/")
        return clean, posixpath.normpath(posixpath.join(posixpath.dirname(r["doc"]), clean))

    tracked_sets: dict[str, set[str]] = {root: repo.tracked}

    def tracked_in(w: str, p: str) -> bool:
        """A file another worktree tracks is newer (or older) history, not a local-only file."""
        if w not in tracked_sets:
            tracked_sets[w] = set(git(w, "ls-files").splitlines())
        return posixpath.normpath(p) in tracked_sets[w]

    worktrees = [root] if "--no-live" in sys.argv else [root] + [l[9:] for l in git(root, "worktree", "list", "--porcelain").splitlines()
                          if l.startswith("worktree ") and l[9:] != root]
    raw += section_citations(repo, root, include_vendored, extra_vendored)
    raw += version_claims(repo, root, steering)
    paths = [p for r in raw if r["type"] == "path" or r["type"] == "link" or r["type"] == "import" for p in forms(r)]
    ignored = repo.ignored(paths)
    findings = []
    for r in raw:
        clean, relative = forms(r)
        if r["type"] in ("path", "link", "import") and (clean in ignored or relative in ignored):
            continue
        if r["type"] in ("path", "link", "import") and r["status"] in ("missing", "missing-name"):
            if relative.startswith("../") and clean.startswith("../"):
                r["status"] = "outside-repo"  # points out of the repository: never portable
                findings.append(r)
                continue
            here = next((w for w in worktrees for p in (clean, relative)
                         if not p.startswith("../") and os.path.exists(os.path.join(w, p))
                         and not tracked_in(w, p)), None)
            if here == root:
                # Present in this checkout only: works for the author, breaks
                # for every clone, CI run and cloud agent.
                r["status"] = "untracked"
            elif here:
                r["status"], r["hint"] = "other-worktree", f"exists untracked only in {here}"
            elif gone := (deleted_near(repo, clean, r["doc"]) or (deleted_in(repo, clean) if DISTINCT_NAME.search(clean) else None)
                          if r["kind"] in ("doc", "spec") and "/" not in clean else deleted_in(repo, clean)):
                r["status"], r["hint"] = "deleted", gone
        if r["kind"] in ("doc", "spec") and r["type"] == "path" and not belongs_here(r, repo):
            continue
        findings.append(r)

    return {
        "repo": root,
        "tracked_files": len(repo.files),
        "vendored_files_skipped": vendored_files,
        "always_loaded_bytes": sum(e["bytes"] for e in steering.get("always", [])),
        "steering": {k: sorted(v, key=lambda e: -e["bytes"]) for k, v in steering.items()},
        "findings": findings,
    }


def emit_json(result) -> bool:
    """--save=FILE writes JSON alongside the text view; --json prints only JSON."""
    save = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--save=")), None)
    if save:
        with open(save, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, default=list)
    if "--json" in sys.argv:
        json.dump(result, sys.stdout, indent=2, default=list)
        return True
    return False


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    result = scan(args[0] if args else ".", include_vendored="--include-vendored" in sys.argv)
    if emit_json(result):
        return
    show_all = "--all" in sys.argv
    ab = result["always_loaded_bytes"]
    print(f"repo: {result['repo']}  tracked files: {result['tracked_files']}"
          f"  vendored skipped: {result['vendored_files_skipped']}")
    print(f"always-loaded instructions: {ab} bytes (~{ab // 4} tokens on every turn)")
    for kind in ("always", "scoped", "on-demand", "config", "spec", "doc", "plan", "history", "payload"):
        items = result["steering"].get(kind, [])
        if items:
            top = ", ".join(f"{e['path']} ({e['bytes']}B)" for e in items[:5])
            more = f" +{len(items) - 5} more" if len(items) > 5 else ""
            print(f"  {kind:9} {len(items):4}  {top}{more}")

    f = result["findings"]
    print(f"\nbroken references: {len(f)}  {dict(Counter(x['status'] for x in f))}")
    order = ["always", "scoped", "on-demand", "spec", "doc", "code", "plan", "history", "payload"]
    for kind in order:
        group = [x for x in f if x["kind"] == kind]
        if not group:
            continue
        print(f"\n[{kind}] {len(group)}")
        if kind in ("plan", "history", "payload") and not show_all:
            per_doc = Counter(x["doc"] for x in group)
            for doc, n in per_doc.most_common(12):
                print(f"  {n:4}  {doc}")
            if len(per_doc) > 12:
                print(f"  ... {len(per_doc) - 12} more docs (use --all)")
            continue
        for x in sorted(group, key=lambda x: (x["doc"], x["line"])):
            hint = f"  ({x['hint']})" if x.get("hint") else ""
            print(f"  {x['doc']}:{x['line']}  {x['type']} `{x['ref']}`  {x['status']}{hint}")


if __name__ == "__main__":
    main()
