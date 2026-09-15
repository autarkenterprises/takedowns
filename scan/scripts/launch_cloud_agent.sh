#!/usr/bin/env bash
# Launch one Cursor Cloud Agent scan (native Cursor model) via POST /v1/agents.
# Reads CURSOR_API_KEY, or repo-root content_scan_api_key.txt (gitignored).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -q -r "$ROOT/requirements.txt"
fi
export PYTHONPATH="$ROOT/src"
exec "$ROOT/.venv/bin/python" -m takedowns_scan.cloud_launch
