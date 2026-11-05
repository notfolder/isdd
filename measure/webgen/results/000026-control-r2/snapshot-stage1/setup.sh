#!/usr/bin/env bash
# Install/prepare the Polls website. Uses only the Python standard library,
# so there is nothing to download; this checks the runtime and creates DATA_DIR.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c "import sqlite3, http.server" || { echo "python3 with sqlite3 is required" >&2; exit 1; }

DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"
echo "Setup complete. Data directory: $DATA_DIR"
