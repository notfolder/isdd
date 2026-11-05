#!/usr/bin/env bash
# Start the Polls website in the foreground.
#   PORT      port to serve on 127.0.0.1 (default 8000)
#   DATA_DIR  directory for the database (default ./data)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"

# exec replaces this shell, so the server keeps the PID of `bash run.sh`.
exec python3 app.py
