import assert from "node:assert/strict"
import { join } from "node:path"
import { test } from "node:test"
import { collect } from "../../scripts/ci_health.mjs"
import { analyze, quantiles, toMarkdown } from "../../scripts/health_report.mjs"
import { node, SCRIPTS } from "./helpers.mjs"

const NOW = new Date("2026-10-30T00:00:00Z")
const TOKEN = `ghp_${"A".repeat(36)}`
const at = (minutes) => new Date(NOW.getTime() - 86_400_000 + minutes * 60_000).toISOString()

function run(i, over = {}) {
  return { id: i, name: i === 1 ? `deploy ${TOKEN}` : "ci", workflow_id: 7, event: i % 2 ? "push" : "pull_request", head_branch: i % 2 ? "main" : "feature", head_sha: `sha${i}`, run_attempt: 1, status: "completed", conclusion: "success", created_at: at(i), run_started_at: at(i + 1), updated_at: at(i + 6), html_url: `https://gh/runs/${i}`, ...over }
}

function fakeApi({ total = 130, failJobsFor = new Set(), rerun = 4 } = {}) {
  const runs = Array.from({ length: total }, (_, k) => run(k + 1, k + 1 === rerun ? { run_attempt: 2 } : k + 1 === 3 ? { conclusion: "failure" } : {}))
  const calls = []
  const api = async (path) => {
    calls.push(path)
    if (path === "repos/o/r") return { default_branch: "main", visibility: "private" }
    const page = /actions\/runs\?per_page=100&page=(\d+)/.exec(path)
    if (page) {
      const n = Number(page[1])
      return { total_count: total, workflow_runs: runs.slice((n - 1) * 100, n * 100) }
    }
    const jobs = /runs\/(\d+)\/attempts\/(\d+)\/jobs/.exec(path)
    if (jobs) {
      const id = Number(jobs[1])
      if (failJobsFor.has(id)) throw Object.assign(new Error("HTTP 403: API rate limit exceeded"), { kind: "rate-limited" })
      const r = runs[id - 1]
      const job = (name, labels) => ({ id: id * 10 + name.length, run_id: id, run_attempt: r.run_attempt, name, status: "completed", conclusion: "success", created_at: r.run_started_at, started_at: r.run_started_at, completed_at: at(id + 5), labels })
      return { total_count: 2, jobs: [job("unit", ["ubuntu-24.04"]), job("macos-build", ["macos-15"])] }
    }
    const attempt = /runs\/(\d+)\/attempts\/(\d+)$/.exec(path)
    if (attempt) return { conclusion: "failure", status: "completed" }
    throw new Error(`unexpected ${path}`)
  }
  return { api, calls }
}

test("Q06 pagination is bounded and truncation is reported, not hidden", async () => {
  const { api, calls } = fakeApi()
  const raw = await collect({ repo: "o/r", maxRuns: 120, maxJobRuns: 10, now: NOW, api })
  assert.equal(raw.runs.length, 120)
  assert.equal(raw.coverage.complete, false)
  assert.equal(raw.coverage.truncated, true)
  assert.ok(raw.coverage.unknowns.some((u) => /10 of 130 runs/.test(u)))
  assert.ok(calls.filter((c) => c.includes("/jobs")).length <= 10)
})

test("audit 5: hitting the job-run bound or a job page bound makes the report partial", async () => {
  const runs = Array.from({ length: 5 }, (_, i) => run(i + 1))
  const api = async (path) => {
    if (path === "repos/o/r") return { default_branch: "main" }
    if (path.includes("actions/runs?")) return { total_count: 5, workflow_runs: runs }
    const page = Number(/[?&]page=(\d+)/.exec(path)?.[1] ?? 1)
    return { total_count: 150, jobs: Array.from({ length: page === 1 ? 100 : 50 }, (_, k) => ({ id: page * 1000 + k, run_id: 1, name: "j", status: "completed", conclusion: "success", labels: [] })) }
  }
  const bounded = await collect({ repo: "o/r", maxJobRuns: 2, now: NOW, api })
  assert.equal(bounded.coverage.complete, false)
  assert.ok(bounded.coverage.unknowns.some((u) => /2 most recent of 5 completed runs/.test(u)))
  const all = await collect({ repo: "o/r", now: NOW, api })
  assert.equal(all.coverage.complete, true, "150 jobs over two pages are read in full")
  assert.equal(all.jobs.length, 5 * 150)
})

test("Q06 a rate-limited source makes the report partial and is named", async () => {
  const { api } = fakeApi({ total: 20, failJobsFor: new Set([2]) })
  const raw = await collect({ repo: "o/r", now: NOW, api })
  assert.equal(raw.coverage.complete, false)
  assert.match(raw.coverage.sources.find((s) => !s.ok).detail, /jobs for run 2: rate-limited/)
})

test("Q06 an unreadable repository yields no report", async () => {
  const raw = await collect({ repo: "o/r", now: NOW, api: async () => { throw Object.assign(new Error("HTTP 404"), { kind: "not-found" }) } })
  assert.match(raw.fatal, /cannot read o\/r/)
})

test("Q07/Q08 attempts, denominators, units, cost and redaction", async () => {
  const { api } = fakeApi({ total: 20 })
  const raw = await collect({ repo: "o/r", now: NOW, api })
  assert.equal(raw.coverage.complete, true)
  const report = analyze(raw, { collectorVersion: "test", collectedAt: NOW.toISOString() })
  assert.equal(report.counts.runsByLatestAttempt.total, 20)
  assert.equal(report.counts.runsByLatestAttempt.reconciles, true)
  assert.equal(report.counts.runsByFirstAttempt.byOutcome.failure, 2, "run 3 failed; run 4 failed on its first attempt")
  const signal = report.rerunSignals.attempts.find((s) => s.runId === 4)
  assert.equal(signal.signal, "rerun-pass")
  assert.equal(signal.confirmedFlakyTest, null)
  assert.equal(report.cost.status, "unknown")
  assert.ok(report.timings.summedJobMinutes.linux > 0 && report.timings.summedJobMinutes.macos > 0)
  assert.ok(report.findings.some((f) => f.id === "default-branch-red" && f.provisional))
  assert.ok(report.findings.some((f) => f.id === "macos-share"))
  assert.ok(!JSON.stringify(report).includes(TOKEN))
  const md = toMarkdown(report)
  assert.match(md, /Cost: unknown/)
  const jobRows = md.split("\n").filter((l) => l.startsWith("| unit · linux"))
  assert.equal(jobRows.length, 1)
  assert.equal(jobRows[0].split("|").length, 5, "a cohort label with | keeps the table at three columns")
  const priced = analyze(raw, { collectorVersion: "t", collectedAt: "x", rates: { source: "https://docs.github.com/billing", date: "2026-10-29", currency: "USD", perMinute: { linux: 0.006 } } })
  assert.equal(priced.cost.status, "estimate")
  assert.ok(priced.cost.excludes.some((e) => /unpriced runner classes: macos/.test(e)))
})

test("nearest-rank quantiles ignore missing values and report n", () => {
  assert.deepEqual(quantiles([5, null, 1, 3, 2, 4]), { n: 5, p50: 3, p90: 5, max: 5 })
  assert.deepEqual(quantiles([]), { n: 0, p50: null, p90: null, max: null })
})

test("CLI rejects invalid input with exit 2", () => {
  assert.equal(node(join(SCRIPTS, "ci_health.mjs"), ["--repo", "not a repo"]).code, 2)
  assert.equal(node(join(SCRIPTS, "ci_health.mjs"), ["--repo", "o/r", "--days", "0"]).code, 2)
})
