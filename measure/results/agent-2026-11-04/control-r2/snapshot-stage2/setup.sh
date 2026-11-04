#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# 外部ライブラリは使わない（Python 3.12 の標準ライブラリだけ）。
python3 -c 'import sqlite3, hashlib, http.server' 
mkdir -p "${DATA_DIR:-data}"
echo "setup done"
