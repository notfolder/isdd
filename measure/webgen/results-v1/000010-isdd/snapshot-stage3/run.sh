#!/usr/bin/env bash
# PORT（既定 8000）と DATA_DIR（既定 プロジェクトルートの data）で Web サーバーを前景で起動する。
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-$(pwd)/data}"
exec python3 -m app
