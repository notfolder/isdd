#!/usr/bin/env bash
# 生物種情報データベースの準備。外部パッケージは使わないため、確認と保存先の作成だけを行う。
# 使い方: bash setup.sh
set -euo pipefail

cd "$(dirname "$0")"

python3 -c '
import sys
if sys.version_info < (3, 9):
    sys.exit("Python 3.9 or later is required (3.12 is recommended).")
print("Python", sys.version.split()[0], "OK")
'

DATA_DIR="${DATA_DIR:-$PWD/data}"
mkdir -p "$DATA_DIR"
echo "Data folder: $DATA_DIR"
echo "Setup complete. Start the site with: PORT=8000 bash run.sh"
