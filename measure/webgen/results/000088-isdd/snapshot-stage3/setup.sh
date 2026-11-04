#!/usr/bin/env bash
# 依存の導入。何度実行しても同じ状態になる。
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  "${PYTHON:-python3}" -m venv .venv
fi
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "setup.sh: dependencies are installed in .venv"
