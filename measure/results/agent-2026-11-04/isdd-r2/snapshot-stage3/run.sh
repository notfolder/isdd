#!/usr/bin/env bash
# アプリを起動する。環境変数 PORT（既定 8000）、HOST（既定 0.0.0.0）、DATA_DIR、SESSION_IDLE_TIMEOUT_SECONDS を読む。
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
exec .venv/bin/python -m equipment_ledger
