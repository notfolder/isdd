#!/usr/bin/env bash
# Starts the Wheel of Fortune web server in the foreground.
#   PORT      port to serve on (default 8000)
#   DATA_DIR  where the database lives (default ./data)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"
exec python3 server.py
