#!/usr/bin/env bash
# isdd 対応表チェックの入口（isdd-setup が生成。再実行で上書き）
# 使い方: bash scripts/isdd/check.sh [--strict]
#   --strict を付けると警告も失敗扱いにする（実装スキルの完了条件用）
set -u
cd "$(dirname "$0")/../.."
exec python3 scripts/isdd/trace_map_checker.py "docs/detail_design.md" "docs/trace_map.md" "src" "$@"
