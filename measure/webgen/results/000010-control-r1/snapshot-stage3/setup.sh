#!/usr/bin/env bash
# One-time setup. The app uses only the Python 3 standard library and
# Node-free static files, so there is nothing to download.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi

python3 - <<'PY'
import sys
if sys.version_info < (3, 8):
    raise SystemExit("Python 3.8+ is required")
import sqlite3
print("Python", sys.version.split()[0], "- sqlite3", sqlite3.sqlite_version, "OK")
PY

echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
