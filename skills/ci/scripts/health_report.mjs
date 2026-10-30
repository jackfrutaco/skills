// Pure analysis for ci_health.mjs: raw runs/jobs/attempts in, schema-1 report out.
// No I/O, so fixtures can test every rule.

export const SCHEMA_VERSION = 1
const SECRET_PATTERNS = [
  /\b(?:ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{20,}\b/g,
  /\bgithub_pat_[A-Za-z0-9_]{20,}\b/g,
  /\bAKIA[0-9A-Z]{16}\b/g,
  /\bxox[abprs]-[A-Za-z0-9-]{10,}\b/g,
  /\bsk-[A-Za-z0-9_-]{20,}\b/g,
  /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
  /\b(Bearer|token)\s+[A-Za-z0-9._~+/-]{16,}=*/gi,
]
const PROVISIONAL_BELOW = 30

export function redact(value) {
  if (typeof value === "string") return SECRET_PATTERNS.reduce((text, re) => text.replace(re, "[REDACTED]"), value)
  if (Array.isArray(value)) return value.map(redact)
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, redact(v)]))
  return value
}

const seconds = (from, to) => (from && to ? Math.max(0, (Date.parse(to) - Date.parse(from)) / 1000) : null)

/** Nearest-rank quantiles over finite numbers; null when there is no data. */
export function quantiles(values) {
  const sorted = values.filter((v) => Number.isFinite(v)).sort((a, b) => a - b)
  const at = (p) => (sorted.length ? sorted[Math.ceil(p * sorted.length) - 1] : null)
  return { n: sorted.length, p50: at(0.5), p90: at(0.9), max: sorted.length ? sorted.at(-1) : null }
}

export function outcome(item) {
  if (item.status && item.status !== "completed") return item.status === "unknown" ? "unknown" : `not-completed:${item.status}`
  return item.conclusion ?? "unknown"
}

function tally(items) {
  const byOutcome = {}
  for (const item of items) byOutcome[outcome(item)] = (byOutcome[outcome(item)] ?? 0) + 1
  const sum = Object.values(byOutcome).reduce((a, b) => a + b, 0)
  return { total: items.length, byOutcome, reconciles: sum === items.length }
}

export function runnerClass(labels) {
  const text = labels.join(" ").toLowerCase()
  if (text.includes("blacksmith")) return "blacksmith"
  if (text.includes("self-hosted")) return "self-hosted"
  if (text.includes("macos")) return "macos"
  if (text.includes("windows")) return "windows"
  if (/ubuntu|linux/.test(text)) return "linux"
  return "other"
}

function groupBy(items, key) {
  const groups = new Map()
  for (const item of items) {
    const k = key(item)
    if (!groups.has(k)) groups.set(k, [])
    groups.get(k).push(item)
  }
  return groups
}

function rerunSignals(runs, attempts) {
  const byRun = groupBy(attempts, (a) => a.runId)
  const signals = []
  for (const run of runs.filter((r) => r.attempt > 1)) {
    const history = [...(byRun.get(run.id) ?? []), { attempt: run.attempt, conclusion: run.conclusion, status: run.status }]
      .sort((a, b) => a.attempt - b.attempt)
      .map((a) => ({ attempt: a.attempt, outcome: outcome(a) }))
    const first = history[0].outcome
    const last = history.at(-1).outcome
    const kind = first === "unknown" ? "first-attempt-unknown" : first !== "success" && last === "success" ? "rerun-pass" : "rerun-no-change"
    signals.push({ runId: run.id, workflow: run.workflow, event: run.event, sha: run.sha, attempts: history, signal: kind, confirmedFlakyTest: null, url: run.url })
  }
  const sameCandidate = []
  for (const [key, group] of groupBy(runs.filter((r) => r.status === "completed"), (r) => `${r.workflowId}@${r.sha}`)) {
    const ordered = group.sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt))
    const red = ordered.findIndex((r) => r.conclusion === "failure")
    if (red >= 0 && ordered.slice(red + 1).some((r) => r.conclusion === "success")) {
      sameCandidate.push({ key, runIds: ordered.map((r) => r.id), signal: "same-candidate-later-pass" })
    }
  }
  return { attempts: signals, sameCandidate, note: "A later pass is a signal of nondeterminism or environment change, not a confirmed flaky test, until test-level evidence identifies the same test and inputs." }
}

function timings(runs, jobs) {
  const firstAttempts = runs.filter((r) => r.attempt === 1)
  const runCohorts = [...groupBy(runs, (r) => `${r.event} | ${r.workflow}`)].map(([cohort, group]) => ({
    cohort,
    wallSecondsProxy: quantiles(group.filter((r) => r.status === "completed").map((r) => seconds(r.startedAt, r.updatedAt))),
  }))
  const jobCohorts = [...groupBy(jobs, (j) => `${j.name} | ${runnerClass(j.labels)} | ${j.labels.join(",")}`)].map(([cohort, group]) => ({
    cohort,
    queueSeconds: quantiles(group.map((j) => seconds(j.createdAt, j.startedAt))),
    durationSeconds: quantiles(group.map((j) => seconds(j.startedAt, j.completedAt))),
  }))
  const minutesByRunner = {}
  for (const job of jobs) {
    const s = seconds(job.startedAt, job.completedAt)
    if (s === null) continue
    const cls = runnerClass(job.labels)
    minutesByRunner[cls] = (minutesByRunner[cls] ?? 0) + s / 60
  }
  return {
    units: "seconds; summed job time in minutes",
    method: "nearest-rank quantiles over the cohort's observations",
    definitions: {
      queueSeconds: "job started_at - created_at: time waiting for a runner. Runs start almost at creation, so run-level queue is not reported",
      wallSecondsProxy: "run updated_at - run_started_at; includes post-completion updates, so it is an upper-bound proxy for end-to-end time",
      durationSeconds: "job completed_at - started_at, including runner setup steps; not pure test time",
      summedJobMinutes: "sum of job durations; overlapping jobs make this larger than wall time",
    },
    firstAttemptRuns: firstAttempts.length,
    runCohorts,
    jobCohorts,
    summedJobMinutes: Object.fromEntries(Object.entries(minutesByRunner).map(([k, v]) => [k, Math.round(v * 10) / 10])),
  }
}

function cost(jobs, repository, rates) {
  if (!rates) return { status: "unknown", reason: "no billing source read and no --rates file supplied; nothing is assumed to be free or zero" }
  const perClass = {}
  const unpriced = new Set()
  for (const job of jobs) {
    const s = seconds(job.startedAt, job.completedAt)
    if (s === null) continue
    const cls = runnerClass(job.labels)
    if (rates.perMinute?.[cls] === undefined) {
      unpriced.add(cls)
      continue
    }
    perClass[cls] = (perClass[cls] ?? 0) + Math.ceil(s / 60)
  }
  const amount = Object.entries(perClass).reduce((sum, [cls, minutes]) => sum + minutes * rates.perMinute[cls], 0)
  return {
    status: "estimate",
    source: rates.source ?? null, rateDate: rates.date ?? null, currency: rates.currency ?? null,
    roundedMinutesByRunner: perClass, listPriceEstimate: Math.round(amount * 100) / 100,
    excludes: ["included free allowance", "storage and cache", "larger-runner multipliers not in the rates file", ...(unpriced.size ? [`unpriced runner classes: ${[...unpriced].join(", ")}`] : [])],
    note: repository.visibility === "public" ? "Standard GitHub-hosted runners are free for public repositories; this list-price figure is not a bill." : "List price before any included allowance; not observed spend.",
  }
}

function findings(report, runs, defaultBranch) {
  const out = []
  const add = (id, priority, title, evidence, next, n) =>
    out.push({ id, priority, title, sampleSize: n, provisional: n !== undefined && n < PROVISIONAL_BELOW, evidence: evidence.slice(0, 5), next })
  if (!report.coverage.complete) add("partial-coverage", "P1", "Collection is partial; conclusions below are limited", report.coverage.unknowns, "Re-run with access/bounds that cover the window, or state the gap in any decision")
  const mainRuns = runs.filter((r) => r.event === "push" && r.branch === defaultBranch && r.status === "completed")
  const mainRed = mainRuns.filter((r) => ["failure", "timed_out", "startup_failure"].includes(r.conclusion))
  if (mainRed.length) add("default-branch-red", "P1", `${mainRed.length} of ${mainRuns.length} ${defaultBranch} push runs did not pass`, mainRed.map((r) => r.url), "Check whether merges are re-verified (merge queue or strict up-to-date) and whether all required checks are actually required", mainRuns.length)
  const reruns = report.rerunSignals.attempts.filter((s) => s.signal === "rerun-pass")
  if (reruns.length) add("rerun-pass", "P2", `${reruns.length} run(s) passed only on a later attempt`, reruns.map((s) => s.url), "Collect test-level reports for those attempts before calling anything flaky; re-runs hide the first failure", runs.length)
  for (const [cohort, group] of groupBy(runs.filter((r) => r.status === "completed" && r.attempt >= 1), (r) => `${r.event} | ${r.workflow}`)) {
    const red = group.filter((r) => ["failure", "timed_out"].includes(r.conclusion))
    if (red.length >= 2 && red.length / group.length >= 0.25 && !(cohort.startsWith("push") && mainRed.length)) {
      add("failing-cohort", "P2", `${cohort}: ${red.length} of ${group.length} runs failed`, red.map((r) => r.url), "Read the first failure of each run (not the re-run) and separate product, test, infrastructure and configuration causes", group.length)
    }
  }
  const startup = runs.filter((r) => ["startup_failure", "action_required"].includes(r.conclusion))
  if (startup.length) add("startup-or-approval", "P2", `${startup.length} run(s) ended in startup_failure or action_required`, startup.map((r) => r.url), "Check workflow syntax, runner labels/app access and fork approval settings", runs.length)
  for (const cohort of report.timings.runCohorts) {
    const p90 = cohort.wallSecondsProxy.p90
    if (cohort.cohort.startsWith("pull_request") && p90 !== null && p90 > 600) {
      add("slow-pr-feedback", "P2", `${cohort.cohort}: p90 ${Math.round(p90 / 60)} min (upper-bound proxy) exceeds the ~10 min feedback objective`, [], "Profile the critical path (setup vs execution) before changing tiers; never drop required evidence to hit the target", cohort.wallSecondsProxy.n)
    }
  }
  for (const cohort of report.timings.jobCohorts) {
    const p90 = cohort.queueSeconds.p90
    if (p90 !== null && p90 > 120) add("runner-queue", "P2", `${cohort.cohort}: p90 queue ${Math.round(p90)} s`, [], "Compare concurrency limits, runner availability and label correctness before buying capacity", cohort.queueSeconds.n)
  }
  const minutes = report.timings.summedJobMinutes
  const total = Object.values(minutes).reduce((a, b) => a + b, 0)
  if (total > 0 && (minutes.macos ?? 0) / total > 0.3) add("macos-share", "P2", `macOS is ${Math.round((100 * minutes.macos) / total)}% of summed job minutes`, [], "Keep macOS for checks that need it (native APIs, signing, packaging); move portable checks to Linux", jobsCount(report))
  const order = { P1: 0, P2: 1, P3: 2 }
  return out.sort((a, b) => order[a.priority] - order[b.priority])
}

const jobsCount = (report) => report.counts.jobs.total

/** Build the schema-1 report. */
export function analyze(raw, { collectorVersion, collectedAt, rates = null }) {
  const report = {
    schemaVersion: SCHEMA_VERSION,
    collectorVersion,
    repository: raw.repository,
    collectedAt,
    window: { ...raw.window, bounds: "start inclusive, end exclusive, by run created_at" },
    limits: raw.limits,
    coverage: raw.coverage,
    cohorts: {
      dimensions: ["event", "workflow", "job name", "runner class and labels"],
      notCollected: ["workflow file revision per run", "cache hit/miss", "runner image version"],
    },
    counts: {
      runsByLatestAttempt: tally(raw.runs),
      runsByFirstAttempt: tally(raw.runs.map((r) => (r.attempt === 1 ? r : raw.attempts.find((a) => a.runId === r.id && a.attempt === 1) ?? { status: "unknown" }))),
      jobs: tally(raw.jobs),
      byEvent: Object.fromEntries([...groupBy(raw.runs, (r) => r.event)].map(([e, g]) => [e, g.length])),
    },
    timings: timings(raw.runs, raw.jobs),
    rerunSignals: rerunSignals(raw.runs, raw.attempts),
    cost: cost(raw.jobs, raw.repository, rates),
    findings: [],
    evidence: {
      runs: raw.runs.map((r) => ({ id: r.id, attempt: r.attempt, workflow: r.workflow, event: r.event, branch: r.branch, sha: r.sha, outcome: outcome(r), url: r.url })),
      jobsRead: raw.jobs.length,
    },
  }
  report.findings = findings(report, raw.runs, raw.repository.defaultBranch)
  return redact(report)
}

const cell = (text) => String(text).replaceAll("|", "·")
const fmt = (q) => (q.n ? `${q.p50}/${q.p90} s (n=${q.n})` : "no data")

export function toMarkdown(report) {
  const c = report.counts
  const lines = [
    `# CI health: ${report.repository.name}`,
    "",
    `Collected ${report.collectedAt} by ${report.collectorVersion}. Window ${report.window.start} to ${report.window.end}.`,
    `Coverage: ${report.coverage.complete ? "complete within the stated limits" : "PARTIAL"}.${report.coverage.unknowns.length ? ` Unknowns: ${report.coverage.unknowns.join("; ")}.` : ""}`,
    "",
    "## Findings",
    ...(report.findings.length ? report.findings.map((f) => `- **${f.priority} ${f.id}**: ${f.title}${f.provisional ? ` (provisional, n=${f.sampleSize})` : ""}. Next: ${f.next}`) : ["- None from the automatic rules. That is not proof of health; read the counts."]),
    "",
    "## Outcomes",
    `Runs (latest attempt, n=${c.runsByLatestAttempt.total}): ${JSON.stringify(c.runsByLatestAttempt.byOutcome)}`,
    `Runs (first attempt, n=${c.runsByFirstAttempt.total}): ${JSON.stringify(c.runsByFirstAttempt.byOutcome)}`,
    `Jobs (n=${c.jobs.total}): ${JSON.stringify(c.jobs.byOutcome)}`,
    "",
    "## Timings (p50/p90, nearest rank)",
    "| Run cohort | Wall (proxy) |",
    "|---|---|",
    ...report.timings.runCohorts.map((r) => `| ${cell(r.cohort)} | ${fmt(r.wallSecondsProxy)} |`),
    "",
    "| Job cohort | Queue for a runner | Duration incl. setup |",
    "|---|---|---|",
    ...report.timings.jobCohorts.map((j) => `| ${cell(j.cohort)} | ${fmt(j.queueSeconds)} | ${fmt(j.durationSeconds)} |`),
    "",
    `Summed job minutes by runner: ${JSON.stringify(report.timings.summedJobMinutes)} (summed work, not wall time).`,
    "",
    `## Cost: ${report.cost.status}`,
    report.cost.status === "estimate" ? `${report.cost.listPriceEstimate} ${report.cost.currency} list price from ${report.cost.source} (${report.cost.rateDate}). ${report.cost.note} Excludes: ${report.cost.excludes.join("; ")}.` : report.cost.reason,
    "",
    `## Re-run signals: ${report.rerunSignals.attempts.filter((s) => s.signal === "rerun-pass").length} rerun-pass, ${report.rerunSignals.sameCandidate.length} same-candidate later pass`,
    report.rerunSignals.note,
    "",
  ]
  return `${lines.join("\n")}\n`
}
