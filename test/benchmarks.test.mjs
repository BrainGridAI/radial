/**
 * The guard for benchmarks/. It ships in a public repo, so the first test runs
 * the secret scanner over the real folder, and the second proves the scanner
 * bites on planted fakes. The rest pin evidence.json to files that exist here.
 */

import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(new URL('.', import.meta.url)), '..');
const BENCH = join(ROOT, 'benchmarks');
const SCAN = join(BENCH, 'scripts', 'scan_secrets.sh');
const scan = (dir) => spawnSync('bash', [SCAN, dir], { encoding: 'utf8' });

test('the benchmark folder has no secrets, private paths or identities', () => {
  const r = scan(BENCH);
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /scan_secrets: PASS/);
});

test('the scanner fails on planted fakes', () => {
  const dir = mkdtempSync(join(tmpdir(), 'scan-probe-'));
  try {
    const fakes = [
      'lin_api_ABCDEFGH12345678',
      'rk_write_abcdef1234',
      'Authorization: Bearer abcdefghijklmnopqrstu',
      '/workspace/private',
      'viewer 01b78fd2-2db2-4609-9e5d-05aea8aeb636',
      'someone@company.test',
    ];
    for (const [i, fake] of fakes.entries()) {
      writeFileSync(join(dir, 'f.txt'), `${fake}\n`);
      const r = scan(dir);
      assert.equal(r.status, 1, `fake #${i} slipped through: ${r.stdout}`);
    }
    writeFileSync(join(dir, 'f.txt'), 'example: admin@atlassian.com\n');
    assert.equal(scan(dir).status, 0, 'a vendor doc example address is allowed');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('every evidence id maps to a file in benchmarks/, once', () => {
  const { evidence } = JSON.parse(readFileSync(join(BENCH, 'evidence.json'), 'utf8'));
  const ids = evidence.map((e) => e.id);
  assert.equal(new Set(ids).size, ids.length, 'duplicate evidence id');
  for (const e of evidence) {
    assert.ok(['MEASURED', 'DOCUMENTED', 'SIMULATED', 'ESTIMATE'].includes(e.label), `${e.id}: bad label ${e.label}`);
    assert.ok(existsSync(join(BENCH, e.file)), `${e.id}: missing ${e.file}`);
  }
  for (const id of ['L-LIVE-MCP-TOOLS', 'R-LIVE-MCP-TOOLS', 'L-LIVE-T1T4', 'L-LIVE-RACE']) {
    assert.ok(ids.includes(id), `missing live id ${id}`);
  }
});

test('the live numbers in evidence.json match the raw outputs', () => {
  const ev = Object.fromEntries(
    JSON.parse(readFileSync(join(BENCH, 'evidence.json'), 'utf8')).evidence.map((e) => [e.id, e.value]),
  );
  const raw = (p) => JSON.parse(readFileSync(join(BENCH, 'runs/2026-11-02', p), 'utf8'));
  assert.equal(ev['L-LIVE-MCP-TOOLS'].tools, raw('linear-live/mcp-tools-list.json').count);
  assert.equal(ev['R-LIVE-MCP-TOOLS'].tools, raw('radial-live/mcp-tools-list.json').count);
  assert.equal(ev['L-LIVE-T1T4'].median_ms, raw('linear-live/tasks-T1-T4-mcp.json').median_ms);
  assert.equal(ev['L-LIVE-RACE'].total_silent_overwrites, raw('linear-live/claim-race-graphql.json').total_silent_overwrites);
});

test('benchmark prose has no em dashes', () => {
  for (const f of ['README.md', 'METHODOLOGY.md', 'coverage-matrix.md']) {
    const text = readFileSync(join(BENCH, f), 'utf8');
    assert.ok(!text.includes('—'), `em dash in benchmarks/${f}`);
  }
});
