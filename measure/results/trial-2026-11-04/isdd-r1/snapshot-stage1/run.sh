#!/usr/bin/env bash
# 起動。環境変数 PORT（既定 8000）、DATA_DIR（既定 data）、SESSION_IDLE_TIMEOUT_SECONDS（既定 1800）を使う。
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-data}"
export SESSION_IDLE_TIMEOUT_SECONDS="${SESSION_IDLE_TIMEOUT_SECONDS:-1800}"

if [ ! -x .venv/bin/waitress-serve ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi

# 社内ネットワークからだけ開く制限は、サーバーのファイアウォールで行う。
exec .venv/bin/waitress-serve --host=0.0.0.0 --port="$PORT" --threads=16 --call app:create_app
