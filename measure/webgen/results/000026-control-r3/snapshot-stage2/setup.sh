#!/usr/bin/env bash
# Install/prepare dependencies. The site uses only the Python 3 standard library,
# so this just verifies the interpreter and creates the data directory.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found." >&2
  exit 1
fi

python3 -c 'import sqlite3, http.server'

DATA_DIR="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR"
echo "Setup complete (Python $(python3 --version 2>&1 | awk '{print $2}'), data dir: $DATA_DIR)."
