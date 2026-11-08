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
    "G04-idle-workers": [
      "Every fast run used 2 workers on a 16-core machine that was 90% idle. scripts/budget.mjs halves the budget for AGENT_SESSION and then divides by three unless GATE_LOCK is set, which only the pre-push hook sets. Size from what is running instead.",
      "The machine is overloaded; add shards or move to a bigger machine.",
    ],
    "G05-small-commit-reruns": [
      "Let the fast check carry a test file's earlier pass to the new commit when selection between the two trees would not pick it, so only affected tests rerun. A lockfile, package.json or config change carries nothing. The complete gate keeps exact-tree receipts and never reads carried passes.",
      "Key receipts by branch name instead of tree so both profiles skip reruns.",
    ],
    "G06-concurrency-speedup": [
      "Not yet. The ping test now starts its clock before the child is forked, so the 300 ms window includes startup, and with concurrency several children start at once. Without awaiting ready, ping() can resolve on the ready message, so it no longer proves a pong. The grace test went from a 1 s margin over the 3 s default to 0.5 s (3500 vs 3000), so a late timer could hide a regression. Run the file several times under load beside the old version before committing.",
      "Looks good: the tests pass and it is 3x faster, commit it.",
    ],
    "G06-concurrency-speedup (loose load wording)": [
      "Not yet: the 300 ms window now includes child startup, the grace margin dropped to 500 ms, and ping() can resolve on ready instead of a pong. Rerun the file 10 times under load first.",
      "Not yet: the 300 ms window now includes child startup, the margin dropped to 500 ms and ping() can resolve on ready, so a loaded machine could fail it.",
    ],
    "G02-reuse-key (a bare no)": [
      "No. The receipt is keyed to the HEAD tree only: a change to scripts/gate-lib.mjs leaves old passes valid, the Node version and installed dependencies are not in the key, and a sandboxed run where the socket test skips can be reused by an unsandboxed one.",
      "Yes. The tree hash identifies the code, so reuse is fine.",
    ],
    "G03-landing-queue-trust (phrased differently)": [
      "Do not turn it on. land.mjs:9 runs the gate from the PR itself, so a PR can replace it with a successful no-op. It pushes without checking the PR is still open and its head unchanged. rm -rf /tmp/land-* removes other runs.",
      "The script fetches the PR and pushes it; consider adding logging.",
    ],
  }
  for (const [id, [good, bad]] of Object.entries(answers)) {
    const dir = mkdtempSync(join(tmpdir(), `ci-fixture-${id}-`))
    const scenario = SCENARIOS[id.split(" ")[0]]
    scenario.build(dir)
    const x = (final) => ({ final, changed: [], read: () => null, post: {} })
    const failed = (final) => scenario.assert(x(final)).filter((c) => !c.ok).map((c) => c.name)
    assert.deepEqual(failed(good), [], `${id}: sound answer`)
    assert.ok(failed(bad).length > 0, `${id}: careless answer`)
  }
})
