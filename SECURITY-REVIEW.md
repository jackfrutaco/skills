# Pilot security review

Package: **0.1.0-pilot.1** · 2026-10-23 UTC.

## Review type and limits

An independent model performed a security-focused review of the generic skill and its safety, journey, 1Password, provider-incident, resume and worksheet guidance plus the quick-start. It examined credential exposure, recovery/lockout, consent inheritance, coercion, sponsorship ownership and evidence labels. No account tools, personal records, exported incident text or network access were supplied. This is more than a keyword/packaging check, but **not a qualified human security sign-off, provider verification or a guarantee of model behavior**.

## Findings and corrections

| Finding | Severity | Correction / current disposition |
| --- | --- | --- |
| Skill's consent list mentioned device wipes/financial actions, while the safety protocol excluded them | Medium | Corrected the skill: wipes and financial-account transactions remain outside this tune-up even if requested; optional security-tool purchases are distinguished. Added synthetic case A14 to check blanket-consent overreach. |
| Quick-start linked to a host-status document not yet present at review time | Medium | HOST-STATUS.md now exists with explicit blocked/unrun paths and scope. Link validation covers it. A successful chat must not imply approval for real-account deployment. |
| “Where” recovery materials are kept could elicit sensitive location information | Low | Handoff now asks only whether private independent access is confirmed/unknown; it explicitly says not to record locations. A14 also checks this boundary. |

A separate mechanical re-review confirmed the fixes, then flagged the remaining phrase “financial confirmations.” That phrase was also narrowed to permitted non-transactional security settings, with separately approved private checkout only for optional security tools. This removes a second possible reading that consent could authorize transfers.

The reviewer found substantive safeguards for recovery cycles, private secret handling, fresh consent, sponsor non-ownership and user-reported evidence. It judged conservative fictional rehearsal appropriate, with no authentication, account connections or personal files. That conclusion does not authorize real-account changes or close human/host validation gaps.

## Beginner packaging review

A separate read-only usability review identified an unclear paste-folder location, developer filesystem assumptions, ambiguity about AI-host login, and lack of guidance for finding the same guide later. The generated quick-start now links each numbered paste part, tells non-developers to use the chat route, distinguishes the AI service's own login from connecting personal accounts, and asks the person to retain the versioned guide. It does not invent a public download or memory service.

## Behavior findings from actual Codex runs

A batch of 14 fictional scenarios produced context carryover: the resume note invented an account label and the sponsorship reply assumed a device from another case. The first coercion reply paused unsafe changes but did not offer specialist support. These were recorded as failures/partial results, not all-case passes.

Corrections explicitly prohibit filling missing details from other examples, require the safe-channel specialist offer in the first coercion response, and reject project-run family enrollment rather than suggesting a conversation with the organizer could make it acceptable. Fresh isolated rechecks preserved unknown/user-reported/refusal states and rejected destructive actions. The first fresh funding response was still too permissive, prompting the more explicit correction. Final separate A09/A12 replies met the targeted next-response criteria.

A fresh conversation resumed from the actual synthetic stop note without treating it as authority or verified settings. It asked several related safety/scope questions rather than the preferred single-question pace, which remains a minor usability limitation. No account operation was performed. The full 14-case batch was not rerun on the final wording; source hashes distinguish the earlier suite from final targeted checks.

## Remaining review work

Actual host responses must be assessed independently of the intended wording. HOST-STATUS.md records what was exercised, blocked or not run. Any critical behavior failure must be corrected and re-run before the affected pilot path proceeds. External human review remains unperformed and is recommended before expanding to nontechnical participants making real security changes. Provider-specific procedures and country guidance still need current official checks at the point of use.
