# Local loop

Local feedback works without any hosted CI. It is how a person or agent learns quickly
whether a change is right; it is not, by itself, an enforced merge gate.

## Tiers by what they prove, then by time

Decide what evidence each change needs (product behavior, supported platforms, security,
data/migrations, release packaging), then place checks:

| Tier | Runs | Objective | Typical content |
|---|---|---|---|
| Pre-commit | staged files | ~10 s | format check, lint of staged files, secret scan |
| Focused (pre-push or on demand) | the change and its dependants | ~3 min | typecheck, affected unit tests |
| Presubmit (PR) | the candidate | ~10 min | all required merge evidence |
| Post-merge / release | the release candidate | as long as it needs | slow integration, platform matrix, packaging |

The times are review triggers from the ten-minute build guidance (see
[sources.md](sources.md)). When a required check is slower, profile and optimize it or
record an exception in the project's test guide. Deferred checks keep an owner, a
response rule, and block release when release depends on them.

## Test sizes are constraints, not names

- **Small (unit):** one process, no network, no real clock or sleep, no shared files.
- **Medium (integration):** one machine. Controlled localhost services, a temp
  database, an OS-assigned port (`listen(0)`), never a live third-party API.
- **Large (system/E2E):** real browsers, devices or deployed services, in an
  environment with an explicit owner.

Wait on events, not time: poll with a bounded deadline, inject clocks. Bind port 0 and
read the assigned port; a "free port" probe does not reserve it.

## One command per tier

Each tier is one repository command that works on a clean machine after the documented
setup. Prefer what the ecosystem already uses:

| Ecosystem | Unit/focused | Static | Notes |
|---|---|---|---|
| Node | `npm test`, `vitest run`, `node --test` | `tsc --noEmit`, `eslint` | `npm ci` from the lockfile |
| Python | `pytest -q` | `ruff check`, `mypy` / `pyright` | `uv sync --locked` or pinned requirements |
| Go | `go test ./...` (`-race` where it matters) | `go vet ./...`, `staticcheck` | `-count=1` defeats the test cache when measuring |
| Rust | `cargo test` or `cargo nextest run` | `cargo clippy -- -D warnings`, `cargo fmt --check` | |
| Ruby | `bundle exec rspec` | `rubocop` | |
| JVM | `./gradlew test` / `mvn -q test` | `./gradlew check` | |
| .NET | `dotnet test` | `dotnet format --verify-no-changes` | |
| Swift | `swift test` / `xcodebuild test` | `swiftlint` | macOS needed for Apple platforms |

If the project already has `make test`, `just test` or a `scripts/` entry, use it.
Do not add Node, npm or a JavaScript tool to a project that does not use them; the
helper scripts in this skill need Node only where they run, and a non-Node project can
skip them and keep native commands. Do not install tools to make an audit run; list
them as missing.

## Hooks

- Keep the hook tool the project has. Add a command to it rather than replacing it.
- Pre-commit sees staged content only. Use the tool's staged-file mode (lint-staged,
  Lefthook `stage_fixed`, pre-commit's stash) so unstaged edits are never formatted,
  committed or lost. Never run a formatter and a reader on the same changing files in
  parallel.
- Keep pre-commit within its objective. Slow checks move to the focused tier, where a
  person can still skip them knowingly; a hook that is routinely bypassed with
  `--no-verify` is a design bug.
- A hook passing is local feedback, not proof that a protected branch is safe.

## Machine limits and cancellation

- Bound work: matrix × workers × simultaneous runs must fit the machine. Several agents
  on one machine multiply this; prefer the project's existing admission or lock.
- Do not start heavy static work (full typecheck, whole-repo analyzers) before an
  existing lock just to hide queue time; that slows the run holding the lock and
  moves cost off the books. Cheap, bounded preflight before the lock is fine.
- Give every command a timeout. On cancel, stop the process group you started and
  nothing else; other projects' and other agents' processes are not yours.

## No remote, or a local gate already exists

- **No remote:** set up the local tiers and say plainly that merges are not enforced.
  Do not create a repository or account to finish setup.
- **Existing local-authoritative gate:** it stays the owner. Respect its candidate
  identity, lock and receipts. Do not add a second locking or receipt engine, and do
  not reuse a result after the candidate, base, dependencies, config or runtime changed.
- **Shared or dirty checkout:** verify a committed candidate (a temporary worktree or
  the gate's own isolation), never the unrelated working-tree edits of someone else.

## Instructions the project keeps

Write a short block into the project's existing test guide, through
`scripts/upsert_block.mjs` so re-running setup is a no-op:

```markdown
## Verification
- Focused: `<command>` (runs in ~N s on this machine; measured <date>)
- Before a PR: `<command>`; CI runs the same commands, gate check name `gate`
- New tests follow the sizes in <guide>: no network or sleeps in unit tests
- A test that fails then passes on retry is reported with both results, not re-run
  until green. Quarantine only through `ci/quarantine.json` with owner, issue and review date
```

Keep it to the commands and the few rules people break. It replaces nothing else in the
file. If a person declines setup, record that in the same guide so it is not offered
again during routine work.
