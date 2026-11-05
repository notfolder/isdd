#!/usr/bin/env bash
# Starts the web server in the foreground. Serves http://127.0.0.1:$PORT
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"

exec "${PYTHON:-python3}" app.py
