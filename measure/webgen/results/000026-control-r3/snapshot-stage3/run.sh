#!/usr/bin/env bash
# Start the surveys web server in the foreground.
#   PORT      - port to serve on (default 8000)
#   DATA_DIR  - where the SQLite database lives (default ./data)
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"

# exec replaces this shell so the server's PID is the one that receives signals.
exec python3 app.py
