# Provider breach and account incident guidance

This is a triage and guided-recovery branch, not digital forensics or an autonomous penetration test. Use it when someone receives a breach notice, sees suspicious access/charges, loses control of an account, or asks what a vendor incident means for them. A headline alone does not prove their account is compromised. Historical chat instructions do not authorize current actions.

## For everyone: the next safe question

Ask one short question at a time; skip known answers. Never demand a screenshot, identifier or secret to continue.

1. **“Is it safe to use this device and talk here?”** If monitoring, coercion, malware or physical danger is possible, use the existing safe-device/specialist route before changes that may alert someone. Do not enter new credentials on a possibly compromised device.
2. **“What happened: an official notice, something you noticed, or a news report?”** Independently reach the provider through its known app/site; don't click the message's sign-in link or call its number. Ask for a short non-secret description, not a forwarded inbox or raw logs. Check the notice's scope/date and whether it actually applies to the person's product/account.
3. **“Can you still sign in, and can you reach your recovery email or backup method?”** Identify the actual account/provider using labels. An old runbook, expired address or currently open browser account is not proof of ownership. Preserve working access while planning the next action.
4. **“Are there unfamiliar charges, sessions, recovery changes or connected apps?”** Review authorized metadata, not passwords or message bodies. Missing logs or inaccessible usage data mean unknown, not clean. Escalate suspicious payments promptly to the bank/provider through a trusted channel; never promise reimbursement.
5. **“Does this password or connection also protect another account?”** Reused passwords, SSO, linked apps and recovery dependencies determine what else needs attention. Don't force everyone to rotate every unique password because one provider had an incident. Follow current official guidance for the actual exposure.
6. **“What would stop working if we changed or removed this access?”** Explain consequences and preserve an independent recovery route. Obtain specific approval before a password change, sign-out, revocation, account migration or deletion. For known active abuse, discuss urgent containment and its disruption explicitly rather than waiting indefinitely for a seamless replacement; use provider/specialist help where needed.
7. **“Did the intended sign-in work, and does the provider show the old access removed?”** The person signs in privately in a separate session, keeps the last working session until replacement access is established where safe, and reports only the non-secret outcome. Password changes do not necessarily revoke sessions or connected-app access. Check the actual applicable controls separately.
8. **“What remains unconfirmed, and who can help next?”** Leave a small private summary of known facts, unknowns, changes, unresolved old access, support routes and next actions. Do not claim an incident is closed because one password was changed. Offer a review date, not an invented scheduled reminder.

Avoid a wall of emergency tasks. Show the most urgent action plus at most two next steps. Lack of technical knowledge is not a reason to ask for broader account access.

## Make each change finishable

Track lifecycle facts separately from evidence status:

| Milestone | Non-secret result to establish |
| --- | --- |
| Planned and approved | Exact target, action, consequence, authority and recovery route understood |
| Privately saved | Person confirms required new access/recovery material is stored without sending it to the assistant |
| Activated | Provider confirms the change actually took effect, rather than remaining requested, pending or staged |
| Intended use checked | A completed sign-in or relevant harmless use reaches the correct account |
| Old access retired | Separately authorized retirement confirmed at the issuer, or an explicit temporary-overlap exception with owner, deadline and reason |
| Dependencies checked | Required notifications, integrations and backup/recovery still work, with anything untested listed |

For each milestone use the existing states such as unknown, attempted, user-reported, verified or blocked. “Configured” is not “active”; “active” is not proof the old access stopped working. An entire change is not verified while a required milestone remains unresolved. Deleting a saved item or environment variable does not revoke its provider credential.

Do not test suspicious or leaked credentials. Use the issuer's authoritative revocation/status information where available; a specialist may separately scope a safe test of an owned system. A timeout, DNS error or blocked network is not proof of revocation. The guide never needs the credential itself.

## If the assistant or another tool exposed a secret

Stop capture and automation, do not repeat the secret, and tell the person plainly. Treat a secret exposed in chat, screenshots or tool output as compromised, including a just-created replacement. Guide issuer-side replacement/revocation privately with fresh approval and recovery planning. Do not say deleting a message, clearing a clipboard or hiding a log guarantees erasure from retained copies. A claim that a helper does not print values is not enough to guarantee the whole tool pipeline is safe.

If a vault or provider step is blocked, stop that route. Do not work around a permission denial, scrape private storage, inspect clipboard contents or repeatedly generate new secrets. Preserve the known non-secret state and request the specific person-controlled handoff needed. Confirm the exact browser/account target when resuming, especially after a window switch; avoid simultaneous sensitive changes by multiple helpers.

## Optional developer and owner/operator extension

Only for explicitly authorized systems the person administers. Ask whether they operate websites/apps/cloud infrastructure before showing this section. Do not make an ordinary consumer configure CI, rotate database passwords or conduct adversarial testing. This section scopes review; it does not grant permission to execute changes or testing.

- **Control and dependencies:** map actual account/organization ownership, recovery, billing, credential issuer and intended consumers using minimal labels. Distinguish adding an owner from moving organization or billing. An unfamiliar account context or policy denial is a stop-and-clarify point, not permission to weaken policy.
- **Credential lifecycle:** inventory in-scope credential metadata only. Replace exposed credentials through a person-controlled or already-approved secret workflow that excludes secrets from model/tool output. Separate stored, staged, deployed and in-use states. Identify consumers with copied values versus managed references; changing the source may not update all running consumers. Check with non-secret metadata and authorized application behavior, never printing values.
- **Containment versus availability:** explicitly agree whether to revoke first (accepting disruption) or temporarily overlap credentials (accepting exposure risk). Active abuse may justify urgent revocation. If overlap is selected, assign retirement ownership and a deadline; never let a sign-in check pending from another person silently become permanent exposure. No generic provider upgrade or forced outage without approval.
- **Unused access and spending:** removing a local variable does not invalidate an issuer key. Revoke unused issuer credentials with consent or escalate inaccessible ownership/billing through official support. Prefer least privilege, short-lived credentials and a suitable spending ceiling where supported; verify whether the control is a hard enforcement limit or only a warning/budget alert. Do not guarantee either stops all charges.
- **Exposure and observability:** review intentionally public services, access roles and available audit/usage logs within scope. Missing records cannot prove that data was not read. Narrow exposed services only after checking dependencies and approval. Preserve evidence; choose privacy-safe logging, not full secrets or personal request content.
- **Application and release review:** if appropriate, scope a separate review of authorization/private-data boundaries, token/link scope and lifetime, resource-exhaustion defenses, untrusted input handling, payment-webhook authenticity and authoritative state, CI/dependency provenance, deploy permissions and telemetry redaction. Confirmed product defects need qualified remediation and tests; this skill is not a substitute for that engagement.
- **Activation and recovery:** identify the exact release/environment, restart/redeploy needs, expected interruption and rollback/forward-recovery plan. Re-check fresh facts before cutover. Preserve a secure recovery path; never quietly restore a known-exposed credential as a rollback. A passing CI job or successful upload does not prove that production uses the fix.
- **Real acceptance checks:** check authorized sign-in methods, email delivery and relevant integrations end-to-end with synthetic/harmless data where possible. Check backups after credentials change, including a harmless restore into an isolated location. No real payments, production-data copies or forced account recovery as generic tests. Report untested features explicitly.
- **Temporary access and sign-out:** if separately approved, narrow scope and expiry for temporary roles/keys, record their removal, and distinguish auth sessions from queues/caches before any invalidation. Do not substitute a whole-cache/database flush for a scoped session operation.
- **Coordination:** one accountable owner per sensitive change, an agreed window when needed, and a non-secret handoff recording current state, authority, interruption risk and next check. Imported approval is not standing authority. Do not deploy or revoke while another helper is performing a dependent change.

Close the review with separate containment, replacement activation, old-access retirement, functional recovery and unresolved-risk states. No blanket “everything is secure” or “no compromise” conclusion follows from a checklist or a lack of visible alerts.
