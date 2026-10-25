#!/usr/bin/env python3
"""List names the project retired that still appear in its files.

Reads commits whose subject says something was retired, removed, renamed or
replaced, takes the names they removed (deleted file stems, quoted or
capitalised terms in the subject), and counts where each still appears.
A survivor in an instruction file or doc tells an agent to use something
that is gone. Stdlib only; read-only.

Usage: retired_names.py [repo] [--since=12.months] [--json]
       retired_names.py [repo] --commit=SHA [--commit=SHA ...] [--json]   after-removal mode
       retired_names.py [repo] --range=BASE..HEAD [--json]                after-removal mode

After-removal mode takes everything the given commits removed, whatever their
subject says: deleted files, exported functions/classes/types, package.json
scripts and dependencies, env vars, and names in the subject. It lists every
line that still mentions one, so a removal can be finished the same day.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import DATED, NEGATED, emit_json, classify, git, is_vendored, vendored_roots  # noqa: E402

RETIRE = re.compile(
    r"\b(retire[ds]?|remov(e|ed|es|ing)|delet(e|ed|es|ing)|drop(s|ped)?|deprecat(e|ed|es)|"
    r"renam(e|ed|es)|replac(e|ed|es)|sunset|rip(ped)? out|kill(ed)?|migrat(e|ed) (off|away)|"
    r"retirement|move[sd]? out of)\b", re.I)
QUOTED = re.compile(r"[`\"“]([^`\"”]{3,40})[`\"”]")
PAREN = re.compile(r"\(([A-Z][\w .-]{2,30})\)")
# A capitalised name, keeping a version that follows it ("Opus 4.7", "GPT-5.2").
CAPITAL = re.compile(r"(?<![\w.])([A-Z][\w]*(?:[ -](?:[A-Z][\w]*|\d+(?:\.\d+)*))*)")
# "rename X to Y", "replace X with Y", "move X out of Y": only X is retired.
CONNECTOR = re.compile(r"\s(?:to|with|by|into|for|in favou?r of|→|->)\s", re.I)
CLAUSE_END = re.compile(r"[;:—]|\s-\s|,\s(?:and\s)?(?:add|record|keep|make|land|use|show|fix)\b", re.I)
# Kebab, snake or camel case: distinctive enough that a survivor is a real lead.
DISTINCT_STEM = re.compile(r"[a-z0-9][-_][a-z0-9]|[a-z][A-Z]")
# Words that are capitalised for grammar, not because they name something.
COMMON = set("""
The A An And Or Of For To In On With From Into Out Off Up Is Are Be It Its This That These
Those No Not Now New Old Dead Unused All Any Each Every Only When Where Why How What Which
Fix Feat Chore Docs Refactor Test Tests Perf Build Ci Merge Revert Release Remove Delete Drop
Retire Rename Replace Deprecate Move Add Make Keep Use Stop Clean Cleanup Land Finish Update
Let Say Show Run Check Cut Trim Mark Record Restore Retirement Rename Readme Todo Wip PR API
UI URL CLI JSON MCP CSS HTML JS TS Node Git GitHub Main Branch Tab Project File Files Code
Settings Mac I We You Our
""".split())
# Language keywords and literals: never a product name, whatever the casing.
KEYWORDS = set("true false none null nil self this undefined void super".split())
PROSE_EXTS = (".md", ".mdx", ".rst", ".txt")
GENERIC_STEMS = set("""
index main utils util types type helpers helper constants config test tests spec mod lib
common shared core base app page layout styles style readme changelog license package
""".split())


def is_common_word(term: str, common_words: set[str]) -> bool:
    """A single plain word (no digit, hyphen, underscore, dot or inner capital)
    that is ordinary prose in this repo, or a language keyword: "Site", "True"."""
    if " " in term:
        return False
    if term.lower() in KEYWORDS:
        return True
    if re.search(r"[\d._+/-]|[a-z][A-Z]", term):
        return False
    return term.lower() in common_words


def prose_words(repo: str) -> set[str]:
    """Lowercase words the project's own prose uses at least three times, from
    its Markdown, reStructuredText and text docs."""
    counts: Counter = Counter()
    budget = 8_000_000
    for p in git(repo, "ls-files").splitlines():
        if not p.lower().endswith(PROSE_EXTS):
            continue
        try:
            size = os.path.getsize(os.path.join(repo, p))
            if size > 400_000:
                continue
            budget -= size
            counts.update(re.findall(r"\b[a-z]{3,}\b", open(os.path.join(repo, p), encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
        if budget < 0:
            break
    return {w for w, n in counts.items() if n >= 3}


def retirements(repo: str, since: str) -> list[tuple[str, str, str]]:
    out = git(repo, "log", f"--since={since}", "--no-merges", "--format=%h%x09%as%x09%s")
    rows = []
    for line in out.splitlines():
        sha, date, subject = (line.split("\t", 2) + ["", ""])[:3]
        if RETIRE.search(subject):
            rows.append((sha, date, subject))
    return rows


def retired_segment(subject: str) -> str:
    """The words that name what was retired, not what replaced it."""
    body = re.sub(r"^\w+(\([^)]*\))?!?:\s*", "", subject)  # drop "chore(x): "
    m = RETIRE.search(body)
    if not m:
        return ""
    after = body[m.end():]
    before = body[:m.start()]
    verb = m.group(0).lower()
    if verb.startswith(("replac", "renam", "move")) and before.strip() and not CONNECTOR.search(after):
        # "browser_observe and browser_act replace the project app pair"
        return CLAUSE_END.split(after, 1)[0]
    after = CLAUSE_END.split(after, 1)[0]
    if verb.startswith(("replac", "renam", "move", "migrat")):
        after = CONNECTOR.split(after, 1)[0]
    return after


DEFINITION = re.compile(
    r"^-\s*(?:export\s+(?:default\s+)?(?:declare\s+)?(?:async\s+)?(?:function\*?|const|let|var|class|interface|type|enum)"
    r"|(?:def|class)|func(?:\s*\([^)]*\))?|pub(?:\(crate\))?\s+(?:fn|struct|enum|trait|const))\s+([A-Za-z_]\w{3,})")
ENV_REF = re.compile(r"(?:process\.env\.|import\.meta\.env\.|os\.environ\[[\"']|getenv\([\"']|env::var\(\")([A-Z][A-Z0-9_]{3,})")
JSON_KEY = re.compile(r'^-\s*"([@\w][\w@/.:-]{2,})"\s*:')
CODE_FILE = re.compile(r"\.(m?[jt]sx?|cjs|py|go|rs|rb|kt|swift|java|cs|php|ex)$")


def removed_identifiers(repo: str, sha: str) -> set[str]:
    """Names a commit defined-away: definitions, package.json keys and env reads that
    appear only on removed lines."""
    diff = git(repo, "show", "--format=", "--unified=0", "--no-color", sha)
    removed: set[str] = set()
    added_text = "\n".join(l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
    current = ""
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            current = line.split(" b/", 1)[-1]
            continue
        if not line.startswith("-") or line.startswith("---"):
            continue
        names = []
        if CODE_FILE.search(current):
            names += [m.group(1) for m in [DEFINITION.match(line)] if m]
            names += ENV_REF.findall(line)
        elif current.endswith("package.json"):
            names += [m.group(1) for m in [JSON_KEY.match(line)] if m]
        for n in names:
            # A generic word ("render", "init") is not distinctive enough to grep for.
            if (DISTINCT_STEM.search(n) or len(n) >= 10 or n.isupper() or "/" in n or "@" in n) \
                    and not re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", added_text):
                removed.add(n)
    return removed


def terms_from(repo: str, sha: str, subject: str, common_words: set[str], force: bool = False) -> set[str]:
    segment = retired_segment(subject) or (re.sub(r"^\w+(\([^)]*\))?!?:\s*", "", subject) if force else "")
    terms = set()
    in_code = set()  # `repairing`: the commit marks it as an identifier on purpose
    for m in QUOTED.finditer(segment):
        terms.add(m.group(1).strip())
        if m.group(0)[0] == "`":
            in_code.add(m.group(1).strip())
    for m in PAREN.finditer(segment):
        terms.add(m.group(1).strip())
    for m in CAPITAL.finditer(segment):
        word = m.group(1).strip(" -")
        parts = word.split()
        if all(w in COMMON for w in parts):
            continue
        if any(word in q for q in terms):
            continue
        terms.add(word)
    # The diff is the evidence: a retiring commit removes the name and doesn't
    # add it back. "Record the Premium retirement in OpenSpec" adds OpenSpec
    # lines; "Remove 'Make a list' under the search" removes one placement.
    diff = git(repo, "show", "--format=", "--unified=0", "--no-color", sha)
    removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    low_removed = [l.lower() for l in removed]
    low_added = [l.lower() for l in added]
    terms = {t for t in terms
             if (r := sum(t.lower() in l for l in low_removed)) >= 2 and r >= 3 * sum(t.lower() in l for l in low_added)}
    # --raw shows the old mode; 120000 is a symlink, whose removal retires
    # the link, not the name it pointed at.
    raw = git(repo, "show", "--diff-filter=D", "--raw", "--no-abbrev", "--format=", sha)
    for line in raw.splitlines():
        meta, _, path = line.partition("\t")
        if not path or meta.split()[0] == ":120000":
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        stem = re.sub(r"\.(test|spec|stories|d)$", "", stem)
        if len(stem) >= 6 and stem.lower() not in GENERIC_STEMS and DISTINCT_STEM.search(stem):
            terms.add(stem)
    # Names are identifiers or product words, not quoted UI strings ("now $0"),
    # and a lone English word ("Still", "Site", "True") names nothing however it got here.
    return {t for t in terms if len(t) >= 4 and re.fullmatch(r"[A-Za-z][\w .+/-]*", t)
            and not is_common_word(t, set() if t in in_code else common_words)}


def text_files(repo: str):
    """(path, kind, text) for every tracked, non-vendored text file under 1 MB."""
    extra = vendored_roots(repo)
    for path in git(repo, "ls-files").splitlines():
        if is_vendored(path, extra):
            continue
        full = os.path.join(repo, path)
        try:
            if os.path.getsize(full) > 1_000_000:
                continue
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        yield path, classify(path), data.decode("utf-8", "replace")


def after_removal(repo: str, shas: list[str]) -> list[dict]:
    live_stems = {os.path.splitext(os.path.basename(p))[0].lower() for p in git(repo, "ls-files").splitlines()}
    common_words = prose_words(repo)
    terms: dict[str, str] = {}
    for sha in shas:
        subject = git(repo, "log", "-1", "--format=%h %as %s", sha).strip()
        found = terms_from(repo, sha, subject.split(" ", 2)[-1], common_words, force=True) | removed_identifiers(repo, sha)
        for t in found:
            if t.lower() not in live_stems:
                terms.setdefault(t, subject)
    if not terms:
        return []
    alt = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    mention = re.compile(rf"(?<![\w-])({alt})(?![\w-])")
    # Still defined, read as an env var, or a package.json key somewhere: the
    # commit removed one copy, not the name.
    defined = re.compile(
        rf"(?:(?:function\*?|const|let|var|class|interface|type|enum|def|func|fn|struct|trait)\s+|"
        rf"env\.|environ\[[\"']|getenv\([\"']|env::var\(\"|^\s*\")({alt})\b(?:\"\s*:)?", re.M)
    alive: set[str] = set()
    lines: dict[str, list[dict]] = defaultdict(list)
    for path, kind, text in text_files(repo):
        if not mention.search(text):
            continue
        for m in defined.finditer(text):
            if not m.group(0).lstrip().startswith('"') or m.group(0).rstrip().endswith(":"):
                alive.add(m.group(1))
        if (kind or "code") in ("history", "payload") or DATED.search(path):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if NEGATED.search(line):
                continue  # "replaced X", "X was removed": describes the removal
            for t in set(mention.findall(line)):
                if len(lines[t]) < 40:
                    lines[t].append({"at": f"{path}:{i}", "kind": kind or "code"})
    weight = {"always": 20, "scoped": 8, "on-demand": 5, "config": 5, "spec": 6, "doc": 2, "plan": 1}
    results = [{"term": t, "retired_in": subj, "lines": lines[t],
                "weight": sum(weight.get(r["kind"], 1) for r in lines[t])}
               for t, subj in terms.items() if lines.get(t) and t not in alive]
    return sorted(results, key=lambda r: -r["weight"])


def scan_files(repo: str, terms: list[str]) -> dict[str, dict[str, list[str]]]:
    """One pass over every tracked text file; case-sensitive whole-name matches."""
    found: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    if not terms:
        return found
    pattern = re.compile(
        r"(?<![\w-])(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")(?![\w-])"
    )
    extra = vendored_roots(repo)
    for path in git(repo, "ls-files").splitlines():
        if is_vendored(path, extra):
            continue
        kind = classify(path)
        if kind is None and DATED.search(path):
            continue  # dated JSON/HTML records, like dated docs, are history
        if kind in ("history", "plan", "payload"):
            continue
        full = os.path.join(repo, path)
        try:
            if os.path.getsize(full) > 1_000_000:
                continue
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        for term in set(pattern.findall(text)):
            found[term][kind or "code"].append(path)
    return found


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    since = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--since=")), "12.months")
    repo = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    shas = [a.split("=", 1)[1] for a in sys.argv if a.startswith("--commit=")]
    rng = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--range=")), None)
    if rng:
        shas += git(repo, "rev-list", "--no-merges", rng).split()
    if shas:
        results = after_removal(repo, shas)
        if emit_json(results):
            return
        print(f"repo: {repo}  after-removal check of {len(shas)} commit(s): {len(results)} removed names still mentioned")
        for r in results[:40]:
            print(f"  {r['term']!r}  ({r['retired_in'][:90]})")
            for row in r["lines"][:8]:
                print(f"      [{row['kind']}] {row['at']}")
            if len(r["lines"]) > 8:
                print(f"      ... +{len(r['lines']) - 8} more")
        return
    # A name that is still a live file stem was replaced in one place, not retired.
    live_stems = {os.path.splitext(os.path.basename(p))[0].lower()
                  for p in git(repo, "ls-files").splitlines()}
    # Lowercase words in the project's own prose: a capitalised word that is
    # also ordinary prose here ("still", "back") is grammar, not a name.
    common_words = prose_words(repo)
    seen_terms: dict[str, tuple[str, str, str]] = {}
    for sha, date, subject in retirements(repo, since):
        for term in terms_from(repo, sha, subject, common_words):
            key = term.lower()
            if key in live_stems or any(t.lower() == key for t in seen_terms):
                continue
            seen_terms.setdefault(term, (sha, date, subject))  # newest retirement wins

    found = scan_files(repo, list(seen_terms))
    results = []
    for term, (sha, date, subject) in seen_terms.items():
        hits = found.get(term)
        if not hits:
            continue
        # Instruction files reach every turn; weight them above docs and code.
        weight = sum({"always": 20, "scoped": 8, "on-demand": 5, "config": 5, "spec": 6, "doc": 2}.get(k, 1) * len(v)
                     for k, v in hits.items())
        results.append({"term": term, "retired_in": f"{sha} {date} {subject}",
                        "weight": weight, "hits": {k: sorted(v) for k, v in hits.items()}})
    results.sort(key=lambda r: -r["weight"])

    if emit_json(results):
        return
    print(f"repo: {repo}  retirement commits since {since}: {len(set(v[0] for v in seen_terms.values()))}"
          f"  retired names: {len(seen_terms)}  still present: {len(results)}")
    for r in results[:40]:
        counts = ", ".join(f"{k} {len(v)}" for k, v in sorted(r["hits"].items(), key=lambda kv: -len(kv[1])))
        sample = next((v[0] for k in ("always", "scoped", "on-demand", "config", "spec", "doc", "code")
                       if (v := r["hits"].get(k))), "")
        print(f"  {r['term']!r:32} {counts:34} e.g. {sample}")
        print(f"  {'':32} retired: {r['retired_in'][:110]}")


if __name__ == "__main__":
    main()
