#!/usr/bin/env bash
# Starts the SpeciesBase web server in the foreground.
#   PORT      port to serve on (default 8000), bound to 127.0.0.1
#   DATA_DIR  directory for the SQLite database (default ./data)
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
exec python3 app.py
