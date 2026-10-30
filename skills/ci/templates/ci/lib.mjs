// Shared helpers for the CI gate scripts. Node 20+ standard library only.
// Copied into the target repository with the other files in this folder, so the
// project's CI never depends on the skill being installed.
import { createHash } from "node:crypto"
import { appendFileSync, readdirSync, readFileSync, realpathSync, statSync } from "node:fs"
import { join, relative } from "node:path"
import { pathToFileURL } from "node:url"

export const SCHEMA_VERSION = 1
const CHECK_NAME = /^[a-z0-9][a-z0-9_-]*$/

export function fail(message, code = 1) {
  const error = new Error(message)
  error.exitCode = code
  throw error
}

/** True when the module at `url` is the script node was asked to run. */
export function isEntry(url) {
  return Boolean(process.argv[1]) && pathToFileURL(realpathSync(process.argv[1])).href === url
}

/** Run a CLI entry point: print the error and exit with its code. */
export async function main(run) {
  try {
    process.exitCode = (await run(process.argv.slice(2))) ?? 0
  } catch (error) {
    console.error(`error: ${error.message}`)
    process.exitCode = error.exitCode ?? 1
  }
}

export function parseArgs(argv, known) {
  const args = { _: [] }
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i]
    if (!token.startsWith("--")) {
      args._.push(token)
      continue
    }
    const [name, inline] = token.slice(2).split(/=(.*)/s)
    if (!known.includes(name)) fail(`unknown option --${name}`, 2)
    args[name] = inline ?? argv[++i]
    if (args[name] === undefined) fail(`--${name} needs a value`, 2)
  }
  return args
}

export function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex")
}

/** Content hash of a file, or of every file under a directory (path + bytes, order-free). */
export function contentDigest(path) {
  if (!statSync(path).isDirectory()) return sha256(readFileSync(path))
  const lines = []
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name)
      if (entry.isDirectory()) walk(full)
      else if (entry.isFile()) {
        const name = relative(path, full).split("\\").join("/")
        lines.push(`${name}\0${sha256(readFileSync(full))}\n`)
      }
    }
  }
  walk(path)
  return sha256(lines.sort().join(""))
}

export function readJson(path, what) {
  let text
  try {
    text = readFileSync(path, "utf8")
  } catch {
    fail(`${what} not found: ${path}`, 2)
  }
  try {
    return JSON.parse(text)
  } catch (error) {
    fail(`${what} is not valid JSON (${path}): ${error.message}`, 2)
  }
}

/**
 * Glob to RegExp, matched against the whole repository-relative path.
 * `**` crosses directories, `*` and `?` stay inside one segment. No braces or classes:
 * a policy that needs them lists the patterns separately.
 */
export function globToRegExp(pattern) {
  let source = ""
  for (let i = 0; i < pattern.length; i++) {
    const c = pattern[i]
    if (c === "*" && pattern[i + 1] === "*") {
      const slash = pattern[i + 2] === "/"
      source += slash ? "(?:.*/)?" : ".*"
      i += slash ? 2 : 1
    } else if (c === "*") source += "[^/]*"
    else if (c === "?") source += "[^/]"
    else source += c.replace(/[.+^${}()|[\]\\]/g, "\\$&")
  }
  return new RegExp(`^${source}$`)
}

export function matchesAny(path, patterns) {
  return (patterns ?? []).some((pattern) => globToRegExp(pattern).test(path))
}

function assertPatterns(value, where) {
  if (value === undefined || value === null) return
  if (!Array.isArray(value) || value.some((p) => typeof p !== "string" || !p)) {
    fail(`${where} must be a list of non-empty glob strings`, 2)
  }
}

/** Validate the checked-in check policy. An invalid policy can never yield a selection. */
export function validatePolicy(policy) {
  if (policy?.schemaVersion !== SCHEMA_VERSION) {
    fail(`policy schemaVersion must be ${SCHEMA_VERSION}`, 2)
  }
  const names = Object.keys(policy.checks ?? {})
  if (names.length === 0) fail("policy declares no checks", 2)
  for (const name of names) {
    if (!CHECK_NAME.test(name)) fail(`check name "${name}" must match ${CHECK_NAME}`, 2)
    const check = policy.checks[name]
    assertPatterns(check.paths, `checks.${name}.paths`)
    if (Array.isArray(check.paths) && check.paths.length === 0) {
      fail(`checks.${name}.paths is empty; omit it to always run the check`, 2)
    }
    if (check.follows !== undefined) {
      const target = policy.checks[check.follows]
      if (!target || target.follows !== undefined || check.paths) {
        fail(`checks.${name}.follows must name a check that does not itself follow, without its own paths`, 2)
      }
    }
  }
  assertPatterns(policy.fullOn?.paths, "fullOn.paths")
  assertPatterns(policy.noop?.paths, "noop.paths")
  assertPatterns(policy.critical, "critical")
  if (policy.afterGate !== undefined) {
    if (!Array.isArray(policy.afterGate) || policy.afterGate.some((n) => !CHECK_NAME.test(n) || names.includes(n))) {
      fail("afterGate must list job ids that run after the gate and are not checks", 2)
    }
  }
  if (policy.noop?.paths?.length && !policy.noop.rationale) {
    fail("noop.paths needs a noop.rationale", 2)
  }
  const attempts = policy.maxAttempts ?? 2
  if (!Number.isInteger(attempts) || attempts < 1) fail("maxAttempts must be a positive integer", 2)
  return names
}

export function policyDigest(path) {
  return sha256(readFileSync(path))
}

/** Append `name=value` lines to $GITHUB_OUTPUT when running in GitHub Actions. */
export function writeOutputs(outputs) {
  const file = process.env.GITHUB_OUTPUT
  if (!file) return
  const lines = Object.entries(outputs).map(([key, value]) => `${key}=${value}`)
  appendFileSync(file, `${lines.join("\n")}\n`)
}

export function writeSummary(markdown) {
  const file = process.env.GITHUB_STEP_SUMMARY
  if (file) appendFileSync(file, `${markdown}\n`)
}
