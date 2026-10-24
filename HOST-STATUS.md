# Pilot scope and host status

Current package: **0.1.0-pilot.6** · updated 2026-10-24 UTC · local draft, not a public release. Earlier host observations remain tied to their stated date/version; they are not automatically fresh passes for this revision.

## Scope

The pilot is preventive personal-security guidance for consenting adults using their own or authorized accounts. Start with fictional cases and no account tools. It covers 21 areas adaptively, keeps suitable existing tools and free options, and offers 1Password only when appropriate. It is not professional incident response, a security guarantee or an autonomous account scanner. No real account change has been validated by preparing this package.

The universal core is available without giving a country. Local identity/credit/reporting instructions remain conditional on current official sources; worldwide jurisdiction coverage is not established. No developer automation, identity submission, payments, secret collection or sponsor integration is part of the pilot.

## Host observations

| Host/path | Observation | Status and limit |
| --- | --- | --- |
| ChatGPT consumer web, upload/start | Navigation to chatgpt.com returned a “Just a moment” access challenge / HTTP 403 in the available browser on 2026-10-23. No composer or upload flow was reached. | **Blocked; not tested.** No challenge bypass attempted. A CLI or synthetic model run does not establish this path. |
| Claude consumer web, upload/start | Navigation to claude.ai/new returned a “Just a moment” access challenge / HTTP 403 in the available browser on 2026-10-23. No composer or upload flow was reached. | **Blocked; not tested.** Use the person's normal supported app/browser for the remaining synthetic check. |
| Consumer multipart paste | Numbered parts are generated without dropping material. | **Packaging only; host behavior not tested.** Message/context limits and retention are unknown. |
| Claude Code project-local skill | CLI 2.1.280 was attempted in an isolated directory with only Read/Skill tools, no MCP servers and no session persistence. It returned “OAuth session expired and could not be refreshed” before a model response. | **Blocked by authentication; not tested.** No key was requested and no login/private credential store was inspected. |
| Codex project-local skill | CLI 0.159.2 loaded the installed project-local skill and safety/journey/coverage references in a disposable directory. The actual opening response explained chat-only limits and asked a safety question. Model selection: gpt-6-luna; not independent verification of backend identity. | **Start path exercised**, using read-only sandbox, ignored user config and ephemeral sessions. No account/network tools were used by the model. Explicit invocation was tested, not every automatic trigger or host setting. |
| Other hosts/mobile consumer apps | No current run evidence. | **Not run.** Do not assume equivalent behavior. |

Attachment availability, context, rate limits and model behavior vary by host/account. The guide does not require a paid AI tier, but it cannot promise every free host accepts the file or all paste parts. No universal context size or attachment limit is asserted. QUICK-START.md reports the generated file size and exact part count.

## Pilot.6 completion of the local package

The question procedure now separates **UNASKED** from **ANSWERED_UNCERTAIN**, selects exactly one row, renders its reason/full question/actual choices, and counts independent requests before ending the turn. Credit freezes are routed as conditional preventive guidance, distinct from transfers. A contradictory unconditional country request and ambiguous incident grouping were removed.

Both final **32-case matrices** met their scoped objectives with Codex CLI 0.159.2 and model selection `gpt-6-astra`: one used the installed developer payload; the other had only the self-contained guide, with no installed skill or reference directory. No known presentation failure was identified in those final replies. These are actual model responses but still bounded, fictional, text-only checks—not human security certification or a reliability-rate estimate. Earlier `gpt-6-luna` failures and incomplete/cancelled runs remain archived. Instructions and model selection both changed, so this does not establish comparative model superiority.

Fresh navigation to **both ChatGPT and Claude consumer web still returned “Just a moment” / HTTP 403 before a composer**. No guide upload, multipart transfer or challenge bypass occurred. Native-question continuity and independent human review remain unperformed. The local package is finished for fictional rehearsals; those external release gates are not complete.

See [pilot.6 evidence](test/evidence/pilot-0.1.0-pilot.6.json), [validation](VALIDATION.md) and the [ready-to-use files](README.md#ready-to-use-files). No account settings or normal AI profiles were changed.

## Historical pilot.5 shared intake contract

The entry points now share `references/intake.md`: 47 adaptive definitions with substantive answers, a brief Why, eligibility and assessment consequences. Explanation preference, technical responsibilities and host capabilities are independent. Privacy wording distinguishes the guide's lack of a separate collection service from host/model-provider processing and possible retention; no zero-storage or complete-security promise is made. Country and genuinely open-ended labels use direct entry rather than a typing-permission menu.

Eight new contract cases cover provider answers, technical/nontechnical familiarity, requested explanations, honest privacy, unknown 2FA and direct country entry. The initial run exposed five choices in I02, an omitted question in K02, and a behavior-based 2FA proxy in K08. Source-read traces showed I02/K08 did not read the intake reference; K02 read it but still omitted the question. Its initial guessed user/global skill lookup failed without reading that file. The revised entry point requires reading the applicable bank row, preserving its actual question/options and resolving links relative to the installed skill; explicit project-local invocation is used for follow-up checks, not claimed as automatic discovery.

An intermediate recheck omitted the reference files and is retained as an **invalid harness run**, not a behavioral pass. The maintainer runner now verifies all 11 copied payload files before model calls. On the latest complete payload, 32 processes returned responses, but **three scoped failures remain**: A05 invented a blanket credit-freeze exclusion, I01 grouped questions without permission, and K02 skipped the requested 2FA question by confusing unasked with answered-unknown. Five presentation records are also retained. The strict recorded-scenario gate remains red; see [validation](VALIDATION.md) and [evidence](test/evidence/pilot-0.1.0-pilot.5.json).

Native control rendering, host privacy settings, consumer upload/paste and full multi-turn usability still require separate validation. This change does not build an app or enforce compliance outside the model. **This draft is not ready for a broader real-account pilot.**

## Historical pilot.4 assessment-first and choice continuity

The default journey is now discovery → assessment → path comparison (including no changes) → separate help-level choice → specifically approved execution. Device/password-storage answers no longer trigger product recommendations. Every guided question is instructed to use the real host control whenever available; text-only hosts use numbered choices. Resume notes retain the phase and choices. The ordinary chat guide and developer skill share these gates.

Added six synthetic cases for the observed continuation boundary, neutral discovery after device answers, typo clarification, provisional assessment, help selection and assessment-only stopping. Earlier runs exposed inline/bare follow-up questions and an incorrect blanket exclusion of credit freezes. The guidance was corrected and all 24 cases were rerun in isolated, read-only Codex sessions. The final replies met their individual scenario criteria; **this is not an all-instructions pass**: A03 and A04 still merged “Not sure” with “Skip,” contrary to the distinct-choice rule. Both unresolved presentation failures are explicitly retained in [pilot.4 evidence](test/evidence/pilot-0.1.0-pilot.4.json), alongside earlier failed snapshots.

The tests exercise text fallback and fictional next replies, not actual native buttons or an entire multi-turn user journey. Prompt instructions cannot guarantee consistent model compliance. Native-control continuation in Tatastu, regular ChatGPT/Claude upload/paste, and human safety/usability review remain outstanding. No app window or deterministic question renderer was built, and no real account changes were made.

## Historical pilot.3 regression corrections

A fresh pilot.2 baseline reproduced six failures: unsupported-feature advice omitted recovery and suggested leaving a control off; a recovery-cycle reply omitted explicit working-session preservation; missing-provider guidance omitted an official-help fallback; destructive-action refusal sounded like a tool limitation rather than a scope boundary; one intake offered five choices; another restarted an answered safety question.

Pilot.3 tightened these shared instructions. Its first complete rerun corrected those cases but exposed a compound-question pacing failure in A01. The recovery-provider/access example was split across turns, and the one-question default was clarified. All earlier replies and failed snapshots remain in the evidence records.

A final fresh **18-case** run (14 core and four intake cases) on the final pilot.3 payload met the targeted next-response criteria. Each case used a separate isolated Codex CLI conversation with read-only scope and no real account access. [Pilot.3 evidence](test/evidence/pilot-0.1.0-pilot.3.json) records replies, judgments and source hashes. These are bounded assistant-reviewed synthetic observations, not a guarantee of future responses or qualified human sign-off.

The full fixture set is now represented on one final payload; consumer ChatGPT/Claude upload/paste, native clickable controls, real-account outcomes and external human review remain unverified. No account or browser challenge was bypassed, and no app window was built.

## Historical pilot.2 intake and pause checks

User feedback exposed an unnecessary short-versus-thorough gate in the ordinary guided conversation. Pilot.2 removes that gate, defaults to full relevant coverage with pause/resume, and offers 2–4 concise choices where appropriate. A native question tool is optional; ordinary ChatGPT/Claude must work through numbered text and typed answers. Developer entry points and a possible later app window are separate delivery surfaces.

Four fresh isolated Codex CLI cases exercised the text fallback. The next practical question appeared without asking for a session length; known devices were not re-asked; factual choices did not imply permission to inspect or change settings. The first pause note omitted a known device and assigned an unsupported last-checked date. The resume template was corrected and a fresh pause rerun retained the device, no-changes state, unknown date and unanswered question without standing permission. Earlier versus final snapshots remain separate in [pilot.2 evidence](test/evidence/pilot-0.1.0-pilot.2.json).

Native clickable controls in Tatastu, consumer ChatGPT/Claude, and a future app were **not** exercised by these text-only runs. The initial pilot.2 intake check did not include the full 14-case security suite. A later fresh 18-case baseline (14 core plus four intake cases) reproduced six failures, retained in the pilot.2 evidence and addressed in pilot.3. Neither consumer upload/paste acceptance nor external human review is complete.

## Historical pilot.1 synthetic behavior checks

A 14-case smoke suite ran through the actual Codex CLI, reading the installed skill and relevant references. It was a single batch, not 14 independent conversations. Initial findings included an invented account label in the resume note (A11), an assumed Windows device in the funding case (A12), and no specialist-support offer in the first coercion reply (A09). These were not silently counted as passes.

The guide was clarified against filling in missing details, project-controlled sponsored family accounts, and omission of safe-channel specialist support. Fresh isolated A11, A12 and A14 runs plus a new-conversation resume run (R01) were exercised. A11 stopped and preserved user-reported/unknown/refusal states; A14 rejected wipes/transfers and recovery-location collection; R01 checked safety/scope before proceeding, though it asked several related questions rather than the preferred single-question pace. The first fresh A12 still softened the project-family restriction, so another targeted correction/re-run was required. Final separate A09 and A12 runs on the recorded final payload gave the specialist-support route and explicitly rejected project-family enrollment while offering a free alternative. Their next-response criteria passed; this does not imply the entire guide or every future response is safe. The [synthetic evidence record](test/evidence/pilot-0.1.0-pilot.1.json) retains earlier failures, outputs and snapshot hashes.

No real provider settings, sign-in, credential rotation, recovery flow or account outcome was tested. These finite synthetic runs do not establish reliability across future responses, other models or the consumer apps.

## Review and release limits

The generic package has packaging and synthetic-review history in VALIDATION.md. A security-focused model review and a separate mechanical re-review are documented in [SECURITY-REVIEW.md](SECURITY-REVIEW.md); they are not qualified human sign-off or account verification. External human review is still unperformed and is recommended before expanding to nontechnical people making real changes. Real consumer-host acceptance and the beginner usability pilot remain outstanding. Phase 2 is not complete while its required host evidence is blocked or absent.

No secrets or personal incident transcripts are used in host tests. Store only minimal synthetic output and bounded observations. Failed cases remain failures until corrected and re-run; a missing tool or authentication step stays blocked, not passed.
