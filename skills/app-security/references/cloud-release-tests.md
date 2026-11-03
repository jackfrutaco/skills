# Cloud, release and operational test methods

Use read-only metadata first. Local declarations express intent; live reads establish
only the account, resource and time actually observed. Never change credential owners
to bypass an unavailable host operation.

## C1: Effective deployment authority

**Setup:** identify the deployed service/resource ID, environment, public ingress,
service bindings, storage and credential owner. Compare admitted metadata with the
configuration. Distinguish resource permissions from network reachability.

**Change:** in authorized fixtures/test accounts, attempt a different resource and
write with a read-only identity. Inspect public storage/listing, admin routes,
origin bypass, debug interfaces and cross-environment bindings.

**Observe:** actual access decisions. An inaccessible dashboard is unknown, not a
secure default. Do not enumerate unrelated customer resources. If only a config file
is available, report source intent and name the missing live evidence.

Provider example: [Cloudflare API token guidance](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
distinguishes permission groups, operations and resource scope; optional lifetime/IP
restrictions are additional constraints. This is a review criterion, not an
instruction to create a token, reconnect or switch away from a shared connection.
Other providers need their own current primary guidance.

## C2: Build dependencies and untrusted changes

**Setup:** inspect lockfiles, build inputs, dependency lifecycle scripts, CI triggers,
runner trust, cache writes and signing permissions. Select a reachable advisory or
suspicious source-to-sink path, not every audit warning as a confirmed incident.

**Change:** model a fork/PR-controlled branch, filename, build argument or cache entry
reaching a privileged job. Use a synthetic build with no signing credentials if
execution is authorized. Check whether an untrusted contributor can change both the
artifact and the verification policy in the same unreviewed path.

**Observe:** which commands execute, credential boundaries and candidate bytes.
Separate dependency presence, affected version, runtime reachability and impact.
No automatic audit-fix, full dependency upgrade, remote source upload or production
build. Record advisory freshness and unsupported ecosystems as limitations.

## C3: Artifact and update consumption

**Setup:** identify the exact built bytes, trusted key/builder/source, expected
channel/architecture and the consumer that must reject invalid artifacts. A public
verification key is intentionally public; it is not a signing credential.

**Change:** alter bytes; use a valid signature with a wrong artifact/digest, builder,
source, target or channel; remove the signature; exercise the stated downgrade policy.
Use fixture signing keys and a disposable installer. Keep a valid install/update case.

**Observe:** rejection before execution/replacement and continued ability to use the
prior valid version. Check the actual shipped verifier and trust configuration,
not just a helper unit test. A generated attestation is not consumer enforcement.

Basis: [SLSA 1.2 artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts)
checks trusted builder/signature, artifact digest and expected build parameters.
Our update/channel/rollback cases extend that reasoning; passing them establishes
no SLSA level.

## C4: Abuse, resource exhaustion and money

**Setup:** identify the expensive effect and all ways to request it. Record actor,
recipient/resource, account and global limits, queue depth, concurrency, byte and
retention bounds. Determine whether client address headers come from a trusted proxy.

**Change:** with a fake billed sink and small limits, vary recipient/account/address,
span two workers, restart one, and retry a request. Check direct-origin access if the
architecture relies on a proxy. Cap total attempts; never measure real maximum harm.

**Observe:** downstream attempts/cost units, durable shared accounting, bound-state
cardinality, retry behavior and legitimate demand. A per-IP in-memory counter may
be a useful layer without being a service-wide budget or recipient-abuse control.
Repairs should preserve intended anonymous use or explicitly identify the product
tradeoff. Distributed failure behavior and billing controls need real service evidence.

## C5: Detection, secrets and restoration

**Setup:** synthetic records, a revoked fixture principal, a disposable backup and
an authorized alert sink. Record recovery objectives and evidence retention.

**Change:** emit a harmless denied operation, rotate a fixture secret, restore a
snapshot into isolation and try the previously revoked identity. Interrupt restore
or withhold a fixture decryption key to test a recoverable error.

**Observe:** useful redacted events, actual alert delivery, replacement credential
success, old access failure, integrity and recovery time. Deleting a leaked value
from source is not revocation. A backup job succeeding is not a restore test.

See [operations](operations.md) for containment and disclosure boundaries. Test
notification/incident ownership only with an authorized destination; do not contact
customers, erase evidence or rotate live credentials merely to finish a report.
