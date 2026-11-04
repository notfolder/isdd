#!/usr/bin/env bash
# Web アプリを起動する（環境変数 PORT 既定 8000、DATA_DIR 既定 ./data）
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
export DATA_DIR="${DATA_DIR:-$PWD/data}"
export PORT="${PORT:-8000}"
exec .venv/bin/python app.py
