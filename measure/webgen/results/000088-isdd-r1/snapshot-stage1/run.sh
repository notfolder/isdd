#!/usr/bin/env bash
# 生物種情報データベースを起動する（前面で動き続ける）。
# 使い方: PORT=8000 bash run.sh
# 環境変数: PORT（既定 8000）、DATA_DIR（既定はプロジェクトの data）
set -euo pipefail

cd "$(dirname "$0")"

export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"

exec python3 -m src.web.server
