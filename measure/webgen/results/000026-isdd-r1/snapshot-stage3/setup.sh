#!/usr/bin/env bash
# 依存の導入: 仮想環境 .venv を作り、requirements.txt を入れる。何度実行しても同じ状態になる。
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "setup complete: $(.venv/bin/python --version)"
