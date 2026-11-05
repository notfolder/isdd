#!/usr/bin/env bash
# サイトを前景で起動する。PORT（既定 8000）と DATA_DIR（既定は ./data）は環境変数で決める。
# 止めるには Ctrl+C か、このプロセスへの終了シグナルを送る。
set -euo pipefail
cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"

exec python3 -m app
