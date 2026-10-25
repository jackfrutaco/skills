# Stack tools

Use the read-only form of each tool. Prefer the project's own installed version
(`pnpm exec`, `uv run`, `bundle exec`) over a fresh download, and the owner's script
over either. Every finding is a candidate for the deletion gate in SKILL.md step 4,
never a verdict. Versions are as of October 2026.

## JavaScript / TypeScript (`package.json`; lockfile names the manager)

| Job | Command | Traps |
|---|---|---|
| Unused files, exports, deps | `npx -y knip@6 --reporter json --no-progress` (exit 1 = findings) | A missing config hint leaves the graph incomplete and reports used code. Public library APIs need `entry` or `/** @public */`. String-built imports and dead code inside one file are missed. Never use `--fix` here. |
| Cycles | `npx knip --include cycles`, or `npx -y madge --circular --json --ts-config tsconfig.json src` | madge needs the tsconfig for path aliases. |
| Unused locals | `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` | Noisy on legacy code: report the count, not every line. |
| Duplicates | `npx -y jscpd --min-lines 5 --reporters json --output /tmp/jscpd src` | Generated code and boilerplate inflate it. |
| Outdated | `npm outdated --json`, `pnpm outdated --format json -r`, `bun outdated` (no JSON) | Distinguish wanted from latest. |
| Vulnerable | `npm audit --json`, `pnpm audit --json`, `bun audit --json` | — |
| Duplicate versions | `pnpm dedupe --check`, `npm dedupe --dry-run` | — |
| Timing | `tsc --noEmit --extendedDiagnostics`; `vitest run --reporter=json --outputFile=f.json`; `eslint --stats -f json` | — |

`depcheck` has been archived since 2025-02, and `ts-prune` is unmaintained on npm.
Both are cobwebs if the project still uses them.

## Python (`pyproject.toml`, `uv.lock`, `poetry.lock`, `requirements*.txt`)

| Job | Command | Traps |
|---|---|---|
| Dead code | `uvx vulture <src> --min-confidence 80` (exit 3 = found; text only) | Framework decorators (`--ignore-decorators "@app.route"`), plugins, `__all__`. |
| Unused imports and args, commented code | `uvx ruff check --select F401,F841,ARG,ERA001 --output-format json` | `__init__.py` re-exports. |
| Unused or missing deps | `uv run --with deptry deptry . --json-output /tmp/deptry.json` | Plugins loaded by entry point; CLI-only packages. |
| Vulnerable | `uvx pip-audit -f json` | Audits the active environment. |
| Outdated | `uv pip list --outdated --format json`; `uv lock --check` | — |
| Timing | `pytest --durations=20 -q`; `python -X importtime -c 'import pkg'` | — |

## Go (`go.mod`)

| Job | Command | Traps |
|---|---|---|
| Dead functions | `go run golang.org/x/tools/cmd/deadcode@latest -test ./...` | Valid for one GOOS/GOARCH/tag set: run each set and intersect. Can't see assembly or `go:linkname`. |
| Unused unexported | `go run honnef.co/go/tools/cmd/staticcheck@latest -checks U1000 -f json ./...` | Exported identifiers in libraries are never flagged. |
| Module hygiene | `go mod tidy -diff` | Run with each build tag set. |
| Outdated / vulnerable | `go list -m -u -json all`; `go run golang.org/x/vuln/cmd/govulncheck@latest ./...` | govulncheck reports only reachable vulnerabilities. |

## Rust (`Cargo.toml`)

| Job | Command | Traps |
|---|---|---|
| Unused deps | `cargo machete --json` (fast, imprecise) or `cargo shear --format=json` | Codegen in `build.rs`; renamed crates. |
| Dead code | `cargo check --message-format json` and filter for the `dead_code` lint | `pub` items in libraries aren't reported. |
| Outdated / vulnerable | `cargo outdated --workspace --format json`; `cargo audit --json` | Use `cargo audit --file Cargo.lock` on untrusted code. |
| Timing | `cargo build --timings` | — |

## Other stacks

| Stack (fingerprint) | Dead code | Deps / outdated / vulnerable | Traps |
|---|---|---|---|
| Ruby (`Gemfile`) | `debride --rails app lib` | `bundle outdated --parseable`; `bundle-audit check --update` | Dynamic dispatch, Rails callbacks and views. |
| PHP (`composer.json`) | `shipmonk/dead-code-detector` (PHPStan) | `composer-unused`; `composer outdated --direct --format=json`; `composer audit --format=json` | Framework-loaded packages; analyse `src` and `tests` together. |
| JVM (`pom.xml`, `build.gradle*`) | detekt `Unused*` rules (Kotlin); Error Prone `UnusedMethod` | Gradle `buildHealth` (dependency-analysis plugin); `mvn dependency:analyze`; `./gradlew dependencyUpdates` | Runtime-only deps (drivers, logging) look unused. |
| Swift (`Package.swift`, `*.xcodeproj`) | `periphery scan` (commercial since 2026; free for OSS and indie) | SwiftPM `swift package show-dependencies` | Only built targets are indexed. Codable/IB/ObjC-visible symbols need flags. |
| .NET (`*.csproj`, `*.sln`) | IDE0051/IDE0052 analyzers via `dotnet build` | `dotnet package list --outdated --vulnerable` (.NET 10; older: `dotnet list package`) | Reflection and DI. |
| Dart / Flutter (`pubspec.yaml`) | `dart analyze` (unused_element etc.), `dart fix --dry-run` | `dart pub outdated --json` | Code reached by codegen. |
| Elixir (`mix.exs`) | The compiler warns about unused code (`mix xref unreachable` is a no-op now) | `mix hex.outdated`; `mix deps.unlock --check-unused` | — |

## Any stack

| Job | Command |
|---|---|
| Size and complexity | `scc --format json --by-file`, `tokei -o json`, or `cloc --json --vcs=git` |
| Hotspots | Churn: `git log --since=1.year --name-only --format= \| grep . \| sort \| uniq -c \| sort -rn \| head -30`. Intersect with the largest files: a big file that changes often is where agents spend their reads. |
| Vulnerable deps | `osv-scanner scan source -r . --format json` |
| Secrets in history | `gitleaks git --redact --no-banner -f json -r - .`. Always redact. A leak needs rotation first. |
| Large history | `git-sizer --json` or `git count-objects -vH`. Rewriting history is outward-facing. |
| CI | `gh run list --limit 100 --json workflowName,conclusion,startedAt,updatedAt`; `actionlint` |
| Dockerfiles | `hadolint --format json Dockerfile` |
| Doc links | `lychee --offline --include-fragments '**/*.md'` |
