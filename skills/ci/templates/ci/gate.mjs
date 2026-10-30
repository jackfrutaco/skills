#!/usr/bin/env node
// Expected-evidence gate for a GitHub Actions pipeline.
//
//   node gate.mjs select --policy ci-policy.json --event <name> --candidate <sha> [--base <sha>]
//   node gate.mjs verify --policy ci-policy.json --candidate <sha> [--attempt N] [--jobs jobs.json]
//       [--out gate-result.json]
//
// `select` decides which checks this candidate must pass (full, affected or no-op) and
// writes a selection record. `verify` passes only when every expected check succeeded,
// every omitted check has a recorded reason, and the selection belongs to this candidate
// and this exact policy. A skipped, missing or cancelled expected check never passes.
// A change to `.github/`, the policy file, its folder or these scripts always selects the
// full set, whatever the policy says, so a pull request cannot narrow its own checks by
// editing them. A pull request still runs its own copy of this code: require code-owner
// review for those paths. With --jobs (this run's job list from the API), verify also
// fails on any job the policy does not account for.
// Exit codes: 0 pass, 1 gate failed, 2 invalid input or policy.
import { execFileSync } from "node:child_process"
import { readFileSync, writeFileSync } from "node:fs"
import { dirname, relative, resolve, sep } from "node:path"
import { fileURLToPath } from "node:url"
import {
  SCHEMA_VERSION,
  fail,
  isEntry,
  main,
  matchesAny,
  parseArgs,
  policyDigest,
  readJson,
  validatePolicy,
  writeOutputs,
  writeSummary,
} from "./lib.mjs"

const FULL_EVENTS = ["push", "merge_group", "workflow_dispatch", "schedule"]
const MODES = new Set(["full", "affected", "noop"])
const FIXED_JOBS = ["select", "gate"]

/** Repository-relative POSIX path, or null when it lies outside the working directory. */
function repoPath(path) {
  const rel = relative(process.cwd(), resolve(path)).split(sep).join("/")
  return rel.startsWith("..") ? null : rel
}

/** Paths whose change always selects the full set: CI configuration and the gate itself. */
export function protectedPathsFor(policyFile, scriptsDir) {
  const out = new Set([".github/**"])
  const policy = repoPath(policyFile)
  if (policy) {
    out.add(policy)
    const dir = dirname(policy)
    if (dir !== ".") out.add(`${dir}/**`)
  }
  const scripts = repoPath(scriptsDir)
  if (scripts) out.add(`${scripts}/**`)
  return [...out]
}

function changedFiles(base, candidate, listPath) {
  if (listPath) return readFileSync(listPath, "utf8").split("\n").filter(Boolean)
  // Two-dot diff of two snapshots: a superset of the PR's own changes, never less.
  // --no-renames lists both the old and the new path of a rename.
  const out = execFileSync("git", ["diff", "--name-only", "--no-renames", base, candidate], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  })
  return out.split("\n").filter(Boolean)
}

/** Pure selection logic, exported for tests. */
export function select(policy, { event, files, baseError, protectedPaths = [".github/**"] }) {
  const names = validatePolicy(policy)
  const full = (rationale) => ({ mode: "full", rationale, expected: names, omitted: {} })
  if ((policy.fullOn?.events ?? FULL_EVENTS).includes(event)) {
    return full(`event "${event}" always runs the full set`)
  }
  if (baseError) return full(`base unavailable (${baseError}); cannot prove a narrower set`)
  if (files.length === 0) return full("no changed files detected; a no-op cannot be proven")
  const config = files.find((file) => matchesAny(file, protectedPaths))
  if (config) return full(`${config} is CI configuration; its changes always run the full set`)
  const global = files.find((file) => matchesAny(file, policy.fullOn?.paths))
  if (global) return full(`${global} is a global input`)
  const product = files.filter((file) => !matchesAny(file, policy.noop?.paths))
  if (product.length === 0) {
    return { mode: "noop", rationale: policy.noop.rationale, expected: [], omitted: Object.fromEntries(names.map((n) => [n, "no-op change"])) }
  }
  const scoped = names.filter((name) => policy.checks[name].paths)
  const unclaimed = product.find((file) => !scoped.some((name) => matchesAny(file, policy.checks[name].paths)))
  if (unclaimed) return full(`${unclaimed} is not claimed by any scoped check or the no-op list`)
  const selected = (name) => {
    const { paths, follows } = policy.checks[name]
    if (follows) return selected(follows)
    return !paths || product.some((file) => matchesAny(file, paths))
  }
  const expected = []
  const omitted = {}
  for (const name of names) {
    const { paths, follows } = policy.checks[name]
    if (selected(name)) expected.push(name)
    else omitted[name] = follows ? `follows ${follows}, which is omitted` : `no changed file matches ${paths.join(", ")}`
  }
  return { mode: "affected", rationale: `${product.length} product file(s) changed`, expected, omitted }
}

function runSelect(args) {
  if (!args.policy || !args.event || !args.candidate) fail("select needs --policy, --event and --candidate", 2)
  const policy = readJson(args.policy, "policy")
  let files = []
  let baseError
  if (!args.base || /^0+$/.test(args.base)) baseError = "no base commit for this event"
  else {
    try {
      files = changedFiles(args.base, args.candidate, args["changed-files"])
    } catch (error) {
      baseError = (error.stderr?.toString() || error.message).trim().split("\n")[0]
    }
  }
  const scriptsDir = dirname(fileURLToPath(import.meta.url))
  const protectedPaths = protectedPathsFor(args.policy, scriptsDir)
  const decision = select(policy, { event: args.event, files, baseError, protectedPaths })
  const record = {
    schemaVersion: SCHEMA_VERSION,
    policySha256: policyDigest(args.policy),
    event: args.event,
    candidate: args.candidate,
    base: args.base || null,
    changedFileCount: files.length,
    ...decision,
  }
  const line = JSON.stringify(record)
  if (args.out) writeFileSync(args.out, `${line}\n`)
  const shards = Object.entries(policy.checks)
    .filter(([, check]) => Number.isInteger(check.reports?.shards))
    .map(([n, check]) => [`shards_${n}`, JSON.stringify(Array.from({ length: check.reports.shards }, (_, i) => i + 1))])
  writeOutputs({
    selection: line,
    max_attempts: String(policy.maxAttempts ?? 2),
    ...Object.fromEntries(shards),
    ...Object.fromEntries(Object.keys(policy.checks).map((n) => [`run_${n}`, String(record.expected.includes(n))])),
  })
  console.log(line)
  return 0
}

/**
 * Jobs in this run that the policy does not account for. `jobs` is the API's job list;
 * matrix jobs appear as "name (1)". Jobs must not set `name:`, or must set it to their id.
 */
export function inventoryProblems(policy, jobs) {
  const known = new Set([...Object.keys(policy.checks), ...FIXED_JOBS, ...(policy.afterGate ?? [])])
  const unknown = new Set()
  for (const job of jobs) {
    const name = String(job.name ?? "").replace(/ \(.*\)$/, "")
    if (!known.has(name)) unknown.add(name)
  }
  return [...unknown].map((name) => `job "${name}" runs in this workflow but is not a policy check, select, gate or afterGate job; add it to the policy and to the gate's needs`)
}

/** Pure verification logic, exported for tests. Returns { passed, problems, rows }. */
export function verify(policy, policySha256, needs, { candidate, attempt }) {
  const names = validatePolicy(policy)
  const problems = []
  const rows = []
  const maxAttempts = policy.maxAttempts ?? 2
  if (needs.select?.result !== "success") {
    return { passed: false, problems: [`select did not succeed (result: ${needs.select?.result ?? "missing"})`], rows }
  }
  let selection
  try {
    selection = JSON.parse(needs.select.outputs?.selection ?? "")
  } catch {
    return { passed: false, problems: ["select succeeded but produced no valid selection record"], rows }
  }
  if (selection.schemaVersion !== SCHEMA_VERSION) problems.push("selection schemaVersion mismatch")
  if (selection.policySha256 !== policySha256) problems.push("selection was made under a different policy revision")
  if (selection.candidate !== candidate) problems.push(`selection is for ${selection.candidate}, not ${candidate}`)
  if (!MODES.has(selection.mode)) problems.push(`unknown selection mode "${selection.mode}"`)
  const expected = Array.isArray(selection.expected) ? selection.expected : []
  const omitted = selection.omitted && typeof selection.omitted === "object" ? selection.omitted : {}
  if (selection.mode === "full" && expected.length !== names.length) problems.push("full selection does not expect every check")
  if (selection.mode === "noop" && expected.length) problems.push("no-op selection still expects checks")
  if (selection.mode !== "noop" && expected.length === 0) problems.push("selection expects no checks but is not a no-op")
  for (const name of names) {
    const inExpected = expected.includes(name)
    if (inExpected === Object.hasOwn(omitted, name)) problems.push(`check "${name}" must be either expected or omitted with a reason`)
  }
  for (const name of [...expected, ...Object.keys(omitted)]) {
    if (!names.includes(name)) problems.push(`selection names "${name}", which the policy does not declare`)
  }
  for (const name of names) {
    const result = needs[name]?.result ?? "missing"
    const wanted = expected.includes(name)
    let ok
    if (wanted) {
      ok = result === "success"
      if (!ok) {
        let why = result === "skipped" ? "expected but skipped" : `expected, result ${result}`
        if (attempt > maxAttempts) why += `; attempt ${attempt} exceeds the cap of ${maxAttempts}, verification incomplete`
        problems.push(`${name}: ${why}`)
      }
    } else {
      ok = result === "skipped" || result === "success"
      if (!ok) problems.push(`${name}: omitted (${omitted[name]}) but ran with result ${result}`)
    }
    rows.push({ name, wanted, result, note: wanted ? "" : (omitted[name] ?? "") })
  }
  for (const [name, need] of Object.entries(needs)) {
    if (name === "select" || names.includes(name)) continue
    if (need.result !== "success") problems.push(`${name}: not in policy, result ${need.result}`)
  }
  return { passed: problems.length === 0, problems, rows, selection }
}

function runVerify(args) {
  if (!args.policy || !args.candidate) fail("verify needs --policy and --candidate", 2)
  const policy = readJson(args.policy, "policy")
  const raw = args.needs ? readFileSync(args.needs, "utf8") : process.env.NEEDS_JSON
  if (!raw) fail("verify needs --needs <file> or NEEDS_JSON", 2)
  let needs
  try {
    needs = JSON.parse(raw)
  } catch {
    fail("needs is not valid JSON", 2)
  }
  const attempt = Number(args.attempt ?? process.env.GITHUB_RUN_ATTEMPT ?? 1)
  const verdict = verify(policy, policyDigest(args.policy), needs, { candidate: args.candidate, attempt })
  let inventory = "job inventory not checked (no --jobs)"
  if (args.jobs) {
    const jobs = readJson(args.jobs, "job list")
    if (!Array.isArray(jobs) || jobs.length === 0) fail("job list must be a non-empty JSON array", 2)
    const extra = inventoryProblems(policy, jobs)
    verdict.problems.push(...extra)
    verdict.passed = verdict.passed && extra.length === 0
    inventory = `job inventory checked: ${jobs.length} job(s)`
  }
  const mode = verdict.selection?.mode ?? "unknown"
  const table = verdict.rows.map((r) => `| ${r.name} | ${r.wanted ? "expected" : "omitted"} | ${r.result} | ${r.note} |`)
  writeSummary(
    [
      `### Gate: ${verdict.passed ? "passed" : "FAILED"} (${mode})`,
      inventory,
      verdict.selection ? `Candidate \`${args.candidate}\`, policy \`${verdict.selection.policySha256.slice(0, 12)}\`: ${verdict.selection.rationale}` : "",
      "",
      "| Check | Selection | Result | Reason omitted |",
      "|---|---|---|---|",
      ...table,
      "",
      ...verdict.problems.map((p) => `- ${p}`),
    ].join("\n"),
  )
  if (args.out) {
    const result = { schemaVersion: SCHEMA_VERSION, passed: verdict.passed, candidate: args.candidate, mode, policySha256: verdict.selection?.policySha256 ?? null, runId: process.env.GITHUB_RUN_ID ?? null, attempt, problems: verdict.problems }
    writeFileSync(args.out, `${JSON.stringify(result, null, 2)}\n`)
  }
  for (const problem of verdict.problems) console.error(`gate: ${problem}`)
  console.log(verdict.passed ? `gate passed (${mode})` : "gate failed")
  return verdict.passed ? 0 : 1
}

const OPTIONS = ["policy", "event", "candidate", "base", "changed-files", "needs", "attempt", "jobs", "out"]
if (isEntry(import.meta.url)) {
  main((argv) => {
    const args = parseArgs(argv, OPTIONS)
    const command = args._[0]
    if (command === "select") return runSelect(args)
    if (command === "verify") return runVerify(args)
    fail("usage: gate.mjs select|verify --policy <file> ...", 2)
  })
}
