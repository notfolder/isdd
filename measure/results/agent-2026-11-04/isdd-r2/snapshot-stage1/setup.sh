#!/usr/bin/env bash
# 採点の前に 1 回実行する。仮想環境を作り、依存と E2E 用の Chromium を入れる。
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
