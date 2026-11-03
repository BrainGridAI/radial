#!/usr/bin/env bash
# Fail if anything under the benchmark folder looks like a secret, a private path or an identity.
# This folder ships in a public repo. Run before every commit that touches it.
# Usage: scripts/scan_secrets.sh [dir]   (default: the benchmarks folder). Exit 1 on any hit.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
dir=${1:-$(dirname "$here")}
self="$here/scan_secrets.sh"

patterns=(
  'lin_api_[A-Za-z0-9]{8,}'                              # Linear API key
  'lin_oauth_[A-Za-z0-9]{8,}'                            # Linear OAuth token
  '\brk_(live|test|read|triage|write)_[A-Za-z0-9]{6,}'   # Radial API key
  '\brk_[A-Za-z0-9]{20,}'                                # Radial API key, other shapes
  '\bsk-[A-Za-z0-9_-]{16,}'                              # OpenAI / Anthropic style key
  '\bsk_(live|test)_[A-Za-z0-9]{8,}'                     # Stripe secret key
  '\b(ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}'                 # GitHub token
  'github_pat_[A-Za-z0-9_]{20,}'
  'xox[abprs]-[A-Za-z0-9-]{10,}'                         # Slack token
  'AKIA[0-9A-Z]{16}'                                     # AWS access key id
  '-----BEGIN [A-Z ]*PRIVATE KEY'
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.'          # JWT
  'Bearer [A-Za-z0-9._~+/-]{16,}'                        # literal bearer token
  '(api[_-]?key|secret|password|token)["'"'"' ]*[:=] *["'"'"'][A-Za-z0-9_./+-]{12,}'
  '/workspace/'                                          # local absolute paths
  '/home/[a-z]'
  '/Users/[A-Za-z]'
  'braingrid-proj-[0-9]+'                                # internal cloud project
  'app\.radial\.build/braingrid'                         # internal workspace URL
  '\.linear-key'
  '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'  # UUIDs (user, viewer, session ids)
)
# Email addresses quoted from vendor docs as examples. Everything else is a hit.
email_ok='^(admin@atlassian\.com|user@atlassian\.com|[A-Za-z0-9._%+-]+@example\.(com|org|net))$'

hits=0
for p in "${patterns[@]}"; do
  out=$(grep -rnIE --exclude-dir=.context --exclude-dir=node_modules -e "$p" "$dir" | grep -v "^$self:")
  if [ -n "$out" ]; then echo "HIT [$p]"; echo "$out" | cut -c1-200; hits=$((hits + 1)); fi
done
emails=$(grep -rnIoE --exclude-dir=.context --exclude-dir=node_modules '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$dir" \
  | grep -v "^$self:" | awk -F: -v ok="$email_ok" '{ if ($NF !~ ok) print }')
if [ -n "$emails" ]; then echo "HIT [email]"; echo "$emails"; hits=$((hits + 1)); fi
secret_files=$(find "$dir" -path "$dir/.context" -prune -o -type f \( -name '.linear-key' -o -name '.env*' -o -name '*.pem' -o -name '*.key' \) -print)
if [ -n "$secret_files" ]; then echo "HIT [secret file]"; echo "$secret_files"; hits=$((hits + 1)); fi

files=$(find "$dir" -path "$dir/.context" -prune -o -type f -print | wc -l | tr -d ' ')
if [ "$hits" -gt 0 ]; then echo "scan_secrets: FAIL, $hits pattern(s) hit across $files files in $dir"; exit 1; fi
echo "scan_secrets: PASS, ${#patterns[@]} patterns + emails + secret file names, 0 hits across $files files in $dir"
