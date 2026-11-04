#!/usr/bin/env bash
# isdd のコードチェックの入口（isdd-setup が生成。再実行で上書き）
# 使い方: bash scripts/isdd/check.sh [--strict]
#   1. 対応表チェック（trace_map_checker.py）。--strict を付けると警告も失敗扱いにする（isdd-build の完了条件用）
#      docs/active_change があれば、そこに書かれた変更の change_detail_design.md を正本に重ねて判定する
#   2. 依存チェック（dependency_checker.py）。scripts/isdd/dependencies.json の規則に反する import をエラーにする
#   3. 受け入れ判定（acceptance_checker.py）。e2e/results/ の JUnit XML を対応表の DS-TS 行と突き合わせ、
#      要件ごとの実装済み判定の表を出す。--strict では不合格・未実行・要再実行を失敗扱いにする
set -u
cd "$(dirname "$0")/../.."
python3 scripts/isdd/trace_map_checker.py "docs/detail_design.md" "docs/trace_map.md" "num2words" --active-change "docs/active_change" --tests "e2e" --granularity "function" "$@"
trace_status=$?
echo
python3 scripts/isdd/dependency_checker.py scripts/isdd/dependencies.json "num2words"
dep_status=$?
echo
python3 scripts/isdd/acceptance_checker.py "docs/requirements.md" "docs/detail_design.md" "docs/trace_map.md" --junit "e2e/results/*.xml" --active-change "docs/active_change" --tests "e2e" --src "num2words" "$@"
acc_status=$?
[ $trace_status -ne 0 ] && exit $trace_status
[ $dep_status -ne 0 ] && exit $dep_status
exit $acc_status
