#!/usr/bin/env bash
# Starts the Wheel of Fortune server in the foreground.
# PORT (default 8000) and DATA_DIR (default ./data) come from the environment.
set -euo pipefail
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"
DATA_DIR="$(cd "$DATA_DIR" && pwd)"
export DATA_DIR
cd "$(dirname "$0")"
exec python3 server.py
