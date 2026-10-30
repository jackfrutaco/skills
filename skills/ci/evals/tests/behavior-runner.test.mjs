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
