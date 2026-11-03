#!/usr/bin/env bash
# Token trials for the no-tracker baseline: T2 "pick up the next task" by a real Claude Code agent.
# Each trial runs in a fresh seeded repo under .context/, with --setting-sources project so no user
# settings, hooks or MCP servers load. RADIAL_KEY is unset. Output: one JSON per trial.
# Usage: scripts/cc-trials.sh <n> <out_dir> [model]
set -euo pipefail
n=${1:-3}; out=${2:-runs/2026-11-02/tokens}; model=${3:-sonnet}
here=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$out"
prompt='This repo tracks work in TODO.md. Pick up the next unclaimed task: change its "(owner: -) [todo]" to "(owner: agent-a) [in-progress]", commit, and push. Reply with only the task id.'
for i in $(seq 1 "$n"); do
  d=$(mktemp -d -p "$here/.context" cc-trial-XXXX)
  repo=$(python3 "$here/scripts/baseline.py" "$d" --seed-only)
  start=$(date +%s%N)
  (cd "$repo" && env -u RADIAL_KEY claude -p "$prompt" --output-format json --setting-sources project \
     --model "$model" --max-budget-usd 0.50 --no-session-persistence \
     --allowedTools "Bash(git:*)" "Bash(grep:*)" "Bash(sed:*)" "Read" "Edit" "Grep") > "$out/t2-trial-$i.json" || true
  end=$(date +%s%N)
  echo "{\"trial\":$i,\"wall_ms\":$(( (end - start) / 1000000 )),\"pushed_head\":\"$(git -C "$repo" log -1 --format=%s origin/main)\"}" > "$out/t2-trial-$i.meta.json"
  rm -rf "$d"
done
