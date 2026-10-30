import { execFileSync, spawnSync } from "node:child_process"
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

export const SKILL = join(dirname(fileURLToPath(import.meta.url)), "..", "..")
export const TEMPLATES = join(SKILL, "templates", "ci")
export const SCRIPTS = join(SKILL, "scripts")

export function tempDir(prefix = "ci-skill-") {
  return mkdtempSync(join(tmpdir(), prefix))
}

export function write(root, path, text) {
  const full = join(root, path)
  mkdirSync(dirname(full), { recursive: true })
  writeFileSync(full, text)
  return full
}

const GIT_ENV = { GIT_AUTHOR_NAME: "t", GIT_AUTHOR_EMAIL: "t@example.com", GIT_COMMITTER_NAME: "t", GIT_COMMITTER_EMAIL: "t@example.com" }

export function git(cwd, ...args) {
  return execFileSync("git", args, { cwd, encoding: "utf8", env: { ...process.env, ...GIT_ENV } }).trim()
}

export function initRepo(files) {
  const root = tempDir("ci-repo-")
  git(root, "init", "-q", "-b", "main")
  for (const [path, text] of Object.entries(files)) write(root, path, text)
  git(root, "add", "-A")
  git(root, "commit", "-q", "-m", "base")
  return root
}

export function commitAll(root, message) {
  git(root, "add", "-A")
  git(root, "commit", "-q", "-m", message)
  return git(root, "rev-parse", "HEAD")
}

/** Run a node script; returns { code, stdout, stderr }. */
export function node(script, args, options = {}) {
  const result = spawnSync(process.execPath, [script, ...args], { encoding: "utf8", ...options })
  return { code: result.status, stdout: result.stdout, stderr: result.stderr }
}

export function junit(cases) {
  const body = cases
    .map(([id, status]) => {
      const [classname, name] = id.split("::")
      const inner = status === "failed" ? '<failure message="boom"/>' : status === "skipped" ? "<skipped/>" : ""
      return `<testcase classname="${classname}" name="${name}">${inner}</testcase>`
    })
    .join("")
  return `<?xml version="1.0"?><testsuites><testsuite name="s" tests="${cases.length}">${body}</testsuite></testsuites>`
}
