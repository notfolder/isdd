#!/usr/bin/env bash
# Install/check dependencies. The app uses only the Python standard library,
# so this just verifies the interpreter is available.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi

python3 -c 'import sqlite3, http.server'
echo "Python $(python3 --version 2>&1) with sqlite3 is available."
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
