// Builds PERSONAL-SECURITY-GUIDE.md: SKILL.md and its references merged into one file
// for people using an ordinary AI chat. Run with --check to fail if the guide is out of date.
import { readFile, writeFile } from 'node:fs/promises';

const root = new URL('../', import.meta.url);
const read = path => readFile(new URL(path, root), 'utf8');
const references = {
  'references/questions.md': 'question-bank',
  'references/coverage.md': 'coverage-areas',
};

const header = `# Personal Security — guide for your AI chat

**For you:** attach this file to a new chat in Claude, ChatGPT or another assistant and say "Use this guide to review my personal security." It asks about your setup one question at a time, explains what it sees, and offers options, including changing nothing. You stay in control: you open your own settings and share only general answers. Never send passwords, codes, recovery details or ID documents, and stop if the assistant asks for them or claims it can see accounts you haven't connected. If you can't attach files, paste this text in a few pieces, then say "that's the whole guide". This isn't an emergency service: if you're in danger or think you're being monitored, use a safe device and contact local specialist support.

**For the assistant:** this file is the complete Personal Security skill: the instructions, then the question bank, then the coverage areas. Links point to sections in this file. Don't look for other files; none are needed. If the guide arrives in several messages, only acknowledge each one until the person says it's complete. In a plain chat you can't see or change accounts: guide the person, and treat what they tell you as user-reported. Use connectors or a browser agent only if they're really connected in this chat, and only as the done-for-you section allows.`;

const slug = heading => heading.toLowerCase().replace(/[^a-z0-9 -]/g, '').replace(/ /g, '-');

const skill = (await read('SKILL.md')).replace(/^---\n[\s\S]*?\n---\n/, '');
const parts = await Promise.all(Object.keys(references).map(read));
const guide = [header, skill, ...parts].map(part => part.trim()).join('\n\n---\n\n')
  .replace(/\]\((references\/[a-z-]+\.md)(#[^)]+)?\)/g, (link, path, hash) => {
    if (!(path in references)) throw new Error(`Unknown reference link: ${link}`);
    return `](${hash ?? `#${references[path]}`})`;
  }) + '\n';

const anchors = new Set([...guide.matchAll(/^#+ (.+)$/gm)].map(([, heading]) => slug(heading)));
for (const [link, target] of guide.matchAll(/\]\(([^)]+)\)/g)) {
  if (/^https:\/\//.test(target)) continue;
  if (!target.startsWith('#') || !anchors.has(target.slice(1))) throw new Error(`Broken link in guide: ${link}`);
}

if (process.argv.includes('--check')) {
  if ((await read('PERSONAL-SECURITY-GUIDE.md')) !== guide) {
    console.error('PERSONAL-SECURITY-GUIDE.md is out of date. Run this script without --check.');
    process.exit(1);
  }
  console.log('PERSONAL-SECURITY-GUIDE.md is up to date.');
} else {
  await writeFile(new URL('PERSONAL-SECURITY-GUIDE.md', root), guide);
  console.log(`Wrote PERSONAL-SECURITY-GUIDE.md (${guide.length.toLocaleString('en-US')} characters).`);
}
