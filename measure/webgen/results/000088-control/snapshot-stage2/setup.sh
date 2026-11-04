#!/usr/bin/env bash
# Setup for the Species Biology Database. Uses only the Python standard library, so there is nothing to install.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sqlite3, sys; assert sys.version_info >= (3, 9), "Python 3.9+ required"'
DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
echo "Setup complete. Data directory: $DATA_DIR"
