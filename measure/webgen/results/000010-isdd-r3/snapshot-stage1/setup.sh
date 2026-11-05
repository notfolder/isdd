#!/usr/bin/env bash
# Prepare the prize wheel site. It uses only the Python standard library, so nothing is installed.
# Usage: bash setup.sh
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found. Install Python 3.9 or later." >&2
  exit 1
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "Python 3.9 or later is required." >&2
  exit 1
fi

if ! python3 -c 'import sqlite3' >/dev/null 2>&1; then
  echo "The sqlite3 module is missing from this Python installation." >&2
  exit 1
fi

DATA_DIR_VALUE="${DATA_DIR:-$(pwd)/data}"
mkdir -p "$DATA_DIR_VALUE"

echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
