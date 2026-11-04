#!/usr/bin/env bash
# Web アプリを起動する。環境変数 PORT（既定 8000）、DATA_DIR（既定 ./data）、
# SESSION_IDLE_TIMEOUT_SECONDS（既定 1800）で設定する。
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
exec .venv/bin/python -m app
