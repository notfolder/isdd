#!/usr/bin/env bash
# 初回の準備: 仮想環境を作り、依存を導入し、E2E 用の Chromium を取得する。
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Python 3.12 以上が必要です" >&2
  exit 1
fi

if [ ! -x .venv/bin/python ]; then
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
echo "準備が終わりました。bash run.sh で起動します。"
