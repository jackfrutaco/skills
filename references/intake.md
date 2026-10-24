# Intake specification: purpose, answers and privacy

This is the shared question specification for the skill and standalone chat guide. A future app may render the same definitions, but no app or data-collection backend is supplied here. The journey defines phase order; this file defines what to ask, why, and how answers affect the assessment. Do not improvise a competing questionnaire.

## Collection contract

- Collect only a missing fact that affects scope, an assessment, a relevant follow-up or a realistic path. Use the question IDs below to avoid duplicates, not to identify the person. This is an adaptive bank, not a mandatory form or a demand for every answer.
- Each row defines a prompt, substantive choices, a short purpose, an eligibility condition and a decision consequence. Minimum collection is the selected category or a short non-secret clarification. A provider name is enough; no address, account name, device identifier or exact location is needed.
- Track **question history separately from protection evidence**. A worksheet's unknown status does not show whether the person has answered. Use the state table below before selecting a row. An explicit request to ask or revisit a safe question selects that question; it does not authorize inspection. Reloading a skill or starting a new model turn does not reset reported answers. An imported historical resume note is different and needs current confirmation.
- Preserve distinct answer states: **unasked**, **reported value**, **reported no**, **answered uncertain**, **declined**, **not applicable with reason**. Protection evidence may remain unknown in several of these states, but only unasked is automatically eligible for another discovery question. No is not unknown. None is exclusive in multi-select. Reports are not independent verification.
- All discovery questions may be skipped. Missing safety/authority or recovery information may block a specific action; explain that limit without requiring disclosure. Country refusal never blocks universal discovery. Do not infer country, technical skill, finances or safe household relationships from a name, platform or provider.
- Never request passwords, codes, private keys, recovery contents/locations, seed phrases, identity documents, actual account addresses, balances, diagnoses, complete account inventories or private incident narratives. Never inspect those materials to make intake easier. Do not record even a volunteered secret; stop collection and use safe exposure guidance without repeating it.
- Use answers only for the requested assessment and authorized guidance in this conversation. Do not create a personal report, analytics event, marketing profile, cross-person dataset or separate upload. A minimal private resume note is optional and user-controlled. An approved storage location does not authorize a full transcript or detailed recovery map. Do not copy participant findings into this repository or share them with other agents by default.

## Select by question history, not an unknown worksheet cell

| Evidence in the conversation | Question state | Next step |
| --- | --- | --- |
| No answer supplied; “we haven't asked”; “ask whether 2FA is enabled, its status is unknown” | UNASKED | Ask the requested or next eligible question. Do not invent a Not sure answer. |
| “I don't know whether 2FA is enabled” or an actual Not sure response | ANSWERED_UNCERTAIN | Keep protection unknown. Do not immediately repeat the question or send the person into settings. |
| A reported value, No, or None | ANSWERED | Preserve the report; follow up only on a different necessary fact. |
| “Skip,” “I'd rather not say,” or a prior refusal | DECLINED | Keep the resulting assessment limit; do not solicit the same disclosure again. |
| The person explicitly asks to revisit or be asked a safe question | REOPENED BY REQUEST | Ask that one question, even if a prior answer was uncertain. This grants no action permission. |

Select **exactly one row per turn**, then stop after its question and answer options. Rows are alternatives for selection, not a batch to display. Only an explicit request for grouped questions permits up to three related rows. A request to continue or for a full review is not a request for grouping.

## Explain privacy without promising secrecy

At an actual new sitting, briefly state the applicable capabilities and this boundary once; do not repeat the full notice after every answer:

> You control what you share. General answers are enough; never send passwords, codes, recovery materials or identity documents. You can skip questions. This guide does not itself connect accounts or collect your answers into a separate database. Your chat host and model provider still process this conversation and may retain it under their settings and policies. A separate report, inspection or change needs your permission.

This describes this guide's behavior, not a guarantee about the host. Never say “nothing is stored,” “only you can see this,” “fully private,” “zero retention,” or “completely secure” without independently established support for that exact claim. Do not claim to have changed privacy settings or disabled training/logging. If asked about a host's exact policy, use current official documentation where available; otherwise state the uncertainty. Do not request account access merely to answer a privacy question. User-selected host privacy controls can reduce some exposure but do not make secret sharing appropriate.

## Delivery and adaptation

1. After safety/scope, calibrate explanation depth and relevant technical responsibilities early, once. If the person already supplied a preference or role, preserve it; do not restart an ongoing intake just to ask a missing preference. Default to concise, respectful language. Being a developer is neither proof of security expertise nor permission to access systems; using a developer host does not establish that role.
2. By default show the row's **Why** as one short sentence before or alongside the question, normally 8–25 words. It must explain a decision, not sell a product. If the person explicitly asks for questions only, omit routine explanations and make the reason available on request; retain critical safety/privacy boundaries. More detail is optional. Use familiar terms such as 2FA directly; explain them when requested or when genuine uncertainty appears, not because someone is a nondeveloper.
3. Select exactly one applicable bank row and use its actual **Question** and **Choices**. Preserve their meaning and count instead of inventing replacements; adapt only an already-known target label. The question itself must be present, even in concise mode: its Why sentence does not replace it. For an UNASKED or explicitly reopened 2FA-status question, ask “Is 2FA enabled on your main email?” with Yes / No / Not sure, including after explaining the term when requested. For ANSWERED_UNCERTAIN, preserve unknown without repeating the question. Do not rewrite that into whether the person remembers using a second step. Stable prompts keep us collecting the intended fact.

   Use 2–4 **substantive answer choices**, not a menu about answering. Never replace Gmail/iCloud/Outlook with “I'll type it / Not sure / Skip.” Questions collect facts, not permission to type. Use real native question controls whenever available, including after explanations and clarifications. Otherwise present the same answers on separate numbered lines. Do not invent buttons.
4. Count the choices before sending. Never append a fifth Declined/Skip/Not sure option; those are answer states, not a reason to ignore the bank's four-choice menu. Host-provided **Enter your own** and **Skip** controls are additional host controls, not choices the agent must duplicate. The 2–4 limit applies to agent-supplied options. Keep a brief standing instruction that the person can type another answer, “not sure,” or “skip.” Where uncertainty is itself a key answer, explicitly include Not sure. Never combine Not sure with Skip, Other or None. Do not fill every menu with escape choices at the expense of useful answers.
5. The bank marks single or multi-select. For multi-select, accept several numbers in text-only hosts and preserve all selections; do not collapse them to the first. Clarify contradictory combinations neutrally using choices. A short clarification still gets actual answers, such as Mac / Windows / Another kind / No computer, not a bare “Did you mean Mac?”
6. Use a short direct-entry question only when the answer space truly cannot be represented meaningfully (for example country or an uncommon provider after Other). Say why and request only the needed non-secret label. Use the host's genuine free-text/custom-answer field or accept the typed reply. Do not add an extra “will you type it?” turn or invent arbitrary country choices. Do not fabricate options simply to satisfy a button rule.
7. Do not substitute login behavior for configured protection. A remembered device can skip a 2FA challenge; a passkey can bypass passwords. Ask about configured 2FA, its methods, and passkeys separately, keeping unknowns unknown. Never ask someone to sign out to answer discovery.
8. Do not turn uncertainty into an instruction to open settings during discovery. Record unknown and continue or offer an explanation. A settings check belongs to a chosen path or an explicitly requested narrow task, with appropriate scope and safeguards.

## Review bank

In the eligibility column, “if unknown” means the fact has not been supplied, not that an actual Not sure answer should be repeated. Apply the question-history table first. For every group, only the listed categories or short provider labels are needed. The common privacy exclusions above apply to every row. The last column says when to ask and how the answer changes the review—not what action is automatically authorized. Adapt singular/plural and known labels, not the meaning of answer states.

### Safety, scope and communication

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| S01 single | Is there an immediate security or personal-safety concern? | No concern; Suspicious activity or lost access; Possible monitoring; Not sure | This tells us whether a routine review is appropriate or safer support should come first. | First unless already answered; concerns/uncertainty trigger safety clarification, not routine changes. No incident details required. |
| S02 single | Whose accounts and devices are we reviewing? | My own; Helping with permission; Both; Not sure | This keeps the review within your authority. | If scope unknown; clarify authority before any inspection or change. |
| S03 single | How much explanation would you like? | Just the questions; Brief context; Step-by-step explanations | This lets me match the detail to you without changing the safety checks. | Early if no preference supplied; never ask about a short-versus-thorough session instead. |
| S04 single | Do you develop software or administer systems? | Neither; Develop software; Administer systems; Both | This helps include relevant technical coverage and skip irrelevant questions. | Early if role unknown; enables optional technical rows, not automatic access or jargon tutorials. |

### Devices and access context

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| D01 multi | What phones do you use for these accounts? | iPhone; Android; Another type; No phone | Device compatibility affects which guidance and recovery options will fit. | If unknown; No phone exclusive; no model/serial requested. |
| D02 multi | What computers do you use for these accounts? | Mac; Windows; Linux or another system; No computer | Cross-device use affects compatibility and independent access. | If unknown/relevant; No computer exclusive. Ask an exact OS/version only later if necessary. |
| D03 single | Are any devices managed by an employer or school? | None; Some; All; Not sure | Managed devices may have policies and protections you cannot change yourself. | If relevant; route managed changes through authorized IT. No employer name needed. |
| D04 single | Are automatic security updates enabled? | All devices; Some devices; None; Not sure | This helps identify possible maintenance gaps without assuming an unsupported device needs replacing. | Personal devices in scope; unknown is not disabled. |
| D05 single | Do your devices use a screen lock? | All; Some; None; Not sure | Screen locks help limit access if a device is lost or left unattended. | If unknown; accessibility/support assessed before suggesting changes. |
| D06 multi | Does anyone else use your devices or know their unlock codes? | Shared device use; Someone knows an unlock code; Neither; Not sure | Shared access changes the privacy and recovery assumptions we can safely make. | After safety; Neither/Not sure exclusive; no names or codes. Recheck safety if a concern emerges. |
| D07 single | Do you use browser extensions? | No; Yes; Not sure | Extensions can have account or browsing access worth considering in the assessment. | Relevant browsers only; number of extensions alone is not a risk finding. No extension inventory yet. |
| D08 single | Is remote-access software installed on a personal device? | Yes; No; Not sure | Remote access may be intentional or a reason for a closer, separately scoped review. | Personal devices only; do not uninstall or infer compromise from Yes. |

### Email, passwords and sign-in

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| A01 single | Which service runs your main email? | Gmail / Google; iCloud / Apple; Outlook / Microsoft; Another provider | Email often recovers other accounts; the provider name helps tailor guidance without your address. | If provider unknown; ask service, not mail app. Another provider may be typed directly. Never infer from device brand. |
| A02 single | Do you use a provider account to sign into other services? | Yes; No; Not sure | Shared sign-in can make several accounts depend on the same recovery root. | Skip if already established; use familiar “Sign in with Google/Apple” examples only if needed. |
| A03 multi | Which sign-in providers do you use? | Google; Apple; Microsoft; Another provider | This identifies shared access dependencies without listing every connected account. | Only after Yes/known use; provider labels only. |
| A04 single | Do important accounts depend on an old email address or phone number you cannot access? | Yes; No; Not sure | An inaccessible recovery contact can cause lockout even when sign-in works today. | If unknown; no address or number requested. Yes informs dependency priority. |
| A05 multi | Where do you store passwords? | Password-manager app; Browser or built-in manager; Notes, documents or paper; Memory | This helps assess the existing setup without assuming it needs replacing. | If unknown; no passwords, screenshots, exports or storage locations. |
| A06 single | Which password manager do you use? | Apple Passwords; Google Password Manager; 1Password; Another manager | Different managers have different compatibility and recovery options. | Only when manager use reported and name needed; adapt common choices to known context without assuming a brand. No vault access. |
| A07 single | Do you reuse passwords across important accounts? | No; Some; Most; Not sure | Reuse can let a compromise of one account affect others. | If unknown; no password samples or identifying account list. |
| A08 single | Do you need to share access with anyone? | No; Family or household; Work or team; Both | Sharing requirements affect which options fit, but do not imply other people are safe or authorized. | If relevant; no recipients' names. Not a request to start sharing. |
| A09 single | Is 2FA enabled on your main email? | Yes; No; Not sure | This establishes the reported sign-in protection before discussing methods or changes. | If UNASKED or explicitly reopened; use 2FA directly unless an explanation is requested. An actual Not sure answer completes the row. Lack of a recent challenge is not No. |
| A10 multi | Which 2FA methods are enabled? | Authenticator app codes; SMS or phone-call codes; Approval prompts; Security keys | Different methods have different recovery dependencies and resistance to phishing. | If 2FA enabled; Other/Not sure may be typed. Do not collapse codes, prompts and security keys into one answer. Never request a code. |
| A11 single | Do you use passkeys for important accounts? | Yes; No; Not sure | Passkeys can change sign-in and recovery without requiring a separate password step. | Separately from 2FA; do not infer a physical key or a disabled factor. Follow up on storage/sync only if needed. |

### Recovery, backups and carrier

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| R01 single | If your phone were unavailable, could you still access your main email? | Yes; No; Not sure | We want to identify lockout risks before recommending changes. | If unknown; ask about access, not codes, contacts or where materials are kept. |
| R02 single | Could you still access your password manager without your main device? | Yes; No; Not sure | Recovery should not depend entirely on the device or vault being unavailable. | Only if a manager exists; unknown is not a failed recovery test. |
| R03 single | Have you configured recovery methods for important accounts? | All; Some; None; Not sure | This identifies recovery coverage that may need attention before account changes. | If unknown; no materials or full account inventory. |
| R04 single | Could you access those recovery methods independently of the affected account or device? | Yes; Some; No; Not sure | Independent recovery helps prevent a circular lockout. | Only if recovery methods exist; no storage locations or secret contents. |
| R05 single | Is important data backed up separately from the original device? | All important data; Some; No; Not sure | A separate backup may reduce data loss if the original device fails. | If data relevant; do not equate sync with recoverable backup. No file contents. |
| R06 single | Have you successfully restored something from that backup? | Recently; Previously; Never; Not sure | A backup's presence does not establish that a restore will work. | Only if backup exists; clarify timing only if it changes the assessment. No restore during discovery. |
| R07 single | Do important accounts use your phone number for sign-in or recovery? | Yes; No; Not sure | Number loss or takeover can affect accounts that rely on it. | If phone-number use relevant; no number or PIN. |
| R08 single | Have you enabled carrier account or number-transfer protections? | Yes; Some; No; Not sure | Carrier protections may reduce unauthorized changes to your number. | If R07 Yes or otherwise relevant; distinguish actual protections later using official carrier guidance. No PIN. |

### Relevant account surface and optional modules

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| C01 multi | Which account categories matter most to you? | Financial services; Work or business; Health or government; Other important accounts | This helps prioritize consequences without collecting your account inventory. | If priorities unknown; no institutions, balances or medical details required. |
| C02 single | Do apps, integrations or AI tools have access to your accounts or files? | Yes; No; Not sure | Connected services may retain access independently of your usual sign-in. | If unknown; no connection inspection or broad OAuth request. |
| C03 single | Do you share account access, files or location with others? | Yes; No; Not sure | Existing sharing changes the privacy and access questions that matter. | After safety; no names or locations; no automatic revocation. |
| C04 single | Are there old accounts or subscriptions you no longer use? | Yes; No; Not sure | Unused access may still have recovery, data or billing dependencies. | If relevant; no deletion or cancellation during discovery. |
| C05 multi | Which additional areas apply? | Home Wi-Fi or smart devices; Domains or websites; Cryptocurrency; Emergency access planning | This keeps optional coverage relevant rather than asking everyone the same technical questions. | Allow None/Not sure through typed/custom answer; activate only selected relevant branches. Never collect seed phrases, addresses or network credentials. |
| C06 single | Would you like country-specific identity and fraud guidance? | Yes; Universal guidance only; Decide later | Local protections vary, but country disclosure is not needed for the universal review. | If not already declined; on Yes ask directly for country using true free text, not invented choices or a typing-permission menu. No address/identity documents. |
| C07 single | Have you received suspicious security or support messages? | No; Yes, unsure about them; Yes, recognized as suspicious; Not sure | This helps decide whether scam-recognition guidance would be useful. | No message upload, sender identity or surprise attack; active loss/fraud routes to safe support. |

### Developer / administrator extension

Ask only for relevant authorized responsibilities, not merely because the host can run commands. Keep language technical and concise when requested; do not assume security expertise.

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| T01 multi | Which systems do you manage? | Repositories or package publishing; Cloud or deployments; DNS or email administration; Other infrastructure | These systems can expose different credentials, data and recovery dependencies. | Developer/admin or explicitly relevant scope only; no company/project/domain identifiers required. |
| T02 multi | Where are development secrets managed? | Secret manager; CI/CD or hosting configuration; Local environment files; Other approach | This distinguishes storage and distribution patterns without inspecting secret values or files. | Only if managing development secrets; no paths, contents, environment dumps or tokens. |
| T03 single | Are development and production credentials separated? | Yes; Partly; No; Not applicable | Separation can reduce the reach of an accidental exposure. | Only where both environments exist; no credentials or infrastructure access requested. |
| T04 single | Have you reviewed tokens, SSH keys and service-account access? | Recently; Previously; Never; Not sure | Old access can persist beyond the task or person it was created for. | Relevant credentials only; no token values, key material or enumeration without separate scope. |
| T05 single | Is independent recovery available for critical administrator accounts? | All; Some; None; Not sure | Administrator lockout can affect the systems and people depending on those accounts. | Relevant admin scope; no recovery material or exact recovery map. |

### Constraints and decision preparation

| ID / mode | Question | Choices | Why we ask | Ask when / assessment consequence |
| --- | --- | --- | --- | --- |
| P01 single | What budget should recommendations assume? | Free only; Paid if worthwhile; No preference yet | Recommendations should be practical without assuming a purchase or sponsorship. | Before assessment if cost matters and not already supplied; not payment consent. |
| P02 single | How much disruption would you consider? | Keep existing tools; Small changes acceptable; Open to larger changes | This helps compare realistic paths without treating change as a commitment. | Before path comparison when relevant; no migration assumed. |
| P03 multi | What matters most to you? | Prevent account takeover; Avoid lockout or data loss; Privacy or unwanted access; Simplicity | Priorities help explain why one path may fit better than another. | If goals unknown; use existing expressed goals instead of asking again. |
| P04 multi | Should recommendations account for practical constraints? | Accessibility needs; Shared devices or limited connectivity; Another constraint; None | This helps make suggestions usable rather than merely technically possible. | Optional; None exclusive. A short accommodation is enough, never a diagnosis or sensitive explanation. |

## After discovery

Give the assessment before asking for a path. Explain strengths, gaps, unknowns, dependencies and trade-offs; label partial assessments provisional. **Path means WHAT to focus on**: for example keep the current setup, address recovery first, address the highest-impact gaps, or review the wider surface. Choose 2–4 meaningful directions from the actual findings, including no changes. **Help level means HOW to do a chosen path**: assessment only, checklist, guided walkthrough, or available tool assistance. A checklist or walkthrough is not a different security path. Never mix the two menus or ask both decisions at once. Do not use a fixed product upsell or claim any path makes someone fully secure.

Then ask separately how they want help: Assessment only / Self-directed checklist / Guided walkthrough / Scoped tool assistance only if genuinely available. Why: “This keeps the level of help under your control; selecting it does not authorize account changes.” Unavailable automation is not a choice. Any inspection, storage or change still needs specific approval and the existing safety gates.

At pause, preserve the phase, explanation preference, relevant technical scope, supplied facts and declined questions in an optional minimal private note. Do not put answers in the generic question bank or claim automatic memory. No-change and assessment-only outcomes are valid.
