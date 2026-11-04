#!/usr/bin/env python3
"""Live Radial benchmark: the claim race from linear_tasks.py, through Radial's atomic REST claim.

10 rounds x 20 workers. Each round creates one issue, releases 20 workers through a barrier, and every
worker calls POST /api/v1/issues/{id}/claim once. The claim is a conditional update (assignee is null or
the caller), so a second caller gets 409. Then a GET reads the assignee as final_owner.

Unassign before the round: on production, an issue created by an agent key is auto-assigned to the key's
human owner, so every claim would 409. After each create, the script PATCHes {"assignee":"none"} and GETs
the issue; it aborts if the assignee is not null. (The first run on 2026-11-04 skipped this step: all 200
of 200 claims were rejected. That run is discarded.)

Modes:
  default            20 keys, one per worker, each a DISTINCT agent identity. This is the atomicity test.
  --single-identity  key 1 for all 20 workers (Linear's setup). A re-claim by the holder is idempotent
                     success, so every worker gets 2xx. This mode does NOT test atomicity; the output says so.

WRITES to the workspace behind RADIAL_KEYS: 10 race issues plus one probe issue per identity (the probe's
creator tells us who each key is). Every issue it creates is deleted at the end (canceled if delete is
refused), and the cleanup is recorded in the output. Use a dedicated test workspace.
Key values, emails and names are never printed or written: identities are mapped to w0..w19 labels.
Output: runs/<today>/radial-live/claim-race-rest.json (claim-race-rest-single.json with --single-identity);
override the directory with RADIAL_BENCH_OUT, the API with RADIAL_API_URL (default
https://www.radial.build/api/v1; the bare /v1 path 404s).
Usage: RADIAL_KEYS=k0,...,k19 RADIAL_TEAM=BENCH python3 scripts/radial_race.py [--single-identity]
"""
import json, os, sys, time, threading, concurrent.futures as cf, urllib.request, urllib.error, urllib.parse
from pathlib import Path

SINGLE = '--single-identity' in sys.argv[1:]
KEYS = [k.strip() for k in os.environ.get('RADIAL_KEYS', '').split(',') if k.strip()]
TEAM = os.environ.get('RADIAL_TEAM', '').strip()
if not TEAM: sys.exit('RADIAL_TEAM is not set (the team key in the dedicated test workspace)')
if SINGLE and not KEYS: sys.exit('RADIAL_KEYS is not set (--single-identity uses the first key)')
if not SINGLE and len(KEYS) != 20: sys.exit(f'RADIAL_KEYS must hold 20 comma-separated agent keys, got {len(KEYS)}')
API = os.environ.get('RADIAL_API_URL', 'https://www.radial.build/api/v1').rstrip('/')
ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get('RADIAL_BENCH_OUT', ROOT / f'runs/{time.strftime("%Y-%m-%d")}/radial-live'))
FILE = 'claim-race-rest-single.json' if SINGLE else 'claim-race-rest.json'
ROUNDS, WORKERS = 10, 20
WKEYS = [KEYS[0]] * WORKERS if SINGLE else KEYS

def req(method, path, key, body=None):
    """Returns (status, parsed JSON or None). Never raises on an HTTP status."""
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data, {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp: st, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e: st, raw = e.code, e.read().decode()
    try: return st, json.loads(raw) if raw else None
    except ValueError: return st, None

def ipath(ident, suffix=''): return '/issues/' + urllib.parse.quote(ident, safe='') + suffix
def err(st, j):  # status + machine code only: the message can name the holder's email
    return f'error:{st} {((j or {}).get("error") or {}).get("code", "")}'.strip()
def who(user): return (user['email'], user['name']) if user else None  # in-memory only

created, cleanup = [], []
def create(key, title):
    st, j = req('POST', '/issues', key, {'title': title, 'team': TEAM})
    if st != 201: raise RuntimeError(f'create "{title}" failed: {err(st, j)}')
    created.append(j['issue']['id']); return j['issue']

def unassign(ident):
    # Production auto-assigns an agent-created issue to the key's human owner; clear it or every claim 409s.
    st, j = req('PATCH', ipath(ident), KEYS[0], {'assignee': 'none'})
    if not 200 <= st < 300: raise RuntimeError(f'unassign {ident} failed: {err(st, j)}')
    st, j = req('GET', ipath(ident), KEYS[0])
    if st != 200: raise RuntimeError(f'read-back of {ident} failed: {err(st, j)}')
    if j['issue']['assignee'] is not None: raise RuntimeError(f'{ident} still has an assignee after unassign')

def clean():
    for ident in created:
        st, j = req('DELETE', ipath(ident), KEYS[0])
        if 200 <= st < 300: cleanup.append({'issue': ident, 'action': 'deleted'}); continue
        st2, j2 = req('PATCH', ipath(ident), KEYS[0], {'status': 'canceled'})
        cleanup.append({'issue': ident, 'action': 'canceled' if 200 <= st2 < 300 else 'failed',
                        'delete': err(st, j), **({} if 200 <= st2 < 300 else {'cancel': err(st2, j2)})})

rounds, label, fatal = [], {}, None
try:
    # Who is each key? The probe issue's creator is the key's subject. Distinct identities are required.
    for k, key in enumerate(KEYS if not SINGLE else KEYS[:1]):
        u = who(create(key, f'race identity probe w{k}')['creator'])
        if u is None: raise RuntimeError(f'probe for w{k} came back with no creator')
        if u in label: raise RuntimeError(f'w{k} is the same identity as {label[u]}: each key must be a distinct agent')
        label[u] = 'w0-w19 (single identity)' if SINGLE else f'w{k}'
    for r in range(ROUNDS):
        iss = create(KEYS[0], f'race round {r}'); unassign(iss['id'])
        bar = threading.Barrier(WORKERS); res = [None] * WORKERS
        def worker(k):
            bar.wait()
            try: st, j = req('POST', ipath(iss['id'], '/claim'), WKEYS[k], {})
            except Exception as e: res[k] = 'error:' + type(e).__name__; return
            res[k] = 'claimed' if 200 <= st < 300 else 'rejected-409' if st == 409 else err(st, j)
        with cf.ThreadPoolExecutor(WORKERS) as ex: list(ex.map(worker, range(WORKERS)))
        st, j = req('GET', ipath(iss['id']), KEYS[0])
        fin = (label.get(who(j['issue']['assignee']), 'unknown') if j['issue']['assignee'] else None) if st == 200 else err(st, j)
        c = sum(1 for x in res if x == 'claimed')
        # One identity holding it after 20 idempotent re-claims overwrote nobody.
        rounds.append({'round': r, 'issue': iss['id'], 'workers': WORKERS, 'believed_claimed': c, 'final_owner': fin,
                       'silent_overwrites': 0 if SINGLE else max(c - 1, 0), 'results': res}); print('race', r, c, fin)
except Exception as e:
    fatal = f'{type(e).__name__}: {e}'; print('aborted:', fatal, file=sys.stderr)
finally:
    clean()

method = ('each race issue is PATCHed to assignee "none" after create and read back as null before the round '
          '(production auto-assigns an agent-created issue to the key\'s human owner; a 2026-11-04 run without this '
          'step got 200 of 200 claims rejected and is discarded); '
          '20 workers per round, barrier, one POST /api/v1/issues/{id}/claim each (conditional update: assignee null or caller, else 409); '
          + ('ONE identity for all 20 workers (Linear setup)' if SINGLE else '20 distinct agent identities, one per worker'))
out = {'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'method': method, 'rounds': rounds,
       'rounds_with_multiple_claimants': sum(1 for x in rounds if x['believed_claimed'] > 1),
       'total_silent_overwrites': sum(x['silent_overwrites'] for x in rounds),
       'mode': 'single-identity' if SINGLE else 'multi-identity', 'api': API, 'distinct_identities': len(label),
       'cleanup': cleanup, 'cleanup_complete': all(c['action'] != 'failed' for c in cleanup)}
if SINGLE:
    out['idempotent_reclaims'] = sum(max(x['believed_claimed'] - 1, 0) for x in rounds)
    out['note'] = ('Every worker shares one identity, and a re-claim by the current holder is idempotent success (2xx). '
                   'believed_claimed > 1 here is expected and is not an overwrite; this mode does not test atomicity. '
                   'Run without --single-identity for the atomicity test.')
if fatal: out['aborted'] = fatal
OUT.mkdir(parents=True, exist_ok=True); (OUT / FILE).write_text(json.dumps(out, indent=1) + '\n'); print('wrote', OUT / FILE)
if fatal or not out['cleanup_complete']: sys.exit(1)
