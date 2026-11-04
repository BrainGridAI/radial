#!/usr/bin/env python3
"""Build evidence.json: one stable id per MEASURED number, pointing at its raw file and command.
Ids are append-only. To retire one, set "retired": true; never reuse an id."""
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs/2026-11-02"
ev = []

def add(eid, value, unit, file, command, path=None, n=None, note=None, label="MEASURED", date="2026-11-02"):
    assert file.exists(), f"{eid}: evidence file missing: {file}"
    ev.append({"id": eid, "label": label, "date": date, "value": value, "unit": unit, "file": str(file.relative_to(ROOT)),
               "json_path": path, "command": command, "n": n, "note": note})

# Baseline (SIMULATED workflow, MEASURED numbers: the harness is a scripted agent, the timings are real)
b = json.loads((RUN / "baseline/summary.json").read_text())
cmd_b = "python3 scripts/baseline.py runs/2026-11-02/baseline --n 10"
f = RUN / "baseline/summary.json"
for t, s in b["tasks"].items():
    add(f"E-BASE-{t}-cmds", s["commands"], "shell commands", f, cmd_b, f".tasks.{t}.commands", s["n"], "scripted agent (SIMULATED workflow)")
    add(f"E-BASE-{t}-ms", [s["median_ms"], s["p10_ms"], s["p90_ms"]], "ms median,p10,p90", f, cmd_b, f".tasks.{t}", s["n"], "tool floor: git + shell only, no LLM time")
    add(f"E-BASE-{t}-bytes", s["context_bytes_median"], "bytes read back (median)", f, cmd_b, f".tasks.{t}.context_bytes_median", s["n"], None)
    add(f"E-BASE-{t}-err", s["errors_total"], "errors across trials", f, cmd_b, f".tasks.{t}.errors_total", s["n"], None)
r = b["claim_race_shared_checkout"]
add("E-BASE-RACE-shared-same", r["same_task"], f"trials of {r['n']} where both agents picked the same task", f, cmd_b, ".claim_race_shared_checkout.same_task", r["n"], "both use 'first open task'")
add("E-BASE-RACE-shared-lost", r["lost_update"], f"trials of {r['n']} with a silent lost claim", f, cmd_b, ".claim_race_shared_checkout.lost_update", r["n"], "no error raised to either agent")
r = b["claim_race_git"]
add("E-BASE-RACE-git-rejected", r["push_rejected"], f"trials of {r['n']} where one push was rejected", f, cmd_b, ".claim_race_git.push_rejected", r["n"], None)
add("E-BASE-RACE-git-conflict", r["rebase_conflict"], f"trials of {r['n']} where the loser hit a rebase conflict", f, cmd_b, ".claim_race_git.rebase_conflict", r["n"], "detectable, but the agent must resolve or re-pick")
for k, v in b["merge_conflicts"].items():
    add(f"E-BASE-MERGE-{k}", v["conflicts"], f"conflicts of {v['n']} merges", f, cmd_b, f".merge_conflicts.{k}", v["n"], None)
for row in b["context_scaling"]:
    add(f"E-BASE-SCALE-{row['decisions']}", row["full_read_bytes_if_agent_cats_both"], "bytes (DECISIONS.md + TODO.md)", f, cmd_b, ".context_scaling[]", 1, f"{row['decisions']} decisions, {row['tasks']} tasks")

# Token trials
trials = sorted((RUN / "tokens").glob("t2-trial-[0-9].json"))
if trials:
    tj = [json.loads(p.read_text()) for p in trials]
    med = lambda xs: statistics.median(xs)
    tin = [t["usage"]["input_tokens"] + t["usage"]["cache_read_input_tokens"] + t["usage"]["cache_creation_input_tokens"] for t in tj]
    cmd_t = "scripts/cc-trials.sh 3 runs/2026-11-02/tokens sonnet"
    ft = RUN / "tokens"
    add("E-TOK-BASE-T2-in", med(tin), "input tokens incl. cache (median)", ft, cmd_t, ".usage", len(tj), "n=3, below the n>=5 bar; model claude-sonnet-5-5")
    add("E-TOK-BASE-T2-cache-read", med(t["usage"]["cache_read_input_tokens"] for t in tj), "cache-read tokens (median)", ft, cmd_t, ".usage.cache_read_input_tokens", len(tj), None)
    add("E-TOK-BASE-T2-out", med(t["usage"]["output_tokens"] for t in tj), "output tokens (median)", ft, cmd_t, ".usage.output_tokens", len(tj), None)
    add("E-TOK-BASE-T2-turns", med(t["num_turns"] for t in tj), "turns (median)", ft, cmd_t, ".num_turns", len(tj), None)
    add("E-TOK-BASE-T2-ms", med(t["duration_ms"] for t in tj), "ms (median)", ft, cmd_t, ".duration_ms", len(tj), None)
    add("E-TOK-BASE-T2-usd", round(med(t["total_cost_usd"] for t in tj), 4), "USD per task (median)", ft, cmd_t, ".total_cost_usd", len(tj), None)
    add("E-TOK-BASE-T2-ok", sum(1 for t in tj if not t["is_error"]), f"successful of {len(tj)}", ft, cmd_t, ".is_error", len(tj), "each pushed 'Claim T-026'; see *.meta.json")

# Radial static
rs = RUN / "radial-static"
cnt = lambda p: len([l for l in (rs / p).read_text().splitlines() if l.strip()])
add("E-RAD-MCP-count", cnt("mcp-tool-names.txt"), "hosted MCP tools", rs / "mcp-tool-names.txt", "grep -E \"^    name: '\" mcp-tools.ts.snapshot", None, 1, "Radial app source at commit 9126321 (private repo; tool lists reproduced from the public hosted MCP). The live hosted list (R-LIVE-MCP-TOOLS) has 45: claim_issue shipped after this commit")
add("E-RAD-STDIO-count", cnt("cli-stdio-mcp-tool-names.txt"), "stdio MCP tools", rs / "cli-stdio-mcp-tool-names.txt", "grep on cli-mcp.ts.snapshot; confirmed by tools/list", None, 1, None)
tl = json.loads((rs / "stdio-mcp-tools-list.jsonl").read_text().splitlines()[1])
add("E-RAD-STDIO-toolslist-bytes", len((rs / "stdio-mcp-tools-list.jsonl").read_text().splitlines()[1].encode()), "bytes of tools/list response", rs / "stdio-mcp-tools-list.jsonl", "printf initialize+tools/list | bun cli/src/index.ts mcp (offline)", ".result.tools", 1, f"{len(tl['result']['tools'])} tools")
add("E-RAD-CLI-help-bytes", (rs / "cli-help.txt").stat().st_size, "bytes of `radial help`", rs / "cli-help.txt", "bun cli/src/index.ts help", None, 1, None)
th = json.loads((rs / "cli-help-timing.json").read_text())
add("E-RAD-CLI-help-ms", [th["median_ms"], th["p10_ms"], th["p90_ms"]], "ms median,p10,p90 (bun, from source)", rs / "cli-help-timing.json", "python3 scripts/timeit.py 10 ... -- bun cli/src/index.ts help", None, th["n"], "CLI startup floor; published build runs on node")
add("E-RAD-CLI-noauth", (rs / "cli-list-noauth.stderr").read_text().strip(), "stderr", rs / "cli-list-noauth.stderr", "env -u RADIAL_KEY bun cli/src/index.ts list --json", None, 1, "machine-readable error with the fix in the message")

# Live phase, 2026-11-02. Numbers are read from the raw outputs, never typed.
ll = RUN / "linear-live"
lt = json.loads((ll / "mcp-tools-list.json").read_text())
add("L-LIVE-MCP-TOOLS", {"tools": lt["count"], "tools_list_bytes": lt["bytes"]}, "tools; bytes of the tools/list JSON-RPC response (all schemas)",
    ll / "mcp-tools-list.json", "LINEAR_API_KEY=... python3 scripts/linear_live.py", ".count, .bytes", 1,
    f"{lt['server']} serverInfo.version {lt['serverInfo'].get('version')}; resolves the earlier UNVERIFIED Linear tool count")
rl = RUN / "radial-live"
rt = json.loads((rl / "mcp-tools-list.json").read_text())
add("R-LIVE-MCP-TOOLS", {"tools": rt["count"], "tools_list_bytes": rt["bytes"]}, "tools; bytes of the tools/list JSON-RPC response (all schemas)",
    rl / "mcp-tools-list.json", "MCP initialize + tools/list against https://mcp.radial.build/mcp with an rk_ key (same client as scripts/linear_live.py)", ".count, .bytes", 1,
    "names only are stored; includes claim_issue")
tk = json.loads((ll / "tasks-T1-T4-mcp.json").read_text())
add("L-LIVE-T1T4", {"mcp_calls": statistics.median(t["n_calls"] for t in tk["trials"]), "median_ms": tk["median_ms"],
    "min_ms": tk["min_ms"], "max_ms": tk["max_ms"], "bytes_median": statistics.median(t["bytes"] for t in tk["trials"])},
    "MCP tools/call per T1-T4 flow; wall ms", ll / "tasks-T1-T4-mcp.json", "LINEAR_API_KEY=... python3 scripts/linear_tasks.py",
    ".median_ms, .trials[].n_calls", tk["n"], f"flow: {tk['flow']}; scripted calls, no LLM time")
cr = json.loads((ll / "claim-race-graphql.json").read_text())
rounds = cr["rounds"]
add("L-LIVE-RACE", {"rounds": len(rounds), "workers_per_round": rounds[0]["workers"],
    "rounds_with_multiple_claimants": cr["rounds_with_multiple_claimants"], "total_silent_overwrites": cr["total_silent_overwrites"],
    "workers_told_claimed": sum(r["believed_claimed"] for r in rounds)},
    "rounds; overwrites", ll / "claim-race-graphql.json", "LINEAR_API_KEY=... python3 scripts/linear_tasks.py",
    ".rounds_with_multiple_claimants, .total_silent_overwrites", len(rounds),
    "single Linear identity (one API key, 20 threads); read-then-update because Linear has no conditional update. Each round ends with one owner; every other worker got success and was never told it lost")
add("R-CLAIM-ATOMIC", "claim_issue present on the live hosted MCP", "tool presence", rl / "mcp-tools-list.json",
    "see R-LIVE-MCP-TOOLS", ".names", 1,
    "Radial's atomic claim (POST /v1/issues/{id}/claim, MCP tool claim_issue) is live on production as of 2026-11-02. The live multi-identity race was run on 2026-11-04 (see R-LIVE-RACE). A 12-way concurrent unit test in the Radial app repo (private) also covers it",
    label="DOCUMENTED")

# Live phase, 2026-11-04
rr = ROOT / "runs/2026-11-04/radial-live/claim-race-rest.json"
cr = json.loads(rr.read_text())
rounds = cr["rounds"]
results = [s for r in rounds for s in r["results"]]
add("R-LIVE-RACE", {"rounds": len(rounds), "workers_per_round": rounds[0]["workers"],
    "rounds_with_multiple_claimants": cr["rounds_with_multiple_claimants"], "total_silent_overwrites": cr["total_silent_overwrites"],
    "workers_told_claimed": sum(r["believed_claimed"] for r in rounds), "workers_rejected_409": results.count("rejected-409"),
    "errors": sum(1 for s in results if s not in ("claimed", "rejected-409")), "distinct_identities": cr["distinct_identities"]},
    "rounds; overwrites; worker outcomes", rr, "RADIAL_KEYS=... RADIAL_TEAM=... python3 scripts/radial_race.py",
    ".rounds_with_multiple_claimants, .total_silent_overwrites, .rounds[].results", len(rounds),
    "20 distinct agent API keys (one per worker) in Radial's own internal workspace on production, temporary team; conditional claim (assignee null or caller, else 409). "
    "On production an issue created by an agent is auto-assigned to the key's human owner, so the harness unassigns each issue and reads it back as null before the round. "
    "A first run without that step was discarded (all 200 claims rejected). All test issues were deleted and the keys revoked after the run",
    date="2026-11-04")

(ROOT / "evidence.json").write_text(json.dumps({"as_of": "2026-11-04", "labels": ["MEASURED", "DOCUMENTED", "SIMULATED", "ESTIMATE"], "evidence": ev}, indent=1) + "\n")
print(len(ev), "evidence rows")
