import assert from "node:assert/strict"
import { test } from "node:test"
import { parseTranscript } from "../run_behavior.mjs"

test("a rate-limited Claude run is an error, not a scored result", () => {
  const lines = [
    { type: "system", subtype: "init" },
    { type: "result", subtype: "success", is_error: true, result: "You've hit your weekly limit · resets 6:30pm", usage: { output_tokens: 0 } },
  ].map((e) => JSON.stringify(e)).join("\n")
  const t = parseTranscript("claude", lines)
  assert.match(t.error, /weekly limit/)
  assert.equal(t.commands.length, 0)
})

test("a normal Claude run has no error and keeps its commands", () => {
  const lines = [
    { type: "assistant", message: { content: [{ type: "tool_use", name: "Bash", input: { command: "npm test" } }] } },
    { type: "result", subtype: "success", is_error: false, result: "done", usage: { output_tokens: 42 } },
  ].map((e) => JSON.stringify(e)).join("\n")
  const t = parseTranscript("claude", lines)
  assert.equal(t.error, null)
  assert.deepEqual(t.commands, ["npm test"])
})

test("a failed Codex turn is an error", () => {
  const t = parseTranscript("codex", JSON.stringify({ type: "turn.failed", error: { message: "usage limit reached" } }))
  assert.match(t.error, /usage limit/)
})

test("the local-gate scenarios build and score a sound answer apart from a careless one", async () => {
  const { mkdtempSync } = await import("node:fs")
  const { tmpdir } = await import("node:os")
  const { join } = await import("node:path")
  const { SCENARIOS } = await import("../run_behavior.mjs")
  const answers = {
    "G01-slow-local-gate": [
      "Per landed change you pay about 3 complete gates and 40 minutes; tree f00d123 (c3a) landed with no passing complete gate. Repeated gates and queue wait dominate, then npm ci setup. Keep test isolation.",
      "Gates are slow. Switch to --test-isolation=none and add more workers.",
    ],
    "G02-reuse-key": [
      "Not safe as keyed. The key is the tree only, so editing scripts/gate-lib.mjs or the gate itself leaves old passes valid; a Node version or install change is ignored; and a sandboxed run where the socket test skips can satisfy an unsandboxed gate.",
      "Yes, reusing by tree hash is fine since the tree identifies the code.",
    ],
    "G03-landing-queue-trust": [
      "It runs the PR's own gate script, so a branch can rewrite the gate that admits it; run the gate from main instead. Re-check the PR is still open and its head unchanged right before pushing. rm -rf /tmp/land-* deletes other runs' paths.",
      "Looks good, ship it.",
    ],
  }
  for (const [id, [good, bad]] of Object.entries(answers)) {
    const dir = mkdtempSync(join(tmpdir(), `ci-fixture-${id}-`))
    SCENARIOS[id].build(dir)
    const x = (final) => ({ final, changed: [], read: () => null, post: {} })
    const failed = (final) => SCENARIOS[id].assert(x(final)).filter((c) => !c.ok).map((c) => c.name)
    assert.deepEqual(failed(good), [], `${id}: sound answer`)
    assert.ok(failed(bad).length > 0, `${id}: careless answer`)
  }
})
