import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { test } from "node:test"
import { upsert } from "../../scripts/upsert_block.mjs"
import { node, SCRIPTS, tempDir, write } from "./helpers.mjs"

const tool = join(SCRIPTS, "upsert_block.mjs")

test("Q05 appends once, then a re-run is byte-identical", () => {
  const dir = tempDir()
  const target = write(dir, "AGENTS.md", "# Project\n\nKeep this line.\n")
  write(dir, "block.md", "## Verification\n\nRun `make test`.\n")
  assert.equal(node(tool, ["AGENTS.md", "block.md"], { cwd: dir }).code, 0)
  const first = readFileSync(target, "utf8")
  assert.match(first, /Keep this line\.\n\n<!-- ci:start -->/)
  const again = node(tool, ["AGENTS.md", "block.md"], { cwd: dir })
  assert.match(again.stdout, /unchanged/)
  assert.equal(readFileSync(target, "utf8"), first)
  assert.equal(node(tool, ["AGENTS.md", "block.md", "--check"], { cwd: dir }).code, 0)
})

test("Q05 replaces only its own block and preserves everything around it", () => {
  const text = "a\n<!-- ci:start -->\nold\n<!-- ci:end -->\nb\n"
  assert.equal(upsert(text, "new"), "a\n<!-- ci:start -->\nnew\n<!-- ci:end -->\nb\n")
  assert.throws(() => upsert("<!-- ci:start -->\n", "x"), /at most one/)
  assert.throws(() => upsert("<!-- ci:end -->\n<!-- ci:start -->\n", "x"), /comes before/)
})

test("--check reports a pending change without writing", () => {
  const dir = tempDir()
  const target = write(dir, "TESTING.md", "x\n")
  write(dir, "block.md", "y")
  assert.equal(node(tool, ["TESTING.md", "block.md", "--check"], { cwd: dir }).code, 1)
  assert.equal(readFileSync(target, "utf8"), "x\n")
})
