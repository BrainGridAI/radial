#!/usr/bin/env python3
"""Build coverage-matrix.json and coverage-matrix.md. Radial lists are read from the
lists in runs/2026-11-02/radial-static/ (Radial app source at commit 9126321, private repo;
tool lists reproduced from the public hosted MCP) and the live tools/list files in runs/2026-11-02/*-live/; other lists are
transcribed from runs/2026-11-02/sources/*.md. Counts are computed here, never typed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RS = ROOT / "runs/2026-11-02/radial-static"
lines = lambda p: [l.strip() for l in (RS / p).read_text().splitlines() if l.strip()]
LIVE = ROOT / "runs/2026-11-02"
linear_live = json.loads((LIVE / "linear-live/mcp-tools-list.json").read_text())
radial_live = json.loads((LIVE / "radial-live/mcp-tools-list.json").read_text())

radial_mcp = lines("mcp-tool-names.txt")
radial_stdio = lines("cli-stdio-mcp-tool-names.txt")
cli_top = ["auth", "whoami", "workspace", "keys", "create", "update", "list", "show", "close", "delete", "move",
           "branch", "comment", "attach", "attachments", "link", "unlink", "inbox", "activity", "recent", "triage",
           "search", "project", "team", "label", "cycle", "import", "export", "skills", "build", "mcp", "logout"]
cli_subs = {
    "workspace": ["show", "list", "use", "current", "available"],
    "keys": ["list", "create", "revoke"],
    "comment": ["<add>", "list", "delete"],
    "attachments": ["<list>", "delete"],
    "project": ["list", "show", "create", "update", "archive", "unarchive", "delete"],
    "team": ["list", "create", "update", "archive", "unarchive", "delete"],
    "label": ["list", "create", "update", "delete"],
    "cycle": ["list", "create", "update", "delete"],
    "skills": ["install", "update", "list", "remove", "extend"],
    "build": ["start", "bind", "drafts", "pipeline", "stage", "child", "gate", "report", "capture", "finish", "sync",
              "show", "search", "export", "hook"],
}
cli_leaves = [c for c in cli_top if c not in cli_subs] + [f"{c} {s}" for c, ss in cli_subs.items() for s in ss]
help_text = (RS / "cli-help.txt").read_text()
missing = [c for c in cli_top if f"  {c} " not in help_text and f"  {c}\n" not in help_text]
assert not missing, f"CLI commands not in help output: {missing}"

jira_observed = ["addGraphContext", "addOrEditJiraIssueComment", "atlassianUserInfo", "createConfluenceContent",
                 "createJiraIssue", "discover", "editJiraIssue", "executeDestructive", "executeRead", "executeWrite",
                 "getAccessibleAtlassianResources", "getCollaborators (beta)", "getConfluenceContent", "getGraphContext",
                 "getGraphObject", "getJiraIssue", "getLoomObjectsContent", "getPeopleInfo (beta)",
                 "getWorkActivity (beta)", "getWorkPortfolio (beta)", "listJiraIssueComments", "search",
                 "searchConfluence", "searchJiraIssuesUsingJql", "transitionJiraIssue", "updateConfluenceContent"]
jira_doc_primary = ["addOrEditJiraIssueComment", "addTeamworkGraphContext", "atlassianUserInfo",
                    "createConfluenceContent", "createJiraIssue", "discover", "editJiraIssue", "executeRead",
                    "executeWrite", "executeDestructive", "getAccessibleAtlassianResources", "getConfluenceContent",
                    "getJiraIssue", "getLoomObjectsContent", "getTeamworkGraphContext", "getTeamworkGraphObject",
                    "listJiraIssueComments", "search (beta)", "searchConfluence", "searchJiraIssuesUsingJql",
                    "transitionJiraIssue", "updateConfluenceContent"]
acli = {
    "admin": ["auth", "user activate", "user cancel-delete", "user deactivate", "user delete"],
    "feedback": ["<feedback>"],
    "rovodev": ["auth"],
    "jira auth": ["login"],
    "jira board": ["list-sprints", "search"],
    "jira dashboard": ["search"],
    "jira field": ["cancel-delete", "create", "delete"],
    "jira filter": ["add-favourite", "change-owner", "list", "search"],
    "jira project": ["archive", "create", "delete", "list", "restore", "update", "view"],
    "jira sprint": ["list-workitems"],
    "jira workitem": ["archive", "assign", "attachment delete", "attachment list", "clone", "comment create",
                      "comment delete", "comment list", "comment update", "comment visibility", "create",
                      "create-bulk", "delete", "edit", "link", "search", "transition", "unarchive", "view",
                      "watcher remove"],
}
acli_leaves = [f"{g} {s}" for g, ss in acli.items() for s in ss]

COLS = ["radial_mcp", "radial_cli", "linear_mcp", "linear_cli", "jira_mcp", "jira_cli"]
Y, P, N, U = "yes", "partial", "no", "unknown"
NA = "none-official"
SRC_R = "SOURCE 9126321"
SRC_L = "DOCUMENTED linear.app/docs/mcp"
SRC_J = "DOCUMENTED developer.atlassian.com/cloud/rovo-mcp/guides/supported-tools/"
SRC_A = "DOCUMENTED developer.atlassian.com/cloud/acli/reference/commands/"

def c(v, how, label):
    return {"value": v, "how": how, "label": label}

def lin_cli():
    return c(NA, "Linear ships no official general-purpose CLI (only linear-release and the CLI Importer)",
             "DOCUMENTED github.com/linear, linear.app/changelog")

ROWS = [
    ("R01", "Create issue", c(Y, "create_issue", SRC_R), c(Y, "create", SRC_R),
     c(Y, "docs: tools for 'finding, creating, and updating objects ... like issues, projects, and comments'", SRC_L),
     lin_cli(), c(Y, "createJiraIssue (primary)", SRC_J), c(Y, "jira workitem create", SRC_A)),
    ("R02", "Update issue", c(Y, "update_issue", SRC_R), c(Y, "update / edit", SRC_R),
     c(Y, "same docs sentence", SRC_L), lin_cli(), c(Y, "editJiraIssue (primary)", SRC_J), c(Y, "jira workitem edit", SRC_A)),
    ("R03", "Search issues", c(Y, "search_issues, list_issues", SRC_R), c(Y, "search, list", SRC_R),
     c(Y, "'finding' objects (tool names unpublished)", SRC_L), lin_cli(),
     c(Y, "searchJiraIssuesUsingJql (primary); search costs up to 10 Rovo credits", SRC_J), c(Y, "jira workitem search --jql --json", SRC_A)),
    ("R04", "Comments", c(Y, "comment, list_comments, delete_comment (no edit: G-13)", SRC_R),
     c(Y, "comment, comment list, comment delete, --reply-to (no edit)", SRC_R),
     c(Y, "docs name comments", SRC_L), lin_cli(),
     c(Y, "addOrEditJiraIssueComment, listJiraIssueComments (primary since 2026-10-28)", SRC_J),
     c(Y, "comment create/update/delete/list/visibility", SRC_A)),
    ("R05", "Status transitions", c(Y, "update_issue status by name, close_issue; names from get_workspace", SRC_R),
     c(Y, "update -s, close -m", SRC_R), c(U, "not stated in docs", SRC_L), lin_cli(),
     c(P, "transitionJiraIssue needs a transition id from listJiraIssueTransitions (deferred: discover + executeRead)", SRC_J),
     c(Y, "jira workitem transition -s, --jql bulk", SRC_A)),
    ("R06", "Labels", c(Y, "list/create/update/delete_label; labels on create/update", SRC_R),
     c(Y, "label sub; -l, --add-label, --remove-label", SRC_R), c(U, "not stated", SRC_L), lin_cli(),
     c(P, "labels field via editJiraIssue; no label tool in primary list", SRC_J),
     c(Y, "create -l, edit -l / --remove-labels", SRC_A)),
    ("R07", "Projects / cycles", c(Y, "5 project tools, 4 cycle tools", SRC_R), c(Y, "project 7 subs, cycle 4 subs", SRC_R),
     c(P, "projects named in docs; cycles not stated", SRC_L), lin_cli(),
     c(P, "projects via deferred tools; no sprint tool in primary list", SRC_J),
     c(P, "jira project 7 subs; sprint list-workitems and board list-sprints only (read)", SRC_A)),
    ("R08", "Attachments", c(Y, "attach_file (3 MB, one file), list_attachments, delete_attachment", SRC_R),
     c(Y, "attach, attachments, attachments delete", SRC_R), c(U, "not stated; API attachments are links to external resources", "DOCUMENTED linear.app/developers/attachments"),
     lin_cli(), c(P, "uploadAttachmentToJiraIssue is deferred (discover + executeWrite)", SRC_J),
     c(P, "attachment list/delete only; no upload documented", SRC_A)),
    ("R09", "Prototype preview URL", c(Y, "attach_file returns a Preview URL served sandboxed at /p/...", SRC_R),
     c(Y, "attach prints the Preview URL", SRC_R), c(N, "no preview feature documented", SRC_L), lin_cli(),
     c(N, "no preview tool (none observed; none in docs)", SRC_J), c(N, "none documented", SRC_A)),
    ("R10", "Session logs", c(P, "read-only: get_build, search_build_events (write is CLI-only by design)", SRC_R),
     c(Y, "build capture / sync / hook / search / show", SRC_R), c(N, "no session-log tool documented", SRC_L), lin_cli(),
     c(N, "no session-log tool", SRC_J), c(N, "none", SRC_A)),
    ("R11", "Claim / assign to agent", c(P, "update_issue assignee 'me'; non-atomic, last write wins (G-10)", SRC_R),
     c(P, "update -a me, triage [a]; non-atomic", SRC_R),
     c(P, "agents assignable as delegate (app:assignable); MCP tool for it not stated", "DOCUMENTED linear.app/developers/agents"),
     lin_cli(), c(P, "assignee via editJiraIssue; atomicity not documented", SRC_J), c(P, "jira workitem assign", SRC_A)),
    ("R12", "Done-proof / gates", c(P, "read gates with provenance: get_build_rollup, get_build", SRC_R),
     c(Y, "build gate --exec (observed), build finish, close -m", SRC_R), c(N, "none documented", SRC_L), lin_cli(),
     c(N, "comment only", SRC_J), c(N, "comment only", SRC_A)),
    ("R13", "Bulk ops", c(Y, "bulk_update_issues", SRC_R), c(N, "no bulk command (G-02)", SRC_R), c(U, "not stated", SRC_L),
     lin_cli(), c(U, "no bulk tool in primary list; deferred catalog not checked per tool", SRC_J),
     c(Y, "edit/transition --jql, create-bulk", SRC_A)),
    ("R14", "Webhooks", c(N, "settings UI only (G-12)", SRC_R), c(N, "settings UI only", SRC_R),
     c(U, "webhooks exist in API (admin); MCP tool not stated", "DOCUMENTED linear.app/developers/webhooks"), lin_cli(),
     c(U, "not in primary list", SRC_J), c(N, "none documented", SRC_A)),
    ("R15", "Relations", c(Y, "add_relation, remove_relation, list_relations", SRC_R), c(Y, "link, unlink, show", SRC_R),
     c(U, "not stated", SRC_L), lin_cli(), c(U, "not in primary list", SRC_J), c(Y, "jira workitem link", SRC_A)),
    ("R16", "Notifications / inbox", c(Y, "list_notifications, mark_notification_read", SRC_R),
     c(P, "inbox lists; no mark-read (G-03)", SRC_R), c(U, "not stated", SRC_L), lin_cli(),
     c(N, "none in primary list", SRC_J), c(N, "watchers only", SRC_A)),
    ("R17", "Import / export", c(N, "no MCP tool (G-04)", SRC_R), c(Y, "import --from linear|jira, export --format json|csv", SRC_R),
     c(U, "not stated (UI CSV export and importers exist, admin only)", "DOCUMENTED linear.app/docs/exporting-data"), lin_cli(),
     c(N, "none in primary list", SRC_J), c(P, "search --csv export; no import", SRC_A)),
    ("R18", "Auth method", c(Y, "OAuth 2.1 (DCR, PKCE) or Bearer rk_ API key", SRC_R),
     c(Y, "device flow OAuth or RADIAL_KEY", SRC_R),
     c(Y, "OAuth 2.1 with DCR, or OAuth token / API key as Bearer", SRC_L), lin_cli(),
     c(P, "OAuth 2.1; API token only if an org admin enables it", "DOCUMENTED developer.atlassian.com/cloud/rovo-mcp/guides/getting-started/"),
     c(Y, "auth login --web or --token from stdin", SRC_A)),
    ("R19", "Headless / CI usable", c(Y, "Bearer rk_ key, no browser", SRC_R), c(Y, "RADIAL_KEY + --json on every command", SRC_R),
     c(Y, "API key in Bearer header", SRC_L), lin_cli(), c(P, "needs admin-enabled API token", SRC_J),
     c(Y, "token on stdin, --json", SRC_A)),
]

rows = []
for rid, name, *cells in ROWS:
    rows.append({"id": rid, "capability": name, **dict(zip(COLS, cells))})

def counts(col):
    vals = [r[col]["value"] for r in rows]
    k = {v: vals.count(v) for v in (Y, P, N, U, NA)}
    k["score"] = k[Y] + 0.5 * k[P]
    return k

out = {
    "as_of": "2026-11-02",
    "radial_commit": (RS / "radial-head.txt").read_text().strip(),
    "scoring": "yes = 1, partial = 0.5, no / unknown / none-official = 0. 'unknown' means the vendor does not publish it; the live phase resolves it.",
    "surfaces": {
        "radial_mcp": {"label": "MEASURED (grep of src/lib/mcp/tools.ts at commit)", "count": len(radial_mcp), "tools": radial_mcp},
        "radial_stdio_mcp": {"label": "MEASURED (grep of cli/src/mcp.ts) and MEASURED tools/list over stdio = 41",
                             "count": len(radial_stdio), "tools": radial_stdio,
                             "missing_vs_hosted": sorted(set(radial_mcp) - set(radial_stdio))},
        "radial_cli": {"label": "MEASURED (cli/src/index.ts HELP + dispatch, help output cross-checked)", "version": "1.3.0",
                       "top_level_count": len(cli_top), "top_level": cli_top, "leaf_count": len(cli_leaves),
                       "leaves": cli_leaves, "aliases": ["login", "edit", "ws", "help", "version"]},
        "radial_mcp_live": {"label": "MEASURED (live tools/list, 2026-11-02, R-LIVE-MCP-TOOLS)", "count": radial_live["count"],
                            "tools_list_bytes": radial_live["bytes"], "tools": radial_live["names"]},
        "linear_mcp": {"label": "MEASURED (live tools/list, 2026-11-02, L-LIVE-MCP-TOOLS). No official page lists tool names; capability cells below still cite docs",
                       "count": linear_live["count"], "tools_list_bytes": linear_live["bytes"], "tools": linear_live["names"],
                       "endpoint": "https://mcp.linear.app/mcp (+ /mcp/readonly)"},
        "linear_cli": {"label": "DOCUMENTED: no official general-purpose CLI as of 2026-11-02", "count": 0,
                       "official_narrow": ["linear-release (sync, complete, update)", "CLI Importer (packages/import)"],
                       "community": [{"repo": "schpet/linear-cli", "stars": 1034, "last_push": "2026-10-23"},
                                     {"repo": "joa23/linear-cli", "stars": 146, "last_push": "2026-09-13"},
                                     {"repo": "nesszer/linear-cli", "stars": 138, "last_push": "2026-09-13"},
                                     {"repo": "evangodon/linear-cli", "stars": 91, "last_push": "2025-10-15"},
                                     {"repo": "mixpeek/linear-cli", "stars": 16, "last_push": "2025-05-08"},
                                     {"repo": "choam2426/Linear-CLI", "stars": 9, "last_push": "2026-04-03"},
                                     {"repo": "aaronkwhite/linear-cli", "stars": 7, "last_push": "2026-09-06"}]},
        "jira_mcp": {"label": "observed list from a connected MCP client; DOCUMENTED primary list from supported-tools page",
                     "observed_count": len(jira_observed), "observed": jira_observed,
                     "documented_primary_count": len(jira_doc_primary), "documented_primary": jira_doc_primary,
                     "documented_catalog_total": 248, "documented_catalog_jira": 52,
                     "notes": ["3 observed names differ from docs: addGraphContext/getGraphContext/getGraphObject vs addTeamworkGraph*",
                               "4 observed beta tools not in docs: getCollaborators, getPeopleInfo, getWorkActivity, getWorkPortfolio",
                               "'~330 operations' behind discover is UNVERIFIED; docs count 248 tools total",
                               "all Jira tools need cloudId (from getAccessibleAtlassianResources)"]},
        "jira_cli": {"label": SRC_A, "count": len(acli_leaves), "commands": acli_leaves},
    },
    "rows": rows,
    "counts": {col: counts(col) for col in COLS},
}
(ROOT / "coverage-matrix.json").write_text(json.dumps(out, indent=1) + "\n")

# ---- markdown ----
HDR = ["Radial MCP", "Radial CLI", "Linear MCP", "Linear CLI", "Jira MCP", "Jira CLI"]
md = ["# Coverage matrix: agent surfaces (2026-11-02)", "",
      "Generated by `scripts/build_matrix.py` from `runs/2026-11-02/radial-static/` and `runs/2026-11-02/sources/`. Do not hand-edit; edit the script. Full cell evidence (tool names, label per cell) is in `coverage-matrix.json`.", "",
      "Cell values: **yes**, **partial**, **no**, **unknown** (the vendor does not publish it; the live phase resolves it), **none-official** (no official tool exists). Score: yes = 1, partial = 0.5.", "",
      "## Surface sizes", "",
      "| Surface | Count | Label |", "|---|---|---|",
      f"| Radial hosted MCP tools (live tools/list) | {radial_live['count']} ({radial_live['bytes']:,} bytes) | MEASURED, `runs/2026-11-02/radial-live/mcp-tools-list.json` |",
      f"| Radial hosted MCP tools (source at 9126321) | {len(radial_mcp)} | MEASURED, `runs/2026-11-02/radial-static/mcp-tool-names.txt` |",
      f"| Radial stdio MCP tools (`radial mcp`) | {len(radial_stdio)} | MEASURED, tools/list over stdio, `stdio-mcp-tools-list.jsonl` |",
      f"| Radial CLI top-level commands | {len(cli_top)} | MEASURED, `cli-help.txt` |",
      f"| Radial CLI leaf commands (with subcommands) | {len(cli_leaves)} | MEASURED, `cli/src/index.ts`, `commands.ts`, `build.ts`, `skills.ts` |",
      f"| Linear official MCP tools (live tools/list) | {linear_live['count']} ({linear_live['bytes']:,} bytes) | MEASURED, `runs/2026-11-02/linear-live/mcp-tools-list.json` |",
      "| Linear official general CLI | 0 | DOCUMENTED, `sources/linear.md` §2 |",
      f"| Jira MCP direct tools (observed in a connected client) | {len(jira_observed)} | observed, not DOCUMENTED |",
      f"| Jira MCP primary tools (documented) | {len(jira_doc_primary)} | DOCUMENTED, supported-tools page |",
      "| Jira MCP full catalog (documented, via discover) | 248 (52 Jira) | DOCUMENTED, counted from the raw page |",
      f"| Jira CLI (acli) leaf commands | {len(acli_leaves)} | DOCUMENTED, acli command reference |", "",
      "## Capabilities", "",
      "| Id | Capability | " + " | ".join(HDR) + " |", "|---|---|" + "---|" * len(HDR)]
for r in rows:
    md.append(f"| {r['id']} | {r['capability']} | " + " | ".join(f"{r[c]['value']}: {r[c]['how']}" if r[c]['value'] != NA else NA for c in COLS) + " |")
md.append("| | **Score (yes + 0.5 partial)** | " + " | ".join(f"**{out['counts'][c]['score']}**" for c in COLS) + " |")
md.append("| | yes / partial / no / unknown | " + " | ".join(f"{out['counts'][c][Y]} / {out['counts'][c][P]} / {out['counts'][c][N]} / {out['counts'][c][U]}" for c in COLS) + " |")
md += ["", "## Reading the scores", "",
       f"- Linear MCP scores low partly because Linear publishes no tool list. {out['counts']['linear_mcp'][U]} of its {len(rows)} cells are `unknown`, not `no`. The live `tools/list` ({linear_live['count']} tools, in `runs/2026-11-02/linear-live/mcp-tools-list.json`) can resolve them; the cells have not been re-scored from it yet.",
       "- Radial MCP and CLI score highest, but the rows were chosen for coding-agent workflows, and three of them (prototype preview, session logs, done-proof) describe features only Radial ships. Without R09, R10 and R12 the scores are: " + ", ".join(f"{h} {out['counts'][c]['score'] - sum((1 if r[c]['value'] == Y else 0.5 if r[c]['value'] == P else 0) for r in rows if r['id'] in ('R09', 'R10', 'R12'))}" for h, c in zip(HDR, COLS)) + ".",
       "- Linear CLI scores 0 because no official CLI exists. Community CLIs (largest: `schpet/linear-cli`, 1,034 stars, last push 2026-10-23) are listed in the JSON and are not scored.",
       "- Jira MCP partials are mostly round-trip costs: transitions and attachments sit behind `discover` + `execute*`, and every Jira call needs a `cloudId` from `getAccessibleAtlassianResources` first.",
       "- Radial loses or ties on: bulk ops in the CLI (Jira CLI yes, Radial CLI no), webhooks (no on both Radial surfaces), import/export over MCP (no), and claim atomicity (partial everywhere, Radial included).", "",
       "## Exact lists", ""]
md.append(f"**Radial hosted MCP ({len(radial_mcp)}):** " + ", ".join(f"`{t}`" for t in radial_mcp) + "\n")
md.append(f"**Radial stdio MCP ({len(radial_stdio)}):** hosted list minus " + ", ".join(f"`{t}`" for t in sorted(set(radial_mcp) - set(radial_stdio))) + "\n")
md.append(f"**Radial CLI top-level ({len(cli_top)}):** " + ", ".join(f"`{t}`" for t in cli_top) + "\n")
md.append(f"**Radial CLI leaves ({len(cli_leaves)}):** " + ", ".join(f"`{t}`" for t in cli_leaves) + "\n")
md.append(f"**Jira MCP observed ({len(jira_observed)}):** " + ", ".join(f"`{t}`" for t in jira_observed) + "\n")
md.append(f"**Jira MCP documented primary ({len(jira_doc_primary)}):** " + ", ".join(f"`{t}`" for t in jira_doc_primary) + "\n")
md.append(f"**acli ({len(acli_leaves)}):** " + ", ".join(f"`{t}`" for t in acli_leaves) + "\n")
(ROOT / "coverage-matrix.md").write_text("\n".join(md) + "\n")
print(json.dumps(out["counts"], indent=1))
