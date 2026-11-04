#!/usr/bin/env node
// Regression test for scripts/map-surface.mjs: plant entries and effects in a
// throwaway repo, plus look-alikes that must not count, and check the map.
// Usage: node evals/test_scripts.mjs   (exit 0 = pass; seconds, no network)
import { execFileSync } from "node:child_process"
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const SCRIPT = join(dirname(fileURLToPath(import.meta.url)), "..", "scripts", "map-surface.mjs")
const repo = mkdtempSync(join(tmpdir(), "map-surface-test-"))
const env = { ...process.env, GIT_AUTHOR_DATE: "2026-01-01T00:00:00", GIT_COMMITTER_DATE: "2026-01-01T00:00:00", GIT_CONFIG_NOSYSTEM: "1", HOME: repo }
const git = (...a) => execFileSync("git", ["-C", repo, ...a], { env, stdio: "pipe" }).toString()
const write = (path, text) => { mkdirSync(dirname(join(repo, path)), { recursive: true }); writeFileSync(join(repo, path), text) }
const map = (...extra) => {
  const out = join(repo, ".map.json")
  execFileSync(process.execPath, [SCRIPT, repo, "--out", out, ...extra], { env, stdio: "pipe" })
  return JSON.parse(readFileSync(out, "utf8"))
}

let failed = 0
const check = (name, ok, detail = "") => { if (!ok) failed++; console.log(`${ok ? "ok" : "not ok"} - ${name}${!ok && detail ? ` (${detail})` : ""}`) }

try {
  git("init", "-q")
  write("tsconfig.json", '{ "compilerOptions": { "paths": { "@lib/*": ["./src/lib/*"] } } } // trailing comment\n')
  // Planted: an HTTP route that reaches a spawn through a relative import.
  write("src/server/routes.ts", 'import { run } from "./runner"\nexport function handle(req, url) { if (url.pathname === "/run") return run(req.body.cmd) }\n')
  write("src/server/runner.ts", 'import { spawn } from "node:child_process"\nexport const run = (c) => spawn("sh", ["-c", c])\n')
  // Planted: an IPC handler that reaches execFile through a tsconfig alias.
  write("src/main/ipc.ts", 'import { exec } from "@lib/exec"\nipcMain.handle("x", () => exec())\n')
  write("src/lib/exec.ts", 'import { execFile } from "node:child_process"\nexport const exec = () => execFile("ls")\n')
  // Planted: Python route with a subprocess effect in the same file.
  write("api/app.py", '@app.post("/build")\ndef build():\n    subprocess.run(["make"])\n')
  // Look-alikes that must not count.
  write("src/server/notes.ts", '// spawn( is mentioned in a comment only\nexport const note = 1\n')
  write("src/server/runner.test.ts", 'import { spawn } from "node:child_process"\nspawn("true")\n')
  write("scripts/build.mjs", 'import { execFileSync } from "node:child_process"\nexecFileSync("tsc")\n')
  write("src/orphan/unused.ts", 'import { writeFileSync } from "node:fs"\nwriteFileSync("/tmp/x", "y")\n')
  git("add", "-A"); git("commit", "-qm", "fixture")

  const m = map()
  const ids = m.groups.map((g) => g.id)
  const group = (id) => m.groups.find((g) => g.id === id)

  check("route reaches spawn through a relative import", group("process-spawn@src/server")?.sample.nearEntries.includes("src/server/routes.ts"), ids.join(", "))
  check("IPC handler reaches execFile through a tsconfig alias", group("process-spawn@src/lib")?.sample.nearEntries.includes("src/main/ipc.ts"), JSON.stringify(group("process-spawn@src/lib")?.sample))
  check("python route and subprocess are mapped", group("process-spawn@api")?.entryKinds["http-route"] === 1, JSON.stringify(group("process-spawn@api")))
  check("a comment mentioning spawn( is not an effect", group("process-spawn@src/server")?.effectSites === 1, String(group("process-spawn@src/server")?.effectSites))
  check("test files are skipped", !m.groups.some((g) => g.files.some((f) => f.endsWith(".test.ts"))))
  check("dev tooling is excluded by default and named", !ids.some((id) => id.endsWith("@scripts")) && m.excludedTooling.includes("scripts"), JSON.stringify(m.excludedTooling))
  check("an effect no entry reaches ranks below reachable ones", group("fs-write@src/orphan")?.score === 0 && ids.indexOf("fs-write@src/orphan") > ids.indexOf("process-spawn@src/server"))
  check("--include-tooling brings tooling back", map("--include-tooling").groups.some((g) => g.id === "process-spawn@scripts"))

  write("src/lib/exec.ts", 'import { execFile } from "node:child_process"\nexport const exec = () => execFile("ls", ["-la"])\n')
  git("commit", "-qam", "change exec")
  const since = map("--since", "HEAD~1")
  check("--since keeps only groups touching changed files", since.groups.length >= 1 && since.groups.every((g) => g.changed) && since.groups.some((g) => g.id === "process-spawn@src/lib") && !since.groups.some((g) => g.id === "process-spawn@api"), since.groups.map((g) => g.id).join(", "))
} finally {
  rmSync(repo, { recursive: true, force: true })
}
console.log(failed ? `${failed} failed` : "all passed")
process.exit(failed ? 1 : 0)
