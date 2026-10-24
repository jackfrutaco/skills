# Start here — Personal Security pilot

**Version 0.1.0-pilot.6 · local draft**

This is a guided tune-up, not a security guarantee. No dashboard, account connection or project signup is required. Review [host status and scope](HOST-STATUS.md) before relying on a compatibility claim. Start with a fictional rehearsal; this draft has not completed all release gates.

## Claude or ChatGPT: upload one file

1. Open a fresh chat in your chosen service. That service may require its own account/login; this package does not provide or manage it. Do not add bank, email or password-manager connectors for this pilot.
2. Attach [PERSONAL-SECURITY-GUIDE.md](PERSONAL-SECURITY-GUIDE.md). Upload this generic guide, **not your personal records or another chat export**.
3. Paste the shared starting prompt below. The first response should explain its limits briefly and ask a safety question—not begin changing accounts.

### Shared starting prompt

> Use the Personal Security guide or skill and its intake specification. Start with safety, then understand my situation one question at a time, with meaningful answer choices and a brief reason. Match the explanation to my familiarity; keep developer coverage separate. Explain privacy honestly and never request secrets. Assess before recommending paths or changes, include no changes, and ask separately before inspection, saving a report or action. Let me skip or pause anytime. Use real question controls when available, otherwise numbered answers; accept my own words.

For your first rehearsal, add: “Use an invented person. I use an Android phone and Windows laptop, have no password manager and no budget, and do not want to share my country. Do not access or change real accounts.” Answer the safety question with fictional facts. Check whether it respects the budget, privacy choice and one-step pace.

## If you cannot attach files

The full guide is 135,745 characters / 136,266 UTF-8 bytes. This is a size measurement, **not a claim it fits your host's context or free-tier limits**.

Open the 17 numbered files in [chat-parts/](chat-parts/): [part-01.txt](chat-parts/part-01.txt), [part-02.txt](chat-parts/part-02.txt), [part-03.txt](chat-parts/part-03.txt), [part-04.txt](chat-parts/part-04.txt), [part-05.txt](chat-parts/part-05.txt), [part-06.txt](chat-parts/part-06.txt), [part-07.txt](chat-parts/part-07.txt), [part-08.txt](chat-parts/part-08.txt), [part-09.txt](chat-parts/part-09.txt), [part-10.txt](chat-parts/part-10.txt), [part-11.txt](chat-parts/part-11.txt), [part-12.txt](chat-parts/part-12.txt), [part-13.txt](chat-parts/part-13.txt), [part-14.txt](chat-parts/part-14.txt), [part-15.txt](chat-parts/part-15.txt), [part-16.txt](chat-parts/part-16.txt), [part-17.txt](chat-parts/part-17.txt). Paste each file's complete text, one message at a time, in numeric order. Each is at most 10,000 characters, including its wrapper. Expect only a receipt until all parts are sent. Then send:

> END PERSONAL SECURITY GUIDE 0.1.0-pilot.6

Follow with the shared starting prompt. If the host refuses a part, loses context, starts early or cannot read a required section, stop and record that limitation. Do not work around it by omitting safety material or paying for a tier the pilot has not shown you need.

## Claude Code or another documented skill host

This section is for people already comfortable managing project files. If that is unfamiliar, use the chat route above—no terminal or skill installation is needed for it.

Review the package first. For an isolated pilot, copy only SKILL.md, pilot.json and the entire references folder into the host's project-local personal-security skill folder:

- Claude Code: .claude/skills/personal-security/
- Codex: .agents/skills/personal-security/

Use a disposable test project without credentials or personal files, not a production repository. Do not overwrite an existing skill. Host settings, hooks and connected tools can change behavior: use the host's restrictive permissions and disable unnecessary integrations; the skill text is not a sandbox.

In Claude Code invoke "/personal-security start", then use the same starting prompt/fictional profile as above. In other hosts ask explicitly to use the personal-security skill. Only hosts actually exercised in [HOST-STATUS.md](HOST-STATUS.md) should be described as tested. No account tool is needed for the first run.

## Stop, resume and report friction

Save your original guide and its version locally so you can load it again; there is no stable public download yet. If you lose it, ask the project owner for that version rather than assuming another chat remembers it.

Say **stop** at any point. Ask for the [minimal private resume note](references/resume.md) if useful. To resume in a fresh chat, load the same guide first and provide only a minimal note you choose to share. Old notes are neither proof of current settings nor approval.

For feedback, report only the guide version, host/model if visible, case/action category, where you got stuck, whether the next step was clear and any unsafe request (paraphrased). Do not send chat histories, passwords, codes, screenshots of settings, actual account identifiers or recovery locations. Never create a real incident to test the guide.

**Before a real preventive sitting:** review the current safety/host findings. Active compromise, coercion/stalking or an unsafe device is not beginner-pilot material. Keep secret entry private and preserve recovery. Use the [acceptance checklist](ACCEPTANCE-TESTS.md) for synthetic rehearsals; unresolved critical findings stop the affected path.
