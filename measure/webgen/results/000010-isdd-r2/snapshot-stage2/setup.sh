#!/usr/bin/env bash
# 一度だけ実行する準備。外部パッケージは使わないので、Python 3.9 以上があることだけを確かめる。
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 が見つかりません。Python 3.12 を入れてから再実行してください。" >&2
  exit 1
fi

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || {
  echo "Python 3.9 以上が必要です: $(python3 --version 2>&1)" >&2
  exit 1
}

mkdir -p data
echo "セットアップ完了: $(python3 --version)。起動は PORT=8000 bash run.sh"
