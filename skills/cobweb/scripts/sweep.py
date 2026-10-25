#!/usr/bin/env python3
"""Run every cobweb check once and print the health card.

Each check's text view and JSON go to the output directory, so the agent
reads details from files instead of re-running checks. Read-only, except
writing to --out (created if missing; files in it are overwritten). Stdlib only.

Usage: sweep.py [repo] [--out=DIR] [--transcripts] [--also=PATH] [--days=60] [--compare=PREV_DIR]
                [--no-ci] [--no-deps] [--no-live] [--no-memory] [--no-global] [--here] [--since=12.months]
  --transcripts  also read this project's local agent session logs (ask the person first)
  --compare=DIR  show what is new and what got fixed since a previous sweep's output folder
  --no-memory    skip this project's agent memory (Claude Code auto-memory and others)
  --no-global    skip the person's global agent setup (user instructions, skills, MCP servers)
  --also=PATH    another clone of the same project whose session logs count (repeatable)
  --no-ci        skip GitHub Actions history (needs gh)
  --no-deps      skip package-manager audit/outdated (needs network)
  --no-live      sweeping a historical snapshot: skip CI, branches, deps and remote checks
  --here         sweep this checkout even if it is behind its base branch
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # keep the installed skill folder clean
sys.path.insert(0, HERE)
from steering_refs import git  # noqa: E402

STEERING_KINDS = ("always", "scoped", "on-demand", "config")


def flag(name: str, default: str | None = None) -> str | None:
    return next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{name}=")), default)


def run_check(name: str, root: str, out: str, extra: list[str]) -> tuple[str, float, int]:
    start = time.time()
    with open(os.path.join(out, f"{name}.txt"), "w", encoding="utf-8") as fh:
        p = subprocess.run([sys.executable, "-I", os.path.join(HERE, f"{name}.py"), root,
                            f"--save={os.path.join(out, name + '.json')}", *extra],
                           stdout=fh, stderr=subprocess.STDOUT, check=False)
    return name, round(time.time() - start, 1), p.returncode


def load(out: str, name: str):
    try:
        return json.load(open(os.path.join(out, f"{name}.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def n(x) -> int:
    return len(x) if isinstance(x, (list, dict)) else 0


def test_lines(ts: dict) -> list[str]:
    mods = ts.get("test_only_modules") or []
    pins = ts.get("source_text_pins") or {}
    gate = pins.get("gate")
    env = ts.get("dormant_env_gates") or {}
    pin_text = (f"source-text pins: the repo's own gate holds {gate.get('baseline_entries')} in its baseline, "
                f"{len(gate.get('found_by_this_scan_not_in_baseline') or [])} outside it" if gate
                else f"tests pinning source text {pins.get('files_found', 0)}")
    return [
        f"modules only tests import {sum(1 for m in mods if m.get('kind') == 'test-only')}, imported by nothing "
        f"{sum(1 for m in mods if m.get('kind') == 'unreachable')}; test support living in src "
        f"{len(ts.get('test_support_in_src') or [])}",
        f"{pin_text}; fixtures nothing loads {len(ts.get('orphan_fixtures') or [])}; "
        f"tests gated on a switch nothing sets {len(env.get('dormant') or [])}",
    ]


def memory_lines(ah: dict) -> list[str]:
    lines = []
    for s in ah.get("claude_memory") or []:
        kinds = s.get("kinds", {})
        lines.append(f"Claude Code memory: {s['files']} files ({', '.join(f'{k} {v}' for k, v in kinds.items())}); "
                     f"MEMORY.md {s['index_bytes']:,} bytes (~{s['index_bytes'] // 4:,} tokens every session)"
                     + ("; OVER THE LOAD LIMIT" if s.get("index_over_limit") else ""))
        by_kind = Counter(c["kind"] for c in s.get("candidates", []))
        lines.append(f"memory files with evidence they're stale: {len(s.get('candidates', []))} "
                     f"({', '.join(f'{k} {v}' for k, v in by_kind.items()) or 'none'})")
        if s.get("days_to_limit") is not None and s["days_to_limit"] <= 60:
            lines.append(f"index reaches its load limit in about {s['days_to_limit']} days at the last month's pace "
                         f"({s['new_files_30d']} new memories); later entries will never load")
    if not ah.get("claude_memory"):
        lines.append("Claude Code memory: none for this repo's paths")
    if ah.get("tracked_memory_files"):
        lines.append(f"memory tracked in git: {ah['tracked_memory_files']} files (checked like docs)")
    for o in ah.get("other_stores") or []:
        lines.append(f"{o['tool']} memory present ({o['owner']}); not read")
    g = ah.get("global") or {}
    if g:
        user = sum(i["bytes"] for i in g.get("instructions", []))
        dead = sum(len(i["dead_paths"]) for i in g.get("instructions", []))
        lines.append(f"your global setup: user instructions {user:,} bytes (dead paths {dead}); "
                     f"diverged skill copies {len(g.get('diverged_copies', []))}, broken skill links "
                     f"{len(g.get('broken_skill_links', []))}, over-long descriptions {len(g.get('long_descriptions', []))}; "
                     f"user MCP servers {sum(len(v) for v in g.get('mcp_servers', {}).values())}; hooks with a missing "
                     f"script {sum(1 for h in g.get('hooks', []) if h.get('script_missing'))}")
        gone = {f: v for f, v in (g.get("stale_trusted_projects") or {}).items() if v[0]}
        extras = [f"{len(g.get('copied_instruction_lines', []))} pairs of tools' user files with copied rules"
                  if g.get("copied_instruction_lines") else "",
                  f"hook scripts nothing runs {len(g['unwired_hook_scripts'])}" if g.get("unwired_hook_scripts") else "",
                  "; ".join(f"{f}: {v[0]} of {v[1]} remembered projects gone" for f, v in gone.items())]
        if any(extras):
            lines.append("also: " + "; ".join(e for e in extras if e))
    return lines


def finding_keys(out: str) -> dict[str, set]:
    """Stable keys per check, for --compare."""
    keys: dict[str, set] = {}
    st = load(out, "steering_refs")
    if st:
        keys["broken references"] = {(x["doc"], x["ref"], x["status"]) for x in st["findings"]
                                     if x["kind"] not in ("history", "payload")}
    rn = load(out, "retired_names")
    if isinstance(rn, list):
        keys["retired names still present"] = {r["term"] for r in rn}
    cf = load(out, "config_refs")
    if cf:
        keys["config entries naming gone paths"] = {(x["file"], x["field"], x["ref"]) for x in cf["findings"]}
    ps = load(out, "prompt_surfaces")
    if ps:
        keys["prompt findings"] = {(x["check"], x["file"], x["token"]) for x in ps.get("findings", [])}
    ts = load(out, "test_scan")
    if ts:
        keys["test-only modules"] = {m["file"] for m in ts.get("test_only_modules", [])}
    ah = load(out, "agent_home")
    if ah:
        keys["stale memory files"] = {c["file"] for s in ah.get("claude_memory", []) for c in s.get("candidates", [])}
    cr = load(out, "cruft_scan")
    if cr:
        for sec, field in (("plan_checkboxes", "doc"), ("authority_claims", "doc"), ("parallel", "file"),
                           ("scratch", "file")):
            v = cr.get(sec)
            if isinstance(v, list):
                keys[sec.replace("_", " ")] = {x[field] for x in v}
    dp = load(out, "deps")
    if dp:
        keys["vulnerable packages"] = {(x["pm"], x["dir"], p) for x in dp.get("results", [])
                                       for p in (x.get("audit") or {}).get("packages", [])}
    return keys


def compare(prev: str, out: str) -> list[str]:
    before, after = finding_keys(prev), finding_keys(out)
    lines = []
    for name in after:
        if name not in before:
            continue
        new, fixed = after[name] - before[name], before[name] - after[name]
        lines.append(f"{name}: {len(after[name])} now, {len(new)} new, {len(fixed)} fixed")
    return lines


def card(out: str, ran: set[str]) -> list[tuple[str, list[str]]]:
    get = lambda k: load(out, k) if k in ran else None
    fp, st, rn, cr, dr, tr, dp, cf, ah, ts, ps = (get(k) for k in (
        "fingerprint", "steering_refs", "retired_names", "cruft_scan", "drag", "transcripts", "deps",
        "config_refs", "agent_home", "test_scan", "prompt_surfaces"))
    rows: list[tuple[str, list[str]]] = []

    if st:
        f = st["findings"]
        by = lambda kinds, statuses=None: [x for x in f if x["kind"] in kinds
                                           and (statuses is None or x["status"] in statuses)]
        steering_files = sum(len(st["steering"].get(k, [])) for k in STEERING_KINDS)
        lines = [
            f"always-loaded {st['always_loaded_bytes']:,} bytes (~{st['always_loaded_bytes'] // 4:,} tokens every turn)",
            f"{steering_files} steering files for {n((fp or {}).get('agent_tools'))} agent tool(s)",
            f"broken references in instruction files: always {len(by(('always',)))}, "
            f"scoped {len(by(('scoped',)))}, on-demand {len(by(('on-demand',)))}",
        ]
        cites = by(("always", "scoped", "on-demand", "spec", "doc", "code"), ("section-gone", "import-stub"))
        if cites:
            lines.append(f"pointers at a section that's gone, or at an instruction file that is now only an import: "
                         f"{len(cites)} (in code comments {sum(1 for x in cites if x['kind'] == 'code')})")
        if ps and ps.get("findings") is not None:
            c = ps.get("counts") or {}
            if ps["findings"]:
                lines.append(f"runtime prompts and tool descriptions in code: {len(ps['findings'])} findings ("
                             + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in c.items()) + ")")
        for w in (fp or {}).get("loading_warnings", []):
            lines.append(f"LOADING: {w}")
        rows.append(("1 Steering", lines))
        if ah is not None:
            rows.append(("2 Memory and agent setup", memory_lines(ah)))

        cs = cr or {}
        plan = cs.get("plan_sprawl") or {}
        missing = ("missing", "missing-name", "deleted", "moved", "missing-script", "untracked", "other-worktree",
                   "outside-repo")
        targets = {x["ref"] for x in by(("doc", "spec"), missing)}
        rows.append(("3 Authority", [
            f"broken references: specs {len(by(('spec',), missing))}, docs {len(by(('doc',), missing))} "
            f"({len(targets)} distinct targets), plans {len(by(('plan',)))}, history {len(by(('history',)))}",
            f"version claims that disagree with the manifest: {len(by(('always', 'scoped', 'on-demand', 'spec', 'doc'), ('version-differs',)))}",
            f"docs whose header says unbuilt: {n(cs.get('plan_status'))}; session-style docs "
            f"{plan.get('session_docs_total', '?')}; unlinked docs {n(cs.get('orphan_docs'))}",
            f"task lists done but not archived, or open with shipped work: {n(cs.get('plan_checkboxes'))}; "
            f"stale plan folders {n(cs.get('stale_plan_dirs'))}; unmarked docs claiming authority {n(cs.get('authority_claims'))}",
            f"links to files this checkout has but git doesn't: {sum(1 for x in f if x['status'] == 'untracked')}; "
            f"found only in another worktree: {sum(1 for x in f if x['status'] == 'other-worktree')}; "
            f"pointing outside the repo: {sum(1 for x in f if x['status'] == 'outside-repo')}",
        ]))
    if rn is not None:
        in_steer = [r for r in rn if any(k in r["hits"] for k in STEERING_KINDS + ("spec",))]
        rows.append(("4 Retired names", [
            f"{len(rn)} retired names still present; {len(in_steer)} in instructions or specs",
            ("top: " + ", ".join(r["term"] for r in rn[:8])) if rn else "none found",
        ]))
    if cr:
        par = cr.get("parallel") or []
        cfg = (cf or {}).get("findings") or []
        rows.append(("5 Ghost code and config", [
            f"config entries naming paths that are gone: {len(cfg)}"
            + (f" ({', '.join(f'{k} {v}' for k, v in list((cf or {}).get('by_file', {}).items())[:4])})" if cfg else ""),
            f"parallel implementations {n(par)} ({sum(1 for p in par if p.get('file_refs') and p.get('sibling_refs'))} "
            f"with both copies referenced), commented-out code blocks in {n(cr.get('commented_code'))} files",
            *(test_lines(ts) if ts else []),
            "UNCHECKED until the stack's dead-code tool runs (references/ecosystems.md)",
        ]))
    drag_lines = []
    if dr:
        size = dr.get("size", {})
        blob = (dr.get("largest_blobs") or [{}])[0]
        drag_lines.append(f"repo pack {size.get('pack')} + loose {size.get('loose')}, "
                          f"largest blob {blob.get('mb')} MB ({blob.get('path')})")
        ci = dr.get("ci") or {}
        cur = [w for w in ci.get("workflows", []) if w.get("current") and w.get("median_min") is not None]
        if cur:
            slow = max(cur, key=lambda w: w["median_min"])
            flaky = max(cur, key=lambda w: w["fail_rate"])
            drag_lines.append(f"slowest CI {slow['workflow']} median {slow['median_min']} min over {slow['runs']} runs; "
                              f"highest failure {flaky['workflow']} {int(flaky['fail_rate'] * 100)}%")
        elif "skipped" in ci:
            drag_lines.append(f"CI: skipped ({ci['skipped']})")
        every = [h["hook"] for h in dr.get("hooks", []) if h.get("every_tool_call")]
        if every:
            drag_lines.append(f"hooks on every agent tool call: {len(every)}")
    if tr is not None:
        total = sum((tr.get("sessions") or {}).values())
        st_ = tr.get("stumbles", {})
        top = [f"{x['what']} ({x['times']}x)" for sig in ("command not found", "missing script", "missing path")
               for x in st_.get(sig, [])[:2]]
        cov = "; LOW COVERAGE" if tr.get("commits_in_window") and total < max(5, tr["commits_in_window"] // 20) else ""
        drag_lines.append(f"agent sessions {total} for {tr.get('commits_in_window', '?')} commits{cov}, "
                          f"tool calls {tr.get('tool_calls', 0):,}, failed {sum(tr.get('tool_errors', {}).values())}; "
                          f"stumbles: {', '.join(top) or 'none'}")
    if drag_lines:
        rows.append(("6 Drag", drag_lines))
    if cr:
        dep_lines = []
        for x in (dp or {}).get("results", []):
            a, o = x.get("audit") or {}, x.get("outdated") or {}
            if "skipped" in x:
                dep_lines.append(f"{x['pm']} {x['dir']}: skipped ({x['skipped']})")
                continue
            vul = a.get("counts") or {}
            dep_lines.append(f"{x['pm']} {x['dir']}: vulnerabilities {vul or 'none'}"
                             + (f"; {o['major_behind_total']} packages a major or more behind" if "major_behind_total" in o else "")
                             + (f"; {len(o['declared_not_installed'])} declared but not installed"
                                if o.get("declared_not_installed") else ""))
        if dp is None:
            dep_lines.append("vulnerable and outdated deps: UNCHECKED (--no-deps or --no-live)")
        env = cr.get("env_vars") or {}
        rows.append(("7 Dependency rot", dep_lines + [
            f"package-manager conflicts {n(cr.get('lockfiles'))}, runtime pins that disagree {n(cr.get('versions'))}",
            f"model IDs outside catalogs {n((cr.get('model_ids') or {}).get('ids'))}",
            f"env vars read but undocumented {n(env.get('used_but_undocumented'))} "
            f"(app {sum(1 for x in env.get('used_but_undocumented', []) if x.get('area') == 'app')}), "
            f"declared but unused {n(env.get('declared_but_unused'))}",
        ]))
        b = (dr or {}).get("branches") or {}
        plan = cr.get("plan_sprawl") or {}
        clutter = [
            f"tracked scratch/backup {n(cr.get('scratch'))}, tracked but in the repo's .gitignore "
            f"{n((cr.get('ignored') or {}).get('by_repo_gitignore'))}, build output dirs {n(cr.get('build_output'))}, "
            f"files over 1 MB {n(cr.get('large_files'))}",
            f"root files nothing names {n(plan.get('root_unreferenced_files'))}, dated piles {n(cr.get('dated_piles'))}, "
            f"unlinked assets {sum(x.get('files', 0) for x in cr.get('orphan_assets') or [] if isinstance(x, dict))}",
        ]
        sec = (dr or {}).get("actions_secrets") or {}
        if sec and "skipped" not in sec:
            clutter.append(f"Actions secrets and variables no workflow reads: {len(sec.get('unused', []))}; "
                           f"read but not defined: {len(sec.get('read_but_not_defined', []))}")
        if b:
            clutter.append(f"local branches merged into base {b.get('merged_into_base')}, upstream gone "
                           f"{n(b.get('upstream_gone'))}; remote branches merged {b.get('remote_merged_into_base')}; "
                           f"worktrees {b.get('worktrees')} ({b.get('prunable_worktrees')} prunable)")
        rows.append(("8 Clutter", clutter))
        eh = cr.get("escape_hatches") or {}
        eh_rows = [x for x in eh.get("rows", []) if isinstance(x, dict)]
        grew = [f"{x['kind']} {x['90_days_ago']}→{x['now']}" for x in eh_rows
                if x.get("90_days_ago") is not None and x["now"] > x["90_days_ago"]]
        todos = cr.get("todos") or {}
        sg = ((ts or {}).get("skip_guards") or {}).get("counts") or {}
        rows.append(("9 Escape hatches", [
            *([f"test skip guards: {', '.join(f'{k} {v}' for k, v in sg.items())}"] if sg else []),
            ("in code: " + ", ".join(f"{x['kind']} {x['now']}" for x in eh_rows)) if eh_rows else "none counted",
            eh.get("note") or f"grew in 90 days: {', '.join(grew) or 'none'} (code files "
                              f"{eh.get('code_files_90_days_ago')}→{eh.get('code_files_now')})",
            f"TODO/FIXME in code {todos.get('total', '?')}, over 180 days {todos.get('over_180_days', '?')}",
        ]))
    return rows


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = git(args[0] if args else ".", "rev-parse", "--show-toplevel").strip()
    if not root:
        sys.exit("not a git repository")
    out = flag("out") or os.path.join(tempfile.gettempdir(),
                                      f"cobweb-{os.path.basename(root)}-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(out, exist_ok=True)
    live = "--no-live" not in sys.argv

    # Fingerprint first: a checkout behind its base reports problems already fixed.
    run_check("fingerprint", root, out, [] if live else ["--offline"])
    fp = load(out, "fingerprint") or {}
    c = fp.get("checkout", {})
    if live and c.get("behind_base") and "--here" not in sys.argv:
        print(f"STOP: this checkout is {c['behind_base']} commits behind {c['base']}. Sweep the base instead:\n"
              f"  git -C {root} worktree add --detach <tmp> {c['base']}\n"
              f"  python3 -I {os.path.join(HERE, 'sweep.py')} <tmp> --also={root} ...\n"
              f"then `git -C {root} worktree remove --force <tmp>`. Pass --here to sweep this checkout anyway.")
        if c.get("base_ref_stale"):
            print(f"Also: local {c['base']} ({c['local_base']}) is older than origin ({c['remote_base']}).")
        return

    also = [a for a in sys.argv if a.startswith("--also=")]
    jobs = [("config_refs", []), ("test_scan", []), ("prompt_surfaces", []), ("steering_refs", [] if live else ["--no-live"]), ("retired_names", [f"--since={flag('since', '12.months')}"]),
            ("cruft_scan", []), ("drag", ["--no-live"] if not live else (["--no-ci"] if "--no-ci" in sys.argv else []))]
    if live and "--no-deps" not in sys.argv:
        jobs.append(("deps", []))
    if "--transcripts" in sys.argv:
        jobs.append(("transcripts", [f"--days={flag('days', '60')}", *also]))
    start = time.time()
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        results = list(pool.map(lambda j: run_check(j[0], root, out, j[1]), jobs))
    # Memory is checked against the retired names, so it runs second. A snapshot's
    # memory is today's, not the snapshot's, so snapshot mode skips it.
    if live and "--no-memory" not in sys.argv:
        home_args = [f"--retired={os.path.join(out, 'retired_names.json')}", *also]
        if "--no-global" in sys.argv:
            home_args.append("--no-global")
        results.append(run_check("agent_home", root, out, home_args))
        jobs.append(("agent_home", home_args))
    results.insert(0, ("fingerprint", 0.0, 0))

    print(f"# Cobweb health card: {root}")
    print(f"swept {time.strftime('%Y-%m-%d')} in {round(time.time() - start)} s wall; details in {out}/<check>.txt")
    if not live:
        print("snapshot mode: CI, branches, deps and remote checks skipped")
    elif c.get("behind_base"):
        print(f"WARNING: --here on a checkout {c['behind_base']} commits behind {c['base']}: "
              "findings include things already fixed there.")
    if live and c.get("base_ref_stale"):
        print(f"WARNING: local {c['base']} ({c['local_base']}) is older than origin ({c['remote_base']}); "
              "findings may already be fixed upstream.")
    if c.get("uncommitted_paths"):
        print(f"note: {c['uncommitted_paths']} uncommitted paths; findings reflect the working tree")
    h = fp.get("history", {})
    print(f"project: since {h.get('first_commit')}, {h.get('commits')} commits ({h.get('commits_30d')} in 30 days), "
          f"stacks {', '.join(fp.get('stacks', {}))}")
    for bucket, lines in card(out, {name for name, _ in jobs} | {"fingerprint"}):
        print(f"\n{bucket}")
        for line in lines:
            print(f"  - {line}")
    failed = [f"{name} (exit {code})" for name, _, code in results if code != 0]
    print("\nchecks: " + ", ".join(f"{name} {t}s" for name, t, _ in results[1:]))
    if failed:
        print("check problems (read the .txt): " + ", ".join(failed))
    if "--transcripts" not in sys.argv:
        print("not run: agent session logs (opt-in: --transcripts)")
    prev = flag("compare")
    if prev:
        print(f"\nsince {prev}:")
        for line in compare(prev, out) or ["nothing comparable (the earlier folder has no matching checks)"]:
            print(f"  - {line}")


if __name__ == "__main__":
    main()
