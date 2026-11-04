#!/usr/bin/env bash
# 起動に必要な準備（採点の前に 1 回だけ実行する）。
# 仮想環境 .venv を作り、requirements.txt を導入し、E2E 用の Chromium を導入する。
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
echo "setup 完了: bash run.sh で起動します"
