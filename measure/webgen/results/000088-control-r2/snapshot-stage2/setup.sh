#!/usr/bin/env bash
# One-time setup. This project uses only the Python standard library,
# so setup just checks the interpreter, prepares the data directory and
# verifies that app.py compiles.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
"$PYTHON" -c 'import sqlite3, http.server; print("Python", __import__("sys").version.split()[0], "OK")'

DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"

"$PYTHON" -m py_compile app.py
rm -rf __pycache__
echo "Setup complete. Data directory: $DATA_DIR"
