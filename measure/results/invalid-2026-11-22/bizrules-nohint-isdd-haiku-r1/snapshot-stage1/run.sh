#!/usr/bin/env bash
# 起動: DB を用意し、gunicorn で Web アプリを PORT（既定 8000）で待ち受ける。
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
DATA_DIR="$(cd "$DATA_DIR" && pwd)"
export DATA_DIR

if [ ! -x .venv/bin/gunicorn ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi

.venv/bin/python src/manage.py migrate --noinput
exec .venv/bin/gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --chdir src config.wsgi:application
