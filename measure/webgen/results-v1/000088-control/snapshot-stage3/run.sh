#!/usr/bin/env bash
# Starts the web server in the foreground on 127.0.0.1:$PORT (default 8000).
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
exec python3 app.py
