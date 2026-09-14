/**
 * The guard for the skills pack. Zero dependencies: `node --test`.
 *
 * Two halves. The first runs the real rules over the real tree, so a bad commit
 * fails here before it reaches anyone's machine. The second runs them over
 * synthetic trees that are each wrong in exactly one way, so every rule is
 * proven to actually bite — a guard nobody has seen fail is a wish.
 */

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  auditRepo,
  buildManifest,
  extractPreambleBlock,
  lintManifest,
  lintReadme,
  lintSkills,
  lintWrapper,
  parseFrontmatter,
  serializeManifest,
} from '../scripts/build-manifest.mjs';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const TEMPLATE = readFileSync(join(ROOT, 'skills', '_template', 'SKILL.md'), 'utf8');
const CANONICAL = extractPreambleBlock(parseFrontmatter(TEMPLATE).body);

// ---------------------------------------------------------------- the real tree

test('the committed tree passes every rule', () => {
  const { errors } = auditRepo(ROOT);
  assert.deepEqual(errors, [], `\n${errors.join('\n')}`);
});

test('the manifest builder is idempotent', () => {
  const { skills } = auditRepo(ROOT);
  assert.equal(serializeManifest(buildManifest(skills)), serializeManifest(buildManifest(skills)));
});

test('the committed manifest is what a fresh build produces', () => {
  const { skills } = auditRepo(ROOT);
  const committed = readFileSync(join(ROOT, 'skills', 'manifest.json'), 'utf8');
  assert.equal(committed, serializeManifest(buildManifest(skills)), 'run: npm run manifest');
});

test('every skill folder holds only prose', () => {
  const { skills } = auditRepo(ROOT);
  for (const skill of skills) {
    for (const file of skill.files) {
      assert.ok(
        file.path.endsWith('.md'),
        `${skill.name}/${file.path} is not markdown; a skill is prose an agent executes`
      );
    }
  }
});

test('bar hooks are unique across the pack', () => {
  const { manifest } = auditRepo(ROOT);
  const owners = new Map();
  for (const skill of manifest.skills) {
    for (const hook of skill.hooks.filter((h) => h.endsWith('-bar'))) {
      assert.equal(owners.get(hook), undefined, `${hook} is declared by ${owners.get(hook)} and ${skill.name}`);
      owners.set(hook, skill.name);
    }
  }
});

// ------------------------------------------------------------ synthetic fixtures

/** A minimal skill that passes every rule; `mutate` breaks exactly one thing. */
function skillFixture(name, { hooks = ['extra-checks', 'after-example'], extraFiles = [], body } = {}) {
  const markers = hooks.map((h) => `[HOOK: ${h}]\n`).join('\n');
  const rows = hooks.map((h) => `| \`${h}\` | somewhere | a rule |`).join('\n');
  const content =
    `---\nname: ${name}\n` +
    `description: Runs a Radial issue tracker chore from Claude Code or Codex.\n` +
    `metadata:\n  short-description: ${name}\n---\n\n` +
    (body ??
      `Does a thing. Leaves a note.\n\n**When to use it.** Now.\n\n**When not to.** Later.\n\n` +
        `${CANONICAL}\n\n## How it runs\n\n${markers}\n` +
        `## Extension points\n\n| Hook | Where it fires | What a section here can add |\n| --- | --- | --- |\n${rows}\n\n` +
        `## What it never does\n\n- Nothing surprising.\n`);
  return { name, dir: `/fake/${name}`, files: [{ path: 'SKILL.md', content }, ...extraFiles] };
}

function readmeFor(manifest, { dropHook = null, wrapper = null } = {}) {
  const lines = manifest.skills.map((s) => {
    const hooks = s.hooks.filter((h) => h !== dropHook).map((h) => `\`${h}\``).join(', ');
    return `| \`${s.name}\` | ${hooks} |`;
  });
  return `# Radial\n\n| Skill | Hooks |\n| --- | --- |\n${lines.join('\n')}\n\n${wrapper ? `\`\`\`markdown\n${wrapper}\`\`\`\n` : ''}`;
}

test('a skill folder missing from the manifest fails', () => {
  const skills = [skillFixture('rd-one'), skillFixture('rd-two')];
  const manifest = buildManifest([skills[0]]);
  const errors = lintManifest(skills, manifest);
  assert.ok(errors.some((e) => e.includes('rd-two') && e.includes('not in the manifest')), errors.join('\n'));
  assert.deepEqual(lintManifest(skills, buildManifest(skills)), []);
});

test('a hook marker sharing its line fails', () => {
  const good = skillFixture('rd-one');
  const bad = {
    ...good,
    files: [{ path: 'SKILL.md', content: good.files[0].content.replace('[HOOK: extra-checks]', 'then [HOOK: extra-checks]') }],
  };
  const errors = lintSkills([bad], CANONICAL);
  assert.ok(errors.some((e) => e.includes('not alone on its line')), errors.join('\n'));
  assert.deepEqual(lintSkills([good], CANONICAL), []);
});

test('two skills declaring the same bar hook fail', () => {
  const a = skillFixture('rd-one', { hooks: ['extra-checks', 'plan-bar'] });
  const b = skillFixture('rd-two', { hooks: ['extra-checks', 'plan-bar'] });
  const errors = lintSkills([a, b], CANONICAL);
  assert.ok(errors.some((e) => e.includes('plan-bar') && e.includes('unique across the pack')), errors.join('\n'));
  const fixed = skillFixture('rd-two', { hooks: ['extra-checks', 'file-bar'] });
  assert.deepEqual(lintSkills([a, fixed], CANONICAL), []);
});

test('an executable inside a skill folder fails', () => {
  const bad = skillFixture('rd-one', { extraFiles: [{ path: 'helper.sh', content: '#!/bin/sh\necho hi\n' }] });
  const errors = lintSkills([bad], CANONICAL);
  assert.ok(errors.some((e) => e.includes('helper.sh') && e.includes('executable')), errors.join('\n'));
  assert.deepEqual(lintSkills([skillFixture('rd-one')], CANONICAL), []);
});

test('a private-tooling string in a body fails', () => {
  const good = skillFixture('rd-one');
  const bad = {
    ...good,
    files: [{ path: 'SKILL.md', content: good.files[0].content.replace('Does a thing.', 'Run gstack first.') }],
  };
  const errors = lintSkills([bad], CANONICAL);
  assert.ok(errors.some((e) => e.includes('private tooling')), errors.join('\n'));
  assert.deepEqual(lintSkills([good], CANONICAL), []);
});

test('a preamble block that differs by one character fails', () => {
  const good = skillFixture('rd-one');
  const bad = {
    ...good,
    files: [{ path: 'SKILL.md', content: good.files[0].content.replace('Project scope wins whole.', 'Project scope wins whole!') }],
  };
  const errors = lintSkills([bad], CANONICAL);
  assert.ok(errors.some((e) => e.includes('byte for byte')), errors.join('\n'));
  assert.deepEqual(lintSkills([good], CANONICAL), []);
});

test('an Extension points table that omits a marker fails', () => {
  const good = skillFixture('rd-one');
  const bad = {
    ...good,
    files: [{ path: 'SKILL.md', content: good.files[0].content.replace('| `after-example` | somewhere | a rule |\n', '') }],
  };
  const errors = lintSkills([bad], CANONICAL);
  assert.ok(errors.some((e) => e.includes('Extension points table')), errors.join('\n'));
});

test('a README missing one hook fails', () => {
  const manifest = buildManifest([skillFixture('rd-one')]);
  const errors = lintReadme(readmeFor(manifest, { dropHook: 'after-example' }), manifest);
  assert.ok(errors.some((e) => e.includes('after-example')), errors.join('\n'));
  assert.deepEqual(lintReadme(readmeFor(manifest), manifest), []);
});

test('a worked wrapper with an unknown section fails', () => {
  const manifest = buildManifest([skillFixture('rd-one')]);
  const wrapper = (heading) =>
    `---\nname: team-one\ndescription: Our rules.\nextends: rd-one\n---\n\nRead rd-one first.\n\n## ${heading}\n\n- Do the thing.\n`;
  const bad = lintReadme(readmeFor(manifest, { wrapper: wrapper('not-a-hook') }), manifest);
  assert.ok(bad.some((e) => e.includes('not a hook of rd-one')), bad.join('\n'));
  assert.deepEqual(lintReadme(readmeFor(manifest, { wrapper: wrapper('extra-checks') }), manifest), []);
});

test('a wrapper may not take a reserved rd-* name', () => {
  const manifest = buildManifest([skillFixture('rd-one')]);
  const errors = lintWrapper('---\nname: rd-mine\ndescription: x\nextends: rd-one\n---\n\nbody\n', manifest);
  assert.ok(errors.some((e) => e.includes('reserved name')), errors.join('\n'));
});

test('a wrapper extending an unknown skill fails', () => {
  const manifest = buildManifest([skillFixture('rd-one')]);
  const errors = lintWrapper('---\nname: team-one\ndescription: x\nextends: rd-nope\n---\n\nbody\n', manifest);
  assert.ok(errors.some((e) => e.includes('not a skill in the manifest')), errors.join('\n'));
});

test('a manifest file path that escapes its folder is rejected', () => {
  const skill = skillFixture('rd-one');
  const manifest = buildManifest([skill]);
  manifest.skills[0].files.push({ path: '../outside.md', sha256: 'x' });
  const errors = lintManifest([skill], manifest);
  assert.ok(errors.some((e) => e.includes('escapes the skill folder')), errors.join('\n'));
});
