#!/usr/bin/env bash
# Starts the barbershop website in the foreground.
#   PORT      port to serve on (default 8000), bound to 127.0.0.1
#   DATA_DIR  where the SQLite database is stored (default ./data)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"

# exec replaces this shell with the server, so killing the PID stops the site.
exec python3 app.py
