#!/usr/bin/env bash
# One-time setup for the Wheel of Fortune site.
# The app uses only the Python 3 standard library, so there is nothing to download.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi
python3 -c 'import sqlite3, http.server' || { echo "python3 lacks sqlite3 support." >&2; exit 1; }

DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"
python3 -m py_compile server.py
echo "Setup complete. Data directory: $DATA_DIR"
