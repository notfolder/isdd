#!/usr/bin/env bash
# Setup for the surveys site. The app uses only the Python standard library,
# so there is nothing to download; this checks the runtime and prepares DATA_DIR.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sqlite3, http.server' 
DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
python3 -m py_compile app.py
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
