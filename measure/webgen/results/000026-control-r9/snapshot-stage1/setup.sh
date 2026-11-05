#!/usr/bin/env bash
# Prepares the polls website. The app uses only the Python 3 standard library,
# so there is nothing to download: this checks the interpreter, creates the
# data directory, and compiles the server once to catch syntax errors early.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3, 8), "Python 3.8+ required"'
mkdir -p "${DATA_DIR:-$PWD/data}"
python3 -m py_compile server.py
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
