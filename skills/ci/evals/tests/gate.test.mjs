import assert from "node:assert/strict"
import { mkdirSync, readFileSync, writeFileSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"
import { inventoryProblems, protectedPathsFor, select, verify } from "../../templates/ci/gate.mjs"
import { commitAll, git, initRepo, node, TEMPLATES, tempDir, write } from "./helpers.mjs"

const policy = JSON.parse(readFileSync(join(TEMPLATES, "ci-policy.example.json"), "utf8"))
const ALL = Object.keys(policy.checks)
const pr = (files, extra = {}) => select(policy, { event: "pull_request", files, ...extra })

test("Q10 a docs-only change is an affirmative no-op with its rationale", () => {
  const s = pr(["docs/guide.md", "LICENSE"])
  assert.equal(s.mode, "noop")
  assert.deepEqual(s.expected, [])
  assert.match(s.rationale, /not read by the build/)
})

test("Q10 Markdown outside the no-op list is not assumed irrelevant", () => {
  assert.equal(pr(["README.md"]).mode, "full")
  assert.equal(pr(["src/content/post.md"]).mode, "affected")
})

test("affected selection keeps checks that always run and follows dependants", () => {
  const s = pr(["e2e/login.spec.ts"])
  assert.equal(s.mode, "affected")
  assert.deepEqual(s.expected, ["static", "e2e"])
  assert.match(s.omitted.unit, /no changed file matches/)
  assert.match(s.omitted["unit-report"], /follows unit/)
  assert.deepEqual(pr(["src/a.ts"]).expected, ALL)
})

test("Q11 global inputs, unclaimed paths and a missing base run the full set", () => {
  assert.equal(pr(["package-lock.json"]).mode, "full")
  assert.equal(pr(["ci/gate.mjs"]).mode, "full")
  assert.equal(pr(["scripts/deploy.sh"]).mode, "full")
  assert.equal(pr(["src/a.ts"], { baseError: "shallow" }).mode, "full")
  assert.equal(pr([]).mode, "full")
})

test("Q12 push, merge group, manual dispatch and schedule always run the full set", () => {
  for (const event of ["push", "merge_group", "workflow_dispatch", "schedule"]) {
    const s = select(policy, { event, files: ["docs/x.md"] })
    assert.equal(s.mode, "full", event)
    assert.deepEqual(s.expected, ALL)
  }
})

test("audit 1: a PR that edits the policy it is judged by still runs the full set", () => {
  const edited = structuredClone(policy)
  edited.fullOn.paths = edited.fullOn.paths.filter((p) => p !== "ci/**")
  edited.noop.paths.push("**")
  const protectedPaths = protectedPathsFor("ci/ci-policy.json", "ci")
  const s = select(edited, { event: "pull_request", files: ["ci/ci-policy.json", "src/a.ts"], protectedPaths })
  assert.equal(s.mode, "full")
  assert.match(s.rationale, /CI configuration/)
  assert.equal(select(edited, { event: "pull_request", files: [".github/workflows/ci.yml"] }).mode, "full")
  assert.equal(select(edited, { event: "pull_request", files: ["ci/gate.mjs"], protectedPaths }).mode, "full")
})

test("protected paths cover .github, the policy, its folder and the scripts' folder", () => {
  assert.deepEqual(protectedPathsFor("ci/ci-policy.json", "tools/ci"), [".github/**", "ci/ci-policy.json", "ci/**", "tools/ci/**"])
  assert.deepEqual(protectedPathsFor("ci-policy.json", "/elsewhere/outside"), [".github/**", "ci-policy.json"])
})

test("audit 12: a job the policy does not account for fails the inventory", () => {
  const jobs = ["select", "static", "unit (1)", "unit (2)", "unit-report", "e2e", "gate", "build", "deploy"].map((name) => ({ name }))
  assert.deepEqual(inventoryProblems(policy, jobs), [])
  const problems = inventoryProblems(policy, [...jobs, { name: "lint" }, { name: "lint" }])
  assert.equal(problems.length, 1)
  assert.match(problems[0], /job "lint" runs in this workflow but is not a policy check/)
})

test("an invalid policy cannot produce a selection", () => {
  assert.throws(() => select({ schemaVersion: 1, checks: {} }, { event: "pull_request", files: ["a"] }), /no checks/)
  assert.throws(() => select({ schemaVersion: 1, checks: { a: { paths: [] } } }, { event: "pull_request", files: ["a"] }), /empty/)
  assert.throws(() => select({ schemaVersion: 1, checks: { a: { follows: "b" } } }, { event: "pull_request", files: ["a"] }), /follows/)
  assert.throws(() => select({ schemaVersion: 1, checks: { a: {} }, noop: { paths: ["docs/**"] } }, { event: "pull_request", files: ["a"] }), /rationale/)
  assert.throws(() => select({ schemaVersion: 1, checks: { a: {} }, afterGate: ["a"] }, { event: "pull_request", files: ["a"] }), /afterGate/)
})

// --- verify ---------------------------------------------------------------
const SHA = "a".repeat(40)
function needsFor(selection, results, selectResult = "success") {
  const needs = { select: { result: selectResult, outputs: selection === undefined ? {} : { selection: JSON.stringify(selection) } } }
  for (const [name, result] of Object.entries(results)) needs[name] = { result, outputs: {} }
  return needs
}
const record = (s) => ({ schemaVersion: 1, policySha256: "p", candidate: SHA, ...s })
const check = (needs, attempt = 1) => verify(policy, "p", needs, { candidate: SHA, attempt })
const fullOk = Object.fromEntries(ALL.map((n) => [n, "success"]))

test("all expected checks succeeded: pass", () => {
  assert.equal(check(needsFor(record(pr(["src/a.ts"])), fullOk)).passed, true)
})

test("Q09 the audit's false-green rows now fail: required E2E skipped, everything skipped", () => {
  const s = record(pr(["src/a.ts"]))
  const e2eSkipped = check(needsFor(s, { ...fullOk, e2e: "skipped" }))
  assert.equal(e2eSkipped.passed, false)
  assert.ok(e2eSkipped.problems.some((p) => /e2e: expected but skipped/.test(p)))
  const allSkipped = Object.fromEntries(ALL.map((n) => [n, "skipped"]))
  assert.equal(check(needsFor(s, allSkipped)).passed, false)
  assert.equal(check(needsFor(s, { ...fullOk, unit: "failure" })).passed, false)
  assert.equal(check(needsFor(s, { ...fullOk, unit: "cancelled" })).passed, false)
})

test("Q09 classifier success without a valid selection fails", () => {
  const allSkipped = Object.fromEntries(ALL.map((n) => [n, "skipped"]))
  assert.equal(check(needsFor(undefined, allSkipped)).passed, false)
  const needs = needsFor(undefined, allSkipped)
  needs.select.outputs.selection = "not json"
  assert.match(check(needs).problems[0], /no valid selection record/)
  assert.equal(check(needsFor(record(pr(["src/a.ts"])), fullOk, "failure")).passed, false)
})

test("Q09 attempt cap exhaustion reports incomplete verification", () => {
  const v = check(needsFor(record(pr(["src/a.ts"])), Object.fromEntries(ALL.map((n) => [n, "skipped"]))), 3)
  assert.equal(v.passed, false)
  assert.ok(v.problems.some((p) => /exceeds the cap of 2, verification incomplete/.test(p)))
})

test("Q10 a recorded no-op passes with every check skipped", () => {
  const v = check(needsFor(record(pr(["docs/a.md"])), Object.fromEntries(ALL.map((n) => [n, "skipped"]))))
  assert.equal(v.passed, true)
  assert.equal(v.selection.mode, "noop")
})

test("selection identity: other candidate, other policy revision, tampered sets", () => {
  const s = pr(["src/a.ts"])
  assert.equal(check(needsFor({ ...record(s), candidate: "b".repeat(40) }, fullOk)).passed, false)
  assert.equal(check(needsFor({ ...record(s), policySha256: "q" }, fullOk)).passed, false)
  const tampered = { ...record(pr(["src/a.ts"])), mode: "full", expected: ["static"], omitted: {} }
  assert.equal(check(needsFor(tampered, fullOk)).passed, false)
  const emptyAffected = { ...record(s), expected: [], omitted: Object.fromEntries(ALL.map((n) => [n, "x"])) }
  assert.equal(check(needsFor(emptyAffected, fullOk)).passed, false)
})

test("an omitted check that ran and failed, or an unlisted job that failed, fails the gate", () => {
  const s = record(pr(["e2e/a.spec.ts"]))
  assert.equal(check(needsFor(s, { ...fullOk, unit: "failure" })).passed, false)
  assert.equal(check(needsFor(s, { static: "success", e2e: "success", unit: "skipped", "unit-report": "skipped", lint: "failure" })).passed, false)
})

test("CLI: select from real git history, write outputs, verify from NEEDS_JSON", () => {
  const repo = initRepo({ "src/a.ts": "1", "docs/a.md": "1", "e2e/a.spec.ts": "1" })
  write(repo, "ci/ci-policy.json", readFileSync(join(TEMPLATES, "ci-policy.example.json"), "utf8"))
  const base = commitAll(repo, "policy")
  git(repo, "mv", "docs/a.md", "docs/b.md")
  const docsOnly = commitAll(repo, "rename doc")
  const out = join(tempDir(), "out")
  writeFileSync(out, "")
  const gate = join(TEMPLATES, "gate.mjs")
  const run = (candidate, from = base) =>
    node(gate, ["select", "--policy", "ci/ci-policy.json", "--event", "pull_request", "--candidate", candidate, "--base", from], { cwd: repo, env: { ...process.env, GITHUB_OUTPUT: out } })
  const noop = run(docsOnly)
  assert.equal(noop.code, 0, noop.stderr)
  const selection = JSON.parse(noop.stdout)
  assert.equal(selection.mode, "noop")
  const outputs = readFileSync(out, "utf8")
  assert.match(outputs, /run_unit=false/)
  assert.match(outputs, /max_attempts=2/)
  assert.match(outputs, /shards_unit=\[1,2\]/)
  write(repo, "ci/ci-policy.json", JSON.stringify({ ...JSON.parse(readFileSync(join(repo, "ci/ci-policy.json"), "utf8")), noop: { paths: ["**"], rationale: "x" } }))
  write(repo, "docs/b.md", "2")
  const selfEdit = commitAll(repo, "policy edits itself")
  assert.equal(JSON.parse(run(selfEdit, docsOnly).stdout).mode, "full", "editing the policy runs everything")
  git(repo, "checkout", "-q", docsOnly, "--", "ci/ci-policy.json")
  commitAll(repo, "restore policy")
  mkdirSync(join(repo, "lib"))
  git(repo, "mv", "src/a.ts", "lib/a.ts")
  const moved = commitAll(repo, "move out of src")
  assert.equal(JSON.parse(run(moved, docsOnly).stdout).mode, "full", "a rename to an unclaimed path runs everything")
  assert.equal(JSON.parse(run(moved, "f".repeat(40)).stdout).mode, "full", "an unknown base runs everything")
  const needs = { select: { result: "success", outputs: { selection: noop.stdout.trim() } } }
  for (const name of ALL) needs[name] = { result: "skipped" }
  writeFileSync(join(repo, "jobs.json"), JSON.stringify(["select", "gate"].map((name) => ({ name }))))
  const verdict = node(gate, ["verify", "--policy", "ci/ci-policy.json", "--candidate", docsOnly, "--jobs", "jobs.json", "--out", "gate.json"], { cwd: repo, env: { ...process.env, NEEDS_JSON: JSON.stringify(needs) } })
  assert.equal(verdict.code, 0, verdict.stderr)
  writeFileSync(join(repo, "jobs.json"), JSON.stringify(["select", "gate", "lint"].map((name) => ({ name }))))
  const extra = node(gate, ["verify", "--policy", "ci/ci-policy.json", "--candidate", docsOnly, "--jobs", "jobs.json"], { cwd: repo, env: { ...process.env, NEEDS_JSON: JSON.stringify(needs) } })
  assert.equal(extra.code, 1)
  assert.match(extra.stderr, /job "lint"/)
  assert.equal(JSON.parse(readFileSync(join(repo, "gate.json"), "utf8")).passed, true)
  const bad = node(gate, ["verify", "--policy", "missing.json", "--candidate", docsOnly], { cwd: repo, env: { ...process.env, NEEDS_JSON: "{}" } })
  assert.equal(bad.code, 2)
})
