# Coverage areas

Twenty-one areas the review can touch. Use the ones that fit the person and mark the rest not applicable, with a reason. Every area starts as unknown, and an area is only verified when every account or device in it passes its check. Notes use labels such as "main email" or "bank A", never real addresses or numbers.

## 01 Scope and safety

What matters to them, who could realistically cause harm, which accounts are theirs, whether this device and chat are safe, budget and accessibility. Find important accounts by everyday use (email, messaging, shopping with saved cards, banking, government, health, work) rather than asking for a full list. Accounts and devices managed by an employer go through their IT. Higher-risk people may need a specialist, not more settings.

## 02 Recovery

What unlocks what: email, password manager, phone number, "sign in with" accounts, passkey sync, trusted devices, backup codes, recovery contacts. Look for loops (the vault's password lives only in the vault; the email's 2FA lives only in the vault) and single points of failure (one phone holding everything). A second device in the same bag isn't independent.

**Check:** they can describe how they'd get back in with the phone lost or the vault locked. Never trigger a real reset to test it.

## 03 Email and sign-in providers

Main and recovery inboxes, Apple, Google and Microsoft accounts, anything used to sign in elsewhere. Review 2FA and recovery methods, signed-in devices, forwarding, filters, delegates, app passwords and connected apps. Forwarding or recovery changes they don't recognize are a warning sign.

**Check:** settings reviewed, a real sign-in works and recovery is reachable. "2FA is on" alone isn't enough.

## 04 Password managers

Long unique passwords in a reputable manager. Keep one that already works; don't migrate for its own sake. If they need one, offer one fitting pick plus an alternative:

- **A built-in manager** (Apple Passwords, Google Password Manager) when it covers all their devices.
- **1Password**, this project's preferred paid option, when it fits. Sponsored access may become possible, but none is confirmed: call it proposed until it is. The person owns their account; no sponsor or project ever sees their vault or recovery details. Never put unrelated people into a project-owned family account; decline that and offer their own account or a free option. Before relying on a funded plan, they should know how long it lasts, what renewal would cost, and how to keep or export their data if it ends. (1Password says cancelled accounts can still view and export data if not deleted.)
- **Bitwarden** as a free option.

**Setup, once they've chosen and said yes:**

1. Get the app from the official site or store, not an ad, a message or a caller.
2. They create the account password privately. With 1Password, the account password, Secret Key / Emergency Kit, recovery code and 2FA are different things; explain which does what.
3. Make sure getting back in doesn't depend only on the vault or the phone. Never keep the vault's only 2FA inside the vault. A 1Password recovery code needs access to the account email and leaves 2FA on; don't trigger recovery as a test.
4. Practice with one low-stakes login: keep the old session open, save the new password, sign in fresh to confirm it reaches the right account.
5. Then move important and reused passwords first, gradually. No exports through chat, and no rotating every unique password just to show progress.

**Check:** a real login works from the manager, reused or exposed passwords on important accounts are dealt with, and recovery is understood.

## 05 2FA, passkeys and sessions

Prefer passkeys or security keys where supported, then authenticator apps, then SMS. SMS beats nothing; don't remove it until a tested replacement works. Synced passkeys, device-bound passkeys and physical keys are different things. Codes stored in the password manager are convenient but share its risk. Hardware keys: two, stored apart, after checking compatibility and recovery. Old sessions, app passwords and tokens can survive a password change.

**Check:** the intended method was used in a real sign-in and the backup method works.

## 06 Old addresses, aliases and domains

Accounts still tied to an email address or domain they can't reach, mistyped or expired. Don't send resets to lost addresses; use official recovery. Aliases are optional and don't fix a compromised inbox. For their own domain: registrar 2FA and lock, renewal, payment method, DNS access.

Changing a login email: the new address receives mail → approved change → the provider confirms → sign in to the same account → recovery and billing email checked. Keep the old address working until nothing depends on it.

## 07 Phone number and carrier

Carrier account password and 2FA, account PIN, number-transfer (port-out) lock, SIM-swap protection, voicemail PIN. A SIM PIN isn't a port-out lock. Never test by attempting a transfer, and never record the PIN.

## 08 Phones and computers

Supported OS and automatic updates, disk encryption (FileVault, BitLocker), screen lock, limited admin use, built-in malware protection, app permissions, remote-access tools. For a stolen unlocked phone: Apple Stolen Device Protection or Android theft protection and Identity Check where supported, lock-screen previews, and how to reach Find My or Find Hub from another device.

If a feature isn't available or biometrics don't work for them, suggest what does work (a solid screen lock, independent recovery). Don't call it a failure, recommend a new phone, or tell them to leave a protection off. Don't test by wiping or remote-locking.

## 09 Browsers and extensions

Review extensions by publisher, permissions and need; remove only with a yes. Trim camera, microphone, location and notification permissions. Avoid competing password stores, and don't delete saved passwords until the new manager is confirmed working.

## 10 Backups

Irreplaceable files backed up somewhere independent; sync alone can copy deletions or ransomware. Check the backup account's security and last successful run, and recheck after changing passwords it uses.

**Check:** restore a harmless sample to a separate location.

## 11 Money and payment fraud

Alerts for sign-ins, payments and new payees; authorized users and linked apps, at a high level, without balances or account numbers. Confirm changed payment details through a channel they already know. The person does all transactions and bank identity checks. Suspicious transfers go to the bank's known fraud line quickly.

## 12 Identity and credit

Use a country they've shared; if they declined, don't ask again. Credit freezes are in scope where they exist. In the US: free freezes at Equifax, Experian and TransUnion, each placed separately and lifted temporarily to apply for credit. A fraud alert is different, and a freeze stops new-credit fraud, not misuse of existing accounts. Elsewhere, use local official sources and don't assume an equivalent exists. Never collect ID numbers or documents. Paid monitoring isn't a freeze.

## 13 Scams and impersonation

A convincing voice, video or spelling doesn't prove who's asking. For urgent money or account requests: pause, hang up, and contact them through a number or app you already know. Never use the link or number in the message. No legitimate service asks for your codes or for you to approve a login prompt. Fake security pop-ups, renewal emails and search-ad "support" are common; an unexpected helper asking for remote access, or to move money "to keep it safe", is a stop sign. A family code word helps but isn't enough alone. Practice with an invented scenario, never a real phishing test.

## 14 Connected apps, AI agents and developer access

Apps with access to email or files, AI tools and agents, MCP servers, agent skills, API tokens and SSH keys. Prefer narrow, read-only, expiring access, with a human approving sending, deleting, paying or running code. Installing a skill or plugin is a trust decision. For an exposed token, revoke it at the issuer with consent; a replacement is done only when the new one is active, the old one no longer works, and everything that needs it still works. Spending limits may only warn rather than stop charges.

**For developers and admins, when relevant:** map who owns the accounts, billing and credentials; keep secret values out of model and tool output; track stored, deployed and in-use separately; decide explicitly between revoking now (risking an outage) and a short overlap (risking exposure), with an owner and deadline; separate development and production credentials; check sign-in, integrations and backups end to end after changes. A passing CI job doesn't prove production uses the fix. Code and infrastructure reviews need their own scope.

## 15 Sharing and privacy

Shared links, location sharing, photo metadata, social visibility, linked messaging devices, lock-screen previews. If stalking or coercion is possible, stop before any change that notifies someone. Data-broker opt-outs are optional and vary by region.

## 16 Home network and smart devices

Router updates, a unique admin password, WPA2 or WPA3, remote admin off, WPS and UPnP off if unneeded, a guest network for smart devices. Make sure essential devices reconnect after changes. A VPN doesn't replace updates or 2FA.

## 17 Household and emergency access

Emergency or legacy access through providers' own features rather than shared passwords, and only when safe. Children and shared devices need age-appropriate consent, never covert monitoring.

## 18 Domains and small-business infrastructure (optional)

Registrar and DNS roles, mail routing, SPF, DKIM and DMARC (check real senders before tightening), renewal, emergency admin access, billing and backups. Not applicable for most people.

## 19 Cryptocurrency (optional)

Trusted wallet sources, transaction and approval risks, offline recovery. Never see a seed phrase, connect a wallet, or sign or move anything. Suspected seed exposure needs wallet-specific specialist help.

## 20 Unused accounts and data

Old accounts, subscriptions and integrations. Check what depends on them first. Deleting an account may not cancel an app-store subscription, and removing app access may not delete data. Each deletion is its own yes.

## 21 Incident readiness and maintenance

A short lost-phone and hacked-account plan with known official contacts, kept somewhere other than the phone or vault. For a breach notice: confirm it independently, work out what's affected, contain with consent, check the new access works, retire old access, and list what's still unknown. A changed password doesn't close an incident. Agree a review date and the events that should trigger one: a new phone or number, a breach notice, a lost key, a move, a household change, or a sponsored plan ending.

## Official sources

Check the provider's current help for the person's platform and country before giving menu steps.

- General: [CISA Secure Our World](https://www.cisa.gov/secure-our-world), [ENISA cyber hygiene](https://www.enisa.europa.eu/topics/cyber-hygiene), [UK NCSC 2-step verification](https://www.ncsc.gov.uk/guidance/setting-2-step-verification-2sv), [FIDO Alliance passkeys](https://fidoalliance.org/passkeys-2/), [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) (written for providers, not a consumer checklist).
- US identity and scams: [FTC credit freezes and fraud alerts](https://consumer.ftc.gov/articles/what-know-about-credit-freezes-fraud-alerts), [IdentityTheft.gov](https://www.identitytheft.gov/), [FTC tech-support scams](https://consumer.ftc.gov/articles/how-spot-avoid-and-report-tech-support-scams).
- Devices and accounts: [Google 2-Step Verification](https://support.google.com/accounts/answer/185839), [Apple Stolen Device Protection](https://support.apple.com/guide/iphone/use-stolen-device-protection-iph17105538b/ios), [Android theft protection](https://support.google.com/android/answer/15146908).
- Password managers: [Apple Passwords](https://support.apple.com/guide/iphone/use-the-passwords-app-iphf9219d8c9/ios), [Google Password Manager](https://support.google.com/accounts/answer/6208650), [1Password recovery codes](https://support.1password.com/recovery-codes/), [1Password billing policy](https://support.1password.com/membership-billing-policy/), [1Password for non-profits](https://1password.com/for-non-profits), [Bitwarden plans](https://bitwarden.com/help/password-manager-plans/).
