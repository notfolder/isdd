#!/usr/bin/env bash
# Web アプリを起動する。環境変数 PORT（既定 8000）、DATA_DIR（既定 ./data）、
# SESSION_IDLE_TIMEOUT_SECONDS（既定 1800）を読む。
set -euo pipefail
cd "$(dirname "$0")"
export PORT="${PORT:-8000}"
export DATA_DIR="${DATA_DIR:-./data}"
export SESSION_IDLE_TIMEOUT_SECONDS="${SESSION_IDLE_TIMEOUT_SECONDS:-1800}"
exec python3 -m app
