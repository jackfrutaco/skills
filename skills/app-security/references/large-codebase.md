# Large and broad reviews

Use this when §1 sends you here: a whole-app request whose entry and effect code
exceeds 3,000 lines, or a change review over a mapped repository. Reading the
codebase is the cost to avoid. Map it with a script, triage from summaries, and
spend model context only on the groups you select.

## 1. Map without a model

```
node scripts/map-surface.mjs <repo> --out <private-dir>/surface.json            # whole app
node scripts/map-surface.mjs <repo> --out <private-dir>/surface.json --since <rev>  # change review
```

The script reads tracked files and makes no network calls. It reports:
- **Entries:** routes, RPC procedures, IPC and protocol handlers, agent tools, CLIs.
- **Effects:** process spawn, eval, external open, credentials, file writes,
  outbound requests, raw queries, message sends.
- **Checks:** names that look like authorization checks.
- **Groups:** one effect kind in one module, plus every entry file that reaches it
  through imports.

A 1.0M-line Electron app mapped to 278 groups in 4 seconds; the median group had
about 440 lines of effect code.

If the host offers a code-search index, query it for entry and effect kinds the
patterns miss (custom routers, plugin registries, message buses) and add them to
the map. The index finds names the regexes do not know.

- **Patterns are heuristics.** A path the map does not show is "unmapped", never
  "safe". For a stack other than JS/TS, Python or Go, add patterns to `PATTERNS`
  or list entries and effects with grep, then continue.
- **Dev tooling is excluded by default** (`scripts/`, `tools/`, `docs/`, `documents/`).
  Name the exclusion in the report, or pass `--include-tooling` if build scripts
  are in scope.

## 2. Add configuration groups

The map sees code paths, not settings. Add one group for each of these that
exists. Each is a coverage row the map cannot reach, and the place real desktop
and release findings live:
- packaging, fuses and entitlements
- window and webview preferences
- CSP
- CI workflows and their secrets
- infrastructure config (wrangler, terraform, k8s)
- dependency lockfiles

## 3. Triage from summaries

Read only the group summaries (id, effect, entry kinds, counts, sample sites),
never code, and rank with §3's rule: worst effect reachable by the least-privileged
actor.

Rank exposure:
- internet route
- renderer IPC or RPC
- agent tool
- local CLI

Rank harm:
- spawn or eval
- credentials or external open
- writes and outbound requests
- queries and sends

The script's score breaks no ties; your ranking must.

- **Whole-app request:** select the top 5 code groups plus every configuration group.
- **Named area:** select the groups inside it.
- **More than 5 groups selected:** tell the user the count and the cost before
  starting. On that app a group review measured 132k–203k tokens (mean about 165k)
  and 7–10 minutes.
- **Write the ledger first:** one line per group, `selected`, `deferred: <reason>`
  or `not applicable`. A deferred group stays visible in coverage.

## 4. Review each selected group in a fresh top-tier context

Give each reviewer (a subagent or a separate session):
- this skill
- the group's effect sites, entry files and file list
- the ledger path

It runs §3–§6 on that group only, reading entry handlers, the path to the effect
and the effect sites, not the whole module. It appends one ledger entry. At most 3
groups run at once.

A fresh context reads only its slice. Measured on a fixture, helpers whose lead
re-read the code anyway cost 1.8× the tokens with no gain in findings.

Ledger entry (`ledger.jsonl`, one JSON object per line):

```json
{"group":"process-spawn@src/main/lib/process","revision":"<sha>","status":"reviewed",
 "findings":[{"id":"SEC-004","title":"…","rating":"High · provisional · supported by source · 1: …","evidence":["file:line"]}],
 "protections":["file:line …"],"unknowns":["…"],"reviewedAt":"2026-11-03"}
```

## 5. Final pass: read the ledger, not the code

1. **Normalize severity** across groups with §5; groups reviewed separately drift.
2. **Shared dependencies.** For each credential, quota, sender, signing key or
   process identity that a finding's effect uses, list the other features that
   depend on it. If one abuse would take those down, the harm includes them.
3. **Merge root causes.** Findings in different groups with one cause become one
   finding with several paths.
4. **Re-open code only** to verify evidence for findings you will report.

Then write one report. Its coverage table lists every group as `reviewed`,
`deferred` or `not applicable`.

## 6. Next run

Run the map with `--since <last ledger revision>` and review only the groups whose
files changed. Carry the other ledger entries forward with their original date. A
change to a shared credential, check or dependency reopens every group that cites it.
