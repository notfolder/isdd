#!/usr/bin/env bash
# Starts the Organism Database web server in the foreground.
#   PORT      (default 8000)  - served at http://127.0.0.1:$PORT
#   DATA_DIR  (default ./data) - SQLite database location
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
exec python3 server.py
