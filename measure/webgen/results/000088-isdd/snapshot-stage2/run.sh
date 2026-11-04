#!/usr/bin/env bash
# Web サーバーの起動。PORT（既定 8000）と DATA_DIR（既定 ./data）を環境変数から読む。
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
if [ ! -x .venv/bin/python ]; then
  bash setup.sh
fi
mkdir -p "$DATA_DIR"
exec .venv/bin/python -m app
