# Evidence and tool selection

## Evidence ladder

| Evidence | It can support | It cannot establish by itself |
| --- | --- | --- |
| User report / earlier audit | A candidate and reproduction lead | Present code, authority, deployed state |
| Source inspection | A reachable path or implemented control, with preconditions | Effective runtime configuration or successful mitigation |
| Owner test / isolated probe | Behavior under the tested inputs and dependencies | All callers, real integrations or deployment |
| Running app / CLI | The exercised entry, identities, effect and failure behavior | Packaged or production parity unless that was the target |
| Packaged artifact | The inspected build's contents and settings | Live service controls or user adoption |
| Authorized live read / exercise | A particular deployed state or observed effect at a time | Universal safety or future state |

Confidence and severity are independent. Source-supported high-impact behavior can
deserve urgent follow-up without being called a reproduced production exploit.

## Choose tools after the threat model

Inspect installed tools and existing project commands first. Read their help and
the project's pinned versions; avoid guessing current flags or installing latest
versions automatically. Execute only within the host's command policy.

| Question | Evidence/tool family | Common false conclusion |
| --- | --- | --- |
| Known vulnerable dependency? | Lockfile-aware ecosystem audit and vendor advisory; inspect runtime reachability | Every advisory is exploitable, or zero advisories means safe |
| Possible credentials in source/history/artifact? | A secret scanner in fully redacted mode, scoped to authorized files | Printing the match is needed, or deleting the string revokes access |
| Input reaches a sensitive sink? | Code tracing, language-aware static analysis, focused synthetic test | A regex hit or configured rule proves exploitable flow |
| Cross-tenant access? | Two fixture identities through the real handler and persistence boundary | UUIDs or a frontend filter supply authorization |
| Web behavior? | Safe local/staging browser or API request with a finite probe plan | CORS blocks arbitrary HTTP clients |
| Cloud configuration? | Admitted account metadata tools / read-only CLI/API | A local config file proves what is deployed |
| Update or release integrity? | Actual artifact, signature verifier, isolated install/rollback exercise | A signature exists, so the consumer must verify it |
| Restore/revocation? | Isolated recovery test with post-restart denial | A backup file or successful logout response proves the lifecycle |

Examples of tool families include Gitleaks, Semgrep, CodeQL, OSV tooling and an
ecosystem's audit command. They are optional candidates, not installation requests
or endorsed current command lines. Check licensing, telemetry, upload behavior and
local availability before choosing one. Some “read-only” network audits disclose
package names or repository metadata. Record such limitations rather than uploading
private code to get a nicer score. Avoid automatic audit-fix and broad upgrades.

## Design a useful probe

1. Declare target, environment, allowed side effects and limits (SKILL.md §2 defaults).
2. Establish a legitimate positive case with synthetic data.
3. Change one attacker-controlled input or authority condition.
4. Observe the persisted or external effect, not only the HTTP status or model prose.
5. Exercise revocation, retry or restart whenever the path persists authority.
6. Record version, command, result and limitations; clean up only owned fixtures.

For a cheap denial-of-service hypothesis, demonstrate the missing bound in code or
with a tiny fixture. Do not consume real service capacity to quantify maximum harm.
Use test clocks and dependency fakes for long expiry windows. Clearly label what
the fake omits.

## Recheck without laundering old evidence

Keep the original finding ID and record the new revision. A patch changes status
to **implemented, verification pending**, not automatically **closed**. Close the
tested scope only after a denial test and a legitimate path pass. Keep deployment
pending, waived checks and accepted risks distinct. Rerun evidence invalidated by
changed dependencies, credentials, ownership or configuration; reuse unchanged
evidence with its date and scope instead of pretending it was rerun.
