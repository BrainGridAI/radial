#!/usr/bin/env python3
"""Live Linear benchmark, part 1: MCP tools/list against Linear's official remote MCP.

The key is read from the LINEAR_API_KEY env var and never printed or written.
Output: runs/2026-11-02/linear-live/mcp-tools-list.json (override with LINEAR_BENCH_OUT).
Usage: LINEAR_API_KEY=... python3 scripts/linear_live.py
"""
import json, os, sys, time, statistics, concurrent.futures as cf, urllib.request, urllib.error
from pathlib import Path

KEY = os.environ.get('LINEAR_API_KEY', '').strip()
if not KEY:
    sys.exit('LINEAR_API_KEY is not set (create a personal API key in a scratch Linear workspace)')
ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get('LINEAR_BENCH_OUT', ROOT / 'runs/2026-11-02/linear-live'))
MCP = 'https://mcp.linear.app/mcp'; GQL = 'https://api.linear.app/graphql'

def post(url, body, hdr):
    r = urllib.request.Request(url, json.dumps(body).encode(), {**hdr, 'Content-Type': 'application/json'})
    t = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=60) as resp: raw = resp.read().decode(); h = dict(resp.headers)
    except urllib.error.HTTPError as e: raw = e.read().decode(); raise RuntimeError(f'{e.code} {raw[:300]}')
    return raw, h, (time.perf_counter() - t) * 1000

def gql(q, v=None):
    raw, _, ms = post(GQL, {'query': q, 'variables': v or {}}, {'Authorization': KEY}); return json.loads(raw), ms

class Mcp:
    def __init__(s): s.sid = None; s.n = 0; s.bytes = 0
    def call(s, method, params=None, notify=False):
        h = {'Authorization': 'Bearer ' + KEY, 'Accept': 'application/json, text/event-stream'}
        if s.sid: h['Mcp-Session-Id'] = s.sid
        body = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notify: s.n += 1; body['id'] = s.n
        raw, hd, ms = post(MCP, body, h); s.bytes += len(raw)
        s.sid = s.sid or hd.get('Mcp-Session-Id') or hd.get('mcp-session-id')
        if notify: return None, ms
        txt = raw
        if 'data:' in raw: txt = [l[5:].strip() for l in raw.splitlines() if l.startswith('data:')][-1]
        return json.loads(txt), ms
    def tool(s, name, args):
        r, ms = s.call('tools/call', {'name': name, 'arguments': args})
        if 'error' in r or r.get('result', {}).get('isError'): raise RuntimeError(json.dumps(r)[:400])
        return r['result'], ms

def dump(n, o):
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(o, open(OUT / n, 'w'), indent=1)

if __name__ == '__main__':
    m = Mcp(); init, _ = m.call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'radial-benchmark', 'version': '1'}})
    m.call('notifications/initialized', notify=True)
    tl, ms = m.call('tools/list'); tools = tl['result']['tools']; raw = json.dumps(tl)
    dump('mcp-tools-list.json', {'server': MCP, 'serverInfo': init['result'].get('serverInfo'), 'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'count': len(tools), 'bytes': len(raw), 'ms': ms, 'names': sorted(t['name'] for t in tools), 'tools': tools})
    print('tools', len(tools), 'bytes', len(raw)); print(sorted(t['name'] for t in tools))
