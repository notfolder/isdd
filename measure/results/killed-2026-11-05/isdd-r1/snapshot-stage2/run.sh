#!/usr/bin/env bash
# 起動: 環境変数 PORT（既定 8000）、DATA_DIR（既定 ./data）、SESSION_IDLE_TIMEOUT_SECONDS（既定 1800）で設定する。
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください。" >&2
  exit 1
fi
PYTHONPATH=src exec .venv/bin/python -m equipment_ledger
