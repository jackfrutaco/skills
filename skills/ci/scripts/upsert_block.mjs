#!/usr/bin/env node
// Insert or replace one marked block in a project's instruction file, leaving every
// other line untouched. Re-running with the same block changes nothing.
//
//   node upsert_block.mjs <target-file> <block-file> [--id ci] [--check]
//
// The block sits between `<!-- <id>:start -->` and `<!-- <id>:end -->`. Without markers
// it is appended after one blank line. --check writes nothing and exits 1 when the file
// would change. Exit codes: 0 unchanged or written, 1 would change (--check),
// 2 invalid input such as an unmatched or repeated marker.
import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs"
import { pathToFileURL } from "node:url"

export function upsert(text, block, id = "ci") {
  const start = `<!-- ${id}:start -->`
  const end = `<!-- ${id}:end -->`
  const body = `${start}\n${block.trim()}\n${end}`
  const starts = text.split(start).length - 1
  const ends = text.split(end).length - 1
  if (starts !== ends || starts > 1) throw new Error(`expected at most one ${start} … ${end} pair`)
  if (starts === 1) {
    const from = text.indexOf(start)
    const to = text.indexOf(end) + end.length
    if (to < from) throw new Error(`${end} comes before ${start}`)
    return text.slice(0, from) + body + text.slice(to)
  }
  if (!text.trim()) return `${body}\n`
  return `${text.replace(/\n*$/, "")}\n\n${body}\n`
}

function run(argv) {
  const check = argv.includes("--check")
  const idFlag = argv.indexOf("--id")
  const id = idFlag >= 0 ? argv[idFlag + 1] : "ci"
  const [target, blockFile] = argv.filter((a, i) => !a.startsWith("--") && argv[i - 1] !== "--id")
  if (!target || !blockFile || !/^[a-z0-9-]+$/.test(id ?? "")) {
    console.error("usage: upsert_block.mjs <target-file> <block-file> [--id ci] [--check]")
    return 2
  }
  const before = existsSync(target) ? readFileSync(target, "utf8") : ""
  let after
  try {
    after = upsert(before, readFileSync(blockFile, "utf8"), id)
  } catch (error) {
    console.error(`error: ${target}: ${error.message}`)
    return 2
  }
  if (after === before) {
    console.log(`unchanged: ${target}`)
    return 0
  }
  if (check) {
    console.log(`would change: ${target}`)
    return 1
  }
  writeFileSync(target, after)
  console.log(`updated: ${target}`)
  return 0
}

if (process.argv[1] && pathToFileURL(realpathSync(process.argv[1])).href === import.meta.url) {
  process.exitCode = run(process.argv.slice(2))
}
