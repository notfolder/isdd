#!/usr/bin/env bash
# Starts the polls website in the foreground at http://127.0.0.1:$PORT
# PORT defaults to 8000; DATA_DIR defaults to ./data (created if missing).
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
exec python3 server.py
