# Web and API test methods

Choose applicable cards. Each test uses synthetic data and the finite limits in
[engagement](engagement.md). Capture effects at the service/store boundary and say
when proxies, identity providers, browsers or external services are simulated.

## W1: Authentication, sessions and recovery

**Setup:** identify the session issuer, verifier, storage, cookies, refresh endpoint,
recovery/linking flow and intentional validity window. Use a legitimate fixture
session first; inspect actual browser cookies and transport only in an authorized run.

**Change:** omit/expire the session; log out then replay it; revoke the user and
retry through another instance and after restart. For signed tokens alter the
signature, issuer, audience and purpose independently. Never obtain real stolen
tokens. For recovery, reuse/expire a fixture link and try linking to an already
owned account. Verify that failed state/PKCE/redirect checks create no session or
account link using the provider's supported test path.

**Observe:** protected data, session records, refresh issuance and linked accounts,
not just a logout screen. Service unavailability must not grant new access. Retain
a legitimate sign-in/refresh test. Document intentional short-lived access windows;
judge them against the stated policy rather than assuming immediate global invalidation.

**Mapping:** ASVS v5.0.0-7.4.1/7.4.2 (termination/disabled users, L1),
v5.0.0-9.1.1–9.1.3 (token integrity/algorithms/keys, L1),
v5.0.0-9.2.1 (validity, L1), v5.0.0-9.2.2/9.2.3 (purpose/audience, L2).
[WSTG v4.2 SESS-06](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/06-Session_Management_Testing/06-Testing_for_Logout_Functionality/)
supplies a logout replay method.

## W2: Object, field, function and tenant authorization

**Setup:** two test principals with known disjoint objects and roles. Establish an
allowed read/write/export. Include nested objects, search, downloads and background
workers actually reachable from the selected operation.

**Change:** exchange the object/tenant identifier; add a protected field; invoke an
admin function as a member; revoke membership between enqueue and execution. Try a
missing identity too. Random IDs reduce discovery but do not authorize access.

**Observe:** returned fields, rows changed, exports created, notifications and job
output. A 403 emitted after a write fails this test. Reopen persistence to check
that denial was durable. Follow the originating principal to the final worker;
a trusted intermediary must not accidentally lend its broader access.

**Repair/retest:** enforce current ownership/role at the trusted effect owner,
preserving allowed operations. Whether revocation is immediate is a policy question;
test the declared window, queued work and stale caches explicitly.

**Mapping:** ASVS v5.0.0-8.2.1/8.2.2 (function/object, L1),
v5.0.0-8.2.3 (field, L2), v5.0.0-8.3.1 (trusted enforcement, L1),
v5.0.0-8.3.2/8.3.3 (immediate changes/originating principal, L3),
v5.0.0-8.4.1 (tenancy, L2).
[WSTG v4.2 ATHZ-04](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References/)
informs the known-object comparison. Higher-level requirements are risk choices,
not automatically mandatory for every product.

## W3: Business transitions, webhooks and concurrency

**Setup:** write the permitted state transitions and the authoritative values for
price, entitlement, ownership and approval. Establish one legitimate transition.

**Change:** skip/reorder/cancel a step, replay a delivered event, change the payload
under the same idempotency key, or run two bounded concurrent fixture requests.
For webhooks check the exact raw-body signature path and freshness/replay policy;
use fixture keys and the provider's documented scheme, not hand-written crypto.

**Observe:** the ledger/payment/message/job count and durable final state. A UI
blocking a button is insufficient. Check restart and delayed delivery. If an
external send succeeds just before a crash, a local "sent" flag alone cannot prove
exactly-once behavior; examine downstream idempotency or reconciliation.

**Repair/retest:** use server-owned transitions and an atomic check-and-set on every
transition that spends, grants or sends.
Repeat both valid and invalid sequences, including retries after an error.
[WSTG v4.2 BUSL-06](https://wstg.owasp.org/v4.2/4-Web_Application_Security_Testing/10-Business_Logic_Testing/06-Testing_for_the_Circumvention_of_Work_Flows/)
informs workflow testing; the concurrency/webhook examples are our extensions.

## W4: Parsing, injection and browser origin boundaries

**Setup:** trace one untrusted value through parsing, validation and the actual SQL,
shell, template, HTML or deserialization sink. Use inert markers with no network,
file destruction or shell effect. Compare a valid input and one malformed input.

**Change:** submit unexpected types, duplicate parameters and syntax characters;
exercise the actual output context in an isolated browser if markup is involved.
For cookie-authenticated mutations test a second origin and the CSRF mechanism.
Test CORS separately: it controls browser reads and is not server authorization.

**Observe:** generated query/argv or fake sink calls, rendered DOM and persisted
changes. Parameterization and context-appropriate encoding are positive evidence;
keyword matches are not. An error must not expose fixture credentials or traces
containing private payloads. CSP is defense in depth, not proof a sink is safe.

**Repair/retest:** preserve data as data using the framework's supported APIs.
Recheck valid Unicode, quoting and expected formatting. Investigate parser-specific
bypasses with current primary documentation rather than inventing a universal regex.

## W5: Outbound requests and redirects

**Setup:** map who controls URLs, which destinations are intended, credential headers,
redirects, DNS and the actual connect operation. Use injected resolver/transport
fixtures; do not contact cloud metadata or private hosts to prove the point.

**Change:** wrong scheme, userinfo, forbidden address, mixed allowed/forbidden DNS
answers, destination change on redirect and resolution change before connection.
Test retries/fallbacks. An allowlisted spelling is not evidence of the connected IP.

**Observe:** attempted destinations and headers, including denied hops. Check byte,
time and redirect limits. The legitimate endpoint must still work with TLS hostname
verification. Avoid a repair that re-resolves after checking or disables certificates.

**Repair/retest:** enforce the intended destination policy at connection time; bind
validation to the address actually used, and either reject redirects or enforce the
same policy on each hop without forwarding unintended credentials. Product-specific
private destinations require an explicit policy, not a blanket "all private is bad".
Basis: [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html).

## W6: Uploads, downloads and filesystem effects

**Setup:** disposable directories, authorized and unauthorized identities, sentinel
files outside the allowed root, and strict byte/count/decompression limits.
Establish a permitted upload and retrieval.

**Change:** filename traversal, absolute paths, symlink/rename before open, mismatched
content type, archive entry escaping its destination and a small over-limit stream.
Use deterministic hooks for races, not destructive stress. Check ownership again at
download; MIME validation does not establish permission to read someone else's file.

**Observe:** which file handle was opened, storage allocation, extracted paths,
cleanup on errors and later retrieval. String containment before a later open can
race. A random download grant is not proof that the open is contained.

**Repair/retest:** use platform-supported safe-open/containment primitives and verify
them on the target OS. Retain intended uploads, names and downloads. A mock filesystem
test cannot establish race resistance in the real filesystem.

The ASVS references above are a partial mapping to the reviewed
[5.0.0 chapters](sources.md); never report them as ASVS conformance.
