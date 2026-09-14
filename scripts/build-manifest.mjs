#!/usr/bin/env node
/**
 * Builds `skills/manifest.json` and holds the rules the guard test enforces.
 *
 * The manifest is the contract three other things read: the `radial skills`
 * installer (files + hashes + hook lists), the radial.build docs (hook tables
 * rendered from it, so a renamed hook cannot drift), and `npx skills` /
 * `$skill-installer` (which read the folders directly). Everything here is
 * pure Node with no dependencies, because this repo is the public source of the
 * pack and installing a toolchain to check a folder of markdown is a tax.
 *
 * Usage:
 *   node scripts/build-manifest.mjs           # write skills/manifest.json
 *   node scripts/build-manifest.mjs --check   # exit 1 if the file is stale
 */

import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, posix, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const MANIFEST_VERSION = 1;

/** Directories under `skills/` starting with `_` are templates, never installed. */
const TEMPLATE_PREFIX = '_';

/** Nothing executable ships inside a skill folder — see README, "What a skill is". */
const FORBIDDEN_EXTENSIONS = ['.sh', '.py', '.mjs', '.cjs', '.js', '.ts', '.rb', '.ps1', '.bat'];

/**
 * Strings that would leak private tooling into a public, generic skill. Each is
 * a regex so `na-` matches the skill-name prefix but not `persona-based`.
 */
const PRIVATE_TOOLING = [
  { label: 'na-* skill name', re: /\bna-[a-z]/ },
  { label: 'gstack', re: /gstack/i },
  { label: 'conductor', re: /\bconductor\b/i },
  { label: 'Dropbox path', re: /Dropbox/ },
  { label: 'PSM team key', re: /\bPSM\b/ },
  { label: 'Plansmith', re: /Plansmith/i },
  { label: 'pipeline-state', re: /pipeline-state/ },
  { label: 'ship-status', re: /ship-status/ },
  { label: '.context/ path', re: /\.context\// },
  { label: 'test-users', re: /test-users/ },
];

/** A hook marker, alone on its own line. */
const MARKER_LINE = /^\[HOOK: ([a-z][a-z0-9-]*)\]\s*$/;
/** The same marker anywhere in a line — used to catch one that isn't alone. */
const MARKER_ANYWHERE = /\[HOOK: [a-z][a-z0-9-]*\]/;

/** The heading that opens the block every built-in carries byte for byte. */
const PREAMBLE_HEADING = '## Extensions (read this first)';

export function sha256(input) {
  return createHash('sha256').update(input).digest('hex');
}

/**
 * A deliberately small YAML reader: `key: value` pairs plus one level of
 * nesting under `metadata:`. Skill frontmatter is a fixed, flat shape, so a
 * full YAML parser would be a dependency bought for nothing — and the guard
 * below rejects anything this cannot read, so an exotic file fails loudly
 * instead of parsing to something surprising.
 */
export function parseFrontmatter(text) {
  if (!text.startsWith('---\n')) return { data: null, body: text, error: 'missing frontmatter' };
  const end = text.indexOf('\n---', 3);
  if (end === -1) return { data: null, body: text, error: 'unterminated frontmatter' };
  const raw = text.slice(4, end + 1);
  const body = text.slice(text.indexOf('\n', end + 1) + 1);

  const data = {};
  let section = null;
  for (const line of raw.split('\n')) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) continue;
    const indented = /^\s+/.test(line);
    const match = line.match(/^\s*([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$/);
    if (!match) return { data: null, body, error: `unreadable frontmatter line: ${line}` };
    const [, key, rawValue] = match;
    const value = unquote(rawValue.trim());
    if (!indented) {
      section = value === '' ? key : null;
      if (value === '') data[key] = {};
      else data[key] = value;
    } else {
      if (!section) return { data: null, body, error: `indented key outside a block: ${line}` };
      data[section][key] = value;
    }
  }
  return { data, body, error: null };
}

function unquote(value) {
  if (value.length >= 2 && ((value[0] === '"' && value.at(-1) === '"') || (value[0] === "'" && value.at(-1) === "'"))) {
    return value.slice(1, -1);
  }
  return value;
}

/** Hook names in the order their markers appear. */
export function extractHooks(body) {
  const hooks = [];
  for (const line of body.split('\n')) {
    const match = line.match(MARKER_LINE);
    if (match) hooks.push(match[1]);
  }
  return hooks;
}

/** Lines that hold a marker but are not exactly a marker line. */
export function malformedMarkerLines(body) {
  return body
    .split('\n')
    .map((line, index) => ({ line, number: index + 1 }))
    .filter(({ line }) => MARKER_ANYWHERE.test(line) && !MARKER_LINE.test(line));
}

/** The `## Extensions (read this first)` block, heading included, verbatim. */
export function extractPreambleBlock(body) {
  // Anchored to the start of a line: the template quotes the heading inside an
  // explanatory comment, and an unanchored search would capture that instead.
  const match = body.match(/^## Extensions \(read this first\)$/m);
  const start = match?.index ?? -1;
  if (start === -1) return null;
  const after = body.indexOf('\n## ', start + PREAMBLE_HEADING.length);
  const block = after === -1 ? body.slice(start) : body.slice(start, after + 1);
  return block.trimEnd();
}

/** The `## ` headings of a body, in order. */
export function headings(body) {
  return body
    .split('\n')
    .filter((line) => line.startsWith('## '))
    .map((line) => line.slice(3).trim());
}

function walk(dir, base = dir) {
  const out = [];
  for (const entry of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.name.startsWith('.')) continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full, base));
    else if (entry.isFile()) out.push(relative(base, full).split(sep).join(posix.sep));
  }
  return out;
}

/**
 * Read `skills/` into `{ name, dir, files: [{ path, content }] }`, templates
 * excluded. `dir` is absolute; `path` is always relative to the skill folder
 * and POSIX-separated, which is what the installer resolves against.
 */
export function readSkills(skillsDir) {
  let entries;
  try {
    entries = readdirSync(skillsDir, { withFileTypes: true });
  } catch {
    return [];
  }
  return entries
    .filter((e) => e.isDirectory() && !e.name.startsWith(TEMPLATE_PREFIX))
    .map((e) => e.name)
    .sort()
    .map((name) => {
      const dir = join(skillsDir, name);
      const files = walk(dir).map((path) => ({
        path,
        content: readFileSync(join(dir, ...path.split(posix.sep)), 'utf8'),
      }));
      return { name, dir, files };
    });
}

/** The digest the installer verifies: every file path and content, in order. */
export function skillDigest(files) {
  const material = files.map((f) => `${f.path}\n${sha256(f.content)}\n`).join('');
  return sha256(material);
}

export function buildManifest(skills) {
  return {
    version: MANIFEST_VERSION,
    skills: skills.map((skill) => {
      const main = skill.files.find((f) => f.path === 'SKILL.md');
      const { data, body } = main ? parseFrontmatter(main.content) : { data: null, body: '' };
      return {
        name: skill.name,
        description: data?.description ?? '',
        shortDescription: data?.metadata?.['short-description'] ?? '',
        files: skill.files.map((f) => ({ path: f.path, sha256: sha256(f.content) })),
        sha256: skillDigest(skill.files),
        hooks: extractHooks(body),
      };
    }),
  };
}

export function serializeManifest(manifest) {
  return `${JSON.stringify(manifest, null, 2)}\n`;
}

/**
 * Every rule a skill body must satisfy. Returns a list of human sentences; an
 * empty list is a pass. Kept as data rather than assertions so the guard test
 * can run it over synthetic bad trees and prove each rule actually bites.
 */
export function lintSkills(skills, canonicalPreamble) {
  const errors = [];
  const barOwners = new Map();

  for (const skill of skills) {
    const where = (msg) => errors.push(`${skill.name}: ${msg}`);
    const main = skill.files.find((f) => f.path === 'SKILL.md');
    if (!main) {
      where('has no SKILL.md');
      continue;
    }

    for (const file of skill.files) {
      if (FORBIDDEN_EXTENSIONS.some((ext) => file.path.endsWith(ext))) {
        where(`ships an executable file (${file.path}); a skill is prose, put deterministic work in the CLI`);
      }
      for (const { label, re } of PRIVATE_TOOLING) {
        if (re.test(file.content)) where(`${file.path} mentions private tooling (${label})`);
      }
    }

    const { data, body, error } = parseFrontmatter(main.content);
    if (error || !data) {
      where(`frontmatter is unreadable (${error ?? 'no data'})`);
      continue;
    }
    if (data.name !== skill.name) where(`frontmatter name "${data.name}" does not match the directory`);
    if (!data.description) where('frontmatter has no description');
    else {
      if (data.description.length > 1024) where('description is over 1024 characters');
      if (!/Radial/.test(data.description)) where('description does not name Radial (skills.sh searches it)');
      if (!/issue/i.test(data.description)) where('description does not say issue tracker (skills.sh searches it)');
      if (!/Claude Code|Codex/.test(data.description)) where('description names neither Claude Code nor Codex');
    }
    if (!data.metadata || !data.metadata['short-description']) {
      where('frontmatter has no metadata.short-description (the Codex picker reads it)');
    }
    if (data.extends) where('a built-in must not declare extends');

    for (const { line, number } of malformedMarkerLines(body)) {
      where(`line ${number} holds a hook marker that is not alone on its line: ${line.trim()}`);
    }

    const hooks = extractHooks(body);
    if (hooks.length === 0) where('declares no extension hooks');
    const seen = new Set();
    for (const hook of hooks) {
      if (seen.has(hook)) where(`declares the hook "${hook}" twice`);
      seen.add(hook);
      if (hook.endsWith('-bar')) {
        const owner = barOwners.get(hook);
        if (owner && owner !== skill.name) {
          errors.push(`bar hook "${hook}" is declared by both ${owner} and ${skill.name}; bar names are unique across the pack`);
        }
        barOwners.set(hook, skill.name);
      }
    }

    const preamble = extractPreambleBlock(body);
    if (preamble === null) where(`has no "${PREAMBLE_HEADING}" block`);
    else if (preamble !== canonicalPreamble) {
      where(`its "${PREAMBLE_HEADING}" block differs from skills/_template/SKILL.md; it must be copied byte for byte`);
    }

    const order = headings(body);
    const extIndex = order.indexOf('Extensions (read this first)');
    const pointsIndex = order.indexOf('Extension points');
    const neverIndex = order.indexOf('What it never does');
    if (extIndex !== 0) where('the Extensions block must be the first "## " heading');
    if (pointsIndex === -1) where('has no "## Extension points" table');
    if (neverIndex === -1) where('has no "## What it never does" section');
    if (pointsIndex !== -1 && neverIndex !== -1 && neverIndex < pointsIndex) {
      where('"What it never does" must come after "Extension points"');
    }
    if (pointsIndex !== -1 && pointsIndex !== order.length - 2) {
      where('"Extension points" must be the second-to-last section');
    }
    if (neverIndex !== -1 && neverIndex !== order.length - 1) {
      where('"What it never does" must be the last section');
    }

    const tableHooks = extensionPointRows(body);
    if (tableHooks.join(',') !== hooks.join(',')) {
      where(`the Extension points table lists [${tableHooks.join(', ')}] but the markers are [${hooks.join(', ')}]`);
    }

    const summary = body.slice(0, body.indexOf(PREAMBLE_HEADING) === -1 ? 0 : body.indexOf(PREAMBLE_HEADING));
    if (!/\*\*When to use it\.\*\*/.test(summary)) where('has no "**When to use it.**" line above the Extensions block');
    if (!/\*\*When not to\.\*\*/.test(summary)) where('has no "**When not to.**" line above the Extensions block');
  }

  return errors;
}

/** The hook names in the "## Extension points" table, in row order. */
export function extensionPointRows(body) {
  const start = body.indexOf('\n## Extension points');
  if (start === -1) return [];
  const after = body.indexOf('\n## ', start + 1);
  const section = after === -1 ? body.slice(start) : body.slice(start, after);
  const rows = [];
  for (const line of section.split('\n')) {
    const match = line.match(/^\|\s*`([a-z][a-z0-9-]*)`\s*\|/);
    if (match) rows.push(match[1]);
  }
  return rows;
}

/** The manifest must describe exactly what is on disk. */
export function lintManifest(skills, manifest) {
  const errors = [];
  if (manifest?.version !== MANIFEST_VERSION) {
    errors.push(`manifest version is ${manifest?.version}, expected ${MANIFEST_VERSION}`);
    return errors;
  }
  const listed = new Set((manifest.skills ?? []).map((s) => s.name));
  for (const skill of skills) {
    if (!listed.has(skill.name)) errors.push(`skills/${skill.name} is on disk but not in the manifest; run npm run manifest`);
  }
  for (const entry of manifest.skills ?? []) {
    const skill = skills.find((s) => s.name === entry.name);
    if (!skill) {
      errors.push(`manifest lists ${entry.name} but skills/${entry.name} does not exist`);
      continue;
    }
    const onDisk = skill.files.map((f) => f.path).join(',');
    const inManifest = (entry.files ?? []).map((f) => f.path).join(',');
    if (onDisk !== inManifest) errors.push(`${entry.name}: manifest files [${inManifest}] do not match disk [${onDisk}]`);
    for (const file of entry.files ?? []) {
      const actual = skill.files.find((f) => f.path === file.path);
      if (actual && sha256(actual.content) !== file.sha256) errors.push(`${entry.name}/${file.path}: sha256 does not match disk`);
      if (file.path.startsWith('/') || file.path.split('/').includes('..')) {
        errors.push(`${entry.name}: file path "${file.path}" escapes the skill folder`);
      }
    }
    if (entry.sha256 !== skillDigest(skill.files)) errors.push(`${entry.name}: skill digest does not match disk`);
    const main = skill.files.find((f) => f.path === 'SKILL.md');
    const hooks = main ? extractHooks(parseFrontmatter(main.content).body) : [];
    if ((entry.hooks ?? []).join(',') !== hooks.join(',')) errors.push(`${entry.name}: manifest hooks do not match the markers in SKILL.md`);
  }
  return errors;
}

/**
 * README parity. The README is the GitHub landing page, so it rots first: this
 * fails the build when a skill or one of its hooks never reaches it, and when a
 * worked wrapper printed there would not actually install.
 */
export function lintReadme(readme, manifest) {
  const errors = [];
  for (const skill of manifest.skills ?? []) {
    if (!readme.includes(`\`${skill.name}\``)) errors.push(`README does not mention \`${skill.name}\``);
    for (const hook of skill.hooks ?? []) {
      if (!readme.includes(`\`${hook}\``)) errors.push(`README does not list the hook \`${hook}\` (${skill.name})`);
    }
  }
  for (const wrapper of workedWrappers(readme)) {
    errors.push(...lintWrapper(wrapper, manifest).map((e) => `README worked wrapper: ${e}`));
  }
  return errors;
}

/** Fenced blocks in a markdown document that are wrapper skill files. */
export function workedWrappers(markdown) {
  const blocks = [];
  const fence = /```[a-z]*\n([\s\S]*?)```/g;
  let match = fence.exec(markdown);
  while (match !== null) {
    if (/^---\n[\s\S]*?\nextends:/m.test(match[1])) blocks.push(match[1]);
    match = fence.exec(markdown);
  }
  return blocks;
}

/**
 * The rules the CLI applies to a wrapper before copying it, restated here so a
 * documented example cannot drift out of installability.
 */
export function lintWrapper(source, manifest) {
  const errors = [];
  const { data, body, error } = parseFrontmatter(source);
  if (error || !data) return [`frontmatter is unreadable (${error ?? 'no data'})`];
  if (!data.name) errors.push('has no name');
  else if (data.name.startsWith('rd-')) errors.push(`takes the reserved name "${data.name}"; rd-* belongs to the pack`);
  if (!data.description) errors.push('has no description');
  const target = manifest.skills?.find((s) => s.name === data.extends);
  if (!target) {
    errors.push(`extends "${data.extends}", which is not a skill in the manifest`);
    return errors;
  }
  for (const heading of headings(body)) {
    if (!target.hooks.includes(heading)) {
      errors.push(`section "## ${heading}" is not a hook of ${target.name} (its hooks: ${target.hooks.join(', ')})`);
    }
  }
  return errors;
}

/** Everything, for a repo root. Returns `{ manifest, errors }`. */
export function auditRepo(root) {
  const skillsDir = join(root, 'skills');
  const skills = readSkills(skillsDir);
  const template = readFileSync(join(skillsDir, '_template', 'SKILL.md'), 'utf8');
  const canonical = extractPreambleBlock(parseFrontmatter(template).body);
  const manifest = buildManifest(skills);

  const errors = [...lintSkills(skills, canonical)];
  let committed = null;
  try {
    committed = JSON.parse(readFileSync(join(skillsDir, 'manifest.json'), 'utf8'));
  } catch {
    errors.push('skills/manifest.json is missing or unreadable; run npm run manifest');
  }
  if (committed) {
    errors.push(...lintManifest(skills, committed));
    if (serializeManifest(committed) !== serializeManifest(manifest)) {
      errors.push('skills/manifest.json is stale; run npm run manifest and commit the result');
    }
  }
  try {
    errors.push(...lintReadme(readFileSync(join(root, 'README.md'), 'utf8'), manifest));
  } catch {
    errors.push('README.md is missing');
  }
  return { manifest, skills, canonical, errors };
}

function main() {
  const root = join(fileURLToPath(new URL('.', import.meta.url)), '..');
  const check = process.argv.includes('--check');
  const skills = readSkills(join(root, 'skills'));
  const manifest = buildManifest(skills);
  const path = join(root, 'skills', 'manifest.json');
  const next = serializeManifest(manifest);
  let current = null;
  try {
    current = readFileSync(path, 'utf8');
  } catch {
    /* not written yet */
  }

  if (check) {
    if (current !== next) {
      process.stderr.write('skills/manifest.json is stale. Run: npm run manifest\n');
      process.exitCode = 1;
      return;
    }
    process.stdout.write(`manifest is current (${manifest.skills.length} skills)\n`);
    return;
  }

  writeFileSync(path, next);
  process.stdout.write(
    `wrote skills/manifest.json — ${manifest.skills.length} skills, ${manifest.skills.reduce((n, s) => n + s.hooks.length, 0)} hooks\n`
  );
}

// Run only when invoked directly, so the test can import the rules above.
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
