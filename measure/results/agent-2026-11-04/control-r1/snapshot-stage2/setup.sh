#!/usr/bin/env bash
# 依存の導入（採点の前に 1 回実行する）
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 以上が必要です"'
python3 -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "setup 完了"
