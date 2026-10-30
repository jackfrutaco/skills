import assert from "node:assert/strict"
import { readFileSync, writeFileSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"
import { denials } from "../../templates/ci/release.mjs"
import { commitAll, git, initRepo, node, TEMPLATES, write } from "./helpers.mjs"

const release = join(TEMPLATES, "release.mjs")

function setup() {
  const repo = initRepo({ "src/a.ts": "1" })
  const older = git(repo, "rev-parse", "HEAD")
  write(repo, "src/a.ts", "2")
  const newer = commitAll(repo, "newer")
  write(repo, "dist/index.js", "export default {}")
  return { repo, older, newer }
}
const gateFile = (repo, candidate, passed = true) => {
  writeFileSync(join(repo, "gate.json"), JSON.stringify({ schemaVersion: 1, passed, candidate, mode: "full", policySha256: "p" }))
  return "gate.json"
}
const manifest = (repo, candidate) =>
  node(release, ["manifest", "--artifact", "dist", "--candidate", candidate, "--gate", gateFile(repo, candidate), "--repository", "o/r", "--out", "release.json"], { cwd: repo })
const check = (repo, candidate, extra = ["--deployed", candidate]) =>
  node(release, ["check", "--manifest", "release.json", "--artifact", "dist", "--candidate", candidate, "--repository", "o/r", ...extra], { cwd: repo })

test("Q24 no manifest without a passing gate for the same candidate", () => {
  const { repo, newer, older } = setup()
  gateFile(repo, newer, false)
  assert.equal(node(release, ["manifest", "--artifact", "dist", "--candidate", newer, "--gate", "gate.json", "--repository", "o/r", "--out", "r.json"], { cwd: repo }).code, 1)
  gateFile(repo, older)
  assert.equal(node(release, ["manifest", "--artifact", "dist", "--candidate", newer, "--gate", "gate.json", "--repository", "o/r", "--out", "r.json"], { cwd: repo }).code, 1)
})

test("Q24 wrong candidate, wrong repository or modified bytes are denied", () => {
  const { repo, newer, older } = setup()
  assert.equal(manifest(repo, newer).code, 0)
  assert.equal(check(repo, newer).code, 0)
  assert.match(check(repo, older).stderr, /manifest is for/)
  assert.equal(node(release, ["check", "--manifest", "release.json", "--artifact", "dist", "--candidate", newer, "--repository", "x/y", "--deployed", newer], { cwd: repo }).code, 1)
  write(repo, "dist/index.js", "export default { evil: true }")
  assert.match(check(repo, newer).stderr, /digest does not match/)
})

test("Q25 an older run finishing last cannot overwrite a newer promotion", () => {
  const { repo, newer, older } = setup()
  assert.equal(manifest(repo, older).code, 0)
  const stale = check(repo, older, ["--deployed", newer])
  assert.equal(stale.code, 1)
  assert.match(stale.stderr, /stale: production already runs/)
  assert.equal(manifest(repo, newer).code, 0)
  assert.equal(check(repo, newer, ["--deployed", older]).code, 0)
  assert.equal(check(repo, newer, ["--deployed", newer]).code, 0, "re-promoting the live candidate is idempotent")
})

test("audit 10: an unknown live version is denied unless someone gives a reason", () => {
  const { repo, newer } = setup()
  assert.equal(manifest(repo, newer).code, 0)
  assert.equal(check(repo, newer, []).code, 2, "--deployed is required")
  const unknown = check(repo, newer, ["--deployed", "unknown"])
  assert.equal(unknown.code, 1)
  assert.match(unknown.stderr, /live version is unknown/)
  assert.equal(check(repo, newer, ["--deployed", "unknown", "--allow-unknown-live", " "]).code, 1)
  const allowed = check(repo, newer, ["--deployed", "unknown", "--allow-unknown-live", "first deploy"])
  assert.equal(allowed.code, 0, allowed.stderr)
  assert.equal(check(repo, newer, ["--deployed", "v1.2"]).code, 2)
})

test("audit 2: the manifest records the bundled entry, which must exist in the artifact", () => {
  const { repo, newer } = setup()
  gateFile(repo, newer)
  const base = ["manifest", "--artifact", "dist", "--candidate", newer, "--gate", "gate.json", "--repository", "o/r", "--out", "release.json"]
  assert.equal(node(release, [...base, "--entry", "worker/missing.js"], { cwd: repo }).code, 2)
  assert.equal(node(release, [...base, "--entry", "index.js"], { cwd: repo }).code, 0)
  assert.equal(JSON.parse(readFileSync(join(repo, "release.json"), "utf8")).artifact.entry, "index.js")
})

test("diverged history is denied unless explicitly allowed", () => {
  const { repo, older } = setup()
  git(repo, "checkout", "-q", "-b", "hotfix", older)
  write(repo, "src/b.ts", "x")
  const hotfix = commitAll(repo, "hotfix")
  const main = git(repo, "rev-parse", "main")
  write(repo, "dist/index.js", "export default {}")
  assert.equal(manifest(repo, hotfix).code, 0)
  assert.match(check(repo, hotfix, ["--deployed", main]).stderr, /does not descend/)
  assert.equal(check(repo, hotfix, ["--deployed", main, "--allow-diverged", "true"]).code, 0)
})

test("denials() requires gate evidence bound to the manifest candidate", () => {
  const m = { schemaVersion: 1, candidate: "c", repository: "o/r", artifact: { sha256: "d" }, gate: { passed: true, candidate: "other" } }
  assert.ok(denials(m, { digest: "d", candidate: "c", repository: "o/r" }).some((r) => /different candidate/.test(r)))
})
