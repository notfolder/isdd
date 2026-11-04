#!/usr/bin/env bash
# Starts the Wheel of Fortune web server in the foreground.
# PORT (default 8000) and DATA_DIR (default ./data) come from the environment.
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
mkdir -p "$DATA_DIR"
exec node src/server.js
