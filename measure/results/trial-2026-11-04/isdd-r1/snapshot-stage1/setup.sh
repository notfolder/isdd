#!/usr/bin/env bash
# 準備（採点の前に 1 回だけ実行する）。Python 3.12 で仮想環境を作り、固定版の依存を入れる。
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)'; then
  echo "Python 3.12 以上が必要です（現在: $("$PY" --version 2>&1)）" >&2
  exit 1
fi

"$PY" -m venv .venv
.venv/bin/python -m pip install --quiet -r requirements.txt
echo "準備が完了しました。bash run.sh で起動します。"
