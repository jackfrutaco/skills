#!/usr/bin/env node
// Maps a repository's security surface without a model: entry points, dangerous
// effects, authorization-looking checks, and which entries can reach each effect
// through the import graph. Groups effects by kind and trust boundary, ranks the
// groups, and writes JSON. Read-only: it lists tracked files with git, reads them,
// and never executes project code or touches the network.
//
//   node map-surface.mjs <repo> [--out surface.json] [--since <git-rev>] [--include-tooling]
//
// --since limits the ranked groups to those containing a file changed since <rev>.
// Dev tooling (scripts/, tools/, docs/, documents/, examples/) is excluded unless
// --include-tooling is given; the output lists what was excluded.
// Patterns are heuristics for JS/TS, Python and Go; extend PATTERNS for other stacks.
import { execFileSync } from "node:child_process"
import { existsSync, readFileSync, statSync, writeFileSync } from "node:fs"
import { dirname, extname, join, normalize, relative, resolve } from "node:path"

const args = process.argv.slice(2)
const root = resolve(args[0] ?? ".")
const flag = (name) => { const i = args.indexOf(name); return i > 0 ? args[i + 1] : undefined }
const outPath = flag("--out")
const since = flag("--since")
const includeTooling = args.includes("--include-tooling")
const TOOLING = /^(scripts|tools|docs|documents|examples|evals?|benchmarks?)\//

const CODE = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go"])
const SKIP = /(^|\/)(node_modules|dist|build|out|release|vendor|\.git)\/|\.d\.ts$|\.min\.js$|(^|\/)(tests?|__tests__|fixtures?|e2e)\/|\.(test|spec)\.[cm]?[jt]sx?$|_test\.go$|(^|\/)test_[^/]*\.py$/
const MAX_FILE_BYTES = 400_000

// kind -> [regex, weight]. Entry weights rank exposure; effect weights rank harm.
const PATTERNS = {
  entry: {
    "http-route": [/\burl\.pathname\s*===|\b(app|router|server)\.(get|post|put|patch|delete|all|route)\(|^export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b|@(app|router)\.(get|post|put|patch|delete|route)\(|\bhttp\.HandleFunc\(|\bHandleFunc\(/, 5],
    "rpc-procedure": [/\b(publicProcedure|protectedProcedure)\b/, 4],
    "ipc-handler": [/\bipcMain\.(handle|on|once)\(/, 4],
    "protocol-handler": [/\bprotocol\.(handle|register\w*Protocol)\(/, 4],
    "navigation-hook": [/\bsetWindowOpenHandler\(|['"]will-navigate['"]|['"]will-redirect['"]/, 3],
    "agent-tool": [/\bregisterTool\(|\bserver\.tool\(|\btool\(\s*['"]/, 4],
    "cli-or-hook": [/\bprocess\.argv\b|\bsys\.argv\b/, 1],
  },
  effect: {
    "process-spawn": [/\b(spawn|spawnSync|execFile|execFileSync|execSync|fork)\(|\bchild_process\b|\bsubprocess\.(run|Popen|call)\(|\bexec\.Command\(/, 5],
    "code-eval": [/\beval\(|\bnew Function\(|\bvm\.(runIn\w+|Script)\b/, 5],
    "external-open": [/\bshell\.(openExternal|openPath|showItemInFolder)\(/, 4],
    "credential": [/\b(safeStorage|keytar|keychain|Keychain)\b|\b[A-Z][A-Z0-9_]*(API_KEY|SECRET|TOKEN|PRIVATE_KEY)\b/, 4],
    "fs-write": [/\b(writeFile|writeFileSync|appendFile|appendFileSync|rm|rmSync|unlink|unlinkSync|rename|renameSync|copyFile|cp|cpSync|mkdtemp)\(|\bos\.(remove|rename)\(/, 3],
    "outbound-request": [/\bfetch\(|\baxios\b|\bhttps?\.request\(|\brequests\.(get|post|put|delete)\(|\bhttp\.(Get|Post)\(/, 3],
    "raw-query": [/\.(prepare|raw|unsafe|query|execute)\(\s*[`'"]/, 3],
    "message-send": [/\b(sendEmail|sendMail|resend|twilio|webhook)\b/i, 2],
  },
  check: {
    "auth-check": [/\b(require|assert|ensure|verify|check)\w*(Auth|Session|Owner|Admin|Member|Access|Permission|Scope|Sender|Origin|Token|Signature|Trusted)\w*\(|\b(can|is)(Read|Write|Access|Trusted|Allowed|Authorized|Owner|Admin|Member)\w*\(|\btimingSafeEqual\(/, 0],
  },
}

function git(...a) { return execFileSync("git", ["-C", root, ...a], { encoding: "utf8", maxBuffer: 1 << 28 }) }

function aliases() {
  const map = []
  for (const name of ["tsconfig.json", "jsconfig.json"]) {
    const file = join(root, name)
    if (!existsSync(file)) continue
    try {
      const text = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\/|(^|[^:])\/\/.*$/gm, "$1").replace(/,(\s*[}\]])/g, "$1")
      const paths = JSON.parse(text).compilerOptions?.paths ?? {}
      for (const [from, [to]] of Object.entries(paths)) map.push([from.replace(/\*$/, ""), to.replace(/\*$/, "")])
    } catch { /* unparseable config: relative imports still resolve */ }
  }
  return map
}

const tracked = git("ls-files").split("\n").filter((f) => CODE.has(extname(f)) && !SKIP.test(f))
const files = tracked.filter((f) => includeTooling || !TOOLING.test(f))
const excludedTooling = [...new Set(tracked.filter((f) => !files.includes(f)).map((f) => f.split("/")[0]))]
const fileSet = new Set(files)
const aliasMap = aliases()
const RESOLVE_EXT = ["", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".jsx", "/index.ts", "/index.tsx", "/index.js"]

function resolveImport(from, spec) {
  let base
  if (spec.startsWith(".")) base = join(dirname(from), spec)
  else {
    const hit = aliasMap.find(([a]) => spec.startsWith(a))
    if (!hit) return null
    base = join(hit[1], spec.slice(hit[0].length))
  }
  base = normalize(base).replace(/\.js$/, "")
  for (const ext of RESOLVE_EXT) if (fileSet.has(base + ext)) return base + ext
  return null
}

// Trust boundary: the first two path segments (src/main, services/api).
const boundary = (f) => f.split("/").slice(0, f.startsWith("src/") || f.startsWith("services/") || f.startsWith("packages/") || f.startsWith("apps/") ? 2 : 1).join("/")
// Review unit: the effect file's directory, at most four segments deep
// (src/main/lib/terminal, services/api/src), so one group fits one context.
const moduleOf = (f) => { const d = dirname(f).split("/"); return d.slice(0, Math.min(d.length, 4)).join("/") || "." }

const info = new Map()
const importers = new Map()
for (const f of files) {
  const abs = join(root, f)
  if (statSync(abs).size > MAX_FILE_BYTES) continue
  const lines = readFileSync(abs, "utf8").split("\n")
  const rec = { entry: [], effect: [], check: [], lines: lines.length, imports: [] }
  lines.forEach((line, i) => {
    if (/^\s*(\/\/|#|\*)/.test(line)) return
    // An import names an effect; only a call performs it.
    const importLine = /^\s*(import\b|export\s+(\*|\{[^}]*\})\s+from\b|(const|let|var)\s+[^=]+=\s*require\(|from\s+\S+\s+import\b)/.test(line)
    for (const cls of ["entry", "effect", "check"]) {
      if (cls === "effect" && importLine) continue
      for (const [kind, [re]] of Object.entries(PATTERNS[cls])) if (re.test(line)) rec[cls].push({ kind, line: i + 1 })
    }
    for (const m of line.matchAll(/\b(?:from|import|require)\s*\(?\s*["']([^"']+)["']/g)) {
      const target = resolveImport(f, m[1])
      if (target) rec.imports.push(target)
    }
  })
  info.set(f, rec)
  for (const t of rec.imports) { if (!importers.has(t)) importers.set(t, new Set()); importers.get(t).add(f) }
}

// Entry files that can reach a file through imports (reverse BFS, bounded depth).
function reachingEntries(file, depth = 6) {
  const seen = new Set([file]); let frontier = [file]; const entries = new Set()
  for (let d = 0; d <= depth && frontier.length; d++) {
    const next = []
    for (const f of frontier) {
      if (info.get(f)?.entry.length) entries.add(f)
      for (const p of importers.get(f) ?? []) if (!seen.has(p)) { seen.add(p); next.push(p) }
    }
    frontier = next
  }
  return entries
}

let changed = null
if (since) changed = new Set(git("diff", "--name-only", `${since}...HEAD`).split("\n").concat(git("diff", "--name-only").split("\n")).filter(Boolean))

const groups = new Map()
for (const [f, rec] of info) {
  for (const e of rec.effect) {
    const id = `${e.kind}@${moduleOf(f)}`
    if (!groups.has(id)) groups.set(id, { id, effect: e.kind, boundary: boundary(f), effectSites: [], effectFiles: new Set(), entryFiles: new Set(), nearEntries: new Set(), checkSites: [], files: new Set() })
    const g = groups.get(id)
    g.effectSites.push(`${f}:${e.line}`); g.files.add(f); g.effectFiles.add(f)
    for (const entry of reachingEntries(f, 2)) g.nearEntries.add(entry)
    for (const entry of reachingEntries(f)) {
      g.entryFiles.add(entry); g.files.add(entry)
      for (const c of info.get(entry).check) g.checkSites.push(`${entry}:${c.line}`)
    }
    for (const c of rec.check) g.checkSites.push(`${f}:${c.line}`)
  }
}

const ranked = [...groups.values()].map((g) => {
  const entryKinds = new Map()
  for (const f of g.entryFiles) for (const e of info.get(f).entry) entryKinds.set(e.kind, (entryKinds.get(e.kind) ?? 0) + 1)
  const exposure = Math.max(0, ...[...entryKinds.keys()].map((k) => PATTERNS.entry[k][1]))
  const lines = [...g.effectFiles].reduce((n, f) => n + info.get(f).lines, 0)
  return {
    id: g.id, effect: g.effect, boundary: g.boundary,
    score: PATTERNS.effect[g.effect][1] * exposure,
    effectSites: g.effectSites.length, nearEntries: g.nearEntries.size, entryFiles: g.entryFiles.size, checkSites: new Set(g.checkSites).size,
    entryKinds: Object.fromEntries(entryKinds), lines,
    changed: changed ? [...g.files].some((f) => changed.has(f)) : undefined,
    sample: { effects: g.effectSites.slice(0, 15), nearEntries: [...g.nearEntries].slice(0, 15) },
    files: [...g.files].sort(),
  }
}).filter((g) => !changed || g.changed).sort((a, b) => b.score - a.score || b.nearEntries - a.nearEntries || b.effectSites - a.effectSites || a.id.localeCompare(b.id))

const totals = { files: info.size, lines: [...info.values()].reduce((n, r) => n + r.lines, 0), entrySites: 0, effectSites: 0 }
for (const r of info.values()) { totals.entrySites += r.entry.length; totals.effectSites += r.effect.length }
const revision = git("rev-parse", "--short", "HEAD").trim()
const result = { revision, since: since ?? null, excludedTooling, totals, groups: ranked }
const json = JSON.stringify(result, null, 1)
if (outPath) writeFileSync(outPath, json + "\n")
if (excludedTooling.length) console.log(`excluded tooling (use --include-tooling): ${excludedTooling.join(", ")}`)
console.log(`revision ${revision}: ${totals.files} files, ${totals.lines} lines, ${totals.entrySites} entry sites, ${totals.effectSites} effect sites, ${ranked.length} groups${since ? ` touched since ${since}` : ""}`)
for (const g of ranked.slice(0, 15)) console.log(`${String(g.score).padStart(3)}  ${g.id}  effects=${g.effectSites} near-entries=${g.nearEntries} entries=${g.entryFiles} checks=${g.checkSites} effect-file-lines=${g.lines}`)
if (outPath) console.log(`full map: ${relative(process.cwd(), outPath) || outPath}`)
