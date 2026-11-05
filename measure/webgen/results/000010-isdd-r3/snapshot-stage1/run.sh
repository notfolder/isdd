#!/usr/bin/env bash
# Start the prize wheel web server in the foreground at http://127.0.0.1:$PORT.
# Environment: PORT (default 8000), DATA_DIR (default ./data, created if missing).
# Usage: PORT=8000 bash run.sh
set -euo pipefail

cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"

exec python3 src/server.py
