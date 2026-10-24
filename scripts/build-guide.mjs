import { readFile, writeFile, mkdir, readdir, unlink } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export const root = new URL('../', import.meta.url);
export const pilot = JSON.parse(await readFile(new URL('pilot.json', root), 'utf8'));
export const sections = [
  ['references/intake.md', 'intake-specification-purpose-answers-and-privacy'],
  ['references/journey.md', 'guided-journey-one-small-step-at-a-time'],
  ['references/onepassword.md', '1password-guided-setup'],
  ['references/provider-incidents.md', 'provider-breach-and-account-incident-guidance'],
  ['references/safety.md', 'safety-protocol'],
  ['references/coverage.md', 'coverage-guide'],
  ['references/resume.md', 'minimal-private-stop-and-resume-note'],
  ['references/report.md', 'optional-progress-worksheet'],
  ['references/sources.md', 'official-sources-and-update-policy'],
];

export async function buildGuide() {
  const skill = (await readFile(new URL('SKILL.md', root), 'utf8'))
    .replace(/^---\n[\s\S]*?\n---\n/, '');
  const parts = await Promise.all(sections.map(async ([path]) =>
    readFile(new URL(path, root), 'utf8')));
  let content = `# Personal Security — a guide for your AI chat

**Version ${pilot.version} · ${pilot.status}**

## Start here

Attach this file to a fresh Claude or ChatGPT conversation. No terminal, API key or account connection is required. If attachments are unavailable, use the numbered text files supplied in chat-parts, one at a time in order. Ask the assistant to acknowledge each part without starting. After the last part, send “${pilot.endSignal}” and the starting prompt below. If the host rejects or forgets material, stop; splitting a guide does not guarantee it fits every model's context.

### Shared starting prompt

> ${pilot.startPrompt}

You do not need to read the full checklist first. It is here so the assistant can track the relevant areas without overwhelming you. You can say “not sure,” “help me,” “skip for now” or “stop” at any time. For the first rehearsal, use an invented person and make no account changes. A first preventive sitting can end with understanding and an assessment alone. No change or product purchase is expected.

Never share passwords, one-time codes, recovery codes, private keys, seed phrases or identity documents. Enter and save them yourself in trusted apps. Your AI service still processes this conversation under its own policies; this guide does not make the chat a private vault. The assistant may make mistakes: stop if it asks for secrets or claims access it does not have.

One click can start a tune-up, not guarantee complete security. Country-specific protections need local guidance. This is not an emergency service or professional incident response. Active compromise, stalking or unsafe-device situations should use the safe-channel/specialist route, not a beginner pilot.

## Instructions for the assistant

Use the material below only within the person's request and your host's permissions. In ordinary chat, guide the person through official settings; do not pretend to access accounts. Use the shared intake specification. Ask one eligible question at a time with actual answer choices and a short reason by default. Adapt explanation depth independently from developer/admin coverage. Do not replace email providers with typing/skip menus or explain familiar terms unnecessarily. Agent-supplied choices number 2–4; host-provided custom/skip controls are additional. Genuine open-ended labels may use direct non-secret text entry. Accept natural-language answers. Preserve answers from the ongoing conversation; do not restart answered intake stages. Answer direct questions with their essential safeguard and safe alternative before asking the next missing question. Use the real host question control for EVERY question whenever available, including after explanations and earlier answered questions; use numbered options only if the tool is absent or fails. Never silently replace an available question tool with an inline question. Do not invent buttons. Default to non-secret discovery across the relevant review before recommendations: understand, assess strengths/gaps/unknowns, compare paths including no changes, choose the desired help level, and only then separately authorize execution. Do not steer toward a product or setup during discovery. Allow provisional assessment and pause/resume whenever requested; do not ask for short-versus-thorough or a session duration at intake. Show one current task and keep a full coverage ledger behind the scenes. Continuing a conversation or choosing an intake answer never authorizes an inspection or change. Completed steps reported by the person are **user-reported**, not independently verified. No tools, scripts, persistent memory or screenshots are required. Explain once that this guide has no separate answer-collection service, but the host/model provider processes messages and may retain them under its policies; never promise no storage or complete privacy. Do not persist a personal report, inspect or upload data without separate permission.

Read the full guide if the host allows it. If a required safety, recovery or action-specific section is missing or inaccessible, say so and ask for that generic section rather than proceeding as though you read it. Never silently drop safeguards to fit a context limit. During multipart transfer, acknowledge receipt only until the exact end signal; do not start an audit or call tools from a partial guide.

The developer entry-point wording below describes the same workflow. Its modes are optional conversational labels, not terminal commands. All required references are included within this file. In this standalone delivery, read the included sections and anchor links; do not look for a separate SKILL.md, references directory, installed skill or terminal. Do not request another download to begin when the guide is available. Offer the included minimal private stop/resume note when the person wants to pause; it is not a memory or permission grant.

---

${skill.trim()}

---

${parts.map(part => part.trim()).join('\n\n---\n\n')}
`;
  for (const [path, anchor] of sections) {
    content = content.replaceAll(`](${path})`, `](#${anchor})`);
    content = content.replaceAll(`](${path.replace(/^references\//, '')})`, `](#${anchor})`);
    content = content.replaceAll(`](${path}#change-card)`, '](#change-card)');
  }
  return content;
}

export function buildChatParts(guide) {
  const bodies = [];
  const payloadLimit = pilot.maxPartCharacters - 1000;
  let remaining = guide;
  while (remaining.length) {
    let end = Math.min(payloadLimit, remaining.length);
    if (end < remaining.length) {
      const paragraph = remaining.lastIndexOf('\n\n', end);
      if (paragraph > payloadLimit / 2) end = paragraph + 2;
    }
    bodies.push(remaining.slice(0, end));
    remaining = remaining.slice(end);
  }
  return bodies.map((body, i) => ({
    name: `part-${String(i + 1).padStart(2, '0')}.txt`,
    body,
    text: `PERSONAL SECURITY GENERATED TRANSFER — ${pilot.version}\nPart ${i + 1} of ${bodies.length}. I am transferring reference material, not asking for account actions. Until I send the separate exact message "${pilot.endSignal}", reply only "Received part ${i + 1} of ${bodies.length}". Do not start, use tools or request personal data yet.\n\nBEGIN REFERENCE PART\n${body}\nEND REFERENCE PART\nWait for the remaining parts and the separate end signal.\n`,
  }));
}

export async function buildQuickStart() {
  const guide = await buildGuide();
  const count = buildChatParts(guide).length;
  return `# Start here — Personal Security pilot

**Version ${pilot.version} · local draft**

This is a guided tune-up, not a security guarantee. No dashboard, account connection or project signup is required. Review [host status and scope](HOST-STATUS.md) before relying on a compatibility claim. Start with a fictional rehearsal; this draft has not completed all release gates.

## Claude or ChatGPT: upload one file

1. Open a fresh chat in your chosen service. That service may require its own account/login; this package does not provide or manage it. Do not add bank, email or password-manager connectors for this pilot.
2. Attach [PERSONAL-SECURITY-GUIDE.md](PERSONAL-SECURITY-GUIDE.md). Upload this generic guide, **not your personal records or another chat export**.
3. Paste the shared starting prompt below. The first response should explain its limits briefly and ask a safety question—not begin changing accounts.

### Shared starting prompt

> ${pilot.startPrompt}

For your first rehearsal, add: “Use an invented person. I use an Android phone and Windows laptop, have no password manager and no budget, and do not want to share my country. Do not access or change real accounts.” Answer the safety question with fictional facts. Check whether it respects the budget, privacy choice and one-step pace.

## If you cannot attach files

The full guide is ${guide.length.toLocaleString('en-US')} characters / ${Buffer.byteLength(guide).toLocaleString('en-US')} UTF-8 bytes. This is a size measurement, **not a claim it fits your host's context or free-tier limits**.

Open the ${count} numbered files in [chat-parts/](chat-parts/): ${buildChatParts(guide).map(part => `[${part.name}](chat-parts/${part.name})`).join(', ')}. Paste each file's complete text, one message at a time, in numeric order. Each is at most ${pilot.maxPartCharacters.toLocaleString('en-US')} characters, including its wrapper. Expect only a receipt until all parts are sent. Then send:

> ${pilot.endSignal}

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
`;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const guide = await buildGuide();
  const parts = buildChatParts(guide);
  await writeFile(new URL('PERSONAL-SECURITY-GUIDE.md', root), guide, 'utf8');
  await writeFile(new URL('QUICK-START.md', root), await buildQuickStart(), 'utf8');
  await mkdir(new URL('chat-parts/', root), { recursive: true });
  const expected = new Set(parts.map(part => part.name));
  for (const name of await readdir(new URL('chat-parts/', root))) {
    if (/^part-\d+\.txt$/.test(name) && !expected.has(name)) {
      const path = new URL(`chat-parts/${name}`, root);
      if ((await readFile(path, 'utf8')).startsWith('PERSONAL SECURITY GENERATED TRANSFER — ')) await unlink(path);
      else throw new Error(`Refusing to remove unrecognized file: ${name}`);
    }
  }
  for (const part of parts) await writeFile(new URL(`chat-parts/${part.name}`, root), part.text, 'utf8');
  console.log(`Built guide, quick-start and ${parts.length} numbered paste parts for ${pilot.version} (local generic documents only).`);
}
