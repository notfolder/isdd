#!/usr/bin/env bash
# Start the wheel of fortune web server in the foreground.
#   PORT      port to listen on at 127.0.0.1 (default 8000)
#   DATA_DIR  folder for the SQLite database (default ./data, created if missing)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"

# exec replaces this shell with the server, so killing the PID stops the site.
exec python3 src/server.py
