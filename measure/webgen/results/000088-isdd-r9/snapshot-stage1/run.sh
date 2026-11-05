#!/usr/bin/env bash
# Start the Species Database web server in the foreground.
#   PORT=8000 bash run.sh      (PORT defaults to 8000)
#   DATA_DIR=/path bash run.sh (DATA_DIR defaults to ./data)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$ROOT/data}"

mkdir -p "$DATA_DIR"
cd "$ROOT"
exec "$PYTHON" src/server.py
