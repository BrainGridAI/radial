# Benchmark methodology: issue trackers for coding-agent workflows

Status: INTERIM, 2026-11-02 (offline phase plus a first live phase against Linear and the Radial hosted MCP). Compares four approaches on the same nine tasks:

| Id | Approach | Agent surface under test |
|---|---|---|
| A-RAD | Radial | hosted MCP (`mcp.radial.build`), stdio MCP (`radial mcp`), CLI `radial` 1.3.0 |
| A-LIN | Linear | official remote MCP (`mcp.linear.app/mcp`), no official general CLI (community `schpet/linear-cli` as the CLI column) |
| A-JIRA | Jira Cloud | Atlassian Rovo remote MCP, Atlassian CLI `acli` |
| A-BASE | No tracker | `TODO.md` + `DECISIONS.md` + `HANDOFF.md` in git, agent session logs as local JSONL |

## Evidence labels

Every number in this directory carries exactly one label.

- **MEASURED**: produced by a command in this directory. The row names the command and the raw output file under `runs/2026-11-02/`.
- **DOCUMENTED**: quoted from a vendor page, with URL, as of November 2026. Raw notes: `runs/2026-11-02/sources/`. Source-code facts about Radial cite a file path in the Radial app source at commit 9126321 (private repo; tool lists reproduced from the public hosted MCP).
- **SIMULATED**: produced by a scripted model of the workflow (for example, a scripted agent in a temp git repo). It measures the tool floor, not an LLM.
- **ESTIMATE**: an assumption, with the reasoning written next to it. Estimates never feed a "winner" claim.

Rows have stable ids (`T2.agent.commands`, `F-03`, `E-BASE-07`). `evidence.json` maps each id to its label, date, file in this folder and JSON path. Ids never get reused; a retired row is marked `retired`, never deleted.

## Tasks

Each task starts from a defined state and ends at a checkable post-condition. A trial passes only when the checker confirms the post-condition, never when the agent says it did.

| Id | Task | Start state | Pass condition (checker) |
|---|---|---|---|
| T0 | Setup to first agent-created issue | Clean machine, account exists, no token | An issue created by the agent exists and is readable by a second credential |
| T1 | Create issue | Authenticated session | Issue exists with title, priority, one label |
| T2 | Pick up the next task | 20 open issues, 0 assigned to the agent | Exactly one issue moved to the agent and to a started status |
| T3 | Update status with proof | Agent owns one started issue | Status is review (or equivalent) and the proof (test output) is attached or linked on the issue |
| T4 | Close with done-note | Issue in review | Status category completed, a done-note comment exists |
| T5 | Find a past decision | 200 decisions recorded across issues/comments; target decision has no id in the prompt | Agent returns the right decision id and its date |
| T6 | Share an HTML prototype | Single-file `prototype.html` (40 KB) on disk | A human with workspace access opens a rendered preview from a URL on the issue |
| T7 | Hand off between two agents | Agent A owns an in-progress issue | Agent B (separate credential and session) owns it and can state the next step from the tracker alone |
| T8 | Resume after a session ends | Prior session closed, its context gone | New session names the in-progress issue, last step, and next step without asking the human |

T6 has no no-tracker equivalent: a committed HTML file renders only after the human clones and opens it. A-BASE records T6 as "unsupported, workaround: commit file + human clones" and counts the human steps.

## Agent metrics (per task, per approach)

| Metric id | Metric | How measured |
|---|---|---|
| `steps` | Shell commands or CLI invocations the agent issues | Counted by the harness wrapper (`scripts/baseline.py` `Agent.sh`) or from `claude -p` transcript tool_use events |
| `mcp_calls` | MCP `tools/call` requests | Count in the `claude -p` stream-json transcript |
| `round_trips` | HTTP requests to the tracker | Local proxy log (live phase); for the Radial CLI the static count of request sites per command (`runs/2026-11-02/radial-static/cli-request-sites-per-command.txt`) |
| `wall_ms` | Wall-clock, median and p10 to p90 | n >= 5 trials, `scripts/timeit.py`; the summary reports n |
| `tokens_in`, `tokens_out` | Model tokens, input split into uncached, cache-read and cache-creation | `claude -p "<prompt>" --output-format json --setting-sources project --model sonnet` from a fresh seeded temp dir under `.context/`, fields `usage.*` |
| `context_bytes` | Bytes the agent reads back into context (tool results, schemas) | Harness counts stdout+stderr bytes; MCP `tools/list` payload measured once per server |
| `errors` | Non-zero exits, MCP `isError`, HTTP 4xx/5xx, retries | Harness and transcript |
| `auth_steps` | Actions to get from no credential to a working call | Scripted for each approach in T0, counted per action (browser consent counts 1, copy-paste of a token counts 1) |

Model, prompt, allowed tools and budget are fixed across approaches (`scripts/cc-trials.sh`). Only the tracker surface changes.

## Human metrics

| Metric id | Metric | How measured |
|---|---|---|
| `h_clicks` | Clicks and keystrokes-with-intent to complete the human side (review a proof, open a prototype, approve a handoff) | Scripted browser run, events counted |
| `h_screens` | Distinct pages or views visited | Same run |
| `h_ttfur` | Time to first useful result: from opening the link to seeing the thing (rendered prototype, proof, decision) | Same run, median of 5 |

## Hidden costs

| Id | Cost | Method |
|---|---|---|
| H-01 | Setup time to first agent-created issue (T0) | MEASURED in the live phase; human steps counted, LLM time excluded |
| H-02 | Maintenance and admin hours per month | ESTIMATE from a task list (token rotation, permission changes, MCP re-auth, workflow scheme edits), each item timed once and multiplied by documented frequency |
| H-03 | Babysitting: human interventions per 100 agent actions | Count of prompts where the agent stops to ask, from the live-phase transcripts |
| H-04 | Context-rebuild per session | T8 `context_bytes` and `tokens_in`, and the human minutes spent re-explaining (counted when the agent asks) |

## Failure-mode catalog

Cost per incident is an ESTIMATE: minutes of human time to notice and repair, at a loaded rate of $100 per hour (ESTIMATE). Rates change per org; the minutes are the portable part.

| Id | Failure | A-BASE | A-RAD | A-LIN | A-JIRA | How measured or cited | Cost per incident (ESTIMATE) |
|---|---|---|---|---|---|---|---|
| F-01 | Stale TODOs (task marked open after work merged) | Likely: no link from commit to task | Git automation moves status forward on PR events (`src/lib/state`, `canMoveStatus`) | GitHub integration (DOCUMENTED in Linear docs) | Development panel / automation rules | Live phase: merge 10 PRs, count tasks left open after 5 min | 10 min |
| F-02 | Two agents claim the same task | MEASURED 20/20 in the scripted race (see below) | Atomic claim live on production as of 2026-11-02 (`POST /v1/issues/{id}/claim`, MCP `claim_issue`). MEASURED live 2026-11-04: 0 of 10 rounds had multiple claimants, 0 silent overwrites; 10 workers claimed, 190 got 409, 0 errors across 10 rounds x 20 workers (R-LIVE-RACE; 20 distinct agent identities, conditional claim) | MEASURED live: 10 of 10 rounds had multiple claimants, 183 silent overwrites across 10 rounds x 20 workers (L-LIVE-RACE; one identity, read-then-update; setups differ, see Known limits) | Not measured | `scripts/baseline.py claim_race_*`; `scripts/linear_tasks.py` for Linear | 30 min (duplicate work, one PR discarded) |
| F-03 | Lost session logs | Local JSONL lost with the machine or container | `radial build capture/sync` journals to disk first, then uploads idempotently (`cli/src/build-journal.ts`, `cli/test/lifecycle.test.ts`) | No session-log tool | No session-log tool | Kill the agent mid-session, count events recoverable | 20 min |
| F-04 | MCP auth expiry | n/a | OAuth refresh tokens are single-use (app source, OAuth section) | OAuth 2.1, API key header alternative (DOCUMENTED) | OAuth 2.1 (see `runs/2026-11-02/sources/atlassian.md`) | Live phase: run 24 h, count re-auth prompts | 5 min |
| F-05 | 429 rate limit | n/a | 120 req/min sustained, 120 burst, per credential per instance (default in `src/lib/api/rate-limit.ts`) | 2,500 req/h per API key, 5,000 req/h per OAuth user (DOCUMENTED) | Cost-based quotas (see sources) | Live phase: burst 300 calls, count 429s and recovery time | 2 min |
| F-06 | Permission errors | Git push rights only | Scopes read / triage / write per key (`src/lib/api/scope.ts`) | Read-only endpoint and scopes (DOCUMENTED) | Project permission schemes | Live phase: run T1-T4 with a read-only and a triage credential, count errors and clarity of the message | 5 min |
| F-07 | Merge conflicts on a shared task file | MEASURED: 10/10 when two branches append a task or close adjacent tasks, 0/10 when edits are 8+ lines apart | n/a (no shared file) | n/a | n/a | `scripts/baseline.py merge_conflicts` | 10 min |

## Multi-user

Each approach is scored on five properties, from docs and from the live phase:

| Id | Property | Check |
|---|---|---|
| MU-1 | Shared state | Two credentials see the same write within 5 s |
| MU-2 | Claiming | Concurrent claim race (F-02) outcome: atomic reject, detectable conflict, or silent last-write-wins |
| MU-3 | Permissions | Can an agent credential be limited below a human member (read-only, triage-only, per-project)? |
| MU-4 | Notifications | Does the agent get notified of assignment/mention, and how does it read them (tool, webhook, poll)? |
| MU-5 | Audit trail | Can a human answer "which agent changed this status and when" from the tracker? |

## Enterprise practical setup

Scope is practical setup only: SSO, permissions, audit trail, agent governance, API token management, required plan tier and cost. Each row is DOCUMENTED with URL, or for Radial with source path. The Enterprise rows are not part of this public release yet.

## Cost per 100 agent actions

An agent action is one successful tracker write or read that a task needs (T1 to T8 each count their tool calls). Cost per 100 actions =

`100 * (model cost per action) + (seat or credit cost attributable to those actions)`

- Model cost per action comes from `total_cost_usd / mcp_calls_or_steps` in the `claude -p` trials (MEASURED for A-BASE today, live phase for the others).
- Seat cost: Radial does not bill agents as seats (DOCUMENTED: `src/app/pricing/page.tsx` at `9126321`); Linear says agents are not billable seats (DOCUMENTED, `linear.app/docs/agents-in-linear`); Jira: see sources. Per-action seat cost is 0 when agents are free and the human seats are already paid; it is reported separately so it is not hidden.
- Credit cost: Atlassian Rovo search tools "may consume up to 10 Rovo Credits" (cross-checked in `runs/2026-11-02/sources/atlassian.md`); Linear Agent coding sessions "Require AI credits" (DOCUMENTED). Third-party agent calls through MCP are counted at 0 credits unless docs say otherwise.

## Rate-limit headroom

Headroom = documented or configured limit divided by the peak call rate one agent needs. Peak rate comes from the live-phase transcripts (max calls in any 60 s window). Today only the limits are known (F-05 row); headroom stays blank until the live phase.

## Reproducibility

- `./reproduce.sh plan` prints every step, its label, whether it needs network or credentials, and the output path. `./reproduce.sh offline` runs the steps that need no network and no credentials. `./reproduce.sh tokens` runs the paid `claude -p` trials (about $0.07 each, MEASURED).
- Versions: `runs/2026-11-02/versions.json` (Radial commit, CLI version, bun, node, git, python, Claude Code).
- Radial app source at commit 9126321 (private repo; tool lists reproduced from the public hosted MCP). `reproduce.sh offline` reads it with `git show 9126321:<path>` and `git archive 9126321 cli` from `$RADIAL_REPO`, never from a working tree. Without access to that repo, use the live hosted MCP list in `runs/2026-11-02/radial-live/`. Raw source snapshots are not published here.
- No subprocess sees `RADIAL_KEY`. The Radial CLI runs with `RADIAL_CONFIG_DIR` set to an empty temp dir and every `RADIAL_*_URL` pointed at `127.0.0.1:9` (a closed port), so it cannot reach production.
- Results where Radial loses or ties stay in every table. `README.md` lists the limits.

## Known limits of this interim phase

- Scripted agents (A-BASE, SIMULATED) measure the tool floor: git and shell time, command counts, bytes. They contain no LLM reasoning time. The three `claude -p` trials are the only LLM numbers.
- The scripted claim race picks "first open task" for both agents, which is the usual heuristic and the worst case. With a random pick among k open tasks, the collision rate would be near 1/k.
- Linear's MCP tool list is not published on any official page. The live `tools/list` on 2026-11-02 returned 60 tools (L-LIVE-MCP-TOOLS); the capability cells in `coverage-matrix.md` still cite docs and have not been re-scored from it.
- The two live claim races use different setups. Linear used one API key from 20 threads. Linear has no conditional update, so the workers read the state, then update if it still says Todo. Separate identities would not add a precondition, so we expect the same outcome, but that run was not done. Radial used 20 distinct agent keys, one per worker, because its claim succeeds again for the current holder: with one key, every worker would get 2xx and the race would not test atomicity (`radial_race.py --single-identity` shows this). So the two runs measure each tracker's own claim path, not one identical setup.
