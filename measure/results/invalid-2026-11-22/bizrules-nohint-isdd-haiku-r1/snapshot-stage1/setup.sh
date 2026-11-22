#!/usr/bin/env bash
# 初回の準備: 仮想環境を作り、依存を入れ、E2E 用の Chromium を取得する。何度実行しても同じ状態になる。
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if ! "$PY" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
  echo "Python 3.12 が必要です（PYTHON 環境変数で指定できます）" >&2
  exit 1
fi

[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
.venv/bin/python -m playwright install chromium
echo "準備が終わりました。起動は bash run.sh です。"
