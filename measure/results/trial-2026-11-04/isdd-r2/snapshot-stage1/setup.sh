#!/usr/bin/env bash
# 起動の前に 1 回だけ実行する。外部パッケージは使わないので、導入するものは無い。
# Python 3.12 以上と sqlite3 が使えることを確かめる。
set -euo pipefail
cd "$(dirname "$0")"
python3 -c 'import sys, sqlite3; assert sys.version_info >= (3, 12), "Python 3.12 以上が必要です: " + sys.version; print("python", sys.version.split()[0], "sqlite", sqlite3.sqlite_version)'
echo "準備できました。bash run.sh で起動します。"
