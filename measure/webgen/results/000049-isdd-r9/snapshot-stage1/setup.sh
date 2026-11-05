#!/usr/bin/env bash
# One-time setup. The site uses only the Python standard library, so nothing is installed.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Python 3.9 or later is required"'
python3 -c 'import sqlite3; print("sqlite3 available:", sqlite3.sqlite_version)'
mkdir -p data
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
