#!/usr/bin/env python3
"""Live Linear benchmark, part 2: T1-T4 through the official MCP (n=5) and a claim race through GraphQL.

WRITES to the Linear workspace behind LINEAR_API_KEY: 5 task issues and 10 race issues. Use a scratch
workspace. The team must have Todo, In Progress and Done states and a Bug label (the defaults).
Outputs: tasks-T1-T4-mcp.json, claim-race-graphql.json in runs/2026-11-02/linear-live/.
The viewer id is used for the assignee field only; it is never written to the outputs.
Usage: LINEAR_API_KEY=... python3 scripts/linear_tasks.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linear_live import *
import threading

m = Mcp(); m.call('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'radial-benchmark', 'version': '1'}}); m.call('notifications/initialized', notify=True)
def txt(r): return ''.join(c.get('text', '') for c in r.get('content', []))
teams = json.loads(txt(m.tool('list_teams', {})[0])); team = (teams.get('teams') or teams.get('nodes') or teams)[0]; tname = team['name']
sts = txt(m.tool('list_issue_statuses', {'team': tname})[0]); print('statuses', sts[:400])

# T1-T4 through MCP, n=5
trials = []
for i in range(5):
    calls = []; b0 = m.bytes
    def T(name, args):
        r, ms = m.tool(name, args); calls.append({'tool': name, 'ms': round(ms, 1)}); return json.loads(txt(r)) if txt(r).strip().startswith('{') else txt(r)
    t0 = time.perf_counter()
    iss = T('save_issue', {'title': f'bench T1 trial {i}', 'team': tname, 'priority': 2, 'labels': ['Bug']})
    ident = iss.get('identifier') or iss.get('id')
    T('list_issues', {'team': tname, 'state': 'Todo', 'limit': 5})
    T('save_issue', {'id': ident, 'assignee': 'me', 'state': 'In Progress'})
    T('save_comment', {'issueId': ident, 'body': 'Proof: tests passed (12/12)'})
    T('save_issue', {'id': ident, 'state': 'Done'})
    T('save_comment', {'issueId': ident, 'body': 'Done: shipped in bench'})
    trials.append({'trial': i, 'issue': ident, 'calls': calls, 'n_calls': len(calls), 'wall_ms': round((time.perf_counter() - t0) * 1000, 1), 'bytes': m.bytes - b0})
    print(trials[-1]['n_calls'], trials[-1]['wall_ms'], trials[-1]['bytes'])
w = [t['wall_ms'] for t in trials]
dump('tasks-T1-T4-mcp.json', {'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'surface': MCP, 'flow': 'create(T1) list next(T2) claim+start(T2) proof comment(T3) done(T4) done-note(T4)', 'n': 5, 'median_ms': statistics.median(w), 'min_ms': min(w), 'max_ms': max(w), 'trials': trials})

# Claim race via GraphQL, 10 rounds x 20 workers, one Linear identity.
# Linear has no conditional update, so each worker reads the state and updates if it still says Todo.
me = gql('{viewer{id}}')[0]['data']['viewer']['id']
states = gql('query($t:String!){team(id:$t){states{nodes{id name}}}}', {'t': team['id']})[0]['data']['team']['states']['nodes']
sid = {s['name']: s['id'] for s in states}
rounds = []
for r in range(10):
    iss = gql('mutation($i:IssueCreateInput!){issueCreate(input:$i){issue{id identifier}}}', {'i': {'teamId': team['id'], 'title': f'race round {r}', 'stateId': sid['Todo']}})[0]['data']['issueCreate']['issue']
    bar = threading.Barrier(20); res = [None] * 20
    def worker(k):
        bar.wait()
        st = gql('query($id:String!){issue(id:$id){state{name} description}}', {'id': iss['id']})[0]['data']['issue']
        if st['state']['name'] != 'Todo': res[k] = 'saw-claimed'; return
        o = gql('mutation($id:String!,$i:IssueUpdateInput!){issueUpdate(id:$id,input:$i){success}}', {'id': iss['id'], 'i': {'stateId': sid['In Progress'], 'assigneeId': me, 'description': f'claimed-by-w{k}'}})[0]
        res[k] = 'claimed' if o.get('data', {}).get('issueUpdate', {}).get('success') else 'error:' + json.dumps(o)[:100]
    with cf.ThreadPoolExecutor(20) as ex: list(ex.map(worker, range(20)))
    fin = gql('query($id:String!){issue(id:$id){description}}', {'id': iss['id']})[0]['data']['issue']['description']
    c = sum(1 for x in res if x == 'claimed')
    rounds.append({'round': r, 'issue': iss['identifier'], 'workers': 20, 'believed_claimed': c, 'final_owner': fin, 'silent_overwrites': max(c - 1, 0), 'results': res}); print('race', r, c)
dump('claim-race-graphql.json', {'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'method': '20 workers per round, barrier, read state then issueUpdate if Todo (Linear has no conditional update)', 'rounds': rounds, 'rounds_with_multiple_claimants': sum(1 for x in rounds if x['believed_claimed'] > 1), 'total_silent_overwrites': sum(x['silent_overwrites'] for x in rounds)})
