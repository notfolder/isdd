#!/usr/bin/env bash
# Start the web server in the foreground. PORT defaults to 8000, DATA_DIR defaults to ./data.
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
exec python3 src/app.py
