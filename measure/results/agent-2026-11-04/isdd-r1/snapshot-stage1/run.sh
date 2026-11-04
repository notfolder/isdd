#!/usr/bin/env bash
# アプリを起動する。待ち受けポートは環境変数 PORT（既定 8000）。
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
exec .venv/bin/python -m app
