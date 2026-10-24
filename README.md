# Personal Security

**Practical protection for your digital life—with the AI you already use.**

A public-good project for an age of scalable scams and convincing AI impersonation. It helps people understand their current protections, compare realistic options, and decide what—if anything—to change. Any chosen action preserves recovery and needs specific consent. No fear-based selling, security score or promise that anyone is unhackable.

## Start the pilot

**Version 0.1.0-pilot.6 · local pilot package.** Begin with [QUICK-START.md](QUICK-START.md): one shared starting prompt, two entry points, and a fictional first rehearsal. Check [HOST-STATUS.md](HOST-STATUS.md) for actual evidence and blocked paths; the name of a host in these instructions is not a compatibility certification.

### Ready-to-use files

- **Ordinary chat:** [one self-contained guide](PERSONAL-SECURITY-GUIDE.md).
- **Developer skill:** [download the generic skill ZIP](downloads/personal-security-developer-skill.zip). Extract `personal-security/` into your host's project-local skill directory; do not overwrite an existing installation.
- **Start instructions:** [QUICK-START.md](QUICK-START.md). The [download manifest](downloads/manifest.json) records exact hashes. These files contain no participant reports or repository history.

## For everyone: Claude, ChatGPT or another chat assistant

1. Attach **[PERSONAL-SECURITY-GUIDE.md](PERSONAL-SECURITY-GUIDE.md)** to a fresh conversation. It is the only file the assistant needs for the chat path.
2. Use the shared starting prompt in [QUICK-START.md](QUICK-START.md). If attachments are unavailable, that file explains the generated numbered paste parts and explicit end signal. Do not assume multipart transfer fits every host.
3. Start with the fictional rehearsal. During any later approved real sitting, you stay in control: open settings yourself and return only non-secret results. Stop if the assistant asks for secrets or claims unavailable access.

No terminal, API key, connector, special AI subscription or custom GPT is required by the guide. The chat service's availability and limits still apply. It processes the conversation under its own policies; this is not an offline or confidential vault. Without browsing, ask for official Help/Search guidance rather than guessed menus. Keep an optional progress summary privately so you can resume without relying on AI memory.

## For developers: a local agent skill

Review the files first. Copy **`SKILL.md`, `pilot.json` and the entire `references/` folder** into your host's personal-security skill directory. Prefer an isolated project-local installation for the pilot, as described in QUICK-START.md; keep research, test output and personal notes out of the installed payload. Do not copy this private repository, its history, account notes or credentials to distribute the skill.

| Host | User-local destination | Start |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/personal-security/` | `/personal-security start` |
| Codex | `~/.agents/skills/personal-security/` | Ask it to use the `personal-security` skill and start an assessment |
| Other agents | Follow that host's documented `SKILL.md` support | Ask it to use this skill, or attach the standalone guide |

These paths follow the hosts' official documentation, not an end-to-end compatibility certification. Restart/reload the host if its skill list does not refresh. Do not overwrite an existing skill without comparing it first. Local CLI installation does not automatically install anything into Claude/ChatGPT web chat.

Modes: `start`, `audit`, `guide`, `review`, `incident`. They are instructions interpreted by the assistant, not shell commands or automatic account scanners. Tool access is optional and never grants permission to change an account. This package adds no tools, credentials, hooks or account integrations.

## What it covers

Twenty-one areas: safe scope; recovery; email/SSO; password manager; passkeys/MFA; old addresses/domains; carrier protections; devices; browsers; backups; financial fraud; identity/credit; scams; connected apps/AI/developer access; sharing; home network; household/emergency access; optional infrastructure; optional cryptocurrency; cleanup; maintenance.

The assistant first understands the person's relevant non-secret situation, without steering them toward products or setup. It then explains an assessment of strengths, gaps and uncertainties, compares paths including no changes, and asks separately how much help they want. Only a chosen execution path leads to specifically approved actions. Pausing or requesting a provisional assessment is always allowed; there is no opening short-versus-thorough or duration gate.

The [shared intake specification](references/intake.md) defines 47 adaptive questions, each with actual answer choices, a short Why, an eligibility rule and an assessment consequence. Ask only what is relevant and still unknown—not all 47 in a sitting. Explanation depth, developer/admin responsibilities and host capabilities are separate; nondevelopers are not assumed to need beginner tutorials.

Enumerable questions offer 2–4 substantive choices and accept typed answers. Genuine open-ended labels use direct non-secret entry. Provider names—not “I'll type it” menus—fill provider choices. Host-added custom/skip controls are not duplicated. If the host has a real question tool, use it consistently, including clarifications and follow-ups after explanations. Ordinary ChatGPT/Claude use numbered text when native controls are absent. No question is required after a stop request. Choices never authorize account access or changes. If a manager is part of a chosen plan, selection, private setup, recovery and practice follow the assessment—not the first device answer. A universal core applies across countries; local identity and fraud protections need current regional guidance.

Coverage is personalized, not a claim to cover every possible threat. Ordinary users can skip developer and domain administration with a reason. Higher-risk situations and active incidents may need specialist support. During discovery the assistant shows one question; after assessment it offers paths. Only after selection does it show up to three execution actions, not the entire checklist.

## Preferred setup and sponsorship

After assessment, if the person chooses a path involving a new manager and a paid/sponsored option fits, the guide now has a dedicated **1Password setup and recovery path**. It keeps adequate existing managers and free alternatives. It also asks about unlocked-phone theft, fake support/renewal scams and what happens when funded access ends.

1Password advertises possible nonprofit credits or support, but no sponsorship or eligibility is confirmed. Recipients should retain ownership and control of their personal vaults. See the [second review and staged plan](RESEARCH-PASS-2.md) for the six-source findings, funding questions and remaining gaps.

## When there is a breach notice or suspicious activity

The guide includes a plain-language incident path: confirm what happened through a trusted route, protect recovery, make specifically approved changes, check intended use and retire old access. Saved, staged and active changes are tracked separately. An optional developer/owner section covers service dependencies and release checks without imposing them on ordinary users. See [the generalized incident lessons](INCIDENT-LESSONS.md); no private transcript is bundled.

## Safety comes before convenience

- Passwords, codes, seeds and identity documents never go into chat.
- Preserve recovery and the last working session before changing access.
- Ask before each change; deletion, revocation and financial actions are separate decisions.
- Distinguish **verified**, **user-reported**, **attempted** and **unknown**.
- Do not silently read private stores, install extensions, change accounts or schedule reminders.
- If stalking/coercion or an unsafe device is involved, pause ordinary changes and use a safe-channel specialist route.

## Rollout: guides first, software only if needed

The versioned local pilot package is complete. A security-focused model review and actual Codex synthetic runs found issues that were corrected and rechecked. Consumer ChatGPT/Claude acceptance remains blocked in the available browser, Claude Code needs reauthentication, and external human review is unperformed. Complete the remaining safety/host gates before a real founder sitting and 3–5 beginner trials. Fix observed friction before public beta. Sponsorship is optional; a dashboard, resources database and account connectors are deferred until use demonstrates a need. See [ROLLOUT-PLAN.md](ROLLOUT-PLAN.md) for deliverables, stop conditions and release gates. These are planned stages, not completed validations.

## Package and maintenance

- `pilot.json` — single pilot version and shared starting prompt.
- `QUICK-START.md` — generated human setup instructions and fictional first rehearsal.
- `HOST-STATUS.md` — supported scope, actual host evidence and blocked/unrun paths.
- `ACCEPTANCE-TESTS.md` and `test/acceptance-cases.json` — reproducible synthetic checks, not claimed passes.
- `SECURITY-REVIEW.md` — independent model findings, corrections and review limitations.
- `test/evidence/pilot-0.1.0-pilot.1.json` — historical security smoke outputs and failures/reruns; not inherited as current passes.
- `test/evidence/pilot-0.1.0-pilot.2.json` — historical intake/pause outputs plus the full baseline that reproduced six failures.
- `test/evidence/pilot-0.1.0-pilot.3.json` — historical regression replies and source hashes.
- `test/evidence/pilot-0.1.0-pilot.4.json` — historical assessment-first evidence, including unresolved presentation failures.
- `test/evidence/pilot-0.1.0-pilot.6.json` — current developer/standalone regression evidence; native widgets require separate host validation.
- `test/evidence/pilot-0.1.0-pilot.5.json` — preserved failed pilot.5 evidence, not a current pass.
- `references/intake.md` — shared question bank, reasons, answer semantics, privacy boundaries and adaptation rules.
- `test/intake-contract-cases.json` — meaningful answers, explanation depth, honest privacy and direct-entry regression cases.
- `test/journey-cases.json` — discovery, clarification, provisional assessment, help-level and no-change cases.
- `CHANGELOG.md` — versioned changes and limits.
- `chat-parts/` — generated numbered plain-text fallback; host limits still apply.
- `references/resume.md` — minimal private stop/resume note, also included in the guide.
- `SKILL.md` — developer-agent entry point.
- `PERSONAL-SECURITY-GUIDE.md` — self-contained regular-chat distribution.
- `references/` — safety, coverage, worksheet and official sources.
- `PROJECT-BRIEF.md` — public-good purpose and proposed distribution.
- `ROLLOUT-PLAN.md` — skills-first delivery order, pilot gates and deferred work.
- `RESEARCH.md` — first-pass best practices, country limits and prospective partners.
- `RESEARCH-PASS-2.md` — second-pass gaps, six-stage plan and 1Password funding safeguards (no partnership agreed).
- `references/onepassword.md` — preferred paid/sponsored setup and recovery branch, also included in the standalone guide.
- `INCIDENT-LESSONS.md` — privacy-safe lessons from a supplied historical incident narrative, with evidence limits.
- `references/provider-incidents.md` — consumer incident path plus optional developer extension, included in the standalone guide.
- `scripts/build-guide.mjs` — maintainer-only local document builder; no network or account access.
- `scripts/run-behavior.mjs` — optional maintainer Codex runner for invented cases; validates the complete copied payload before model calls.
- `test/package.test.mjs` — packaging checks and a strict recorded-scenario gate, not a security audit.

From this repository root, maintainers can rebuild and check the standalone guide:

```bash
node skills/personal-security/scripts/build-guide.mjs
python3 skills/personal-security/scripts/build-bundle.py
node --test skills/personal-security/test/package.test.mjs
```

Maintainers can optionally run the synthetic cases with `node skills/personal-security/scripts/run-behavior.mjs` (or append case IDs); add `--guide` for standalone-file mode. The default reference model is `gpt-6-astra`; `--model=<id>` records a different selection explicitly. This is a maintainer test choice, not a model/subscription requirement for using the guide. This uses the configured Codex account/model service and may incur usage charges; host processing policies apply. It writes invented case outputs to a temporary directory, not participant reports. Never substitute personal data. The offline document builder is separate. Exit code 0 means execution succeeded, not that the responses passed review.

**Package status:** local pilot **0.1.0-pilot.6**, prepared for fictional rehearsals. The final developer and standalone matrices each met their 32 scoped scenario objectives with model selection `gpt-6-astra`; the earlier failures remain archived, not relabeled. See [validation](VALIDATION.md) and [exact evidence](test/evidence/pilot-0.1.0-pilot.6.json). This does not establish all-model reliability, actual consumer-host acceptance or readiness for a broader real-account pilot. Codex was exercised only in disposable test directories; nothing was installed into your normal AI profiles. Consumer Claude/ChatGPT interfaces remain untested beyond blocked navigation attempts. Public registry/download/one-command installation is not live. Publish only the reviewed generic package after the remaining review gates and a public-home/license decision; keep personal history and audit reports out of it.
