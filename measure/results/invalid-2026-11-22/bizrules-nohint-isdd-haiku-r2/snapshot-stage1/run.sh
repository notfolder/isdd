#!/usr/bin/env bash
# Web アプリを起動する。待ち受けは環境変数 PORT（既定 8000）、データの保存先は DATA_DIR。
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
exec .venv/bin/python src/main.py
