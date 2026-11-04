#!/usr/bin/env bash
# 初回に 1 回だけ実行する。仮想環境 .venv を作り、依存を導入する。
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
