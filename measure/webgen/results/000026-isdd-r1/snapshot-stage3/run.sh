#!/usr/bin/env bash
# 起動: PORT（既定 8000）で Web サーバーを前景で動かす。DATA_DIR（既定 ./data）に SQLite を保存する。
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
mkdir -p "$DATA_DIR"
if [ ! -x .venv/bin/python ]; then
  echo "virtual environment not found. Run: bash setup.sh" >&2
  exit 1
fi
exec .venv/bin/python src/main.py
