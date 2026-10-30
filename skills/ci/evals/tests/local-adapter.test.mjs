// Runs the generated local commands for the node:test adapter on a throwaway project:
// sharded runs with JUnit reports, per-shard and merged report checks, red -> green.
// Also runs the pinned workflow validators on the example workflow when installed.
import assert from "node:assert/strict"
import { spawnSync } from "node:child_process"
import { mkdirSync, readFileSync, rmSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"
import { parseJUnit } from "../../templates/ci/reports.mjs"
import { node, SKILL, TEMPLATES, tempDir, write } from "./helpers.mjs"

const POLICY = { schemaVersion: 1, checks: { unit: { reports: { shards: 2, pattern: "unit-{shard}.xml" } } } }

function project(broken = false) {
  const dir = tempDir("ci-node-project-")
  write(dir, "ci/ci-policy.json", JSON.stringify(POLICY))
  for (const name of ["a", "b", "c", "d"]) {
    const ok = !(broken && name === "c")
    write(dir, `test/${name}.test.mjs`, `import { test } from "node:test"\nimport assert from "node:assert"\ntest("${name} works", () => assert.equal(${ok ? 1 : 2}, 1))\n`)
  }
  return dir
}

function shard(dir, i) {
  // node:test does not create the reporter destination's directory.
  mkdirSync(join(dir, "reports"), { recursive: true })
  const result = spawnSync(process.execPath, ["--test", `--test-shard=${i}/2`, "--test-reporter=junit", `--test-reporter-destination=reports/unit-${i}.xml`, "test/"], { cwd: dir, encoding: "utf8" })
  return result.status
}

const check = (dir, extra) => node(join(TEMPLATES, "reports.mjs"), ["--policy", "ci/ci-policy.json", "--check", "unit", "--dir", "reports", ...extra], { cwd: dir })

test("node:test adapter: green shards pass per shard and merged", () => {
  const dir = project()
  for (const i of [1, 2]) {
    const code = shard(dir, i)
    assert.equal(code, 0)
    assert.equal(check(dir, ["--shard", String(i), "--exit-code", String(code)]).code, 0)
  }
  const merged = check(dir, [])
  assert.equal(merged.code, 0, merged.stderr)
  assert.match(merged.stdout, /4 tests in 2 report/)
})

test("node:test adapter: a broken test is red; a reviewed quarantine makes only it nonblocking", () => {
  const dir = project(true)
  const codes = [1, 2].map((i) => shard(dir, i))
  assert.ok(codes.some((c) => c !== 0))
  assert.equal(check(dir, []).code, 1)
  const failing = [1, 2].flatMap((i) => parseJUnit(readFileSync(join(dir, `reports/unit-${i}.xml`), "utf8"), { root: dir })).find((c) => c.status === "failed")
  // Node 26 names the file in the report; Node 20 does not.
  assert.match(failing.id, /^(test\/c\.test\.mjs::)?test::c works$/)
  write(dir, "ci/quarantine.json", JSON.stringify({ entries: [{ test: failing.id, owner: "@o", issue: "https://x/1", reason: "r", riskApproval: "@m", entered: "2026-10-20", review: "2099-01-01" }] }))
  const allowed = check(dir, ["--quarantine", "ci/quarantine.json"])
  assert.equal(allowed.code, 0, allowed.stderr)
  assert.match(allowed.stdout, /quarantined failure \(nonblocking\)/)
  write(dir, "ci/quarantine.json", JSON.stringify({ entries: [{ test: failing.id, owner: "@o", issue: "https://x/1", reason: "r", riskApproval: "@m", entered: "2026-10-20", review: "2099-01-01" }, { test: "gone::test", owner: "@o", issue: "https://x/2", reason: "r", riskApproval: "@m", entered: "2026-10-20", review: "2099-01-01" }] }))
  assert.match(check(dir, ["--quarantine", "ci/quarantine.json"]).stdout, /matches no reported test.*gone::test/)
})

test("node:test adapter: a lost shard report fails the merge", () => {
  const dir = project()
  for (const i of [1, 2]) shard(dir, i)
  rmSync(join(dir, "reports/unit-2.xml"))
  const merged = check(dir, [])
  assert.equal(merged.code, 1)
  assert.match(merged.stderr, /unit-2.xml: report missing/)
})

const workflow = join(SKILL, "evals", "fixtures", "workflows", "ci.yml")
const has = (cmd) => spawnSync("sh", ["-c", `command -v ${cmd}`]).status === 0

test("example workflow passes actionlint", { skip: has("actionlint") ? false : "actionlint not installed: workflow NOT validated" }, () => {
  const r = spawnSync("actionlint", [workflow], { encoding: "utf8" })
  assert.equal(r.status, 0, r.stdout + r.stderr)
})

test("example workflow passes zizmor", { skip: has("zizmor") || has("uvx") ? false : "zizmor not installed: workflow NOT validated" }, () => {
  const [cmd, ...args] = has("zizmor") ? ["zizmor"] : ["uvx", "zizmor@1.31.1"]
  const r = spawnSync(cmd, [...args, "--offline", workflow], { encoding: "utf8" })
  assert.equal(r.status, 0, r.stdout + r.stderr)
})
