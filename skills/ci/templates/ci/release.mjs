#!/usr/bin/env node
// Bind a release artifact to the exact verified candidate, then refuse promotion of
// anything else.
//
//   node release.mjs manifest --artifact <path> --candidate <sha> --gate gate-result.json
//       --repository owner/repo [--entry <file in artifact>] [--run-id ID --attempt N --workflow NAME]
//       --out release.json
//   node release.mjs check --manifest release.json --artifact <path> --candidate <sha>
//       --repository owner/repo --deployed <sha|unknown> [--allow-unknown-live <reason>]
//       [--allow-diverged true]
//
// `manifest` refuses to describe an artifact unless the gate result passed for the same
// candidate. `check` runs in the deploy job: the artifact's digest, candidate, repository
// and gate evidence must match, and the candidate must be newer than (a descendant of)
// what production runs, so an older run finishing last cannot overwrite a newer release.
// When the live version cannot be identified (first deploy, an untagged manual deploy,
// an unreadable provider), pass `--deployed unknown`: promotion is denied unless
// --allow-unknown-live gives the reason someone accepted that. The digest proves the bytes, not who built them: download the manifest
// and artifact only from the trusted workflow run you are promoting.
// Exit codes: 0 allowed, 1 denied, 2 invalid input.
import { execFileSync } from "node:child_process"
import { existsSync, statSync, writeFileSync } from "node:fs"
import { basename, join } from "node:path"
import { SCHEMA_VERSION, contentDigest, fail, isEntry, main, parseArgs, readJson } from "./lib.mjs"

function isAncestor(older, newer, cwd) {
  try {
    execFileSync("git", ["merge-base", "--is-ancestor", older, newer], { cwd, stdio: "ignore" })
    return true
  } catch (error) {
    if (error.status === 1) return false
    fail(`cannot compare ${older} and ${newer}: fetch both commits first`, 1)
  }
}

/** Pure checks over a manifest; returns a list of reasons to deny. */
export function denials(manifest, { digest, candidate, repository }) {
  const reasons = []
  if (manifest?.schemaVersion !== SCHEMA_VERSION) reasons.push("manifest schemaVersion mismatch")
  if (manifest?.gate?.passed !== true) reasons.push("manifest does not carry a passing gate result")
  if (manifest?.gate?.candidate !== manifest?.candidate) reasons.push("gate result is for a different candidate than the manifest")
  if (manifest?.candidate !== candidate) reasons.push(`manifest is for ${manifest?.candidate}, not ${candidate}`)
  if (manifest?.repository !== repository) reasons.push(`manifest is from ${manifest?.repository}, not ${repository}`)
  if (manifest?.artifact?.sha256 !== digest) reasons.push("artifact digest does not match the manifest (different or modified bytes)")
  return reasons
}

function runManifest(args) {
  for (const key of ["artifact", "candidate", "gate", "repository", "out"]) {
    if (!args[key]) fail(`manifest needs --${key}`, 2)
  }
  if (args.entry) {
    const inside = statSync(args.artifact).isDirectory() ? join(args.artifact, args.entry) : null
    if (!inside || !existsSync(inside)) fail(`--entry ${args.entry} is not a file inside ${args.artifact}`, 2)
  }
  const gate = readJson(args.gate, "gate result")
  if (gate.passed !== true || gate.candidate !== args.candidate) {
    console.error("release: refusing to describe an artifact without a passing gate for this candidate")
    return 1
  }
  const manifest = {
    schemaVersion: SCHEMA_VERSION,
    repository: args.repository,
    candidate: args.candidate,
    workflow: args.workflow ?? process.env.GITHUB_WORKFLOW ?? null,
    runId: args["run-id"] ?? process.env.GITHUB_RUN_ID ?? null,
    attempt: Number(args.attempt ?? process.env.GITHUB_RUN_ATTEMPT ?? 1),
    artifact: { name: basename(args.artifact), entry: args.entry ?? null, sha256: contentDigest(args.artifact) },
    gate: { passed: gate.passed, candidate: gate.candidate, mode: gate.mode, policySha256: gate.policySha256, runId: gate.runId, attempt: gate.attempt },
    createdAt: new Date().toISOString(),
  }
  writeFileSync(args.out, `${JSON.stringify(manifest, null, 2)}\n`)
  console.log(`release manifest for ${args.candidate}: ${manifest.artifact.sha256}`)
  return 0
}

function runCheck(args) {
  for (const key of ["manifest", "artifact", "candidate", "repository", "deployed"]) {
    if (!args[key]) fail(`check needs --${key}${key === "deployed" ? " (the live candidate SHA, or unknown)" : ""}`, 2)
  }
  const manifest = readJson(args.manifest, "release manifest")
  const reasons = denials(manifest, { digest: contentDigest(args.artifact), candidate: args.candidate, repository: args.repository })
  if (args.deployed === "unknown") {
    const reason = (args["allow-unknown-live"] ?? "").trim()
    if (!reason) reasons.push("the live version is unknown, so a stale promotion cannot be ruled out; pass --allow-unknown-live <reason> only for a first or deliberately untagged deploy")
    else console.log(`live version unknown; allowed: ${reason}`)
  } else if (!/^[0-9a-f]{7,64}$/i.test(args.deployed)) {
    fail(`--deployed must be a commit SHA or unknown, not "${args.deployed}"`, 2)
  } else if (args.deployed !== args.candidate) {
    if (isAncestor(args.candidate, args.deployed, args.cwd)) reasons.push(`stale: production already runs ${args.deployed}, which is newer than ${args.candidate}`)
    else if (!isAncestor(args.deployed, args.candidate, args.cwd) && args["allow-diverged"] !== "true") {
      reasons.push(`${args.candidate} does not descend from deployed ${args.deployed}; promote across branches only with --allow-diverged true`)
    }
  }
  for (const reason of reasons) console.error(`release denied: ${reason}`)
  if (reasons.length === 0) console.log(`release allowed: ${args.candidate} ${manifest.artifact.sha256}`)
  return reasons.length ? 1 : 0
}

const OPTIONS = ["artifact", "candidate", "gate", "repository", "entry", "run-id", "attempt", "workflow", "out", "manifest", "deployed", "allow-unknown-live", "allow-diverged", "cwd"]
if (isEntry(import.meta.url)) {
  main((argv) => {
    const args = parseArgs(argv, OPTIONS)
    if (args._[0] === "manifest") return runManifest(args)
    if (args._[0] === "check") return runCheck(args)
    fail("usage: release.mjs manifest|check ...", 2)
  })
}
