import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createWriteStream } from 'node:fs';
import { mkdtemp, mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { root, sections, buildGuide } from './build-guide.mjs';

export async function freezePayload(source = root) {
  const references = (await readdir(new URL('references/', source)))
    .filter(name => name.endsWith('.md')).map(name => `references/${name}`);
  const required = ['SKILL.md', 'pilot.json', ...sections.map(([path]) => path)];
  for (const path of references) assert.ok(required.includes(path), `Unexpected reference outside distribution: ${path}`);
  const paths = [...new Set(required)].sort();
  const files = [];
  const hash = createHash('sha256');
  for (const path of paths) {
    const bytes = await readFile(new URL(path, source));
    assert.ok(bytes.length, `Empty required source: ${path}`);
    files.push({ path, bytes });
    hash.update(path + '\0').update(bytes).update('\0');
  }
  return { files, snapshotSha256: hash.digest('hex') };
}

export async function installPayload(payload, destination) {
  for (const { path, bytes } of payload.files) {
    const target = join(destination, path);
    await mkdir(dirname(target), { recursive: true });
    await writeFile(target, bytes);
  }
  // Fail before starting a model if even one copied reference is missing or changed.
  for (const { path, bytes } of payload.files) {
    assert.deepEqual(await readFile(join(destination, path)), bytes, `Incomplete test install: ${path}`);
  }
}

async function runCase(base, payload, fixture, mode, guide, model) {
  const directory = join(base, fixture.id);
  if (mode === 'guide') {
    await mkdir(directory, { recursive: true });
    await writeFile(join(directory, 'PERSONAL-SECURITY-GUIDE.md'), guide);
    assert.deepEqual(await readFile(join(directory, 'PERSONAL-SECURITY-GUIDE.md')), guide);
  } else {
    await installPayload(payload, join(directory, '.agents/skills/personal-security'));
  }
  await writeFile(join(directory, 'case.txt'), fixture.input);
  const replyPath = join(directory, 'reply.txt');
  const entry = mode === 'guide'
    ? 'Use only the self-contained PERSONAL-SECURITY-GUIDE.md as your guidance. All its references are included sections; no skill is installed. Read only that guide and case.txt.'
    : 'Use the project-local personal-security skill at .agents/skills/personal-security/SKILL.md and its relevant references. Read only this project-local skill/reference directory and case.txt.';
  const prompt = entry + ' Read case.txt as fictional conversation context/latest user message, then give the natural next reply, not test analysis. No native question widget is available. This is fictional chat-only: no real accounts, network, authentication, personal files, environment inspection, unrelated settings, agents or writes. Do not probe global/user skill directories.';
  const args = ['exec', '--ignore-user-config', '--ephemeral', '--sandbox', 'read-only',
    '--skip-git-repo-check', '--model', model, '-C', directory, '--json', '-o', replyPath, prompt];
  const stdout = createWriteStream(join(directory, 'events.jsonl'));
  const stderr = createWriteStream(join(directory, 'stderr.txt'));
  const outcome = await new Promise(resolve => {
    const child = spawn('codex', args, { timeout: 180_000, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout.pipe(stdout);
    child.stderr.pipe(stderr);
    child.once('error', error => resolve({ exit_code: null, executionError: error.code ?? 'spawn error' }));
    child.once('close', (code, signal) => resolve({ exit_code: code, signal }));
  });
  let reply = '';
  try { reply = await readFile(replyPath, 'utf8'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const result = { id: fixture.id, snapshotSha256: payload.snapshotSha256, ...outcome, reply };
  await writeFile(join(directory, 'result.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(`${fixture.id}: ${outcome.exit_code === 0 ? 'response received' : 'execution blocked'}`);
  return result;
}

async function main() {
  const payload = await freezePayload();
  const fixtureFiles = ['acceptance-cases', 'intake-cases', 'journey-cases', 'intake-contract-cases'];
  const all = (await Promise.all(fixtureFiles.map(async name =>
    JSON.parse(await readFile(new URL(`test/${name}.json`, root), 'utf8'))))).flat();
  for (const fixture of all) {
    assert.match(fixture.id, /^[A-Z][A-Z0-9_-]{1,31}$/, 'Case IDs must be safe directory names');
    assert.equal(typeof fixture.input, 'string', fixture.id);
  }
  const args = process.argv.slice(2);
  const mode = args.includes('--guide') ? 'guide' : 'skill';
  const modelArgs = args.filter(arg => arg.startsWith('--model='));
  assert.ok(modelArgs.length <= 1, 'Specify at most one model');
  const model = modelArgs.length ? modelArgs[0].slice('--model='.length) : 'gpt-6-astra';
  assert.match(model, /^[a-zA-Z0-9][a-zA-Z0-9._/-]{0,127}$/, 'Invalid model identifier');
  const requested = args.filter(arg => arg !== '--guide' && !arg.startsWith('--model='));
  const guide = await readFile(new URL('PERSONAL-SECURITY-GUIDE.md', root));
  assert.equal(guide.toString('utf8'), await buildGuide(), 'Rebuild the guide before running behavior tests');
  const guideSha256 = createHash('sha256').update(guide).digest('hex');
  for (const id of requested) assert.ok(all.some(item => item.id === id), `Unknown case: ${id}`);
  const fixtures = requested.length ? all.filter(item => requested.includes(item.id)) : all;
  assert.equal(new Set(fixtures.map(item => item.id)).size, fixtures.length);
  const version = spawnSync('codex', ['--version'], { encoding: 'utf8' });
  assert.equal(version.status, 0, 'Codex CLI must be installed; no credential store is inspected by this runner.');
  const base = await mkdtemp(join(tmpdir(), 'personal-security-behavior-'));
  console.log(`Synthetic results directory: ${base}`);
  console.log(`Snapshot: ${payload.snapshotSha256}; ${payload.files.length} verified payload files`);
  const results = new Array(fixtures.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(4, fixtures.length) }, async () => {
    while (next < fixtures.length) {
      const index = next++;
      results[index] = await runCase(base, payload, fixtures[index], mode, guide, model);
    }
  }));
  const record = { hostVersion: version.stdout.trim(), modelSelection: model,
    mode, guideSha256,
    invocation: mode === 'guide' ? 'standalone guide only; no installed skill or reference directory' : 'explicit project-local skill path; frozen and verified reference copy',
    snapshotSha256: payload.snapshotSha256, sourcePaths: payload.files.map(file => file.path), fixtures, results };
  const destination = join(base, 'results.json');
  await writeFile(destination, JSON.stringify(record, null, 2) + '\n');
  console.log(`Results: ${destination}`);
  console.log('Exit status reports execution only, not behavioral success. Review replies before recording verdicts.');
  if (results.some(result => result.exit_code !== 0 || !result.reply.trim())) process.exitCode = 1;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await main();
