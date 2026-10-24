# Research: practical protection for an online identity

**Follow-up:** [Second review and staged plan](RESEARCH-PASS-2.md) adds 1Password-specific recovery, phone-theft and fake-support protections, plus sponsorship/exit safeguards. It records the project's later preference for 1Password when a paid/sponsored option fits; the initial shortlist below is retained as the first pass, not a current vendor ranking.

## Scope and evidence limits

This is a source-by-source web review, authorized as the alternative to the unavailable specialized research runner. It combines generalized lessons from the earlier tune-up with official standards, government consumer guidance and providers' own documentation. It is not a systematic literature review, an independent audit of vendors, or evidence that any partner has agreed to participate. Pages and plan features can change; verify them at the point of use.

The earlier implementation provides a useful workflow: dependency mapping, preserving mail/recovery continuity, separating attempted from confirmed changes, and verifying the intended sign-in. It does **not** prove universal effectiveness or that every recommended control was implemented. Personal history is excluded from this public-facing package.

## Conclusions

1. **Universal core, conditional modules.** Everyone should be offered a review of account recovery, email/SSO, credentials, authentication, devices, backups and scams. A full coverage ledger routes the additional relevant domains rather than dumping a questionnaire on the person. Government IDs, credit systems, reporting, product availability and consumer law require regional guidance.
2. **One click to begin, not to become invulnerable.** An assistant can ask questions, prioritize and explain. It cannot safely skip identity checks, handle recovery secrets, guarantee compatibility, or independently change every provider's settings. A download/launch can be one click; sensitive actions stay consent-based.
3. **Teach by doing.** If the person lacks a manager, help choose an appropriate built-in or standalone manager, establish its recovery, and save/use one login before scaling up. Do not make them migrate everything first.
4. **Keep the product vendor-neutral.** Keep an adequate existing setup. Offer one suitable recommendation and a reasonable alternative, explain trade-offs, and avoid forced purchases, affiliate incentives or central custody of credentials.
5. **Completion means accounted-for scope, not “secure.”** Every relevant category has a status, evidence and next action; unknown and deferred areas stay visible. No scoring system can establish that an individual cannot be hacked.

## Evidence ledger

| Claim | Primary evidence | Application and limit |
| --- | --- | --- |
| Use long, unique passwords; a manager makes this practical | [ENISA Cyber Hygiene](https://www.enisa.europa.eu/topics/cyber-hygiene) recommends long unique passwords/passphrases, preferably generated/stored using a manager | Applicable broadly. Not an endorsement of a specific vendor. |
| Prefer phishing-resistant authentication where supported | ENISA guidance above; [FIDO Alliance passkeys](https://fidoalliance.org/passkeys-2/) describes phishing resistance and synced/device-bound credentials | Passkeys reduce credential phishing risk, not malware, coercion, malicious OAuth consent or all recovery attacks. Protect the sync identity and backup access. |
| Enable 2SV especially on email and important accounts; save backup access | [NCSC setting up 2SV](https://www.ncsc.gov.uk/guidance/setting-2-step-verification-2sv) explains the extra barrier and safe backup codes | SMS is weaker than other options but better than no 2SV. Do not remove the working method before testing its replacement. |
| Do not impose arbitrary password rotation | [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html), password-verifier requirements: no periodic changes, change when compromise is evidenced | Requirements target credential providers/verifiers, not a consumer compliance checklist. The consumer recommendation is unique credentials and targeted change after compromise/reuse, not monthly busywork. |
| Manager choice must account for devices, MFA and primary credential safety | [Canada Get Cyber Safe: password managers](https://www.getcybersafe.gc.ca/en/secure-your-accounts/password-managers) covers integration, primary password and MFA | The page also suggests memorizing sensitive account passwords and mentions old-password prompts. We do not turn those into universal rules; doing so could increase reuse or contradict the no-arbitrary-rotation approach. Retain independent recovery for the vault instead. |
| A built-in manager is a real option, not automatically inadequate | [Apple strong-password autofill](https://support.apple.com/guide/iphone/use-the-passwords-app-iphf9219d8c9/ios); [Google Password Manager](https://support.google.com/accounts/answer/6208650) document generation/storage and use within their ecosystems | Check actual device/browser mix, sync account protection, recovery and sharing needs. These sources are not cross-platform comparative security audits. |
| A no-cost standalone option exists | [Bitwarden plans](https://bitwarden.com/help/password-manager-plans/) lists free core features including unlimited login storage, generator and access across devices | Some features such as emergency access and certain reports are paid. Do not promise every feature is free or require self-hosting. [Official getting started](https://bitwarden.com/help/getting-started-webvault/) supplies the current setup path. |
| Credit freezes are region-specific and not the same as alerts | [US FTC freezes and fraud alerts](https://consumer.ftc.gov/articles/what-know-about-credit-freezes-fraud-alerts) explains free freezes at all three bureaus, versus an initial alert via one bureau | Do not prescribe US bureaus worldwide or imply a freeze prevents existing-account fraud. Each action requires consent and private identity verification. |

## Regional routing, not a false worldwide checklist

| Region | Grounded starting point | What this package can honestly claim |
| --- | --- | --- |
| United States | FTC credit-freeze guidance above; [IdentityTheft.gov](https://www.identitytheft.gov/) | Specific evidence for freezes versus alerts; identity-recovery website identified but its JavaScript workflow was not exercised. State/individual eligibility still needs checking. |
| United Kingdom | NCSC 2SV guidance above | Evidence for general protective habits, not proof of current UK credit, police-reporting or identity-recovery procedures. Look those up locally before giving steps. |
| EU/EEA | ENISA consumer guidance above | Shared hygiene guidance, not a single EU consumer reporting or identity-protection procedure. Ask the member country when needed. |
| Canada | Get Cyber Safe manager guidance above | National consumer education verified. Credit freezes, fraud reporting and provincial rules are not established by that page; verify separately. |
| Australia | [ASD/ACSC identity-theft guidance](https://www.cyber.gov.au/guidance/recover-from-identity-theft) surfaced in official-domain search results | Search results identify ReportCyber and IDCARE, but both attempted full-page fetches on cyber.gov.au timed out. Treat detailed local instructions as unverified pending a readable current source. |
| Elsewhere / country withheld | Universal core, then current national cyber authority, consumer protection, financial institution and trusted local support | Do not invent equivalents, collect nationality/ID documents, or mark regional protections complete without evidence. Country can be skipped; unresolved local controls remain unknown. |

This is a starter set, **not researched coverage of every country**. A maintained country pack should record jurisdiction, language, eligibility, official source, last review date, identity-data handling, fees if any, and safe support route. Separate residence from account/provider jurisdiction only when it changes advice. Do not ask immigration status or citizenship as routine intake.

## Recommended partner shortlist

Rankings below are our fit judgments based on public evidence, not independent vendor security ratings. The optimal combination is education/distribution + an optional practical tool + targeted escalation, not one company entrusted with everyone's digital identity.

| Priority / role | Candidate and evidence | Proposed ask | Limit / conflict to resolve |
| --- | --- | --- | --- |
| 1 — Broad education and distribution | [National Cybersecurity Alliance partnership program](https://www.staysafeonline.org/partner) explicitly describes collaboration across nonprofits, education, industry and government, practical resources and awareness campaigns | Review the plain-language flow and explore a small consumer pilot or distribution collaboration | Partnership page includes sponsorship/visibility benefits. Fees, acceptance, global reach and independent editorial review are unconfirmed; do not buy a badge as a substitute for validation. |
| 2 — Accessible password-manager option | [Bitwarden free personal plan](https://bitwarden.com/help/password-manager-plans/) provides the relevant core functions without a paid plan | Review onboarding instructions; explore optional education/support collaboration without exclusivity | A public free product is not a partnership. No nonprofit-specific benefit was established by reviewed sources. Keep built-in and other suitable options. |
| 3 — Authentication education | [FIDO Alliance](https://fidoalliance.org/passkeys-2/) links passkey guidance, design/communication resources and supporting-service information | Technical review of passkey/recovery explanations and links to current educational materials | No partnership commitment, grant, universal provider coverage or right to use branding is established. Standards/education body, not personal incident help desk. |
| 4 — Nonprofit organizational support / paid alternative | [1Password for Non-Profits](https://1password.com/for-non-profits) states eligible organizations may receive a credit, discounted accounts or other support | If the project establishes eligible status, ask about support for facilitators or a pilot | Conditional, not a universally free consumer offer. Eligibility, terms and organization type must be confirmed. Do not assume this project's existing entities qualify. |
| 5 — Targeted escalation | [Access Now Digital Security Helpline](https://www.accessnow.org/help/) and [FAQ](https://www.accessnow.org/help/helpline-faq/) describe free civil-society assistance with mandate-based vetting | Establish an appropriate referral protocol for at-risk civil-society users | Not a universal consumer help desk, nor legal/medical/physical-safety assistance. Never promise eligibility or send personal cases without informed consent. |

Libraries, community organizations, credit unions, employers and digital-inclusion groups are promising **distribution hypotheses**, not researched named partners in this pass. Choose a launch jurisdiction and pilot audience before ranking specific local organizations. Hardware-key makers and paid monitoring/identity services are optional later candidates, not baseline dependencies; neither should steer the guide toward compulsory purchases.

### Partner selection gates

Require transparent cost and eligibility; accessibility and language support; platform/region fit; independently reviewable security and privacy claims; no sale/collection of audit maps or credentials; no mandatory broad OAuth; no hidden affiliate steering; clear support and correction routes; and an exit path without losing access. Confirm permission before using logos or claiming endorsement. No organization has been contacted and no integration has been built.

## What remains to validate

- Independent expert review of the full workflow, especially recovery, coercion and cross-provider migrations.
- Real usability sessions with nontechnical people and accessibility needs; time-to-complete is not yet measured.
- Consumer-chat and developer-host end-to-end runs, with synthetic accounts first and no secrets in transcripts.
- Country-specific packs beyond the limited evidence above.
- Actual partner interest, commercial terms, eligibility and responsibilities.
- Public licensing, release home and maintenance ownership before distribution.
