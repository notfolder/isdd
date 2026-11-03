#!/usr/bin/env bash
# 単体テスト（tests/）を、このマシンにある複数の版の Python で実行する。
# スクリプトは Python 3.9 以上の標準ライブラリだけで動かす決まりなので、
# 最も古い版（macOS 標準の 3.9）と新しい版の両方で通ることを確かめる。
# 非推奨の警告（DeprecationWarning・SyntaxWarning）も失敗として扱い、将来の版で消える書き方を早めに見つける。
#
# 使い方: bash tools/test_pythons.sh
#   見つける Python: PATH 上の python3 と python3.9〜python3.20、/usr/bin/python3、uv が管理する版（uv がある場合）
set -u
cd "$(dirname "$0")/.."

candidates=()
add() { [ -x "$1" ] && candidates+=("$1"); }
add /usr/bin/python3
for name in python3 python3.9 python3.10 python3.11 python3.12 python3.13 python3.14 python3.15 python3.16 python3.17 python3.18 python3.19 python3.20; do
  path="$(command -v "$name" 2>/dev/null || true)"
  [ -n "$path" ] && add "$path"
done
if command -v uv >/dev/null 2>&1; then
  for minor in 9 10 11 12 13 14 15 16 17 18 19 20; do
    path="$(uv python find "3.$minor" --no-project 2>/dev/null || true)"
    [ -n "$path" ] && add "$path"
  done
fi

# 同じ版を 2 回走らせない
log="$(mktemp)"
seen=" "
tested=0
failed=0
for py in "${candidates[@]}"; do
  version="$("$py" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null)" || continue
  minor="${version%.*}"
  case "$seen" in *" $minor "*) continue ;; esac
  seen="$seen$minor "
  case "$minor" in 3.[0-8]) echo "対象外: Python ${version}（3.9 未満）: $py"; continue ;; esac
  if PYTHONWARNINGS="error::DeprecationWarning,error::SyntaxWarning" "$py" -m unittest discover -s tests -t tests -q >"$log" 2>&1; then
    echo "合格: Python ${version}（${py}）"
  else
    echo "失敗: Python ${version}（${py}）"
    tail -20 "$log"
    failed=$((failed + 1))
  fi
  tested=$((tested + 1))
done
rm -f "$log"

tested_list="${seen# }"
echo "実行した版: ${tested} 種類（${tested_list% }）"
if [ "$tested" -lt 2 ]; then
  echo "注意: 1 種類の版でしか確かめていない。古い版（3.9）と新しい版の両方を入れてから実行する（例: uv python install 3.9 3.14）" >&2
fi
[ "$failed" -eq 0 ]
