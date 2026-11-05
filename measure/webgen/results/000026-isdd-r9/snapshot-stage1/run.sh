#!/usr/bin/env bash
# Start the Polls website in the foreground. PORT defaults to 8000, DATA_DIR defaults to ./data.
set -euo pipefail

cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
mkdir -p "$DATA_DIR"

# Prefer Python 3.12 when it is installed under that name; fall back to python3.
PYTHON_BIN="python3"
if command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="python3.12"
fi

exec "$PYTHON_BIN" app/server.py
