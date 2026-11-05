#!/usr/bin/env bash
# Prepare the project. The site uses only the Python 3.12 standard library, so no packages are installed.
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required (Python 3.12 is recommended)." >&2
  exit 1
fi
mkdir -p "${DATA_DIR:-./data}"
python3 -c 'import sqlite3, http.server; print("Python", __import__("sys").version.split()[0], "ok")'
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
