# Coverage menu

This is an original review menu, not an exhaustive standard or a claim of ASVS
conformance. Choose depth by the product's exposure and the requested scope.
For each applicable row record its owner, evidence, status and next check. “Unknown”
is useful; it must not disappear from the report because the happy path passed.

| Area | What to trace | A useful denial or failure check |
| --- | --- | --- |
| Assets and boundaries | Data classes, roles, tenants, admin tools, deployments, public and local entry points; who owns each sensitive effect | Reach an alternate route or worker and verify it enforces the same policy |
| Authentication and recovery | Sign-in, enrollment, MFA/passkeys, password handling, OAuth state/PKCE/redirects, magic links, recovery and account linking | Reuse or expire a token; interrupt recovery; verify no session or unintended account link results |
| Sessions and devices | Cookie attributes in the running service, token audience/issuer/lifetime, CSRF, device trust, logout and revocation | Reuse old access after logout, password reset, device removal and process restart; document any intentional validity window |
| Authorization and tenancy | Server-side role, object and field ownership on every read/write/export/search/job; membership changes | Two fixture accounts exchange object IDs, tenant IDs and nested fields; the other account receives no data and causes no effect |
| Business logic | State transitions, invitations, approvals, pricing/entitlements, refunds, concurrent updates, replay and idempotency | Repeat or reorder a request; race two workers; same idempotency key with changed payload must not become a second action |
| Parsing and injection | SQL/NoSQL, shell arguments, templates, markup, deserialization, expression engines, archive extraction | Inert fixture metacharacters and unexpected types remain data; errors contain no secrets; inspect the sink |
| Browser surfaces | Output encoding, sanitization, CSP, framing, redirects, CORS and CSRF distinctions, third-party scripts | Render inert hostile markup in an isolated page; cross-origin requests cannot rely on CORS as authorization |
| API and transport | HTTP/WebSocket authentication, schema bounds, trusted proxy headers, TLS, pagination and subscription lifetime | Unauthenticated upgrade, oversized streamed body and revoked subscription fail before expensive or sensitive work |
| Outbound requests | URL parsing, allowed protocols/destinations, DNS resolution, redirect policy, credential forwarding | Simulated redirect to an internal destination is rejected; use a fake resolver/service rather than contacting real metadata endpoints |
| Files and local data | Canonical containment, symlinks, opened handles, archive traversal, MIME/content checks, upload quotas, download permissions | A fixture symlink or renamed file cannot redirect an authorized read/write outside its root |
| Secrets and cryptography | Secret owner, minimal scopes, storage, environment/argv/log/URL exposure, refresh, rotation, revocation, recovery; standard crypto libraries | Synthetic secret never reaches unintended outputs/children; revoked material stops working without losing the new credential |
| Data lifecycle and privacy | Collection, retention, exports, deletion, caches, logs, backups, analytics and subprocessors | Deleted access stays deleted in caches and restores; an export includes only the requesting subject's permitted data |
| Desktop and native | Renderer/preload/main, IPC sender and operation, navigation, protocol links, permissions, debug interfaces, runtime modes and entitlements | A child frame, preview or unexpected deep link cannot invoke a privileged operation; verify the packaged binary separately |
| AI tools and plugins | Untrusted instructions, tool scope, approvals, connector grants, sandbox, egress, retrieved memory and output handling | A malicious fixture document cannot authorize a send, secret read or cross-project action; a resumed job retains the original restrictions |
| Dependencies and build | Lockfiles, transitive reachability, lifecycle scripts, action pins, runner trust, PR credentials, caches and artifacts | Untrusted PR/job input cannot obtain a signing credential or write the release candidate |
| Distribution and updates | What actually ships, signatures and trust roots, manifests, channel/architecture binding, downgrade policy, provenance verification | Tampered, wrong-target, missing-signature and disallowed older artifacts are rejected; a valid update still installs in a disposable build |
| Infrastructure | Actual ingress, IAM, storage exposure, network/service bindings, origin protection, environment separation, debug/admin routes | Read-only live metadata agrees with the intended target; test credentials cannot reach production authority |
| Abuse and cost | Email/SMS/AI/upload/compute spend, account creation, recipient limits, cardinality, concurrency, queues and budget enforcement | A small synthetic test spans two workers and restarts; a local memory counter is not reported as a global spending limit |
| Detection and response | Useful security events, redaction, alert owner, escalation, dependency advisories and incident containment | A harmless denied operation produces the expected redacted event; an authorized test alert reaches its owner |
| Recovery and continuity | Backup isolation, restoration, revoked identities, release rollback, signing-key loss, break-glass access | Restore synthetic data in isolation and verify integrity, access policy and recovery time; the existence of a backup job is insufficient |

## Select a useful depth

- **Narrow repair:** the touched boundary, its legitimate path, one credible denial
  path, and affected restart/error states. State what was excluded.
- **Pre-launch review:** map every row, test exposed high-impact paths, inspect the
  distributable and runtime settings, and identify operational owners.
- **Deep review:** add independent attack-path review, realistic role combinations,
  concurrency/recovery tests and staging exercises the owner authorized. Arrange
  specialist review for custom cryptography, native memory corruption, complex
  identity protocols or regulated assurance beyond the agent's evidence.

Coverage expands with evidence and authority, not with alarming scanner counts.
Open source distribution, public client identifiers and verification public keys are
not secret exposure. Missing server controls are not repaired by hiding their names.

## Method routing

Use W1 for identity/sessions, W2 for authorization, W3 for workflows, W4 for
parsing/browser, W5 for outbound requests and W6 for files in
[web/API methods](web-api-tests.md). Use D1/D2 and A1–A4 in
[desktop/agent methods](desktop-agent-tests.md). Use C1–C5 in
[cloud/release methods](cloud-release-tests.md) for infrastructure, supply chains,
distribution, abuse and recovery. Data-retention/privacy and specialist protocol
coverage require a target-specific method; this menu alone does not verify them.
