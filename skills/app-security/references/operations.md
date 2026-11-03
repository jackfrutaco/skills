# Operations, incidents and recovery

## A suspected leak or intrusion

Establish the affected asset and whether harm may be ongoing. Preserve a minimal,
private record: times, relevant event IDs, affected credential identifiers, version
and observed effects. Never copy secret values into the report. Do not erase logs,
rewrite history, wipe devices or run an unfamiliar “cleanup” script.

Identify the authorized operator and the admitted account route. Prepare containment
that names affected consumers, interruption risk, rollout, verification and rollback.
Execute only containment already authorized by the user and host. For exposed
credentials, stopping old access matters; deleting a local file does not revoke it.
Confirm the replacement works and the old credential is rejected, including cached
sessions, workers and queued jobs. Use metadata or a designated test client where
possible, without redisclosing the old secret. An unavailable account operation is
a concrete limitation, not a reason to use another credential owner.

Stay inside authorized disclosure channels. A repository author's request for a
review is not permission to publish an exploitable weakness or contact customers.
Regulatory notification and legal obligations go to the owner's counsel; never
state a notification deadline yourself.

## Secure operation after the patch

Agree on an owner and observable failure signal. Check that logs preserve useful
security events while excluding secrets, unnecessary personal data and raw private
payloads. Restrict access to reports, backups and diagnostic exports. Test alerts
only through authorized destinations with clearly synthetic events.

Give accepted risks an owner, rationale, compensating controls, review trigger and
expiry date. “Accepted” is a decision supported by current authority,
not a synonym for difficult to repair. A code comment can document a past decision;
it does not prove that the risk has been reviewed for the present exposure.

## Prove recovery

Use an isolated restore, synthetic records and a separate test identity. Confirm
that restored data is complete enough for the stated recovery objective, and that
revoked users or credentials do not regain access. Verify backup encryption and key
recovery together; a backup whose key is unavailable cannot restore service.

For update rollback, check the product's intentional downgrade policy and signing
trust. Re-enabling a known vulnerable release may restore availability at the cost
of reopening an exploit. Name that tradeoff and obtain the missing decision.

Reassess after identity, privilege, hosting, dependency, data-retention or release
changes. Provide a review trigger; do not claim to have created monitoring, reminders
or an incident response program unless those actions actually occurred.
