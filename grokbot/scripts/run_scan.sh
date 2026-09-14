#!/usr/bin/env bash
# Ingest candidate JSON produced by a Cursor Cloud Agent Automation.
# Does not call xAI/Grok. Usage: ./grokbot/scripts/run_scan.sh path/to/inbox.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

JSON="${1:-}"
if [[ -z "$JSON" ]]; then
  echo "usage: $0 <candidates.json>" >&2
  exit 2
fi

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
export PYTHONPATH="$ROOT/src"
exec .venv/bin/python -m takedowns_grokbot.cli --from-json "$JSON"
