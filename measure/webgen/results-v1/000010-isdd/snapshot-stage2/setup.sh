#!/usr/bin/env bash
# 実行に必要な Python を確かめる。外部パッケージは使わないため、インストールは無い。
set -euo pipefail
cd "$(dirname "$0")"
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "Python 3.9 or later is required." >&2
  exit 1
fi
echo "No external packages are needed. $(python3 -V) is ready."
