#!/usr/bin/env bash
# アプリを起動する。事前に bash setup.sh を 1 回実行しておくこと。
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "先に bash setup.sh を実行してください" >&2
  exit 1
fi
exec .venv/bin/python -m src.main
