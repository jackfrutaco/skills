#!/usr/bin/env node
// Read-only GitHub Actions health collector.
//
//   node ci_health.mjs --repo OWNER/REPO [--days 14] [--max-runs 500] [--max-job-runs 200]
//       [--format json|markdown] [--rates rates.json]
//
// Uses the installed `gh` login and documented read endpoints only. It never changes
// settings, dispatches or re-runs workflows, executes project code or asks for a new
// credential. JSON goes to stdout; diagnostics go to stderr.
// Exit codes: 0 complete collection (NOT "CI is healthy"; read the findings),
// 3 usable but partial report, 2 invalid input, 1 nothing usable collected.
import { execFile } from "node:child_process"
import { readFileSync, realpathSync } from "node:fs"
import { pathToFileURL } from "node:url"
import { promisify } from "node:util"
import { analyze, redact, toMarkdown } from "./health_report.mjs"

export const COLLECTOR_VERSION = "ci_health/1.1.0"
const PAGE = 100
const CONCURRENCY = 3
const MAX_JOB_PAGES = 10
const run = promisify(execFile)

/** Classify a `gh api` failure so callers can record why a source is missing. */
export function classify(message) {
  if (/rate limit/i.test(message)) return "rate-limited"
  if (/HTTP 40[13]/.test(message)) return "forbidden"
  if (/HTTP 404/.test(message)) return "not-found"
  if (/HTTP 5\d\d|ETIMEDOUT|ECONNRESET|EAI_AGAIN|timeout/i.test(message)) return "transient"
  return "error"
}

/** `gh api` reader with one retry for transient failures. */
export async function ghApi(path) {
  for (let attempt = 1; ; attempt++) {
    try {
      const { stdout } = await run("gh", ["api", "-H", "Accept: application/vnd.github+json", path], { maxBuffer: 64 * 1024 * 1024, timeout: 60_000 })
      return JSON.parse(stdout)
    } catch (error) {
      const message = String(error.stderr || error.message).trim()
      const kind = classify(message)
      if (kind === "transient" && attempt === 1) continue
      throw Object.assign(new Error(message.split("\n")[0]), { kind })
    }
  }
}

async function pool(items, limit, worker) {
  const results = new Array(items.length)
  let next = 0
  const lanes = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const index = next++
      results[index] = await worker(items[index])
    }
  })
  await Promise.all(lanes)
  return results
}

function runRecord(r) {
  return {
    id: r.id, workflow: r.path || r.name, title: r.name, workflowId: r.workflow_id, event: r.event, branch: r.head_branch, sha: r.head_sha,
    attempt: r.run_attempt ?? 1, status: r.status, conclusion: r.conclusion, createdAt: r.created_at,
    startedAt: r.run_started_at ?? null, updatedAt: r.updated_at, url: r.html_url,
  }
}

function jobRecord(j) {
  return {
    id: j.id, runId: j.run_id, attempt: j.run_attempt ?? 1, name: j.name, status: j.status, conclusion: j.conclusion,
    createdAt: j.created_at ?? null, startedAt: j.started_at, completedAt: j.completed_at, labels: j.labels ?? [],
    runnerGroup: j.runner_group_name ?? null, url: j.html_url,
  }
}

/** Collect raw evidence through `api(path)`. Never throws for a single missing source. */
export async function collect({ repo, days = 14, maxRuns = 500, maxJobRuns = 200, now = new Date(), api = ghApi }) {
  const end = now
  const start = new Date(end.getTime() - days * 86_400_000)
  const coverage = { complete: true, truncated: false, sources: [], unknowns: [] }
  const note = (source, ok, detail) => {
    coverage.sources.push({ source, ok, ...(detail ? { detail } : {}) })
    if (!ok) coverage.complete = false
  }
  let repository
  try {
    repository = await api(`repos/${repo}`)
    note("repository", true)
  } catch (error) {
    return { fatal: `cannot read ${repo}: ${error.message}`, kind: error.kind }
  }
  const runs = []
  const created = encodeURIComponent(`>=${start.toISOString().slice(0, 19)}Z`)
  let totalCount = null
  for (let page = 1; runs.length < maxRuns; page++) {
    let body
    try {
      body = await api(`repos/${repo}/actions/runs?per_page=${PAGE}&page=${page}&created=${created}`)
    } catch (error) {
      note(`runs page ${page}`, false, `${error.kind}: ${error.message}`)
      break
    }
    totalCount = body.total_count ?? totalCount
    const batch = body.workflow_runs ?? []
    runs.push(...batch.filter((r) => new Date(r.created_at) < end).map(runRecord))
    if (batch.length < PAGE) break
  }
  if (runs.length > maxRuns) runs.length = maxRuns
  if (totalCount !== null && totalCount > runs.length) {
    coverage.truncated = true
    coverage.complete = false
    coverage.unknowns.push(`${totalCount - runs.length} of ${totalCount} runs in the window were not read (--max-runs ${maxRuns} or the API's search limit)`)
  }
  if (coverage.sources.length === 1) note("runs", true)
  const partial = (message) => {
    coverage.unknowns.push(message)
    coverage.truncated = true
    coverage.complete = false
  }
  const completed = runs.filter((r) => r.status === "completed")
  const detailed = completed.slice(0, maxJobRuns)
  if (detailed.length < completed.length) {
    partial(`jobs read for the ${detailed.length} most recent of ${completed.length} completed runs only (--max-job-runs ${maxJobRuns})`)
  }
  const failures = []
  const jobs = []
  const attempts = []
  await pool(detailed, CONCURRENCY, async (r) => {
    try {
      let read = 0
      let total = 0
      for (let page = 1; page <= MAX_JOB_PAGES; page++) {
        const body = await api(`repos/${repo}/actions/runs/${r.id}/attempts/${r.attempt}/jobs?per_page=${PAGE}&page=${page}`)
        const batch = body.jobs ?? []
        jobs.push(...batch.map(jobRecord))
        read += batch.length
        total = body.total_count ?? read
        if (batch.length < PAGE || read >= total) break
      }
      if (read < total) partial(`run ${r.id}: ${read} of ${total} jobs read`)
    } catch (error) {
      failures.push(`jobs for run ${r.id}: ${error.kind}`)
    }
    for (let n = 1; n < r.attempt; n++) {
      try {
        const earlier = await api(`repos/${repo}/actions/runs/${r.id}/attempts/${n}`)
        attempts.push({ runId: r.id, attempt: n, conclusion: earlier.conclusion, status: earlier.status, startedAt: earlier.run_started_at ?? null, updatedAt: earlier.updated_at })
      } catch (error) {
        failures.push(`attempt ${n} of run ${r.id}: ${error.kind}`)
        attempts.push({ runId: r.id, attempt: n, conclusion: null, status: "unknown" })
      }
    }
  })
  if (failures.length) note("jobs and attempts", false, `${failures.length} read(s) failed: ${failures.slice(0, 5).join("; ")}`)
  else note("jobs and attempts", true)
  return {
    repository: { name: repo, defaultBranch: repository.default_branch, visibility: repository.visibility ?? (repository.private ? "private" : "public") },
    window: { start: start.toISOString(), end: end.toISOString(), days },
    limits: { maxRuns, maxJobRuns, concurrency: CONCURRENCY, retriesPerRequest: 1 },
    coverage, runs, jobs, attempts,
  }
}

function parse(argv) {
  const args = { days: "14", "max-runs": "500", "max-job-runs": "200", format: "json" }
  for (let i = 0; i < argv.length; i++) {
    const name = argv[i].replace(/^--/, "")
    if (!argv[i].startsWith("--") || !(name in args || name === "repo" || name === "rates")) throw new Error(`unknown argument ${argv[i]}`)
    args[name] = argv[++i]
  }
  if (!/^[\w.-]+\/[\w.-]+$/.test(args.repo ?? "")) throw new Error("--repo OWNER/REPO is required")
  for (const key of ["days", "max-runs", "max-job-runs"]) {
    if (!/^\d+$/.test(args[key]) || Number(args[key]) < 1) throw new Error(`--${key} must be a positive integer`)
  }
  if (!["json", "markdown"].includes(args.format)) throw new Error("--format must be json or markdown")
  return args
}

async function cli(argv) {
  let args
  let rates = null
  try {
    args = parse(argv)
    if (args.rates) rates = JSON.parse(readFileSync(args.rates, "utf8"))
  } catch (error) {
    console.error(`error: ${error.message}`)
    return 2
  }
  const raw = await collect({ repo: args.repo, days: Number(args.days), maxRuns: Number(args["max-runs"]), maxJobRuns: Number(args["max-job-runs"]) })
  if (raw.fatal) {
    console.error(`error: ${redact(raw.fatal)}`)
    return 1
  }
  const report = analyze(raw, { collectorVersion: COLLECTOR_VERSION, collectedAt: new Date().toISOString(), rates })
  process.stdout.write(args.format === "markdown" ? toMarkdown(report) : `${JSON.stringify(report, null, 2)}\n`)
  return report.coverage.complete ? 0 : 3
}

if (process.argv[1] && pathToFileURL(realpathSync(process.argv[1])).href === import.meta.url) {
  cli(process.argv.slice(2)).then((code) => { process.exitCode = code })
}
