import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"
import { evaluate, parseJUnit, quarantineFor } from "../../templates/ci/reports.mjs"
import { junit, node, TEMPLATES, tempDir, write } from "./helpers.mjs"

const policy = JSON.parse(readFileSync(join(TEMPLATES, "ci-policy.example.json"), "utf8"))
const TODAY = "2026-10-30"
const entry = (over = {}) => ({ test: "s::flaky", owner: "@o", issue: "https://x/1", reason: "timer race", riskApproval: "@m", entered: "2026-10-20", review: "2026-11-03", ...over })
const files = ["unit-1.xml", "unit-2.xml"]

test("parses JUnit cases and rejects non-JUnit text", () => {
  assert.deepEqual(parseJUnit(junit([["s::a", "passed"], ["s::b", "failed"], ["s::c", "skipped"]])).map((c) => c.status), ["passed", "failed", "skipped"])
  assert.equal(parseJUnit("Error: worker crashed"), null)
  assert.deepEqual(parseJUnit('<testsuite><testcase classname="a &amp; b" name="x"/></testsuite>'), [{ id: "a & b::x", status: "passed" }])
})

test("Q15 a shard that died before writing its report is named, not dropped", () => {
  const r = evaluate({ files, contents: { "unit-1.xml": junit([["s::a", "passed"]]) }, allowed: new Map() })
  assert.equal(r.passed, false)
  assert.match(r.problems[0], /unit-2.xml: report missing/)
})

test("Q15 corrupt reports and zero discovered tests fail", () => {
  assert.equal(evaluate({ files: ["unit-1.xml"], contents: { "unit-1.xml": "<html>502</html>" }, allowed: new Map() }).passed, false)
  const empty = evaluate({ files: ["unit-1.xml"], contents: { "unit-1.xml": "<testsuites></testsuites>" }, allowed: new Map() })
  assert.match(empty.problems[0], /zero tests discovered/)
})

test("Q17 a failing command with no reported test failure is infrastructure, not a pass", () => {
  const r = evaluate({ files: ["unit-1.xml"], contents: { "unit-1.xml": junit([["s::a", "passed"]]) }, allowed: new Map(), exitCode: 1 })
  assert.match(r.problems[0], /setup or infrastructure/)
})

test("only a valid quarantine entry makes one failing assertion nonblocking", () => {
  const { allowed, problems } = quarantineFor({ entries: [entry()] }, policy, "unit", TODAY)
  assert.deepEqual(problems, [])
  const contents = { "unit-1.xml": junit([["s::flaky", "failed"], ["s::ok", "passed"]]) }
  const r = evaluate({ files: ["unit-1.xml"], contents, allowed, exitCode: 1 })
  assert.equal(r.passed, true)
  assert.deepEqual(r.quarantined, ["s::flaky"])
  const other = evaluate({ files: ["unit-1.xml"], contents: { "unit-1.xml": junit([["s::other", "failed"]]) }, allowed, exitCode: 1 })
  assert.equal(other.passed, false)
})

test("Q16 expired and critical quarantine entries escalate instead of suppressing", () => {
  const expired = quarantineFor({ entries: [entry({ review: "2026-10-29" })] }, policy, "unit", TODAY)
  assert.equal(expired.allowed.size, 0)
  assert.match(expired.problems[0], /has passed; restore the test to blocking or renew it through review/)
  const critical = quarantineFor({ entries: [entry({ test: "test/auth.test.ts::rejects expired token" })] }, policy, "unit", TODAY)
  assert.match(critical.problems[0], /critical pattern/)
})

test("Q17 incomplete quarantine metadata is a policy failure", () => {
  const { problems } = quarantineFor({ entries: [entry({ owner: "", riskApproval: undefined })] }, policy, "unit", TODAY)
  assert.match(problems[0], /missing owner, riskApproval/)
})

test("audit 4: a missing quarantine file means nothing is quarantined", () => {
  const dir = tempDir()
  write(dir, "ci-policy.json", JSON.stringify(policy))
  write(dir, "reports/unit-1.xml", junit([["s::a", "passed"]]))
  write(dir, "reports/unit-2.xml", junit([["s::b", "passed"]]))
  const ok = node(join(TEMPLATES, "reports.mjs"), ["--policy", "ci-policy.json", "--check", "unit", "--dir", "reports", "--quarantine", "ci/quarantine.json"], { cwd: dir })
  assert.equal(ok.code, 0, ok.stderr)
  assert.match(ok.stdout, /nothing is quarantined/)
  write(dir, "ci/quarantine.json", "{ not json")
  assert.equal(node(join(TEMPLATES, "reports.mjs"), ["--policy", "ci-policy.json", "--check", "unit", "--dir", "reports", "--quarantine", "ci/quarantine.json"], { cwd: dir }).code, 2)
})

test("audit 15: a report that names the file makes the id unique per file", () => {
  const xml = (file) => `<testsuites><testcase name="x works" classname="test" file="${file}"/></testsuites>`
  assert.deepEqual(parseJUnit(xml("/repo/test/a.test.mjs"), { root: "/repo" }), [{ id: "test/a.test.mjs::test::x works", status: "passed" }])
  assert.notEqual(parseJUnit(xml("/repo/test/a.test.mjs"), { root: "/repo" })[0].id, parseJUnit(xml("/repo/test/b.test.mjs"), { root: "/repo" })[0].id)
  assert.equal(parseJUnit(xml("/other/a.test.mjs"), { root: "/repo" })[0].id, "/other/a.test.mjs::test::x works")
})

test("CLI: expired quarantine fails the merge step and leaves the test and entry in place", () => {
  const dir = tempDir()
  write(dir, "ci-policy.json", JSON.stringify(policy))
  const quarantinePath = write(dir, "quarantine.json", JSON.stringify({ entries: [entry({ review: "2026-10-01", entered: "2026-09-20" })] }))
  write(dir, "reports/unit-1.xml", junit([["s::flaky", "failed"]]))
  write(dir, "reports/unit-2.xml", junit([["s::b", "passed"]]))
  const before = readFileSync(quarantinePath, "utf8")
  const r = node(join(TEMPLATES, "reports.mjs"), ["--policy", "ci-policy.json", "--check", "unit", "--dir", "reports", "--quarantine", "quarantine.json", "--today", TODAY], { cwd: dir })
  assert.equal(r.code, 1)
  assert.match(r.stderr, /has passed/)
  assert.match(r.stderr, /s::flaky failed/)
  assert.equal(readFileSync(quarantinePath, "utf8"), before)
})
