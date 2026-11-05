#!/usr/bin/env bash
# Start the Wheel of Fortune web server in the foreground.
#   PORT      (default 8000)
#   DATA_DIR  (default ./data)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"

# exec so this shell is replaced by the server process (same PID; killing it stops the site).
exec python3 server.py
