#!/usr/bin/env bash
# isdd のコードチェックの入口（isdd-setup が生成。再実行で上書き）
# 使い方: bash scripts/isdd/check.sh [--strict]
#   1. 対応表チェック（trace_map_checker.py）。--strict を付けると警告も失敗扱いにする（isdd-build の完了条件用）
#      docs/active_change があれば、そこに書かれた変更の change_detail_design.md を正本に重ねて判定する
#   2. 依存チェック（dependency_checker.py）。scripts/isdd/dependencies.json の規則に反する import をエラーにする
set -u
cd "$(dirname "$0")/../.."
python3 scripts/isdd/trace_map_checker.py "docs/detail_design.md" "docs/trace_map.md" "src" --active-change "docs/active_change" --tests "e2e" --granularity "function" "$@"
trace_status=$?
echo
python3 scripts/isdd/dependency_checker.py scripts/isdd/dependencies.json "src"
dep_status=$?
[ $trace_status -ne 0 ] && exit $trace_status
exit $dep_status
