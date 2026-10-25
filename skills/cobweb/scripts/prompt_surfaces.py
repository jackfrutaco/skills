#!/usr/bin/env python3
"""Stale text in the places that steer a shipped AI agent.

Products that ship an agent steer it with text inside code: system prompts and
prompt templates, tool descriptions (MCP `description`, zod `.describe()`, JSON
schema), reminder strings, and shipped skills. Stale text there reaches every
user's agent. Read-only, stdlib only.

It extracts string literals and comments from JS/TS (a small state machine:
quotes, template literals with nested ${}, regex literals, comments; Go reuses it,
Python uses tokenize), marks the prompt-like ones (>=120 chars with a prompt shape)
and the descriptions, measures them, then checks:
  A  dead pointers        a repo path in a prompt, description or comment that is gone
                          and that git history says was deleted or renamed
  B  settings breadcrumbs "Settings -> X" / "in X settings" naming a label the
                          settings or navigation source does not have
  C  orphan tool names    `mcp__server__tool` or backticked snake_case a prompt or
                          shipped skill names that nothing in the code registers
  D  prompt builders      exported build*Prompt/Block/Guidance/Instructions that only
                          tests, tools, scripts or evals import
  E  model drift          claude-<tier>-N and gpt-N IDs older than the generation the
                          repo itself uses in two or more files, in prompts and config
  F  shipped-skill hygiene  links that climb out of the skill folder; "unreleased",
                          "development checkout", "disposable QA" in shipped text
  G  banned vocabulary    words the repo's own rules say never to show, in prose literals

The scan runs only where the repo shows agent code: a dependency on an LLM or agent SDK, a
tool registration it can harvest, or a shipped SKILL.md. Anywhere else it reports
{"agent_code": false} and no findings (a docstring's parameter names and a shell completion
template are not prompts). Python docstrings are read as comments, never as prompt literals.

Usage: prompt_surfaces.py <repo> [--json] [--save=FILE] [--all]
  --all   print every finding in the text view, not the first few per check
"""

from __future__ import annotations

import bisect
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import time
import tokenize
from concurrent.futures import ThreadPoolExecutor
from collections import Counter, defaultdict
from io import StringIO

sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from steering_refs import (  # noqa: E402
    FILE_EXTS, LINK, NEGATED, Repo, classify, deleted_in, emit_json, git, is_path_claim, is_vendored, resolve,
    vendored_roots,
)

GREP_EXTS = "ts tsx js jsx mjs cjs mts cts py go rs json jsonc yaml yml toml sh swift kt java rb".split()
JS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".go"}  # Go shares the JS scanner
PY_EXT = {".py"}
MD_EXT = {".md", ".mdx"}
CONFIG_EXT = {".json", ".jsonc", ".yaml", ".yml", ".toml"}
PROMPT_FILE_EXT = {".txt", ".yaml", ".yml", ".prompt", ".j2", ".hbs"}
MAX_BYTES = 1_500_000

TESTISH = re.compile(r"(^|/)(tests?|__tests__|specs?|e2e|fixtures?|__mocks__|testdata|__snapshots__|harness-evals?|evals?)/|"
                     r"[._-](test|spec|stories|eval|fixtures?)\.[a-z]+$|(^|/)(test_[^/]*\.py|conftest\.py|[^/]*_test\.go)$")
GENERATED = re.compile(r"(\.min\.js|\.d\.ts|\.generated\.\w+|\.gen\.\w+|\.snap|\.map)$|"
                       r"(^|/)(generated|_generated|__generated__|dist|build|\.tatastu-sketches|\.2code)/")
TEST_IMPORTER = re.compile(r"^(tools|scripts|tests?|evals?|e2e|bench|benchmarks?)/|(^|/)(tests?|__tests__|evals?|"
                           r"harness-evals?|e2e|fixtures?)/|[._-](test|spec|eval)\.[a-z]+$")

# ---------------------------------------------------------------- extraction

SHAPE = re.compile(r"\bYou are\b|\bYou're\b|\bMUST\b|\bNEVER\b|\bNever\b|\bDO NOT\b|\bDo not\b|<system-reminder>|"
                   r"(?m:^#{1,4} \S)")
IMPERATIVES = set("""
use call run do don't never always avoid prefer keep ensure make write read ask check send return pass set include
treat add remove create delete update verify confirm report explain show tell say stop start wait retry open close
list find search fetch apply follow respect mention note remember put take give choose pick provide specify wrap
group batch merge summarize state name output respond reply answer skip only ignore assume mark inspect compare
""".split())
SENTENCE = re.compile(r"(?<=[.!?:])\s+|\n+|\\n")
DESC_BEFORE = re.compile(r"""(?:\bdescription|\bdescribe)["']?\s*(?:[:=]|\(|\)\s*\()\s*(?:\(\s*)?$|"""
                         r"""(?:DESCRIPTION|PROMPT|INSTRUCTIONS|GUIDANCE|REMINDER)\w*\s*(?::[^=\n]{1,60})?=\s*[\[(]?\s*$""")
GAP = re.compile(r"\s*[,+]?\s*")
NL = re.compile(r"\n")

CAND = re.compile(r"""['"`/]""")
CAND_B = re.compile(r"""['"`/{}]""")
SQ = re.compile(r"'(?:[^'\\\n]|\\[\s\S])*'")
DQ = re.compile(r'"(?:[^"\\\n]|\\[\s\S])*"')
RE_LIT = re.compile(r"/(?![/*])(?:[^/\\\[\n]|\\.|\[(?:[^\]\\\n]|\\.)*\])+/[a-z]*")
TPL_SPECIAL = re.compile(r"[`\\$]")
REGEX_KEYWORDS = {"return", "typeof", "case", "in", "of", "delete", "void", "throw", "new", "else", "do", "yield", "await"}
WORD_END = re.compile(r"([A-Za-z]+)$")


class Piece:
    __slots__ = ("s", "e", "kind", "masks", "nested", "value_cache")

    def __init__(self, s: int, e: int, kind: str, masks=(), nested: bool = False):
        self.s, self.e, self.kind, self.masks, self.nested = s, e, kind, masks, nested


def scan_js(text: str) -> tuple[list[Piece], list[tuple[int, int]]]:
    """Return (string/template pieces, comment spans). Offsets index `text`."""
    pieces: list[Piece] = []
    comments: list[tuple[int, int]] = []
    n = len(text)

    def scan(i: int, in_expr: bool, depth_nested: bool) -> int:
        cand = CAND_B if in_expr else CAND
        depth = 0
        while True:
            m = cand.search(text, i)
            if not m:
                return n
            pos = m.start()
            ch = text[pos]
            if ch == "{":
                depth += 1
                i = pos + 1
            elif ch == "}":
                if depth == 0:
                    return pos + 1
                depth -= 1
                i = pos + 1
            elif ch == "'" or ch == '"':
                if ch == "'" and pos and (text[pos - 1].isalnum() or text[pos - 1] == "_"):
                    i = pos + 1  # an apostrophe in JSX text or a doc comment, not a string
                    continue
                sm = (SQ if ch == "'" else DQ).match(text, pos)
                if sm:
                    pieces.append(Piece(pos, sm.end(), "s", (), depth_nested or in_expr))
                    i = sm.end()
                else:
                    i = pos + 1
            elif ch == "`":
                i = scan_template(pos, depth_nested or in_expr)
            else:  # "/"
                nxt = text[pos + 1:pos + 2]
                if nxt == "/":
                    j = text.find("\n", pos)
                    j = n if j < 0 else j
                    comments.append((pos, j))
                    i = j
                elif nxt == "*":
                    j = text.find("*/", pos + 2)
                    j = n if j < 0 else j + 2
                    comments.append((pos, j))
                    i = j
                else:
                    k = pos - 1
                    while k >= 0 and text[k] in " \t\r\n":
                        k -= 1
                    prev = text[k] if k >= 0 else ""
                    division = bool(prev) and (prev in ")]}\"'`" or prev.isalnum() or prev in "_$")
                    if division and prev.isalpha():
                        wm = WORD_END.search(text, max(0, k - 10), k + 1)
                        if wm and wm.group(1) in REGEX_KEYWORDS:
                            division = False
                    if not division:
                        rm = RE_LIT.match(text, pos)
                        i = rm.end() if rm else pos + 1
                    else:
                        i = pos + 1

    def scan_template(start: int, nested: bool) -> int:
        i = start + 1
        masks: list[tuple[int, int]] = []
        while True:
            m = TPL_SPECIAL.search(text, i)
            if not m:
                pieces.append(Piece(start, n, "t", tuple(masks), nested))
                return n
            pos = m.start()
            ch = text[pos]
            if ch == "`":
                pieces.append(Piece(start, pos + 1, "t", tuple(masks), nested))
                return pos + 1
            if ch == "\\":
                i = pos + 2
            elif text.startswith("{", pos + 1):
                j = scan(pos + 2, True, True)
                masks.append((pos, j))
                i = j
            else:
                i = pos + 1

    scan(0, False, False)
    pieces.sort(key=lambda p: p.s)
    return pieces, comments


def scan_py(text: str) -> tuple[list[Piece], list[tuple[int, int]]]:
    starts = [0]
    for m in NL.finditer(text):
        starts.append(m.end())
    pieces: list[Piece] = []
    comments: list[tuple[int, int]] = []
    # A string that is the first statement of a module, class or def is documentation for
    # people: it goes with the comments, not with the prompt-like literals.
    module_first, line_first, at_start = True, "", True
    expect_doc = saw_indent = False
    try:
        for tok in tokenize.generate_tokens(StringIO(text).readline):
            if tok.type == tokenize.NEWLINE:
                expect_doc, saw_indent, at_start = line_first in ("def", "class", "async"), False, True
                continue
            if tok.type == tokenize.INDENT:
                saw_indent = expect_doc
                continue
            if tok.type in (tokenize.NL, tokenize.DEDENT, tokenize.ENCODING):
                continue
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                if at_start:
                    line_first, at_start = tok.string, False
                expect_doc = saw_indent = module_first = False
                continue
            s = starts[tok.start[0] - 1] + tok.start[1]
            e = starts[tok.end[0] - 1] + tok.end[1]
            if tok.type == tokenize.COMMENT:
                comments.append((s, e))
                continue
            if module_first or (expect_doc and saw_indent):
                comments.append((s, e))
                module_first = expect_doc = saw_indent = False
                at_start = False
                continue
            if at_start:
                line_first, at_start = "", False
            module_first = expect_doc = saw_indent = False
            pieces.append(Piece(s, e, "py"))
    except (tokenize.TokenError, IndentationError, SyntaxError, IndexError):
        pass
    return pieces, comments


def piece_value(text: str, p: Piece) -> str:
    """The literal's text, same length as the source slice so offsets map back."""
    if p.kind == "py":
        return text[p.s:p.e]
    raw = text[p.s + 1:p.e - 1]
    if not p.masks:
        return raw
    chars = list(raw)
    for a, b in p.masks:
        for k in range(max(a - p.s - 1, 0), min(b - p.s - 1, len(chars))):
            if chars[k] != "\n":
                chars[k] = "\x01"
    return "".join(chars)


class FileText:
    """A file's text with lazy line lookup."""

    def __init__(self, path: str, text: str):
        self.path, self.text = path, text
        self._nl: list[int] | None = None

    def line(self, off: int) -> int:
        if self._nl is None:
            self._nl = [m.start() for m in NL.finditer(self.text)]
        return bisect.bisect_left(self._nl, off) + 1


CODEY = re.compile(r"[{};=()<>\[\]]")
SHELL_LINE = re.compile(
    r"(?m)^[ \t]*(?:local[ \t]+\w|\w+=\S|\w+\(\)[ \t]*\{|if[ \t]+\[|fi[ \t]*$|then[ \t]*$|else[ \t]*$|esac[ \t]*$|"
    r"done[ \t]*$|case[ \t]|for[ \t]+\w+[ \t]+in[ \t]|compgen\b|complete[ \t]+-|compdef\b|export[ \t]+\w+=|\[\[|"
    r"\$\{|\$\w+[ \t]*=|function[ \t]+[\w:-]+|Register-ArgumentCompleter|\}[ \t]*$|set[ \t]+-\w|end[ \t]*$|"
    r"echo[ \t]|complete[ \t]|commandline\b)")
FORMAT_SLOT = re.compile(r"%\[\d+\][sdqv]|\{\{-?[ \t]*[.\w]")


def is_shell_or_template(joined: str) -> bool:
    """An embedded shell script or template (a CLI's completion scripts): not instructions."""
    if joined.lstrip().startswith("#!"):
        return True
    lines = joined.count("\n") + 1
    hits = len(SHELL_LINE.findall(joined))
    if len(FORMAT_SLOT.findall(joined)) >= 5 and hits >= 3:
        return True  # a printf or text/template body around script lines
    return hits >= 6 and hits * 5 >= lines


def is_prompt_like(joined: str) -> bool:
    if len(joined) < 120:
        return False
    if is_shell_or_template(joined):
        return False
    if len(CODEY.findall(joined)) > 0.08 * len(joined) and not re.search(r"\bYou are\b|<system-reminder>", joined):
        return False  # an embedded script or shader, not instructions
    if SHAPE.search(joined):
        return True
    count = 0
    for sentence in SENTENCE.split(joined):
        words = sentence.strip().lstrip("-*#0123456789.) `").split()
        if len(words) >= 3 and words[0].lower().strip("`*_,:") in IMPERATIVES:
            count += 1
            if count >= 4:
                return True
    return False


def clusters(text: str, pieces: list[Piece]) -> list[list[Piece]]:
    """Group literals separated only by a comma or `+` (arrays of lines, concatenation)."""
    out: list[list[Piece]] = []
    cur: list[Piece] = []
    for p in pieces:
        if p.nested:
            out.append([p])
            continue
        if cur and p.s >= cur[-1].e and p.s - cur[-1].e <= 40 and GAP.fullmatch(text[cur[-1].e:p.s]):
            cur.append(p)
        else:
            if cur:
                out.append(cur)
            cur = [p]
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------- patterns

PATHISH = re.compile(r"(?<![\w@./:~$-])((?:\.{1,2}/)?[\w.-]+(?:/[\w.@+-]+)+/?)")
SETTINGS_ARROW = re.compile(r"\bSettings\s*(?:→|->|›|»|>)\s*[`*_\"“']*([^\n→›»]{1,80})")
NAMED_SETTINGS = re.compile(r"\b(?:in|from|under|open|opens|on|to)\s+(?:the\s+)?((?:[A-Z][A-Za-z]+)(?: [A-Z][A-Za-z]+){0,2}) settings\b")
OTHER_APP = re.compile(r"(?:1Password|Xcode|macOS|System|iOS|iPhone|iPad|Android|Chrome|Safari|Firefox|Windows|GitHub|"
                       r"Cloudflare|Railway|Vercel|Slack|Google|Apple|Docker|Raycast|Zoom|Discord|Notion|Linear|Figma|"
                       r"VS ?Code|Claude|Codex|Cursor|Brave|Edge|Stripe|Resend|Supabase|Netlify|AWS|Azure|Jira|npm|Git|"
                       r"Terminal|iTerm|Finder|Homebrew|Wi-?Fi|Bluetooth|Screen Time|WSL|BIOS|Linux|Ubuntu|Gmail)['’]?s?\s*$")
OS_LABELS = {"privacy", "privacy & security", "security", "accessibility", "bluetooth", "wi-fi", "wifi", "network",
             "apple id", "screen recording", "full disk access", "automation", "camera", "microphone", "notifications",
             "developer", "passwords", "siri", "display", "sound", "keyboard", "battery", "apps", "advanced"}
SEG_CUT = re.compile(r"\*\*|`|\"|”|'(?!\w)|[.,;:)(]\s|[.,;:)(]$|\s—\s|\s-\s|\s(?:to|and|or|then|so|if|for|when|where|in|on|instead|rather|from|into|under|page|tab|section|menu|screen|"
                     r"panel|pane)\b|\s\s")
NAV_TOKENS = {"nav", "navigation", "sidebar", "menu", "pages", "sections", "routes", "tabs"}


def is_nav_file(path: str) -> bool:
    """A file that lists the settings or navigation destinations (settings-pages.ts, SettingsSidebarNav.tsx)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    toks = [t.lower() for t in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", stem)]
    return bool(NAV_TOKENS & set(toks)) or toks == ["settings"] or toks[:2] == ["settings", "search"] \
        or toks[:2] == ["settings", "dialog"] or toks[:2] == ["settings", "modal"] \
        or toks == ["settings", "route", "screen"]


LABEL_PROP = re.compile(r"""\b(?:label|title|name|text|heading|displayName|tabLabel|aria-label)["']?\s*[:=]\s*\{?["'`]([^"'`\n]{2,40})["'`]""")
MCP_REF = re.compile(r"\bmcp__([A-Za-z0-9_-]+?)__([A-Za-z0-9_-]+)")
SNAKE_TICK = re.compile(r"\\?`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\\?`")
TOOL_CONTEXT = re.compile(r"\b(?:tools?|call|calls|called|invoke|use|using|server|MCP)\b", re.I)
HOST_TOOLS = set("""
update_plan request_user_input exit_plan_mode enter_plan_mode apply_patch local_shell view_image web_search web_fetch
str_replace_editor str_replace_based_edit_tool read_file write_file list_dir list_directory spawn_agent send_input
wait_agent close_agent resume_agent text_editor bash_output kill_shell ask_user_question todo_write multi_edit
notebook_edit list_mcp_resources read_mcp_resource shell_command exec_command write_stdin image_gen tool_search
tool_use tool_result tool_call tool_calls function_call computer_use code_interpreter file_search
""".split())
TOOL_REGISTRATIONS = [
    re.compile(r"""\bTool\.make\(\s*["']([\w.-]+)["']"""),
    re.compile(r"""\.tool\(\s*["']([\w.-]+)["']"""),
    re.compile(r"""\bregisterTool\(\s*["']([\w.-]+)["']"""),
    re.compile(r"""\btool\(\s*["']([\w.-]+)["']\s*,"""),
    re.compile(r"""\b[A-Z][A-Z0-9_]*_TOOL_NAMES?\s*(?::[^=\n]+)?=\s*["']([\w.-]+)["']"""),
    re.compile(r"""@mcp\.tool(?:\([^)]*name\s*=\s*["']([\w.-]+)["'][^)]*\))?\s*\n\s*(?:async\s+)?def\s+(\w+)"""),
    re.compile(r"""\bmcp\.NewTool\(\s*"([\w.-]+)\""""),
]
NAME_LITERAL = re.compile(r"""\bname\s*:\s*["']([a-z][\w.-]*)["']""")
SERVER_REGISTRATIONS = [
    re.compile(r"""createSdkMcpServer\(\s*\{[^}]{0,200}?\bname\s*:\s*["']([\w-]+)["']"""),
    re.compile(r"""\bserverName\s*:\s*["']([\w-]+)["']"""),
    re.compile(r"""\b[A-Z][A-Z0-9_]*_SERVER_NAME\s*=\s*["']([\w-]+)["']"""),
    re.compile(r"""\bnew McpServer\(\s*\{\s*name\s*:\s*["']([\w-]+)["']"""),
    re.compile(r"""\bFastMCP\(\s*["']([\w-]+)["']"""),
    re.compile(r"""\bNewMCPServer\(\s*"([\w-]+)\""""),
]
BUILDER_EXPORT = re.compile(r"^[ \t]*export\s+(?:async\s+)?(?:function\*?\s+|const\s+)"
                            r"(build\w*(?:Prompt|Block|Guidance|Instructions))\b", re.M)
CLAUDE_ID = re.compile(r"\bclaude-(opus|sonnet|haiku|fable)-(\d+)(?:-(\d{1,2}))?(?!\d)|"
                       r"\bclaude-(\d+)(?:-(\d{1,2}))?-(opus|sonnet|haiku)(?!\w)")
GPT_ID = re.compile(r"\bgpt-(\d+)(?:\.(\d+))?(?![\d.]?\d)(?:-([a-z]+))?")
BAN_TRIGGER = re.compile(r"\b(?:never|do not|don'?t|must not|avoid)\s+(?:call|say|show|use|name|write|label|refer to|"
                         r"display|put|mention|print|tell|title|describe)\b", re.I)
BAN_QUOTED = re.compile(r"[\"“]([A-Za-z][A-Za-z -]{1,28}[A-Za-z])[\"”]")
RULE_FILE = re.compile(r"(^|/)(AGENTS|CLAUDE|GEMINI)\.md$|^docs/agents/[^/]+\.md$|(^|/)DESIGN\.md$|"
                       r"^(docs|design|\.agents/design)/(?:[^/]+/)*design[^/]*\.md$|^\.claude/rules/|^\.cursor/rules/", re.I)
VENDOR_BEFORE = re.compile(r"(?:Railway|Vercel|Slack|Linear|Notion|Google|Cloudflare|Supabase|Figma|Terraform|Datadog|"
                           r"Sentry|Stripe|Xcode|VS ?Code|JetBrains|Jira|Asana|Airtable|Azure|AWS|GitHub|Bitbucket|"
                           r"Conductor|Cursor|Windsurf|Zed|Claude|Slack's)['’]?\s+$")
SQLISH = re.compile(r"\b(?:SELECT|FROM|JOIN|INSERT INTO|DELETE FROM|WHERE|GROUP BY)\b")
LOG_CALL = re.compile(r"(?:console|logger|log)\.\w+\(\s*$|\b(?:logger?|debug|trace|warn)\(\s*$")
JSX_TEXT = re.compile(r">([^<>{}\n;=]{12,200})<")
RELEASE_WORDS = re.compile(r"\bunreleased\b|\bdevelopment checkout\b|\bdisposable QA\b", re.I)
VENDOR_NAMES = ("railway", "vercel", "slack", "linear", "notion", "supabase", "figma", "stripe", "github", "cloudflare",
                "netlify", "datadog", "sentry", "zernio")
DEV_TOOLING = re.compile(r"^(scripts|tools|design|documents|openspec|docs)/|(^|/)scripts/")
FENCE_LINE = re.compile(r"^\s*(```|~~~)")


def words(s: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z']*", s))


def mask_fences(md: str) -> str:
    out, in_fence = [], False
    for line in md.split("\n"):
        if FENCE_LINE.match(line):
            in_fence = not in_fence
            out.append(re.sub(r"[^\n]", " ", line))
        elif in_fence:
            out.append(re.sub(r"[^\n]", " ", line))
        else:
            out.append(line)
    return "\n".join(out)


def window(text: str, pos: int, before: int = 100, after: int = 40) -> str:
    return text[max(0, pos - before):pos + after]


def model_version(m: re.Match) -> tuple[str, tuple[int, int]]:
    if m.group(0).startswith("claude"):
        if m.group(1):
            return "claude-" + m.group(1), (int(m.group(2)), int(m.group(3) or 0))
        return "claude-" + m.group(6), (int(m.group(4)), int(m.group(5) or 0))
    return "gpt", (int(m.group(1)), int(m.group(2) or 0))


# ----------------------------------------------------------------------- scan

# ---------------------------------------------------------------- agent signals

MANIFESTS = {"package.json": "npm", "pyproject.toml": "toml-py", "Pipfile": "toml-py", "setup.cfg": "cfg",
             "setup.py": "setup-py", "go.mod": "go", "Cargo.toml": "toml-rs", "Gemfile": "ruby", "*.gemspec": "ruby"}
JS_SDK = re.compile(r"^(anthropic|openai|ai|langchain|llamaindex|ollama|groq-sdk|cohere-ai|litellm|@google/genai|"
                    r"@google/generative-ai|@anthropic-ai/.+|@modelcontextprotocol/.+|@ai-sdk/.+|@langchain/.+|"
                    r"@llamaindex/.+|@openai/.+|@mistralai/.+|@mastra/.+|@openrouter/.+)$")
PY_SDK = re.compile(r"^(anthropic|openai|langchain|langchain-.+|langgraph|langgraph-.+|llama-index|llama-index-.+|"
                    r"llamaindex|google-genai|google-generativeai|google-adk|ollama|mcp|fastmcp|litellm|"
                    r"claude-agent-sdk|claude-code-sdk|openai-agents|pydantic-ai|pydantic-ai-slim|crewai|smolagents|"
                    r"pyautogen|autogen-agentchat|mistralai|cohere|groq|instructor)$")
GO_SDK = ("anthropics/anthropic-sdk-go", "liushuangls/go-anthropic", "sashabaranov/go-openai", "openai/openai-go",
          "modelcontextprotocol/", "mark3labs/mcp-go", "tmc/langchaingo", "google/generative-ai-go",
          "googleapis/go-genai", "ollama/ollama", "cloudwego/eino", "firebase/genkit")
RS_SDK = {"async-openai", "anthropic", "rmcp", "genai", "ollama-rs", "langchain-rust", "rig-core", "misanthropy"}
RB_SDK = {"ruby-openai", "anthropic", "ruby-anthropic", "ruby_llm", "langchainrb", "mcp", "openai"}
QUOTED = re.compile(r"""["']\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*(?:[<>=!~;@ ,]|["'])""")


def toml_dependencies(text: str) -> list[str]:
    """Dependency names from pyproject.toml, Pipfile or Cargo.toml: keys of a *dependencies table and the
    strings in a dependencies array (keywords and descriptions are not dependencies)."""
    out: list[str] = []
    section, in_array = "", False
    for line in text.splitlines():
        s = line.strip()
        if in_array:
            out += QUOTED.findall(s)
            in_array = "]" not in s
            continue
        if s.startswith("["):
            if not s.startswith("[["):
                section = s.strip("[] \t").lower()
            continue
        key = re.match(r"""^["']?([A-Za-z0-9._-]+)["']?\s*=\s*(.*)$""", s)
        if not key:
            continue
        name, rest = key.group(1), key.group(2)
        if "dependenc" in section and not rest.startswith("["):
            out.append(name)
        elif rest.startswith("[") and ("dependenc" in section or re.search(r"dependenc|requires", name)):
            out += QUOTED.findall(rest[1:])
            in_array = "]" not in rest
    return out


def manifest_dependencies(kind: str, text: str) -> list[str]:
    if kind == "npm":
        try:
            data = json.loads(text)
        except ValueError:
            return []
        return [n for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies")
                for n in (data.get(field) or {}) if isinstance(data.get(field), dict)]
    if kind == "pip":
        return [m.group(1) for line in text.splitlines() if (m := re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", line))
                and not line.lstrip().startswith(("-", "#"))]
    if kind in ("toml-py", "toml-rs"):
        return toml_dependencies(text)
    if kind == "cfg":
        m = re.search(r"(?ms)^install_requires\s*=(.*?)(?=^\S)", text)
        return [x.group(1) for x in re.finditer(r"(?m)^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", m.group(1))] if m else []
    if kind == "setup-py":
        return QUOTED.findall(text)
    if kind == "go":
        return re.findall(r"(?m)^\s*(?:require\s+)?([\w.-]+\.[\w.-]+/[\w./-]+)\s+v", text)
    if kind == "ruby":
        return re.findall(r"""(?m)^\s*(?:gem|\w+\.add(?:_runtime|_development)?_dependency)\s*\(?\s*["']([\w.-]+)["']""", text)
    return []


def agent_dependency(kind: str, name: str) -> bool:
    if kind == "npm":
        return bool(JS_SDK.match(name))
    if kind in ("pip", "toml-py", "cfg", "setup-py"):
        return bool(PY_SDK.match(re.sub(r"[._]+", "-", name.lower())))
    if kind == "go":
        return any(g in name for g in GO_SDK)
    if kind == "toml-rs":
        return name in RS_SDK
    return name in RB_SDK


class Scan:
    def __init__(self, root: str):
        self.root = root
        self.repo = Repo(root)
        self.vroots = vendored_roots(root)
        self.findings: list[dict] = []
        self.files = {}  # path -> {"spans": [(s, e, kind)]}
        self.stats = {}  # path -> {"literals", "bytes", "descriptions"}
        self.registry: set[str] = set()        # label-like properties in settings/navigation files
        self.registry_loose: set[str] = set()  # any capitalised UI string in a settings or navigation path
        self.registry_files: set[str] = set()
        self.registered: set[str] = set()
        self.servers: set[str] = set()
        self.builders: dict[str, str] = {}
        self.mentions: dict[str, list[dict]] = defaultdict(list)
        self.breadcrumbs: list[dict] = []
        self.banned: dict[str, set[str]] = {}
        self.ban_candidates: list[dict] = []
        self.skill_files: list[str] = []
        self.skipped_vendored = 0
        self.ban_re = None

    def add(self, check: str, path: str, line: int, token: str, evidence: str, surface: str, confidence: str = "medium"):
        self.findings.append({"check": check, "file": path, "line": line, "token": token,
                              "evidence": evidence, "surface": surface, "confidence": confidence})

    def read(self, path: str) -> str | None:
        try:
            if os.path.getsize(os.path.join(self.root, path)) > MAX_BYTES:
                return None
            return open(os.path.join(self.root, path), encoding="utf-8", errors="replace").read()
        except OSError:
            return None

    # -- selection
    def shipped_md(self, path: str) -> bool:
        return path.lower().endswith(tuple(MD_EXT)) and classify(path) == "payload" and not TESTISH.search(path)

    def prompt_file(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return (ext in PROMPT_FILE_EXT and re.search(r"(^|/)(prompts?|instructions?|system)[^/]*(/|\.)", path) is not None
                and classify(path) != "history" and not TESTISH.search(path)
                and os.path.basename(path) not in ("package.json", "pnpm-lock.yaml"))

    # -- rules for check G
    def harvest_bans(self):
        for path in self.repo.files:
            if not RULE_FILE.search(path) or is_vendored(path, self.vroots) or classify(path) in ("history", "plan"):
                continue
            text = self.read(path)
            if text is None:
                continue
            for m in BAN_TRIGGER.finditer(text):
                end = re.search(r"[.!?](?:\s|$)|\n\n", text[m.start():m.start() + 220])
                span = text[m.start():m.start() + (end.start() if end else 220)]
                for q in BAN_QUOTED.findall(span):
                    phrase = q.lower().strip()
                    if len(phrase.split()) <= 3 and phrase not in ("the", "and", "you"):
                        self.banned.setdefault(phrase, set()).add(path)

    # -- does this repo ship an agent at all
    def dependency_signals(self) -> list[str]:
        out: list[str] = []
        for path in self.repo.files:
            base = os.path.basename(path)
            kind = MANIFESTS.get(base) or (MANIFESTS.get("*" + os.path.splitext(base)[1]) if "." in base else None)
            if base.startswith("requirements") and base.endswith((".txt", ".in")):
                kind = "pip"
            if not kind or is_vendored(path, self.vroots) or TESTISH.search(path):
                continue
            text = self.read(path)
            if text is None:
                continue
            for name in manifest_dependencies(kind, text):
                if agent_dependency(kind, name):
                    out.append(f"{path}: {name}")
                    break
        return out

    def preharvest_registrations(self):
        """The cheap half of the main pass: only the tool and server registrations."""
        for path in self.repo.files:
            ext = os.path.splitext(path)[1].lower()
            if ext not in JS_EXT and ext not in PY_EXT or is_vendored(path, self.vroots) \
                    or TESTISH.search(path) or GENERATED.search(path):
                continue
            text = self.read(path)
            if text is not None and ("ool" in text or "erver" in text or "FastMCP" in text):
                self.harvest_registrations(path, text)

    def agent_signals(self) -> list[str]:
        signals = self.dependency_signals()
        signals += [f"shipped skill: {p}" for p in self.repo.files
                    if os.path.basename(p) == "SKILL.md" and not is_vendored(p, self.vroots) and not TESTISH.search(p)][:3]
        if not signals:
            self.preharvest_registrations()
            if self.registered:
                signals.append(f"tool registration: {sorted(self.registered)[0]}")
            elif self.servers:
                signals.append(f"MCP server registration: {sorted(self.servers)[0]}")
        return signals

    # -- the main pass
    def run(self):
        self.signals = self.agent_signals()
        self.agent_code = bool(self.signals)
        if not self.agent_code:
            return
        self.pool = ThreadPoolExecutor(max_workers=3)
        self.model_rows = self.pool.submit(
            self.grep, [r"claude-(opus|sonnet|haiku|fable|[0-9])|gpt-[0-9]"], fixed=False, words_only=False,
            only_matching=False)
        self.harvest_bans()
        ban_re = self.ban_re = None
        if self.banned:
            ban_re = self.ban_re = re.compile(r"(?<![\w./_-])(" + "|".join(re.escape(p) for p in sorted(self.banned, key=len, reverse=True))
                                + r")(?:s|es)?(?![\w/_-]|\.\w)", re.I)
        for path in self.repo.files:
            if is_vendored(path, self.vroots):
                self.skipped_vendored += 1
                continue
            ext = os.path.splitext(path)[1].lower()
            if TESTISH.search(path) or GENERATED.search(path):
                continue
            if ext in JS_EXT or ext in PY_EXT:
                if (text := self.read(path)) is not None:
                    self.scan_code_file(path, ext, text, ban_re)
            elif self.shipped_md(path) or self.prompt_file(path):
                if (text := self.read(path)) is not None:
                    self.scan_prose_file(path, text)
            elif ext in CONFIG_EXT and not os.path.basename(path).startswith(("package", "tsconfig")):
                pass  # config literals are read through git grep (check E)
        self.check_skill_hygiene()

    def scan_code_file(self, path: str, ext: str, text: str, ban_re):
        if len(text) < 60:
            return
        ft = FileText(path, text)
        pieces, comments = (scan_py if ext in PY_EXT else scan_js)(text)
        spans: list[tuple[int, int, str]] = []
        if ext in JS_EXT or ext in PY_EXT:
            self.harvest_registrations(path, text)
        if re.search(r"settings|nav", path, re.I) and ext in (".ts", ".tsx", ".js", ".jsx", ".mjs"):
            self.harvest_labels(path, text, pieces)
        if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts"):
            for m in BUILDER_EXPORT.finditer(text):
                self.builders.setdefault(m.group(1), path)

        n_prompt = n_desc = prompt_bytes = 0
        for group in clusters(text, pieces):
            values = [piece_value(text, p) for p in group]
            joined = "\n".join(values)
            first = group[0]
            before = text[max(0, first.s - 90):first.s]
            prompt = is_prompt_like(joined)
            desc = (not prompt) and bool(DESC_BEFORE.search(before)) and words(joined) >= 3
            if prompt:
                n_prompt += 1
                prompt_bytes += len(joined)
            elif desc:
                n_desc += 1
                prompt_bytes += len(joined)
            kind = "prompt" if prompt else "description" if desc else None
            for p, v in zip(group, values):
                if kind:
                    spans.append((p.s, p.e, kind))
                    self.check_text(ft, p.s + (0 if p.kind == "py" else 1), v, kind, text_kind="literal")
                elif "Settings" in v or " settings" in v:
                    if words(v) >= 4:
                        self.check_breadcrumbs(ft, p.s + 1, v, "string")
                if ban_re and not DEV_TOOLING.search(path) and words(v) >= 5 and not v.lstrip().startswith("[") and p.kind != "py":
                    self.collect_ban(ft, p, v, ban_re, text)
        for s, e in comments:
            body = text[s:e]
            spans.append((s, e, "comment"))
            if "/" in body:
                self.check_dead_paths(ft, s, body, "comment")
            if "Settings" in body or " settings" in body:
                pass  # developer notes: breadcrumbs only matter where the agent or a person reads them
        if ban_re and ext in (".tsx", ".jsx") and not DEV_TOOLING.search(path):
            for m in JSX_TEXT.finditer(text):
                if words(m.group(1)) >= 5:
                    self.collect_ban_text(ft, m.start(1), m.group(1), ban_re, text)
        if n_prompt or n_desc:
            self.stats[path] = {"literals": n_prompt, "descriptions": n_desc, "bytes": prompt_bytes}
        if spans:
            self.files[path] = {"spans": sorted(spans)}

    def scan_prose_file(self, path: str, text: str):
        ft = FileText(path, text)
        if self.ban_re is not None and not any(path in f for f in self.banned.values()):
            off, in_fence = 0, False
            for line in text.split("\n"):
                if FENCE_LINE.match(line):
                    in_fence = not in_fence
                elif not in_fence and words(line) >= 5:
                    self.collect_ban_text(ft, off, line, self.ban_re, text)
                off += len(line) + 1
        self.stats[path] = {"literals": 1, "descriptions": 0, "bytes": len(text), "skill": True}
        if self.shipped_md(path):
            self.skill_files.append(path)
        self.files[path] = {"spans": [(0, len(text), "prompt")]}
        if path.lower().endswith(tuple(MD_EXT)):
            self.check_text(ft, 0, mask_fences(text), "skill", text_kind="md")
        else:
            self.check_text(ft, 0, text, "prompt", text_kind="literal")

    # -- harvesting
    def harvest_registrations(self, path: str, text: str):
        if "ool" in text or "NewTool" in text:  # Tool.make, .tool(, registerTool, _TOOL_NAME, @mcp.tool, mcp.NewTool
            for rx in TOOL_REGISTRATIONS:
                for m in rx.finditer(text):
                    self.registered.update(g for g in m.groups() if g)
            if "description" in text and "name" in text:
                for m in NAME_LITERAL.finditer(text):
                    lo = m.start()
                    for _ in range(5):
                        lo = text.rfind("\n", 0, lo)
                        if lo < 0:
                            lo = 0
                            break
                    hi = m.end()
                    for _ in range(5):
                        hi = text.find("\n", hi + 1)
                        if hi < 0:
                            hi = len(text)
                            break
                    if "description" in text[lo:hi]:
                        self.registered.add(m.group(1))
        if "erver" in text or "FastMCP" in text or "MCPServer" in text:
            for rx in SERVER_REGISTRATIONS:
                for m in rx.finditer(text):
                    self.servers.add(m.group(1))

    def harvest_labels(self, path: str, text: str, pieces: list[Piece]):
        if re.search(r"(^|/)(settings|preferences)[^/]*/", path, re.I) or re.search(r"Settings\.\w+$", path):
            stem = re.sub(r"(Settings|Panel|Tab|Page|Screen|RouteScreen|Section|-tab|-settings|-panel)$", "",
                          os.path.splitext(os.path.basename(path))[0])
            name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", stem).replace("-", " ").replace("_", " ").strip().lower()
            if 1 < len(name) <= 40:
                self.registry.add(name)
        if is_nav_file(path):
            for m in LABEL_PROP.finditer(text):
                if 1 < len(m.group(1)) <= 40:
                    self.registry.add(m.group(1).strip().lower())
            for m in re.finditer(r">\s*([A-Z][^<>{}\n]{1,38}?)\s*<", text):
                if len(m.group(1).split()) <= 4:
                    self.registry.add(m.group(1).strip().lower())
        before = len(self.registry_loose)
        for p in pieces:
            v = piece_value(text, p) if p.kind != "t" or not p.masks else ""
            v = v.strip()
            if 1 < len(v) <= 40 and (v[0].isupper() or v[0].isdigit()) and not re.search(r"[/_.:{}<>]|\x01", v) \
                    and len(v.split()) <= 5:
                self.registry_loose.add(v.lower())
        for m in re.finditer(r">\s*([A-Z][^<>{}\n]{1,38}?)\s*<", text):
            if len(m.group(1).split()) <= 5:
                self.registry_loose.add(m.group(1).strip().lower())
        if len(self.registry_loose) > before:
            self.registry_files.add(path)

    # -- the per-text checks (A, B, C mentions)
    def check_text(self, ft: FileText, base: int, value: str, surface: str, text_kind: str):
        if "/" in value:
            self.check_dead_paths(ft, base, value, surface)
        if "Settings" in value or " settings" in value:
            self.check_breadcrumbs(ft, base, value, surface)
        if "mcp__" in value or "`" in value:
            self.collect_mentions(ft, base, value, surface)

    def check_dead_paths(self, ft: FileText, base: int, value: str, surface: str):
        seen = set()
        for m in PATHISH.finditer(value):
            tok = m.group(1).rstrip(".,:;")
            if tok in seen:
                continue
            seen.add(tok)
            if not is_path_claim(tok, self.repo):
                continue
            status, _hint = resolve(tok, ft.path, self.repo)
            if status != "missing":
                continue
            clean = posixpath.normpath(tok.split("#")[0]).lstrip("./")
            clean = re.sub(r":L?\d+(?::\d+)?(?:-L?\d+)?$", "", clean)
            gone = deleted_in(self.repo, clean)
            if not gone:
                continue
            if NEGATED.search(value[max(0, m.start() - 90):m.start()] + " " + value[m.end():m.end() + 30]):
                continue
            self.add("dead_pointer", ft.path, ft.line(base + m.start()), tok, f"gone; deleted or renamed in {gone}",
                     surface, "high" if surface == "comment" else "medium")

    def check_breadcrumbs(self, ft: FileText, base: int, value: str, surface: str):
        for m in SETTINGS_ARROW.finditer(value):
            if OTHER_APP.search(value[max(0, m.start() - 24):m.start()]):
                continue
            seg = SEG_CUT.split(m.group(1).strip().strip("*_ "), maxsplit=1)[0].strip()
            if seg and seg[0].isupper() or seg[:1].isdigit():
                self.breadcrumbs.append({"file": ft.path, "line": ft.line(base + m.start()), "seg": seg,
                                         "text": value[max(0, m.start() - 30):m.end()].replace("\n", " ")[:140],
                                         "surface": surface, "named": False})
        for m in NAMED_SETTINGS.finditer(value):
            if OTHER_APP.search(m.group(1) + " "):
                continue
            self.breadcrumbs.append({"file": ft.path, "line": ft.line(base + m.start()), "seg": m.group(1),
                                     "text": value[max(0, m.start() - 30):m.end() + 20].replace("\n", " ")[:140],
                                     "surface": surface, "named": True})

    def collect_mentions(self, ft: FileText, base: int, value: str, surface: str):
        for m in MCP_REF.finditer(value):
            if "\x01" in m.group(0):
                continue
            self.mentions[m.group(2)].append({"file": ft.path, "line": ft.line(base + m.start()), "surface": surface,
                                              "server": m.group(1), "mcp": m.group(0), "high": True})
        for m in SNAKE_TICK.finditer(value):
            tok = m.group(1)
            ctx = window(value, m.start(), 70, 70)
            self.mentions[tok].append({"file": ft.path, "line": ft.line(base + m.start()), "surface": surface,
                                       "server": None, "mcp": None, "high": bool(TOOL_CONTEXT.search(ctx))})

    def collect_ban(self, ft: FileText, p: Piece, v: str, ban_re, text: str):
        if LOG_CALL.search(text[max(0, p.s - 40):p.s]):
            return
        self.collect_ban_text(ft, p.s + 1, v, ban_re, text)

    def collect_ban_text(self, ft: FileText, base: int, v: str, ban_re, text: str):
        for m in ban_re.finditer(v):
            phrase = m.group(1).lower()
            if ft.path in self.banned.get(phrase, ()):
                continue
            if SQLISH.search(v) or VENDOR_BEFORE.search(v[max(0, m.start() - 24):m.start()]):
                continue
            around = v[max(0, m.start() - 1):m.end() + 1]
            if (around[:1] in "\"“`'" and around[-1:] in "\"”`'") or re.search(r"\b(?:never|avoid|don'?t|do not)\b", v[max(0, m.start() - 60):m.start()], re.I):
                continue  # the word is mentioned (quoted or banned) rather than shown
            if any(vn in ft.path.lower() for vn in VENDOR_NAMES):
                continue
            self.ban_candidates.append({"file": ft.path, "line": ft.line(base + m.start()), "phrase": phrase,
                                        "text": v[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")})
            break

    # -- F
    def check_skill_hygiene(self):
        roots = sorted({posixpath.dirname(p) for p in self.repo.files
                        if os.path.basename(p) == "SKILL.md" and self.shipped_md(p)}, key=len, reverse=True)
        if not roots:
            return
        for path in self.skill_files:
            root = next((r for r in roots if path == r or path.startswith(r + "/")), None)
            if root is None:
                continue
            text = self.read(path)
            if text is None:
                continue
            in_fence = False
            for lineno, line in enumerate(text.split("\n"), 1):
                if FENCE_LINE.match(line):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for m in LINK.finditer(line):
                    target = m.group(1)
                    if re.match(r"^[a-z][a-z0-9+.\-]*:|^#|^/", target, re.I):
                        continue
                    rel = target.split("#")[0].split("?")[0]
                    if not rel:
                        continue
                    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), rel))
                    if resolved == ".." or resolved.startswith("../") or not (resolved == root or resolved.startswith(root + "/")):
                        self.add("skill_hygiene", path, lineno, target,
                                 f"link climbs out of the skill folder {root}/ (resolves to {resolved})", "skill", "high")
                for m in RELEASE_WORDS.finditer(line):
                    if re.search(r"changelog|release notes", line, re.I):
                        continue
                    self.add("skill_hygiene", path, lineno, m.group(0),
                             "shipped skill text names the development checkout rather than the released app: "
                             + line.strip()[:120], "skill", "high")

    # -- resolution of deferred checks
    def surface_lines(self, path: str, lines: set[int]) -> dict[int, set[str]]:
        spans = self.files.get(path, {}).get("spans")
        if not spans:
            return {}
        text = self.read(path)
        if text is None:
            return {}
        ft = FileText(path, text)
        ft.line(0)
        out: dict[int, set[str]] = {}
        nl = ft._nl
        for ln in lines:
            ls = (nl[ln - 2] + 1) if ln > 1 and ln - 2 < len(nl) else 0
            le = nl[ln - 1] if ln - 1 < len(nl) else len(text)
            kinds = {k for s, e, k in spans if s < le and e > ls}
            if kinds:
                out[ln] = kinds
        return out

    def grep(self, patterns: list[str], extra: list[str] = (), fixed: bool = True, words_only: bool = True,
             only_matching: bool = True, include_md: bool = False) -> list[tuple[str, int, str]]:
        if not patterns:
            return []
        fd, pf = tempfile.mkstemp(prefix="cobweb-ps-", suffix=".txt")
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write("\n".join(patterns) + "\n")
            args = ["grep", "-I", "-n", "-f", pf]
            if fixed:
                args.append("-F")
            else:
                args.append("-E")
            if words_only:
                args.append("-w")
            if only_matching:
                args.append("-o")
            args += list(extra)
            args += ["--"] + [f":(glob)**/*.{e}" for e in GREP_EXTS]
            out = git(self.root, *args)
        finally:
            os.remove(pf)
        rows = []
        for line in out.splitlines():
            parts = line.split(":", 2)
            if len(parts) == 3 and parts[1].isdigit() and not is_vendored(parts[0], self.vroots):
                rows.append((parts[0], int(parts[1]), parts[2]))
        return rows

    # A done inline; B
    def resolve_breadcrumbs(self):
        strict = len(self.registry) >= 8
        labels = self.registry if strict else self.registry_loose
        if len(labels) < 8:
            self.registry_note = "no settings or navigation source with labels found; breadcrumbs not checked"
            return
        self.registry_note = "" if strict else "settings labels read loosely from every settings/nav file (low confidence)"
        for b in self.breadcrumbs:
            loose_hit = False
            ws = re.findall(r"[A-Za-z0-9&'’-]+", b["seg"])
            norm = [w.lower() for w in ws]
            if not norm:
                continue
            if b["named"]:
                ok = any(" ".join(norm[k:]) in labels or " ".join(norm[k:]) + " settings" in labels for k in range(len(norm)))
                if ok or " ".join(norm) in OS_LABELS or norm[-1] in OS_LABELS:
                    continue
                token = f"{b['seg']} settings"
                why = f"no settings or navigation label \"{norm[-1].title()}\""
            else:
                ok = any(" ".join(norm[:k]) in labels for k in range(1, min(len(norm), 4) + 1))
                if ok or " ".join(norm[:2]) in OS_LABELS or norm[0] in OS_LABELS:
                    continue
                loose_hit = any(" ".join(norm[:k]) in self.registry_loose for k in range(1, min(len(norm), 4) + 1))
                shown = []
                for i, w in enumerate(ws[:4]):
                    if i and not (w[0].isupper() or w[0].isdigit()):
                        break
                    shown.append(w)
                token = "Settings → " + " ".join(shown)
                why = f"first segment \"{' '.join(shown)}\" is not a settings or navigation label" \
                      + (" (it appears only as ordinary UI text in those files)" if loose_hit else "")
            self.add("settings_breadcrumb", b["file"], b["line"], token, why + ": " + b["text"], b["surface"],
                     "medium" if strict and not loose_hit else "low")

    def prefetch(self):
        """Start the two git greps that need pass-1 results; they overlap with each other and with B."""
        self.tool_cands = {t for t in self.mentions if t not in HOST_TOOLS}
        self.tool_rows = self.pool.submit(self.grep, sorted(self.tool_cands)) if self.tool_cands else None
        self.builder_rows = self.pool.submit(self.grep, sorted(self.builders)) if self.builders else None

    # C
    def resolve_tools(self):
        cands = self.tool_cands
        if not cands:
            return
        outside = self.occurrences_outside_prompts(self.tool_rows.result())
        for tok, refs in self.mentions.items():
            if tok in HOST_TOOLS or tok in self.registered or tok in outside:
                continue
            for r in refs:
                if r["mcp"]:
                    if r["server"] not in self.servers:
                        continue  # a server this repo does not own
                    evidence = f"{r['mcp']}: no tool registered or defined in code as `{tok}`"
                else:
                    evidence = f"`{tok}` is named but no tool registration or code token defines it"
                self.add("orphan_tool", r["file"], r["line"], r["mcp"] or tok, evidence, r["surface"],
                         "high" if r["high"] else "low")

    def occurrences_outside_prompts(self, rows: list[tuple[str, int, str]]) -> set[str]:
        by_file: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for path, line, tok in rows:
            by_file[path].append((line, tok))
        found: set[str] = set()
        for path, hits in by_file.items():
            kinds = self.surface_lines(path, {ln for ln, _ in hits}) if path in self.files else {}
            for ln, tok in hits:
                if tok in found:
                    continue
                if kinds.get(ln, set()) & {"prompt", "description"}:
                    continue
                found.add(tok)
        return found

    # D
    def resolve_builders(self):
        if not self.builders:
            return
        rows = self.builder_rows.result()
        refs: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for path, _ln, name in rows:
            if os.path.splitext(path)[1].lower() in JS_EXT:
                refs[name][path] += 1
        for name, home in sorted(self.builders.items()):
            real: set[str] = set()
            for path in refs.get(name, {}):
                if path == home:
                    continue
                text = self.read(path)
                if text is None:
                    continue
                total = len(re.findall(rf"\b{re.escape(name)}\b", text))
                reexp = sum(len(re.findall(rf"\b{re.escape(name)}\b", m.group(0)))
                            for m in re.finditer(r"export\s*(?:type\s*)?(?:\{[^}]*\}|\*(?:\s+as\s+\w+)?)\s*from\b[^;\n]*", text, re.S))
                if total - reexp > 0:
                    real.add(path)
            tests_only = bool(real) and all(TEST_IMPORTER.search(p) for p in real)
            text = self.read(home) or ""
            line = next((i for i, l in enumerate(text.split("\n"), 1) if re.search(rf"\b{name}\b", l)), 1)
            home_lines = {ln for path, ln, n in rows if path == home and n == name and ln != line}
            kinds = self.surface_lines(home, home_lines) if home in self.files else {}
            own_calls = [ln for ln in home_lines if "comment" not in kinds.get(ln, set())]
            unreferenced = not real and not own_calls
            if not (tests_only or unreferenced):
                continue
            if tests_only:
                ev = "only " + ", ".join(sorted(real)[:3]) + (" +%d more" % (len(real) - 3) if len(real) > 3 else "") \
                     + " import it; the shipped agent never receives this text"
                if own_calls:
                    ev += f" (its own file also calls it, line {min(own_calls)}: probably exported only for tests)"
            else:
                ev = "nothing imports it and its own file does not call it"
            self.add("builder_unwired", home, line, name, ev, "code", "low" if own_calls or unreferenced else "medium")

    # E
    def resolve_models(self):
        rows = self.model_rows.result()
        per_file: dict[str, list[tuple[int, str, tuple[int, int], int]]] = defaultdict(list)
        for path, line, content in rows:
            if TESTISH.search(path) or GENERATED.search(path) or len(content) > 3000 or classify(path) == "history":
                continue
            for rx in (CLAUDE_ID, GPT_ID):
                for m in rx.finditer(content):
                    fam, ver = model_version(m)
                    per_file[path].append((line, fam, ver, m.start()))
                    if rx is GPT_ID:
                        per_file[path][-1] = (line, fam, ver, m.start())
        # id text per hit for evidence
        live_files: dict[str, dict[tuple[int, int], set[str]]] = defaultdict(lambda: defaultdict(set))
        catalogs = 0
        content_by = {(p, l): c for p, l, c in rows}
        for path, hits in per_file.items():
            distinct = set()
            for line, fam, ver, off in hits:
                content = content_by[(path, line)]
                m = (CLAUDE_ID.match(content, off) or GPT_ID.match(content, off))
                distinct.add(m.group(0) if m else fam)
            if len(distinct) >= 5:
                catalogs += 1
                continue
            for line, fam, ver, off in hits:
                live_files[fam][ver].add(path)
        live: dict[str, tuple[int, int]] = {}
        for fam, versions in live_files.items():
            ok = [v for v, fs in versions.items() if len(fs) >= 2]
            if ok:
                live[fam] = max(ok)
        self.model_live = {f: ".".join(map(str, v)) for f, v in live.items()}
        self.model_catalogs = catalogs
        wanted: dict[str, list[tuple[int, str, tuple[int, int], int]]] = {}
        for path, hits in per_file.items():
            old = [h for h in hits if h[1] in live and h[2] < live[h[1]]]
            if old and len({h for h in hits}) < 25:
                distinct = set()
                for line, fam, ver, off in hits:
                    content = content_by[(path, line)]
                    m = (CLAUDE_ID.match(content, off) or GPT_ID.match(content, off))
                    distinct.add(m.group(0) if m else fam)
                if len(distinct) < 5:
                    wanted[path] = old
        for path, old in wanted.items():
            ext = os.path.splitext(path)[1].lower()
            shipped_md = self.shipped_md(path)
            if ext in MD_EXT and not shipped_md:
                continue
            kinds = {} if ext in CONFIG_EXT or shipped_md else self.surface_lines(path, {h[0] for h in old})
            for line, fam, ver, off in old:
                content = content_by[(path, line)]
                m = (CLAUDE_ID.match(content, off) or GPT_ID.match(content, off))
                surface = "config" if ext in CONFIG_EXT else "skill" if shipped_md else None
                if surface is None:
                    ks = kinds.get(line, set())
                    surface = "prompt" if "prompt" in ks else "description" if "description" in ks else None
                if surface is None or NEGATED.search(content[max(0, off - 100):off + 60]):
                    continue
                live_s = ".".join(map(str, live[fam])).replace(".0", "") if live[fam][1] == 0 else ".".join(map(str, live[fam]))
                self.add("model_drift", path, line, m.group(0) if m else fam,
                         f"older than the {fam} generation {live_s} that two or more non-test files use", surface, "medium")

    # G
    def resolve_bans(self):
        by_phrase: dict[str, list[dict]] = defaultdict(list)
        for c in self.ban_candidates:
            by_phrase[c["phrase"]].append(c)
        for phrase, items in by_phrase.items():
            rules = ", ".join(sorted(self.banned[phrase])[:2])
            for c in items:
                self.add("banned_vocab", c["file"], c["line"], phrase,
                         f"rule in {rules} says never to show \"{phrase}\": …{c['text'].strip()}…", "prose",
                         "low" if len(items) > 100 else "medium")


def scan(root: str) -> dict:
    t0 = time.time()
    s = Scan(root)
    s.run()
    if not s.agent_code:
        return {"repo": root, "agent_code": False, "tracked_files": len(s.repo.files),
                "vendored_files_skipped": 0, "seconds": round(time.time() - t0, 1),
                "note": "no agent code found: no LLM or agent SDK dependency, no tool registration, no shipped SKILL.md",
                "counts": {}, "findings": []}
    s.prefetch()
    s.resolve_breadcrumbs()
    s.resolve_tools()
    s.resolve_builders()
    s.resolve_models()
    s.resolve_bans()

    total_literals = sum(v["literals"] for v in s.stats.values())
    total_desc = sum(v["descriptions"] for v in s.stats.values())
    total_bytes = sum(v["bytes"] for v in s.stats.values())
    skill_bytes = sum(v["bytes"] for v in s.stats.values() if v.get("skill"))
    top = sorted(({"file": f, **v} for f, v in s.stats.items()), key=lambda x: -x["bytes"])[:15]
    order = {"high": 0, "medium": 1, "low": 2}
    s.findings.sort(key=lambda f: (f["check"], order[f["confidence"]], f["file"], f["line"]))
    counts = Counter(f["check"] for f in s.findings)
    return {
        "repo": root,
        "agent_code": True,
        "agent_signals": s.signals[:6],
        "tracked_files": len(s.repo.files),
        "vendored_files_skipped": s.skipped_vendored,
        "seconds": round(time.time() - t0, 1),
        "prompt_surfaces": {
            "prompt_like_literals": total_literals - len(s.skill_files),
            "descriptions": total_desc,
            "shipped_skill_files": len(s.skill_files),
            "bytes": total_bytes,
            "approx_tokens": total_bytes // 4,
            "skill_bytes": skill_bytes,
            "largest_files": top,
        },
        "registries": {"settings_labels": len(s.registry) or len(s.registry_loose), "settings_files": len(s.registry_files),
                       "registered_tools": len(s.registered), "mcp_servers": sorted(s.servers),
                       "prompt_builders": len(s.builders), "banned_phrases": {p: sorted(f) for p, f in s.banned.items()},
                       "model_live": getattr(s, "model_live", {}), "model_catalogs_skipped": getattr(s, "model_catalogs", 0),
                       "note": getattr(s, "registry_note", "")},
        "counts": dict(counts),
        "findings": s.findings,
    }


CHECK_TITLES = {
    "dead_pointer": "A  dead pointers (path is gone and git history deleted or renamed it)",
    "settings_breadcrumb": "B  settings breadcrumbs naming a label the settings source lacks",
    "orphan_tool": "C  tool names nothing registers",
    "builder_unwired": "D  prompt builders the shipped agent never receives",
    "model_drift": "E  model IDs older than the repo's live generation",
    "skill_hygiene": "F  shipped-skill hygiene",
    "banned_vocab": "G  vocabulary the repo's own rules ban",
}


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    result = scan(os.path.abspath(args[0]) if args else os.getcwd())
    if emit_json(result):
        return
    show_all = "--all" in sys.argv
    if not result["agent_code"]:
        print(f"repo: {result['repo']}  tracked files: {result['tracked_files']}  ({result['seconds']}s)")
        print(result["note"])
        return
    ps, rg = result["prompt_surfaces"], result["registries"]
    print("agent code: " + "; ".join(result["agent_signals"][:3]))
    print(f"repo: {result['repo']}  tracked files: {result['tracked_files']}  vendored skipped: "
          f"{result['vendored_files_skipped']}  ({result['seconds']}s)")
    print(f"agent-steering text in code: {ps['prompt_like_literals']} prompt-like literals, {ps['descriptions']} descriptions, "
          f"{ps['shipped_skill_files']} shipped skill/prompt files; {ps['bytes']} bytes (~{ps['approx_tokens']} tokens), "
          f"{ps['skill_bytes']} of them in skill files")
    for f in ps["largest_files"][:8]:
        print(f"  {f['bytes']:>8}B  {f['file']}  ({f['literals']} prompt, {f['descriptions']} desc)")
    print(f"registries: {rg['settings_labels']} settings labels in {rg['settings_files']} files, "
          f"{rg['registered_tools']} registered tools, {len(rg['mcp_servers'])} MCP servers, "
          f"{rg['prompt_builders']} prompt builders, live models {rg['model_live'] or 'none'}"
          + (f"\n  note: {rg['note']}" if rg["note"] else ""))
    findings = result["findings"]
    print(f"\nfindings: {len(findings)}  {result['counts']}")
    for check, title in CHECK_TITLES.items():
        group = [f for f in findings if f["check"] == check]
        if not group:
            continue
        print(f"\n[{title}] {len(group)}")
        limit = len(group) if show_all else 12
        for f in group[:limit]:
            print(f"  {f['file']}:{f['line']}  {f['token']}  [{f['confidence']}, {f['surface']}]  {f['evidence'][:200]}")
        if len(group) > limit:
            print(f"  ... {len(group) - limit} more (use --all)")


if __name__ == "__main__":
    main()
