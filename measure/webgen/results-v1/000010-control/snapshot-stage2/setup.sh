#!/usr/bin/env bash
# Installs nothing: the site uses only the Python 3 standard library (sqlite3, http.server).
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sqlite3, http.server, sys; assert sys.version_info >= (3, 9)'
echo "setup complete"
