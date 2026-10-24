import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, access, readdir, mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { freezePayload, installPayload } from '../scripts/run-behavior.mjs';
import { buildGuide, buildQuickStart, buildChatParts, pilot, root } from '../scripts/build-guide.mjs';

const read = path => readFile(new URL(path, root), 'utf8');
const anchors = text => new Set([...text.matchAll(/^#{1,6} (.+)$/gm)].map(([, h]) =>
  h.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').replace(/ /g, '-')));

async function markdownFiles(dir = '') {
  const entries = await readdir(new URL(dir || './', root), { withFileTypes: true });
  const paths = await Promise.all(entries.map(entry => {
    const path = dir + entry.name;
    return entry.isDirectory() ? markdownFiles(path + '/') : path.endsWith('.md') ? [path] : [];
  }));
  return paths.flat();
}

test('skill metadata has a portable name and quoted nonempty description', async () => {
  const skill = await read('SKILL.md');
  const match = skill.match(/^---\nname: ([a-z0-9-]+)\ndescription: ("[^\n]+")\n---\n/);
  assert.ok(match, 'Use simple, unambiguous YAML metadata');
  assert.equal(match[1], 'personal-security');
  assert.ok(JSON.parse(match[2]).length > 40);
});

test('standalone guide is generated from current sources and has no external file dependencies', async () => {
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  assert.equal(guide, await buildGuide());
  for (const [, link] of guide.matchAll(/\]\(([^)]+)\)/g)) {
    assert.ok(link.startsWith('https://') || link.startsWith('#'), `Not self-contained: ${link}`);
  }
  assert.ok(guide.includes('## Password-manager branch: only after assessment and a chosen path'));
  assert.ok(guide.includes('## Regional branch'));
});

test('pilot version and shared start prompt remain consistent across distributions', async () => {
  assert.match(pilot.version, /^\d+\.\d+\.\d+-pilot\.\d+$/);
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  const quick = await read('QUICK-START.md');
  assert.equal(quick, await buildQuickStart());
  for (const text of [guide, quick]) {
    assert.ok(text.includes(pilot.version));
    assert.ok(text.includes(pilot.startPrompt));
    assert.ok(text.includes(pilot.endSignal));
  }
  assert.ok((await read('SKILL.md')).includes(pilot.version));
  assert.ok(guide.includes('# Minimal private stop and resume note'));
  assert.ok(guide.includes('This note grants no permission to act'));
});

test('paste parts preserve the full guide in order and stay within the declared character bound', async () => {
  const guide = await buildGuide();
  const parts = buildChatParts(guide);
  assert.equal(parts.map(part => part.body).join(''), guide);
  assert.ok(parts.length > 1);
  assert.deepEqual((await readdir(new URL('chat-parts/', root))).sort(), parts.map(part => part.name).sort());
  for (const part of parts) {
    assert.equal(await read(`chat-parts/${part.name}`), part.text);
    assert.ok(part.text.length <= pilot.maxPartCharacters, part.name);
    assert.ok(part.text.includes('Do not start, use tools or request personal data yet'));
    assert.ok(part.text.includes(pilot.endSignal));
  }
});

test('acceptance cases have unique IDs and explicit success and failure criteria', async () => {
  const cases = JSON.parse(await read('test/acceptance-cases.json'));
  assert.equal(cases.length, 14);
  assert.equal(new Set(cases.map(item => item.id)).size, cases.length);
  for (const item of cases) {
    assert.ok(item.input.length > 20 && item.must.length && item.mustNot.length, item.id);
  }
});

test('intake defaults to resumable full coverage with bounded choices, not a pacing gate', async () => {
  const skill = await read('SKILL.md');
  const journey = await read('references/journey.md');
  assert.ok(skill.includes('Default to the full relevant review'));
  assert.ok(journey.includes('A factual choice is **not action consent**'));
  assert.ok(journey.includes('2–4 short choices'));
  assert.ok(journey.includes('If no structured-question tool exists'));
  assert.ok(!journey.includes('| Pace |'));
  assert.ok(!journey.includes('Would you like a short first session'));
  assert.ok(!skill.includes('Offer an essentials sitting'));
  const cases = JSON.parse(await read('test/intake-cases.json'));
  assert.deepEqual(cases.map(item => item.id), ['I01', 'I02', 'I03', 'I04']);
});

test('recorded scenario evidence covers every fixture and retains presentation failures', async () => {
  const evidence = JSON.parse(await read(`test/evidence/pilot-${pilot.version}.json`));
  const fixtures = [
    ...JSON.parse(await read('test/acceptance-cases.json')),
    ...JSON.parse(await read('test/intake-cases.json')),
    ...JSON.parse(await read('test/journey-cases.json')),
    ...JSON.parse(await read('test/intake-contract-cases.json')),
  ];
  const runs = evidence.targetedReruns;
  assert.deepEqual(evidence.fixtures, fixtures, 'Changed cases need fresh input evidence and an explicit re-review');
  assert.equal(evidence.summary.unresolvedPresentationFailures, evidence.knownPresentationFailures.length);
  assert.equal(evidence.summary.allInstructionChecksPassed,
    evidence.knownPresentationFailures.length === 0 && runs.every(run => run.verdict === 'passed'));
  assert.deepEqual(runs.map(run => run.id).sort(), fixtures.map(item => item.id).sort());
  for (const run of runs) {
    assert.equal(run.snapshotSha256, evidence.finalSnapshotSha256, run.id);
    assert.equal(run.exit_code, 0, run.id);
    assert.equal(run.verdict, 'passed', run.id);
    assert.ok(run.reply.trim(), run.id);
  }
  for (const id of ['I01', 'I02', 'I03', 'J01', 'J02', 'J03', 'K01', 'K02', 'K03', 'K07', 'K08']) {
    const reply = runs.find(run => run.id === id).reply;
    const choices = reply.match(/^\s*\d+[.)]\s+/gm) ?? [];
    assert.ok(choices.length >= 2 && choices.length <= 4, `${id}: ${choices.length} numbered choices`);
  }
  for (const id of ['K02', 'K08']) {
    assert.match(runs.find(run => run.id === id).reply,
      /\b(?:is|do you have) (?:2fa|two-factor authentication) (?:enabled|turned on)[^?]*\?/i,
      `${id}: asks about configured 2FA, with an actual question`);
  }
  const firstStep = runs.find(run => run.id === 'A01').reply;
  assert.ok((firstStep.match(/\?/g) ?? []).length <= 1, 'A01 bundles independently answerable questions');
});

test('assessment-first gates and persistent choice delivery reach both entry points', async () => {
  const skill = await read('SKILL.md');
  const journey = await read('references/journey.md');
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  for (const content of [skill, guide]) {
    assert.ok(content.includes('understand → assess → choose a path → separately authorize execution'));
    assert.ok(content.includes('Every guided question must offer 2–4'));
    assert.ok(content.includes('not just intake'));
  }
  assert.ok(journey.includes('before every question'));
  assert.ok(journey.includes('Earlier questions being answered, or a batch of calls ending, does not mean the tool disappeared'));
  assert.ok(journey.includes('Assessment-only and no-change outcomes are valid'));
  assert.ok(skill.includes('not just question marks'));
  assert.ok(skill.includes('an inline phrase like “iPhone, Android or other?” is NOT the fallback format'));
  assert.ok(!journey.includes('Start one useful approved action once enough is known'));
  const cases = JSON.parse(await read('test/journey-cases.json'));
  assert.deepEqual(cases.map(item => item.id), ['J01', 'J02', 'J03', 'J04', 'J05', 'J06']);
});

test('shared intake bank defines purpose, meaningful answers and collection limits', async () => {
  const intake = await read('references/intake.md');
  const rows = intake.split('\n').filter(line => /^\| [A-Z]\d{2} (single|multi) \|/.test(line))
    .map(line => line.split('|').slice(1, -1).map(cell => cell.trim()));
  assert.equal(rows.length, 47);
  assert.equal(new Set(rows.map(row => row[0].split(' ')[0])).size, rows.length);
  for (const row of rows) {
    assert.equal(row.length, 5, row[0]);
    assert.ok(row.every(Boolean), row[0]);
    const options = row[2].split(';');
    assert.ok(options.length >= 2 && options.length <= 4, row[0]);
    assert.ok(!options.some(option => /I'll type it|I’ll type it/i.test(option)), row[0]);
    assert.ok(row[3].split(/\s+/).length <= 25, row[0]);
  }
  assert.ok(intake.includes('Being a developer is neither proof of security expertise nor permission'));
  assert.ok(intake.includes('may retain it under their settings and policies'));
  assert.ok(intake.includes('Do not substitute login behavior for configured protection'));
  assert.ok(intake.includes('All discovery questions may be skipped'));
  assert.ok((await read('SKILL.md')).includes('references/intake.md'));
  assert.ok((await read('PERSONAL-SECURITY-GUIDE.md')).includes(intake.trim()));
  const cases = JSON.parse(await read('test/intake-contract-cases.json'));
  assert.deepEqual(cases.map(item => item.id), ['K01', 'K02', 'K03', 'K04', 'K05', 'K06', 'K07', 'K08']);
});

test('question history, single-row rendering and conditional credit scope survive distribution', async () => {
  for (const path of ['SKILL.md', 'PERSONAL-SECURITY-GUIDE.md']) {
    const text = await read(path);
    for (const phrase of ['UNASKED', 'ANSWERED_UNCERTAIN', 'Select exactly ONE question',
      'Options alone are never a complete question', 'allowed topic, unavailable local instructions']) {
      assert.ok(text.includes(phrase), `${path}: ${phrase}`);
    }
  }
  const intake = await read('references/intake.md');
  assert.ok(intake.includes('REOPENED BY REQUEST'));
  assert.ok(intake.includes('not that an actual Not sure answer should be repeated'));
  const coverage = await read('references/coverage.md');
  assert.ok(!coverage.includes('Ask country first.'));
  assert.ok(coverage.includes('Credit-freeze guidance is conditionally in scope'));
});

test('standalone behavior evidence covers the same fixtures without claiming consumer-host acceptance', async () => {
  const evidence = JSON.parse(await read(`test/evidence/pilot-${pilot.version}.json`));
  const standalone = evidence.standaloneRun;
  assert.equal(standalone.mode, 'guide');
  assert.equal(standalone.guideSha256, evidence.finalGuideSha256);
  assert.equal(standalone.snapshotSha256, evidence.finalSnapshotSha256);
  assert.deepEqual(standalone.fixtures, evidence.fixtures);
  assert.deepEqual(standalone.results.map(run => run.id), evidence.targetedReruns.map(run => run.id));
  assert.equal(evidence.consumerHostAcceptance, false);
  for (const run of standalone.results) {
    assert.equal(run.snapshotSha256, evidence.finalSnapshotSha256, run.id);
    assert.equal(run.exit_code, 0, run.id);
    assert.equal(run.verdict, 'passed', run.id);
  }
});

test('behavior runner rejects incomplete sources and verifies every installed reference', async () => {
  const temporary = await mkdtemp(join(tmpdir(), 'personal-security-runner-test-'));
  try {
    const incomplete = join(temporary, 'incomplete');
    await mkdir(join(incomplete, 'references'), { recursive: true });
    await writeFile(join(incomplete, 'SKILL.md'), 'placeholder');
    await writeFile(join(incomplete, 'pilot.json'), '{}');
    await assert.rejects(freezePayload(pathToFileURL(incomplete + '/')), { code: 'ENOENT' });
    const payload = await freezePayload();
    assert.ok(payload.files.some(file => file.path === 'references/intake.md'));
    const installed = join(temporary, 'installed');
    await installPayload(payload, installed);
    for (const { path, bytes } of payload.files) {
      assert.deepEqual(await readFile(join(installed, path)), bytes, path);
    }
    await writeFile(join(installed, 'references', 'not-for-distribution.md'), 'synthetic private-note placeholder');
    await assert.rejects(freezePayload(pathToFileURL(installed + '/')), /Unexpected reference outside distribution/);
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
});

test('developer download manifest matches the reviewed generic payload', async () => {
  const manifest = JSON.parse(await read('downloads/manifest.json'));
  const evidence = JSON.parse(await read(`test/evidence/pilot-${pilot.version}.json`));
  assert.equal(manifest.version, pilot.version);
  assert.equal(manifest.snapshotSha256, evidence.finalSnapshotSha256);
  assert.equal(manifest.guideSha256, evidence.finalGuideSha256);
  assert.deepEqual(Object.keys(manifest.files).sort(), evidence.finalSourcePaths.slice().sort());
  for (const [path, hash] of Object.entries(manifest.files)) {
    assert.equal(createHash('sha256').update(await read(path)).digest('hex'), hash, path);
  }
  const archive = await readFile(new URL(`downloads/${manifest.archive}`, root));
  assert.equal(createHash('sha256').update(archive).digest('hex'), manifest.archiveSha256);
});

test('every local markdown link and fragment resolves', async () => {
  for (const file of await markdownFiles()) {
    const text = await read(file);
    for (const [, link] of text.matchAll(/\]\(([^)]+)\)/g)) {
      if (/^https?:/.test(link)) continue; // Network availability is not a packaging test.
      const [path, fragment] = link.split('#');
      const target = path ? new URL(path, new URL(file, root)) : new URL(file, root);
      assert.ok(target.href.startsWith(root.href), `Escapes package: ${file}: ${link}`);
      await access(target);
      if (fragment) assert.ok(anchors(await readFile(target, 'utf8')).has(fragment), `${file}: missing ${link}`);
    }
  }
});

test('all 21 coverage controls appear exactly once and start unknown in worksheet', async () => {
  const coverage = await read('references/coverage.md');
  const ids = [...coverage.matchAll(/^## \d{2} .+\(`([^`]+)`\)$/gm)].map(match => match[1]);
  assert.equal(ids.length, 21);
  assert.equal(new Set(ids).size, 21);
  const report = await read('references/report.md');
  for (const id of ids) {
    const rows = report.split('\n').filter(row => row.startsWith(`| ${id} |`));
    assert.equal(rows.length, 1, id);
    assert.ok(rows[0].endsWith('| unknown |'), id);
  }
});

test('standalone guide retains essential safety and evidence boundaries', async () => {
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  for (const phrase of [
    'Never sign out the last working session',
    'User reports remain user-reported',
    'do not change sharing, sessions, or credentials on the possibly monitored device',
    'No automated transactions or wallet signing',
    'A skipped country never blocks universal steps',
    'Do not ask for, inspect, screenshot, copy, export, or log passwords',
  ]) assert.ok(guide.includes(phrase), `Missing boundary: ${phrase}`);
});

test('1Password branch and second-pass boundaries are included in ordinary-chat distribution', async () => {
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  assert.ok(guide.includes('# 1Password guided setup'));
  for (const phrase of [
    'A recovery code alone is not an independent recovery plan',
    'Existing 2FA remains enabled',
    'Do not trigger account recovery as a test',
    'No confirmed credits means no promise of free access',
    'No sponsor receives personal findings or vault/recovery access',
    'Keep an adequate existing manager',
    'Do not test by stealing, remotely locking or wiping the device',
    'Do not call a number in a pop-up/message',
  ]) assert.ok(guide.includes(phrase), `Missing second-pass boundary: ${phrase}`);
});

test('incident branch preserves lifecycle, privacy and scope boundaries in the chat guide', async () => {
  const guide = await read('PERSONAL-SECURITY-GUIDE.md');
  assert.ok(guide.includes('# Provider breach and account incident guidance'));
  for (const phrase of [
    'Historical chat instructions do not authorize current actions',
    'Missing logs or inaccessible usage data mean unknown, not clean',
    'Deleting a saved item or environment variable does not revoke its provider credential',
    'Do not test suspicious or leaked credentials',
    'A timeout, DNS error or blocked network is not proof of revocation',
    'including a just-created replacement',
    'Do not make an ordinary consumer configure CI',
    'No whole-change “verified” status while a required milestone is unresolved',
  ]) assert.ok(guide.includes(phrase), `Missing incident boundary: ${phrase}`);
  const worksheet = await read('references/report.md');
  assert.ok(worksheet.includes('## Change lifecycle when relevant'));
  assert.ok(worksheet.includes('Old access retired, or overlap explicitly tracked'));
});

test('recorded final synthetic snapshot matches the shipped generic payload', async () => {
  const evidence = JSON.parse(await read(`test/evidence/pilot-${pilot.version}.json`));
  assert.equal(evidence.version, pilot.version);
  assert.equal(evidence.finalGuideSha256, createHash('sha256').update(await read('PERSONAL-SECURITY-GUIDE.md')).digest('hex'));
  const paths = ['SKILL.md', 'pilot.json', ...(await readdir(new URL('references/', root))).filter(path => path.endsWith('.md')).map(path => `references/${path}`)].sort();
  const hash = createHash('sha256');
  for (const path of paths) hash.update(path + '\0').update(await read(path)).update('\0');
  assert.equal(evidence.finalSnapshotSha256, hash.digest('hex'), 'Changed guidance needs explicitly updated run evidence, not an inherited pass');
  assert.ok(evidence.targetedReruns.length > 0);
  for (const run of evidence.targetedReruns) assert.equal(run.snapshotSha256, evidence.finalSnapshotSha256);
  const prior = JSON.parse(await read('test/evidence/pilot-0.1.0-pilot.1.json'));
  assert.equal(prior.batch.responses.length, 14, 'Keep earlier failures and evidence; do not silently inherit them as current passes');
  assert.ok(evidence.blocked.some(item => item.host === 'ChatGPT web'));
});

test('second-pass evidence remains bounded to six listed primary sources', async () => {
  const report = await read('RESEARCH-PASS-2.md');
  const rows = [...report.matchAll(/^\| S([1-6]) \|/gm)].map(match => match[1]);
  assert.deepEqual(rows, ['1', '2', '3', '4', '5', '6']);
  const urls = new Set([...report.matchAll(/\]\((https:[^)]+)\)/g)].map(match => match[1]));
  assert.equal(urls.size, 6);
  assert.ok(report.includes('not the bounded multi-agent run'));
});
