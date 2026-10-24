# Skills-first rollout plan

## Decision

**Start with the skill and regular Claude/ChatGPT guide. Learn from use before building a dashboard or connectors.**

One maintained security workflow, two entry points:

- An uploadable/pasteable guide for ordinary AI chat; manual settings changes are the default.
- An inspectable skill for compatible developer agents; tool presence never authorizes account changes.

A person should be able to start, finish one meaningful protection, understand the limits, and resume safely without giving this project their credentials or creating another account.

**Current state:** a local draft package, research, source references, synthetic exercises and packaging checks exist. Consumer-host end-to-end use, beginner trials, independent security review and public distribution are not established. See [validation](VALIDATION.md). This plan does not mark those stages complete or authorize live account changes, outreach or publication.

## What we are not building for the first release

No dashboard, hosted AI agent, custom GPT dependency, universal account connector, vault integration, autonomous credential rotation, central recovery database, security score, mandatory subscription or sponsored onboarding dependency. No promise to cover every country or make a person unhackable.

The reference Markdown files are the initial resources library. A database is unnecessary until there is a demonstrated maintenance or product need. A simple public README/download page may later distribute the files; that is not a dashboard.

## 1. Finish a small pilot package — complete as a local draft

**Goal:** make the existing material easy to begin, not expand it into another product.

- [x] Define a single plain-language starting prompt and a short human quick-start for each entry point.
- [x] Keep comprehensive coverage available to the assistant, while presenting only one current action and at most three next actions to the person. Review attachment length, context limits and paste-in-parts usability without dropping safety boundaries. Numbered parts and their bounds are generated/tested; actual consumer paste behavior remains a phase-2 gap.
- [x] Include a minimal private stop/resume summary: completed/user-reported steps, unresolved risks and next action. Do not imply cross-chat memory or persistent consent.
- [x] Preserve a suitable existing password manager. Offer 1Password as the preferred new paid/sponsored option when it fits, plus a viable free path; confirmed funding is not assumed.
- [x] Make manual use sufficient: no connector, API key, special AI tier or terminal required by the guide. Clearly state host availability/attachment limits and that host privacy policies still apply.
- [x] Give the pilot files an explicit draft version and record their supported scope and known gaps.

Delivered as **0.1.0-pilot.1**: [quick-start](QUICK-START.md), standalone guide, numbered paste parts, shared prompt/version metadata, minimal resume note, host-status matrix and reproducible acceptance cases. This is packaging completion, not a completed beginner usability pilot.

**Exit gate:** an unfamiliar reader can locate the correct file and starting prompt and understands what not to share. Both distributions carry the same core coverage and safety rules. Packaging/link checks pass. This does not yet establish real host behavior or user success.

## 2. Establish safety and actual host behavior — partially complete, blocked paths remain

**Goal:** identify unsafe or confusing behavior before involving unsupervised beginners.

[Host status](HOST-STATUS.md), [security review](SECURITY-REVIEW.md) and [validation](VALIDATION.md) record the evidence. Actual Codex skill/start and synthetic case runs were performed. Consumer ChatGPT and Claude returned HTTP 403/access challenges; Claude Code authentication expired. No consumer upload/paste path has passed. An independent security-focused model review was completed and its findings corrected; this is not qualified human sign-off.

- [ ] Obtain an independent security review of recovery, secret handling, consent, incident escalation and vendor-specific advice. An automated consistency review is useful but not a substitute.
- [ ] Run the actual uploaded/pasted guide in fresh consumer ChatGPT and Claude conversations, recording the date, host/model/version where visible, guide version and capabilities. No private account data in shared test material.
- [x] Install/run the skill in at least one documented developer host in an isolated test project. Codex CLI 0.159.2 was exercised with explicit project-local skill invocation, read-only sandbox and synthetic data. Automatic triggering and other hosts are not inferred.
- [x] Use synthetic cases for no manager/no budget, adequate existing manager, unsupported phone features, no second device, missing recovery, withheld country, a failed new-factor sign-in, a secret offered to the assistant, imported blanket approval, an incident/coercion signal, interrupted progress and funding expiry. A 14-case Codex batch exposed context carryover; focused fresh sessions and a fresh resume were run, with failures and corrections retained. This does not count as consumer-host or real-account testing.
- [ ] Verify that manual users can continue when browsing, tools, attachments or persistence are unavailable; unsupported routes must be labelled rather than invented.

**Stop conditions:** secret requests, changes without specific approval, lockout-prone advice, false verification, ignored refusal or inappropriate coercion/incident handling. Fix and re-run affected cases before advancing. Record limitations and failures, not just successful examples. No blanket host or security certification follows from a finite set of tests.

**Exit gate:** independent feedback is addressed or explicitly blocks release, and the claimed host paths have been exercised with no unresolved critical safety findings. Unavailable hosts remain unverified rather than silently counted as supported.

## 3. Run the founder's first real sitting

**Goal:** check the complete human journey with one consenting person who understands it is a draft.

- [ ] Use a fresh conversation and the intended download/upload or install path, not this development conversation's accumulated context.
- [ ] Complete discovery → assessment → comparison of paths (including no changes) → separate help-level selection. Do not recommend a product or setup during discovery, or make an action the expected outcome.
- [ ] If the person chooses execution, pick one genuinely useful, low-disruption protection appropriate to the assessment, obtain specific approval, and guide private settings → non-secret result → progress summary. Do not undo a working control or force migration simply to generate a demonstration.
- [ ] Stop and resume in a fresh conversation using only the minimal summary. Re-establish current scope and permission before further actions.
- [ ] Note confusing wording, unexpected host behavior, approximate effort, whether question reasons and actual answer choices made sense, and whether the next step was clear. Check that explanation depth matches the person's preference independently of developer/admin scope. Confirm they understand the host-processing/retention limit rather than believing the guide promises no storage. Keep real security details private; do not turn a transcript into promotional evidence.

**Exit gate:** the person understands the assessment and options, chooses a path and help level without pressure (including no changes), remaining gaps are visible, and resumption preserves the current phase without assuming memory or permission. If execution is chosen, one useful action has the correct evidence label and preserved access. Record an assessment-only outcome honestly; it is not evidence of a real account improvement.

## 4. Pilot with 3–5 nontechnical volunteers

**Goal:** learn whether ordinary people can use it, not prove statistical effectiveness.

- [ ] Recruit consenting adults for ordinary preventive hygiene, including different device mixes and at least one free/existing-manager path. Do not use active compromise, coercion/stalking or highly targeted cases as beginner pilot material; offer appropriate support instead.
- [ ] Explain that the guide is experimental, participation is voluntary, actions can be declined, and no passwords, codes, recovery maps or account identifiers should be shared with the project.
- [ ] Let each person understand the assessment, choose a path and help level (including no changes), and set their own pace. If they choose execution, they select one useful action and operate settings privately; no screen recording of authentication or secret-bearing pages.
- [ ] Collect only voluntary, minimal feedback: where they got stuck, whether the assessment and path choices made sense, whether any chosen action finished, whether they retained access, whether the next step was clear and any unsafe assistant request. Do not require chat histories or screenshots. Agree how long feedback is kept and remove unnecessary personal details.
- [ ] Make developer users a separate small track so their tool-assisted success does not stand in for nontechnical usability.

**Stop conditions:** any suspected secret disclosure, lockout or unsafe instruction pauses that participant's flow and affected pilot path for review. Do not continue merely to finish the checklist.

**Exit gate:** review every participant's outcome, blockers and safety issues; revise and re-run failed paths. A small successful pilot supports a usability claim only, not “prevents hacks,” worldwide coverage or universal model reliability.

## 5. Revise and release a public beta

**Goal:** distribute a maintained, honest guide—not a claim of complete protection.

- [ ] Fix the pilot's recurring friction without adding unnecessary questions or products; re-run safety/host cases after consequential changes.
- [ ] Choose the public name/home and license with the owner. Publish only the reviewed generic package, never this private repository, its history or personal exports.
- [ ] Provide a versioned chat guide, skill package, quick-start, source list, supported-host/scope notes, changelog and private security-reporting/correction route. Do not solicit secrets in bug reports.
- [ ] Re-check the release download and installation from a clean environment. Offer a one-command installer only once a real reviewed distribution exists; do not invent an install URL.
- [ ] Keep reference entries versioned with applicability, official source, review date, maintenance owner and limitations. Publish only country-specific steps actually researched; allow the universal core to work when the country is unknown.
- [ ] Optionally include a short founder story distilled from the existing material, after the owner reviews its factual claims and redactions. Clearly distinguish historical reported results from current verified state. It is context, not proof of effectiveness or a release blocker.

**Exit gate:** the generic public files are available and usable, the maintenance/correction responsibilities are assigned, and the release accurately describes remaining limits. No publish action occurs just because this roadmap exists.

## 6. Explore funding without making it a dependency

This optional track may run alongside public-beta preparation **after the pilot provides something concrete to show**.

- [ ] Prepare a small, consented, non-identifying pilot summary and a specific access/education proposal for 1Password or an appropriate nonprofit partner.
- [ ] Confirm actual program eligibility and terms before promising credits. A public-good intention is not nonprofit status, and a general discount page is not a committed sponsorship.
- [ ] Require recipient ownership, clear funded duration, renewal/payment consent, accessible support, data minimization and a private exit/migration path.
- [ ] Keep the guide useful with no funding and no vendor purchase. Sponsorship must not control recommendations or give the sponsor access to personal findings, vaults or recovery.

**Exit gate:** written terms and eligibility are confirmed before enrolling funded recipients. No outreach, application, purchase, branding claim or data sharing is implied by documenting this track.

## 7. Decide whether software is justified

Only consider a separate interface after repeated pilot/public feedback identifies a problem the files and host chats cannot reasonably solve.

- If the problem is finding the guide, improve distribution and quick-starts.
- If the problem is remembering progress, improve private summaries first; evaluate an optional minimal progress UI only if that remains inadequate.
- If the problem is stale instructions, improve source ownership/review before building a resources database.
- If the problem is repetitive observation, consider one narrow read-only connector, not “connect everything.”
- If actual changes are later automated, build specific action previews, approval enforcement outside the model, narrow permissions, safe authentication handoffs, non-secret auditability, interruption handling and recovery checks before granting write access. Preserve manual mode.

**Exit gate:** a defined user problem, evidence from use, a security/privacy threat model and explicit approval for the next scoped build. A dashboard is not inevitable, and action automation is a separate security-sensitive project—not a hidden milestone of the first release.

## Immediate order

**Pilot package → independent review and real-host checks → founder sitting → 3–5-person pilot → fixes and public beta → optional funding → evidence-led UI/automation.**

The pilot package and acceptance-test checklist are now delivered. The next gate is completing the blocked consumer-host synthetic checks and outstanding independent review requirements—not a website, more broad research, a new database or a sponsorship dependency. Use [QUICK-START.md](QUICK-START.md) in the person's normal supported consumer app; do not bypass access challenges or start real-account changes to compensate for missing test evidence. If a specific security uncertainty blocks a step, do targeted research on that question instead of indefinitely expanding the framework.
