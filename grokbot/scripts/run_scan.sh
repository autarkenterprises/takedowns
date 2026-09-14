#!/usr/bin/env bash
# One-shot GrokBot catalog scan for Cursor Cloud (and local CLI).
# Requires XAI_API_KEY. Never starts the FastAPI server.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -z "${XAI_API_KEY:-}" ]]; then
  echo "XAI_API_KEY is not set; refusing to scan." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
export PYTHONPATH="$ROOT/src"
exec .venv/bin/python -m takedowns_grokbot.cli "$@"
