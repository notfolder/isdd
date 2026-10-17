#!/usr/bin/env bash
# claude モード用に、新しい GitHub Copilot CLI を evals/.copilot-cli/ に入れる。
#
# 背景: waza 0.38.10 が同梱する Copilot ランタイム（1.0.85）は、Haiku 5.5 に
# 旧式の思考設定（thinking.type=enabled）を送るため 400 で落ちる。
# 新しい Copilot CLI（1.0.98 以降）は適応型思考を使うので通る。
# run-all.sh claude は、ここに入れた CLI を COPILOT_CLI_PATH として自動で使う。
#
# 使い方: bash evals/install-copilot-cli.sh [version]   （既定: 1.0.98）
set -eu

version="${1:-1.0.98}"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo_root/evals/.copilot-cli"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm が見つかりません。Node.js を入れてから実行してください" >&2
  exit 1
fi

mkdir -p "$dest"
cd "$dest"
[[ -f package.json ]] || printf '{"name":"isdd-copilot-cli","private":true}\n' > package.json
npm install --no-audit --no-fund "@github/copilot@${version}"

bin="$(ls -d "$dest"/node_modules/@github/copilot-*/copilot 2>/dev/null | head -1)"
if [[ -z "$bin" || ! -x "$bin" ]]; then
  echo "Copilot CLI の実行ファイルが見つかりません: $dest/node_modules/@github/copilot-*/copilot" >&2
  exit 1
fi
"$bin" --version
echo "installed: $bin"
echo "run-all.sh claude はこの CLI を自動で使います（COPILOT_CLI_PATH を明示すればそちらを優先）"
