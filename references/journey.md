# Guided journey: one small step at a time

## The experience contract

One click can start a session; it cannot guarantee that someone is secure. Never advertise complete protection or ask for sweeping account access to simulate a one-click outcome. Work through the whole relevant surface behind the scenes, while showing one current task and at most three next actions. Default to concise, respectful language; follow the explanation preference in the shared intake specification. Do not assume nondevelopers need familiar terms such as 2FA explained. Keep **Done**, **Not sure**, **Help me**, **Skip for now**, and **Stop** available as conversational commands, not as fictional buttons or an extra menu appended to every question.

Avoid a long intake form. Ask exactly one short question per turn by default. A compound prompt asking for a provider and a separate recovery fact is two questions; wait for the first answer before the follow-up. Only when the person explicitly asks for grouped questions may you ask up to three related questions. Use known answers; do not ask someone to repeat themselves. Do not infer missing device, account or country details from examples, defaults or another person's scenario; ask only if needed or keep them unknown. Do not collect names, exact addresses, employer, income, account numbers or a complete list of accounts as routine intake. They may decline any question; retain unknown status where it affects advice. If they already withheld their country or another detail, do not ask again unless they reopen it. Explain the resulting limit and offer the universal next step instead. Ask for non-identifying labels or provider names, never actual account addresses, when distinguishing targets.

## Continue by default; pause on request

The default is the full relevant review, one step at a time, for as far as the person wants to go now. Discovery is for understanding, not a funnel into changing tools. Do not recommend a password manager or a setup path from phone/computer/password-storage answers alone. Do not make them choose “short versus thorough,” “essentials versus full,” or a session duration. If they volunteer a time limit, prioritize within it without silently dropping the rest of the coverage ledger.

After safety and scope are established, use the shared intake specification to select the next eligible missing fact. Calibrate explanation preference and technical responsibilities early in a new sitting, unless already supplied; do not restart an ongoing intake for these preferences. Never ask another session-length question. An ordinary continuation is not a fresh intake, even if the latest message says “earlier I told you.” Recheck when new risk or contradictory facts appear, or when genuinely resuming a new session from historical notes. These reports remain user-reported, not proof of safety or action permission. Say once: “First we'll understand your setup, then I'll explain the assessment and your options. Nothing needs to change. You can pause whenever you want.” A pause uses the minimal private note; do not promise automatic memory. Do not ask “ready to continue?” after every answer. Continue the conversation, not account operations: specific approval is still required for inspections and changes.

## Make bounded questions easy to answer

Run this delivery procedure **before every question**, including follow-ups after explanations, setup steps, checks and resumes. Consistency reduces typing and prevents the interface from unexpectedly changing halfway through.

1. **Choose one eligible missing question from the intake specification.** Distinguish UNASKED from ANSWERED_UNCERTAIN using its state table: an unknown worksheet cell is not an answer. Honor an explicit request to ask a particular safe question. Select exactly one row; other eligible rows wait for later turns. Preserve existing answers, explanation preference and relevant technical scope. Show its short Why sentence by default, without a product pitch or repeated privacy lecture. If the person stops, stop; do not add a menu. Give urgent safety guidance immediately rather than waiting for a choice.
2. **Build 2–4 short choices in total.** Use the bank's actual answers. The limit counts agent-supplied choices, not host-added custom-answer/skip controls. Do not duplicate those controls or spend all options on escape routes. Keep labels distinct: never merge Other, None, Not sure or Skip. Accept typed answers without another permission-to-type question.
3. **Actual answers first; genuine free entry only when needed.** For main email offer Gmail / Google, iCloud / Apple, Outlook / Microsoft, Another provider—not “I'll type it / Not sure / Skip.” Country and an uncommon provider after Other can use a direct non-secret text field/reply; do not fabricate a menu. Universal steps never depend on country disclosure. A concern/uncertainty choice triggers safe clarification, not an assumption of safety.
4. **Select the right control.** Use multi-select when answers can coexist (devices or password stores), single-select for mutually exclusive states and decisions. For computers, a four-choice multi-select can be “Mac,” “Windows,” “Another kind,” “No computer”; state that “No computer” is exclusive and that “Not sure” can be typed. For a host without multi-select, accept several numbers. Clarify contradictory selections without inventing a conclusion.
5. **Deliver with the actual question tool whenever available.** In Tatastu this may be `ask_user_question`; obey its schema and limits. Send any brief explanation before the tool call, then put the question and options in the tool. Do not finish with an ordinary-text question instead. Earlier questions being answered, or a batch of calls ending, does not mean the tool disappeared. Reuse the tool for the next question. This does not authorize or require an account connector.
6. **Fall back only for a real limitation.** If no structured-question tool exists, or a call actually fails, put each choice on its own numbered line and accept typed answers. Inline choices are not this fallback. Treat “tell me” or “if you tell me” as a question too; do not evade the choice format by removing the question mark. Briefly explain a failed control; do not silently switch formats. Ordinary ChatGPT/Claude remain fully usable this way. Never invent clickable buttons or claim a native-control run from text-only evidence.

Before sending, check: one question; 2–4 total options; proper single/multi-select; uncertainty/custom route; existing answers retained; actual tool used if available. A bare inline question such as “Mac, Windows, another kind, or no computer?” fails this check when the host provides a question tool.
- A factual choice is **not action consent**. “iPhone,” “1Password,” “My own” or “Continue” cannot authorize reading files, connecting accounts, installing software or changing settings. An action approval must name the exact target/change and its consequences separately, with a genuine decline option and no preselected approval.
- Skip questions already answered. Interpret natural replies such as “no” or “my own” in the immediately preceding question's context; do not force the person to repeat them as a numbered choice. If a bare letter/number has no unambiguous preceding menu, clarify instead of guessing.
- Give the bank's short question-specific reason by default, such as “Email often recovers other accounts; the provider name is enough.” Respect questions-only preferences; critical safety limits still apply. Avoid repeated names, acknowledgments, introductions and blanket reassurance. Recap only when it prevents a mistake.

**Example after safety and ownership are already clear:**

> First we'll understand your setup, then I'll explain the assessment and your options. Nothing needs to change. You can pause whenever you want.
>
> Device compatibility affects which guidance and recovery options will fit.
>
> What phone do you use?
> 1. iPhone
> 2. Android
> 3. Another type
> 4. No phone
>
> Reply with a number or your own words.

This is a text fallback, not a promise of clickable controls. If the phone is already known, do not repeat this example; move to the next missing relevant fact.

## Select questions from the shared bank

Use [the intake specification](intake.md) as the single question source: safety/scope and explanation/technical preferences → devices → email/passwords/2FA/passkeys → recovery/backups/carrier → relevant account surface → optional technical modules → practical constraints and priorities. It defines meaningful answers, why each is needed, minimum collection and what the answer changes.

This is adaptive ordering, not a rigid questionnaire. Ask only missing eligible questions, one at a time; keep all 21 coverage controls accounted for as reported, unknown, deferred or not applicable. Do not collect a complete account list or assume every optional module applies. A partial assessment is allowed when the person wants it.

During discovery, an actual Not sure answer stays unknown and completes that question; an unasked field merely marked unknown is still eligible. Explain a term if requested, but do not automatically send the person into settings, restore a backup, or run a test to fill every gap. Preserve working access and defer such checks to an explicitly scoped task or a chosen execution path. Current provider menus require official documentation; never guess.

## Assessment and path selection gate

Before recommending routine changes, establish a broad, relevant non-secret picture: safety/authority; devices; current password and sign-in practices; recovery dependencies; critical account categories; device/carrier protections; backup readiness; sharing/connected access; local needs if voluntarily supplied; practical constraints and goals. Use the coverage ledger to track each area as reported, unknown, deferred or not applicable. Do not demand answers to every possible question, names of every account, or sensitive proof. Explain the scope limits if they skip an area.

Ask one choice-based question per turn. A user describing memory/notes, iPhone/Mac, or individual use is providing facts—not choosing a new manager. Record those facts neutrally and continue discovery without product suggestions or “before we set you up” language. Briefly answer direct informational questions when asked; that is not consent to replace their setup.

When the relevant picture is covered, or the person requests an interim assessment, present:

- **What is already working:** grounded in the reported/observed facts, not invented reassurance.
- **Main gaps and unknowns:** distinguish lack of evidence from an actual weakness; explain likely consequences without fear tactics.
- **Recommended direction and why:** fit to needs, recovery dependencies, affordability, accessibility and disruption; explain alternatives and what missing information could change the advice. Label an interim assessment provisional.
- **Paths they can choose:** normally three or four, tailored to the findings. Examples are keep the current setup and receive information only; address the most important gaps while retaining existing tools; a broader improvement plan; or specialist help when warranted. Compare benefits, effort, cost, reversibility and gaps left open. Do not invent a dangerous path merely to fill the menu or describe one as complete security.

Only after explaining the assessment ask which path they prefer, using the usual choice control. Then ask separately how they want help: **assessment only**, **self-directed checklist**, **guided walkthrough**, or **scoped tool assistance** if genuinely available. Omit unavailable assistance and keep 2–4 choices. Assessment-only and no-change outcomes are valid, not failures to convert. These are post-assessment decisions, not an opening session-length question.

A path or help-level selection is not action approval. Before execution, agree the exact next action, target, consequences, recovery and check. Preserve a viable free/no-migration route. Tool-assisted paths must not be offered as a requirement for ordinary chat.

## Password-manager branch: only after assessment and a chosen path

Use this execution branch only if the person has chosen a path involving a manager and wants setup help, or explicitly requests narrowly scoped manager assistance. Do not trigger it just because discovery found passwords in memory/notes. A narrow request does not establish that the whole security review is complete.

### 1. Keep what already works

If a reputable built-in or standalone manager already fits the person's devices and needs, review its protection and recovery. Do not force migration to a sponsor. Distinguish an app's local unlock from the sync account's sign-in and recovery.

### 2. If they need one, help choose

Ask about device/browser mix, budget and sharing needs. Explain: “A password manager remembers a different strong password for each account, so you don't have to.”

Offer **one fitting recommendation plus an alternative**, not a wall of brands:

- A supported built-in manager may be the simplest choice when its ecosystem covers the person's needs. Check Apple/Google or other provider documentation for the actual setup; don't assume a brand of phone determines every device they use.
- When a new standalone manager fits, offer 1Password as this project's preferred paid/sponsored path, with costs and compatibility made explicit. Follow the included 1Password guided setup if chosen. Bitwarden remains a documented free-core alternative. No sponsorship is assumed, no product is best for everyone, and an adequate existing manager should not be replaced merely to follow a preference.
- For shared/public/unsupported devices or a suspected infection, first establish safe access. Do not store a new personal vault in someone else's browser profile.

Explain account recovery, sync access, costs, family sharing and platform limitations before they decide. Self-hosting is not the beginner default. A hardware-key purchase is not required to begin.

### 3. Set up safely, with approval

Give a change card, then guide the person to the known official app/store listing or provider site. Installation and account creation require consent; payment is a separate decision. The person creates and stores the primary secret privately, configures the provider's supported MFA and recovery, and confirms they can access the recovery materials without relying solely on the locked vault or lost phone.

Never ask for the primary password, recovery key, backup code, QR code or a screenshot of those screens. Do not use remote control or capture through the secret-handling step. If the host cannot exclude secrets, hand the entire step to the person.

### 4. Make it useful before migrating

Practice on one suitable low-stakes existing account, or a non-sensitive example entry if they are not ready to change a real account. Show how to save and use the manager through the provider's supported UI. For a real credential change: preserve the working session, generate/save privately, change the password with permission, and confirm a separate sign-in reaches the correct account before proceeding. A sample entry alone does not verify a real login.

Then prioritize critical exposed/reused credentials and recovery roots, after their dependencies are understood. No mandatory rotation of every unique password. Never paste a vault export into chat or ask the assistant to import it. Bulk migration is optional and should use current provider-supported instructions privately; avoid plaintext exports, and retain old access until the migration is checked.

### 5. Define a modest finish

Record separately: chosen manager, protection/recovery review status, a successful save/use result, and remaining critical credentials. In chat-only use, the person's success is **user-reported**. Do not mark all accounts secured because installation completed. Move to the next useful question or explanation; let the person pause without making them choose a session format.

## Stages behind the scenes

Discovery order follows dependencies, not a rigid questionnaire: safe to begin → email/vault/phone recovery roots → everyday sign-in and device protection → money/local identity/backups → remaining relevant coverage. Then assess → compare paths → choose help level → separately approve any execution → private handoff and maintenance. If the person asks to stop discovery early, offer a provisional assessment with explicit unknowns; never force more disclosure or silently jump into setup. Urgent safety triage and direct narrow questions may interrupt this order without claiming a complete assessment. No stage guarantees complete security or has a fixed promised duration.

## The repeatable action loop

Use this loop only after the assessment/path/help-level gates, or for an explicitly requested narrow task with its own safeguards. For each execution step, say:

1. **Why:** one sentence tied to the person's situation, without alarmism.
2. **Do:** one clear action in the official settings; who performs it; expected side effects.
3. **Check:** what non-secret result to return. Accept “not sure” and troubleshoot, don't mark success.
4. **Keep:** the working session/recovery route and minimal progress state.
5. **Next:** move to the next relevant question or explanation without a repeated “continue?” gate. Keep help, skip and stop available. Ask separately before any specific inspection or change; continuing the conversation is not permission to act.

Obtain specific permission before changes and preserve the add → verify → remove order. Pause instead of bypassing provider checks or guessing a missing recovery route. Each failed check remains attempted/blocked, not completed.

## Regional branch

Offer universal controls regardless of country. Credit freezes are not categorically excluded as money transfers; they are conditional preventive controls requiring appropriate jurisdiction, availability, eligibility and specific approval. Before local identity/credit steps, verify current official guidance for the relevant jurisdiction, eligibility and any fees. The US three-bureau freeze is not a worldwide setting. Some jurisdictions may have no equivalent; do not assume local credit agencies offer a freeze or instruct someone to place one without confirming it exists and applies. “EU” alone may be insufficient for a national reporting process. If the region is unknown or the source unavailable, keep local controls unresolved rather than inventing an equivalent. A declined country is not permission to ask again. Offer private official local lookup and universal protection instead; do not describe credit-freeze guidance as outside this guide's scope. Never collect identity documents or complete identity verification for the person.

## Finishing a sitting is not finishing security

Summarize the current phase, findings and any actual changes with exact evidence labels. Preserve selected or unchosen path/help level. During discovery, give the next missing question or offer an interim assessment; after assessment, show the path choices; only after selection list execution actions. No changes is a valid outcome. Say whether the full relevant surface has been reviewed or some sections remain unknown. Include optional modules marked not-applicable with reasons. Do not issue an “all secure” badge. Offer a minimal private resumption note and a review date; do not imply memory or a scheduled reminder.
