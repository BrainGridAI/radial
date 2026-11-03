#!/usr/bin/env bash
# One-command reproduction of the benchmark.
#   ./reproduce.sh plan      print every step, its label, what it needs, where it writes (default)
#   ./reproduce.sh offline   run every step that needs no network and no credentials
#   ./reproduce.sh tokens    run the paid claude -p token trials (about $0.07 each, 3 trials)
#   ./reproduce.sh live      print the live-phase steps (need credentials)
#   ./reproduce.sh linear    run L02 against Linear (needs LINEAR_API_KEY for a SCRATCH workspace; writes issues there)
# Never writes to Radial production: RADIAL_KEY is unset, and the Radial CLI points at a closed local port.
# S02-S04 read the Radial app source at commit 9126321 (private repo) from $RADIAL_REPO. Without it,
# use the hosted MCP tool list already in runs/2026-11-02/radial-live/.
set -euo pipefail
cd "$(dirname "$0")"
unset RADIAL_KEY
RADIAL_REPO=${RADIAL_REPO:-}
RADIAL_COMMIT=${RADIAL_COMMIT:-9126321a3edfc7f26f2f5054d6cc1601dfca413b}
RUN=${RUN:-runs/2026-11-02}
mode=${1:-plan}

steps=(
  "S01|MEASURED|offline|$RUN/versions.json|record tool versions"
  "S02|MEASURED|offline|$RUN/radial-static/*.snapshot|snapshot Radial MCP + CLI sources from git show \$RADIAL_COMMIT (read only)"
  "S03|MEASURED|offline|$RUN/radial-static/mcp-tool-names.txt, cli-stdio-mcp-tool-names.txt, mcp-hosted-minus-stdio.txt|count and diff MCP tools"
  "S04|MEASURED|offline|$RUN/radial-static/cli-help.txt, stdio-mcp-tools-list.jsonl, cli-help-timing.json, cli-list-noauth.*|run CLI from git archive with closed-port URLs: help bytes, stdio tools/list bytes, startup ms, no-auth error"
  "S05|MEASURED|offline|$RUN/baseline/*.json|no-tracker baseline: T1-T5, T7, T8 (n=10), claim races (n=20), merge conflicts (n=10), context scaling"
  "S06|MEASURED|paid, network (Anthropic API only)|$RUN/tokens/t2-trial-*.json|claude -p token trials for baseline T2 (n=3)"
  "S07|DOCUMENTED|network (read-only web)|$RUN/sources/*.md|vendor docs research (manual / agent WebFetch; not scripted)"
  "S08|derived|offline|coverage-matrix.json, coverage-matrix.md|scripts/build_matrix.py"
  "S09|derived|offline|evidence.json|scripts/build_evidence.py"
  "L01|MEASURED|rk_ key for a scratch Radial workspace|$RUN/radial-live/|DONE 2026-11-02: hosted MCP tools/list. TODO: T0-T8; multi-identity race through POST /v1/issues/{id}/claim (needs several agent keys)"
  "L02|MEASURED|free Linear workspace + LINEAR_API_KEY|$RUN/linear-live/|DONE 2026-11-02: tools/list (scripts/linear_live.py); T1-T4 via MCP n=5 and claim race 10x20 (scripts/linear_tasks.py)"
  "L03|MEASURED|Atlassian Cloud site (Standard trial) + API token, acli installed|$RUN/jira-live/|TODO: tools/list, T0-T8 via MCP and acli; claim race; Rovo credit draw"
  "L04|MEASURED|all three + a scripted browser|$RUN/human/|TODO: human clicks, screens, time to first useful result for T3, T6, T7"
)

plan() {
  printf '%-4s %-10s %-50s %s\n' ID LABEL NEEDS OUTPUT
  for s in "${steps[@]}"; do IFS='|' read -r id label needs out what <<<"$s"; printf '%-4s %-10s %-50s %s\n      %s\n' "$id" "$label" "$needs" "$out" "$what"; done
}

radial_cli() {
  local cfg; cfg=$(mktemp -d -p .context)
  env -u RADIAL_KEY RADIAL_CONFIG_DIR="$PWD/$cfg" RADIAL_API_URL=http://127.0.0.1:9 RADIAL_AUTH_URL=http://127.0.0.1:9 \
    RADIAL_MCP_URL=http://127.0.0.1:9 bun .context/radial-cli/cli/src/index.ts "$@"
}

offline() {
  mkdir -p .context "$RUN"/{radial-static,baseline,tokens,sources}
  local R=$RUN/radial-static
  if [ -z "$RADIAL_REPO" ]; then
    echo "S01-S04: skipped (set RADIAL_REPO to a clone of the private Radial app repo to run them)"
  else
    radial_source
  fi
  echo "S05: baseline"
  python3 scripts/baseline.py $RUN/baseline --n 10 > $RUN/baseline/stdout.txt
  echo "S08-S09: derived files"
  python3 scripts/build_matrix.py > /dev/null
  python3 scripts/build_evidence.py
}

radial_source() {
  local R=$RUN/radial-static
  echo "S02-S03: snapshot Radial at $RADIAL_COMMIT (snapshots are gitignored; only derived lists are published)"
  git -C "$RADIAL_REPO" rev-parse "$RADIAL_COMMIT" > $R/radial-head.txt
  git -C "$RADIAL_REPO" show "$RADIAL_COMMIT:src/lib/mcp/tools.ts" > $R/mcp-tools.ts.snapshot
  git -C "$RADIAL_REPO" show "$RADIAL_COMMIT:cli/src/mcp.ts" > $R/cli-mcp.ts.snapshot
  git -C "$RADIAL_REPO" show "$RADIAL_COMMIT:cli/src/commands.ts" > $R/cli-commands.ts.snapshot
  git -C "$RADIAL_REPO" show "$RADIAL_COMMIT:cli/src/build.ts" > $R/cli-build.ts.snapshot
  git -C "$RADIAL_REPO" show "$RADIAL_COMMIT:cli/README.md" > $R/cli-README.snapshot.md
  git -C "$RADIAL_REPO" ls-tree -r --name-only "$RADIAL_COMMIT" src/app/api/v1 | grep route.ts | sed 's#src/app/api/v1/##; s#/route.ts##' > $R/rest-v1-routes.txt
  grep -E "^    name: '" $R/mcp-tools.ts.snapshot | sed -E "s/.*name: '([^']+)'.*/\1/" > $R/mcp-tool-names.txt
  grep -E "^    name: '" $R/cli-mcp.ts.snapshot | sed -E "s/.*name: '([^']+)'.*/\1/" > $R/cli-stdio-mcp-tool-names.txt
  comm -23 <(sort $R/mcp-tool-names.txt) <(sort $R/cli-stdio-mcp-tool-names.txt) > $R/mcp-hosted-minus-stdio.txt
  awk '/^export async function cmd[A-Za-z]+/{name=$4} /client\.(request|requestText)/{c[name]++} END{for(k in c) print k, c[k]}' \
    $R/cli-commands.ts.snapshot | sed 's/(client://' | sort > $R/cli-request-sites-per-command.txt
  echo "S04: Radial CLI offline (closed-port URLs)"
  mkdir -p .context/radial-cli
  git -C "$RADIAL_REPO" archive "$RADIAL_COMMIT" cli | tar -x --overwrite -C .context/radial-cli
  radial_cli help > $R/cli-help.txt 2>&1
  printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"bench","version":"0"}}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | timeout 10 bash -c "$(declare -f radial_cli); radial_cli mcp" > $R/stdio-mcp-tools-list.jsonl 2>$R/stdio-mcp-stderr.txt || true
  local cfg; cfg=$(mktemp -d -p .context)
  RADIAL_CONFIG_DIR="$PWD/$cfg" RADIAL_API_URL=http://127.0.0.1:9 RADIAL_AUTH_URL=http://127.0.0.1:9 \
    python3 scripts/timeit.py 10 $R/cli-help-timing.json -- bun .context/radial-cli/cli/src/index.ts help
  radial_cli list --json > $R/cli-list-noauth.stdout 2> $R/cli-list-noauth.stderr || true
  echo "S01: versions"
  jq -n --arg radial_commit "$(cat $R/radial-head.txt)" --arg cli "$(jq -r .version .context/radial-cli/cli/package.json)" \
    --arg bun "$(bun --version)" --arg node "$(node --version)" --arg git "$(git --version)" --arg python "$(python3 --version)" \
    --arg claude "$(claude --version 2>/dev/null || echo n/a)" --arg os "$(uname -sr)" --arg date "$(date -Iseconds)" \
    '{date:$date,radial_commit:$radial_commit,radial_cli_source_version:$cli,bun:$bun,node:$node,git:$git,python:$python,claude_code:$claude,os:$os}' > $RUN/versions.json
}

linear() {
  : "${LINEAR_API_KEY:?set LINEAR_API_KEY to a key for a scratch Linear workspace}"
  LINEAR_BENCH_OUT=$RUN/linear-live python3 scripts/linear_live.py
  LINEAR_BENCH_OUT=$RUN/linear-live python3 scripts/linear_tasks.py
  python3 scripts/build_matrix.py > /dev/null
  python3 scripts/build_evidence.py
  scripts/scan_secrets.sh
}

case "$mode" in
  plan) plan ;;
  offline) offline ;;
  tokens) scripts/cc-trials.sh 3 $RUN/tokens sonnet && python3 scripts/build_evidence.py ;;
  live) plan | grep -A1 '^L0' ;;
  linear) linear ;;
  *) echo "usage: $0 plan|offline|tokens|live|linear" >&2; exit 2 ;;
esac
