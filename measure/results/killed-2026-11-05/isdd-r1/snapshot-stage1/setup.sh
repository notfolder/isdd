#!/usr/bin/env bash
# 導入: 仮想環境を作り、本番とテストの依存を入れ、E2E 用の Chromium を入れる。採点の前に 1 回実行する。
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
echo "導入が完了しました。起動は bash run.sh です。"
