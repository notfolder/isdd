#!/usr/bin/env bash
# Installs/prepares everything needed. The app uses only the Python standard
# library, so there is no package to install; this checks the runtime and
# prepares the data directory.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi
python3 -c "import sqlite3, http.server" 
mkdir -p "${DATA_DIR:-$PWD/data}"
python3 -m py_compile server.py
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
