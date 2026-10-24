# Second review: making everyday protection complete enough to use

## Decision and method

**Product direction:** make 1Password the preferred paid/sponsored setup path when a person needs a manager and it fits their devices, accessibility and budget. Keep an adequate existing manager, a built-in option and a free-core alternative. This is the project's chosen direction, **not evidence that 1Password is universally the safest or easiest product**.

This was a **direct review of six primary sources, not the bounded multi-agent run**. It extends the earlier [research](RESEARCH.md) and generalized tune-up lessons; it does not replace them or claim a comprehensive worldwide survey. Confidence below means confidence in the cited statement, not a security rating or proof about a person's account. No accounts, recovery flows, purchases or partnerships were activated.

## Sources read in this pass

| ID | Primary source | Supported finding | Confidence and limit |
| --- | --- | --- | --- |
| S1 | [1Password: Generate and use recovery codes](https://support.1password.com/recovery-codes/) | Personal/family recovery codes require access to the account email. Recovery changes the account password and Secret Key, requires device sign-in again, and leaves existing 2FA enabled. Codes are reusable; generating one does not activate recovery. Teams/business use different recovery arrangements. | High for documented behavior. No live recovery test; current account type and instructions must be checked. |
| S2 | [1Password for Non-Profits](https://1password.com/for-non-profits) | Depending on account type and situation, an applicant may qualify for a one-time credit, discounted accounts or similar support. | High that the conditional program is advertised; **unknown** eligibility, consumer vouchers, size/duration of support or willingness to sponsor this project. |
| S3 | [1Password subscription billing](https://support.1password.com/membership-billing-policy/) | After cancellation/freeze, users can still sign in to view/export data if they have not deleted the account. Representative-managed subscriptions require consultation on their terms. | High for stated general policy, not a promise of unchanged daily features, a guarantee of access after credential loss, or a substitute for negotiated sponsorship terms. |
| S4 | [Apple: Stolen Device Protection](https://support.apple.com/guide/iphone/use-stolen-device-protection-iph17105538b/ios) | Supported iPhones can require biometrics without passcode fallback for protected operations and delay sensitive changes. Settings include away-from-familiar-locations or always. | High for the documented feature. Not every action is protected; compatibility, biometric accessibility and delays must be considered. |
| S5 | [Google: Protect personal data against theft](https://support.google.com/android/answer/15146908?hl=en) | Theft-lock features, Identity Check, Remote Lock, lock-screen privacy and Find Hub reduce specific theft risks. Support varies; Remote Lock has screen-lock, SIM, verified-number, Find Hub and connectivity prerequisites. | High for documented feature conditions. Detection is not guaranteed; unsupported devices are not a failed user. The guide identifies exceptions, including some Chrome autofill behavior. |
| S6 | [FTC: Tech support scams](https://consumer.ftc.gov/articles/how-spot-avoid-and-report-tech-support-scams) | Fake warnings, renewal notices, search results and ads can direct people to impostors seeking remote access or payments. Use independently known support routes, not the number in the warning/message. | High for documented scam patterns. The protective habit generalizes; FTC reporting is US-specific. |

## What the first framework missed or under-specified

The first pass already named most categories. The main gap was **operational detail**, not a need to add dozens of extra checkboxes.

| Gap | Why it matters | Addition to the guide | Basis |
| --- | --- | --- | --- |
| A vault recovery code is not an independent recovery plan | Someone may have a code but no access to the email or second factor needed to use it | A 1Password-specific setup/recovery branch, checking email and MFA dependencies independently; no live recovery as a test | S1, high |
| An unlocked stolen phone is different from a lost locked phone | Screen lock and MFA alone do not address all actions a thief can take after observing a passcode or taking an unlocked device | Ask about theft settings, lock-screen notifications, safe device-finding access and biometric usability; inspect supported settings, do not perform a remote lock/wipe drill | S4–S5, high |
| The guide itself can resemble a scam | A person taught to install tools or follow helpers can be redirected to fake support | Teach a no-surprise-contact rule, independent official routes, and one fake-renewal/support tabletop; this project never requests remote control to inspect secrets or a payment to “protect” money | S6; application to this product is a design judgment, medium |
| Sponsorship can create a new dependency | A funded trial can end, renewal can cost money, and organizational enrollment can alter recovery/ownership | Explain term, renewal consent, who controls the account, and a safe exit before onboarding; do not put unrelated recipients into a project-managed family/business vault by default | S1–S3 for differences/policy; proposed safeguards are design requirements |
| “All accounts” was too abstract | People do not remember every service when asked a broad question | Ask by use-case: communication/social, shopping with saved payment details, finance, government/tax/benefits, health, work/school, and any other high-impact service. Use labels, not full account inventories or exports | Design judgment based on the coverage review; not a measured detection rate |
| Household help needs boundaries | A helper's convenience must not become access to everyone's personal secrets | Ask whose device/account it is, what is actually shared, and whether a helper is safe. Keep individual ownership and explicit sharing; use current vendor guidance for recovery roles | Existing safety protocol; no new claim that a provider supports every desired sharing model |
| Finishing setup was easier to count than continued usefulness | Installing a manager does not prove routine autofill, recovery or habit change | Add acceptance gates for safe save/use, key-account changes, harmless restore and a lost-phone tabletop; unresolved controls stay visible | Design judgment; usability and real-world effectiveness not measured |

## A simple staged plan for an average person

These are dependency-based stages, not promises about time or a security score. Ask only the next needed question; each stage may take more than one sitting.

1. **Safe to begin.** Check incidents/coercion, authorized scope, trustworthy device, existing tools and budget. Choose what the person can do today. If a device is unsafe, stop credential setup there.
2. **Keep control of the essentials.** Map phone → primary email/SSO → password manager and recovery in both directions. Establish independent backup access. Set up 1Password if appropriate, using the [guided branch](references/onepassword.md); otherwise preserve the suitable existing/free choice.
3. **Protect daily access.** Guide important accounts to unique credentials and supported passkeys/MFA; address known exposure first. Review device updates, lock, supported theft settings, carrier protections and visible notification content. Test new access in a separate session, keeping the last working one.
4. **Protect money, identity and irreplaceable data.** Review applicable everyday account categories, alerts, backups and a harmless restore. Add local credit/identity steps only with current jurisdiction-specific guidance. Practice rejecting a fake support/renewal request without sending money or granting access.
5. **Close relevant gaps.** Review browser extensions, connected apps/AI, sharing/messaging sessions, home network, emergency helper, unused accounts and optional infrastructure/crypto. Label irrelevant areas with reasons and preserve unresolved work. No bulk cleanup.
6. **Leave a usable handoff.** Minimal private next-actions note, lost-phone/support route, remaining blockers, and optional review date. If subsidized, include funding end date and renewal/exit choice. A completed sitting is not “all secure.”

**Historical first-sitting proposal (superseded):** this research pass originally proposed finishing one protective action early. The current [guided journey](references/journey.md) instead requires discovery → assessment → path/help selection before routine execution. An assessment-only or no-change sitting is valid. The action-oriented stages above are conditional post-assessment coverage, not instructions to steer someone into setup during discovery.

## 1Password sponsorship: promising, but not established

**Best evidenced first contact:** 1Password's published nonprofit-support route (S2). It explicitly mentions possible credits. Whether this project qualifies, whether credits can fund individual/family accounts, and whether a public-benefit pilot can distribute them are all unverified. An existing corporation or a public-good intention does not establish nonprofit eligibility.

**Recommended proposal, not an action already taken:** a limited, independently evaluated beginner pilot with recipient-owned accounts, clear support responsibilities and a finite funded term. Ask about individual/family redemption or another vendor-approved arrangement; do not assume a voucher API or invent one. If the project does not qualify, ask whether an eligible nonprofit can lead the pilot or whether a separate education/access program exists. Do not misrepresent status.

Confirm before offering credits:

- Eligible organization and recipients, countries, languages, supported plans and accessibility.
- Number of recipients, actual discount/credit value, funded period, tax/fee implications and approval process.
- Whether a payment card is required, how renewal works, and explicit opt-in before a recipient incurs a charge.
- Who owns/administers/recover-controls the account; personal vaults must not be pooled under a project-controlled organization merely to obtain seats.
- What happens if the program ends, a person leaves, changes country or needs to switch tools. Explain view/export policy accurately (S3), but don't promise ongoing paid functionality. Any migration is private and provider-supported; do not ask for vault exports.
- What recipient data the sponsor receives, retention, support escalation and deletion. No vault contents, recovery maps, browsing history or identifiable security findings as proof of participation.
- No exclusivity preventing a suitable free choice, compulsory endorsement, hidden referral commission or logo use without permission.

Other potential funders—community organizations, libraries, credit unions, employers or foundations—remain **unverified sponsor categories**, not named committed partners. Earlier NCA/FIDO/Access Now suggestions address education or specialist referral; they are not evidence of credit funding. Do not spend this pass expanding the brand list instead of validating the core flow.

## Questions the next pilot must answer

- Can a beginner finish a useful step without exposing a secret or needing a terminal?
- Can they explain what happens if their phone, inbox or vault is unavailable, without triggering real recovery?
- Does the flow recognize an adequate existing setup and avoid selling an unnecessary replacement?
- Can it handle unsupported theft features, inability to use biometrics, no second device, no budget and a withheld country without getting stuck or shaming the person?
- Does it keep attempted, user-reported and directly verified outcomes separate?
- Does it refuse a fake support caller, a request to paste recovery material, or a sponsor requesting access to personal vaults?
- Does it leave the person with a manageable next step rather than a false green badge?

These are evaluation questions, not claims that a real participant study has happened.

## Remaining uncertainty

The six-source limit leaves carrier-specific controls, OS backup variants, country packs, real 1Password usability, nonprofit eligibility, funding terms, vendor security comparisons and consumer-host behavior unverified in this pass. Earlier evidence still applies only within its original limits. The extra chat reference was not accessible during this six-source review. The person subsequently supplied its exported text; it was read in full and informed the separately documented [incident lessons](INCIDENT-LESSONS.md). Those are historical narrative evidence, not a seventh web source or fresh account verification. No private chat identifiers are included here. No one can certify that this framework covers every possible threat.
