#!/usr/bin/env bash
# 採点の前に 1 回だけ実行する。仮想環境を作り、依存と E2E 用のブラウザを入れる。
set -euo pipefail
cd "$(dirname "$0")"

if command -v python3.12 >/dev/null 2>&1; then
  PY=python3.12
else
  PY=python3
fi
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
  echo "Python 3.12 が必要です（python3.12 か、Python 3.12 を指す python3）" >&2
  exit 1
fi

"$PY" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
echo "準備が終わりました。bash run.sh で起動します。"
