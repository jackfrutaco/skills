#!/usr/bin/env node
// Check that a check's test reports exist, discovered tests, and failed only where a
// reviewed quarantine entry allows it.
//
//   node reports.mjs --policy ci-policy.json --check unit --dir reports
//       [--shard N --exit-code CODE] [--quarantine quarantine.json] [--today YYYY-MM-DD]
//
// Without --shard it evaluates every report the policy expects (the merge step), so a
// shard that died before writing its report is named, not dropped. With --shard it
// evaluates that shard's report against the test command's exit code: a failing command
// with no reported test failure is a setup or infrastructure failure, never a pass.
// Only test assertions listed in a valid, unexpired, non-critical quarantine entry are
// nonblocking. Missing, corrupt or empty reports and bad quarantine entries fail.
// A missing --quarantine file means nothing is quarantined; an invalid one fails.
// Test ids are `classname::name`. When a report names the test's file (node:test does),
// the id is `file::classname::name`, with the file relative to the working directory.
// Exit codes: 0 pass, 1 fail, 2 invalid input or policy.
import { existsSync, readFileSync, realpathSync } from "node:fs"
import { isAbsolute, join, relative, sep } from "node:path"
import { fail, isEntry, main, matchesAny, parseArgs, readJson, validatePolicy, writeSummary } from "./lib.mjs"

const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" }
const decode = (text) => text.replace(/&(amp|lt|gt|quot|apos);/g, (_, e) => ENTITIES[e])
const REQUIRED = ["test", "owner", "issue", "reason", "riskApproval", "entered", "review"]

function attributes(text) {
  const out = {}
  for (const [, key, value] of text.matchAll(/([\w:-]+)\s*=\s*"([^"]*)"/g)) out[key] = decode(value)
  return out
}

function fileLabel(file, root) {
  if (!file || !isAbsolute(file)) return file
  const rel = relative(root, file)
  return rel.startsWith("..") ? file : rel.split(sep).join("/")
}

/** Parse JUnit XML into test cases. Returns null when the file is not a JUnit report. */
export function parseJUnit(xml, { root = process.cwd() } = {}) {
  let realRoot = root
  try {
    realRoot = realpathSync(root)
  } catch {}
  if (!/<testsuites?\b/.test(xml)) return null
  const cases = []
  for (const match of xml.matchAll(/<testcase\b([^>]*?)(?:\/>|>([\s\S]*?)<\/testcase>)/g)) {
    const attrs = attributes(match[1])
    const body = match[2] ?? ""
    const local = attrs.classname ? `${attrs.classname}::${attrs.name}` : attrs.name
    const id = attrs.file ? `${fileLabel(attrs.file, realRoot)}::${local}` : local
    const status = /<(failure|error)\b/.test(body) ? "failed" : /<skipped\b/.test(body) ? "skipped" : "passed"
    cases.push({ id, status })
  }
  return cases
}

export function expectedReports(policy, check) {
  const spec = policy.checks[check]?.reports
  if (!spec) fail(`policy has no reports entry for check "${check}"`, 2)
  if (spec.files) return spec.files
  if (Number.isInteger(spec.shards) && spec.shards > 0 && spec.pattern?.includes("{shard}")) {
    return Array.from({ length: spec.shards }, (_, i) => spec.pattern.replace("{shard}", String(i + 1)))
  }
  fail(`checks.${check}.reports needs "files" or positive "shards" with a {shard} pattern`, 2)
}

/** Validate quarantine entries for one check. Returns { allowed: Map(id → entry), problems }. */
export function quarantineFor(quarantine, policy, check, today) {
  const allowed = new Map()
  const problems = []
  for (const [i, entry] of (quarantine?.entries ?? []).entries()) {
    if (entry.check && entry.check !== check) continue
    const label = entry.test ?? `entry ${i + 1}`
    const missing = REQUIRED.filter((key) => !entry[key])
    if (missing.length) {
      problems.push(`quarantine ${label}: missing ${missing.join(", ")}`)
      continue
    }
    if (matchesAny(entry.test, policy.critical)) {
      problems.push(`quarantine ${label}: matches a critical pattern and cannot be made nonblocking`)
      continue
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.review) || entry.review < entry.entered) {
      problems.push(`quarantine ${label}: review date must be YYYY-MM-DD on or after entered`)
      continue
    }
    if (entry.review < today) {
      problems.push(`quarantine ${label}: review date ${entry.review} has passed; restore the test to blocking or renew it through review (${entry.issue})`)
      continue
    }
    allowed.set(entry.test, entry)
  }
  return { allowed, problems }
}

/** Pure evaluation of report files already read from disk. */
export function evaluate({ files, contents, allowEmpty, allowed, exitCode }) {
  const problems = []
  const shards = []
  const quarantined = []
  const seen = new Set()
  let total = 0
  for (const file of files) {
    const xml = contents[file]
    if (xml === undefined) {
      problems.push(`${file}: report missing (the run failed before writing it, or was never started)`)
      shards.push({ file, state: "missing" })
      continue
    }
    const cases = parseJUnit(xml)
    if (cases === null) {
      problems.push(`${file}: not a JUnit report (corrupt or truncated)`)
      shards.push({ file, state: "corrupt" })
      continue
    }
    const failed = cases.filter((c) => c.status === "failed")
    total += cases.length
    for (const test of cases) seen.add(test.id)
    if (cases.length === 0 && !allowEmpty) problems.push(`${file}: zero tests discovered`)
    for (const test of failed) {
      if (allowed.has(test.id)) quarantined.push(test.id)
      else problems.push(`${file}: ${test.id} failed`)
    }
    shards.push({ file, state: "read", tests: cases.length, failed: failed.length })
  }
  if (exitCode !== undefined && exitCode !== 0) {
    const reportedFailures = shards.reduce((n, s) => n + (s.failed ?? 0), 0)
    if (reportedFailures === 0) problems.push(`test command exited ${exitCode} without a reported test failure: setup or infrastructure failure`)
  }
  return { passed: problems.length === 0, problems, shards, quarantined, total, seen }
}

function run(argv) {
  const args = parseArgs(argv, ["policy", "check", "dir", "shard", "exit-code", "quarantine", "today"])
  if (!args.policy || !args.check || !args.dir) fail("needs --policy, --check and --dir", 2)
  const policy = readJson(args.policy, "policy")
  validatePolicy(policy)
  let files = expectedReports(policy, args.check)
  if (args.shard !== undefined) {
    const index = Number(args.shard) - 1
    if (!files[index]) fail(`--shard ${args.shard} is outside the policy's ${files.length} report(s)`, 2)
    files = [files[index]]
  }
  const today = args.today ?? new Date().toISOString().slice(0, 10)
  let quarantine = null
  if (args.quarantine && existsSync(args.quarantine)) quarantine = readJson(args.quarantine, "quarantine")
  else if (args.quarantine) console.log(`no quarantine file at ${args.quarantine}: nothing is quarantined`)
  if (quarantine && !Array.isArray(quarantine.entries)) fail(`${args.quarantine} needs an "entries" list`, 2)
  const { allowed, problems: policyProblems } = quarantineFor(quarantine, policy, args.check, today)
  const contents = {}
  for (const file of files) {
    const path = join(args.dir, file)
    if (existsSync(path)) contents[file] = readFileSync(path, "utf8")
  }
  const exitCode = args["exit-code"] === undefined ? undefined : Number(args["exit-code"])
  const result = evaluate({ files, contents, allowEmpty: policy.checks[args.check].reports.allowEmpty === true, allowed, exitCode })
  const problems = [...policyProblems, ...result.problems]
  const rows = result.shards.map((s) => `| ${s.file} | ${s.state} | ${s.tests ?? "-"} | ${s.failed ?? "-"} |`)
  writeSummary(
    [
      `### ${args.check} reports: ${problems.length ? "FAILED" : "passed"} (${result.total} tests)`,
      "| Report | State | Tests | Failed |",
      "|---|---|---|---|",
      ...rows,
      ...result.quarantined.map((id) => `- quarantined failure (nonblocking): \`${id}\` ${allowed.get(id).issue}`),
      ...problems.map((p) => `- ${p}`),
    ].join("\n"),
  )
  const obsolete = args.shard === undefined ? [...allowed.keys()].filter((id) => !result.seen.has(id)) : []
  for (const id of obsolete) console.log(`quarantine entry matches no reported test (remove it if the test is gone): ${id}`)
  for (const id of result.quarantined) console.log(`quarantined failure (nonblocking): ${id}`)
  for (const problem of problems) console.error(`reports: ${problem}`)
  console.log(`${args.check}: ${result.total} tests in ${files.length} report(s); ${problems.length ? "failed" : "passed"}`)
  return problems.length ? 1 : 0
}

if (isEntry(import.meta.url)) main(run)
