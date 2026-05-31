#!/usr/bin/env bash
# install.sh
# スキルディレクトリを各AIエージェントの互換パスにセットアップするスクリプト
#
# 処理概要:
#   1. skills/ → .agents/skills/ にコピー（OpenCode / AGENTS.md 互換）
#   2. .claude/skills → ../.agents/skills のシンボリックリンクを作成（Claude Code 互換）
set -euo pipefail

# スクリプトが置かれているディレクトリ（プロジェクトルート）を基準にする
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== install.sh: スキルディレクトリのセットアップ ==="

# --------------------------------------------------
# 1. skills/ → .agents/skills/ にコピー
# --------------------------------------------------
echo ""
echo "[1/2] skills/ を .agents/skills/ にコピー中..."

if [ ! -d "skills" ]; then
    echo "    エラー: skills/ ディレクトリが見つかりません" >&2
    exit 1
fi

mkdir -p .agents/skills
rsync -a skills/ .agents/skills/

echo "    完了: skills/ → .agents/skills/"

# --------------------------------------------------
# 2. .claude/skills → ../.agents/skills のシンボリックリンクを作成
# --------------------------------------------------
echo ""
echo "[2/2] .claude/skills → ../.agents/skills のシンボリックリンクを作成中..."

mkdir -p .claude
CLAUDE_SKILLS=".claude/skills"
AGENTS_SKILLS_REL="../.agents/skills"

if [ -L "$CLAUDE_SKILLS" ]; then
    echo "    スキップ: $CLAUDE_SKILLS はすでにシンボリックリンクです"
elif [ -e "$CLAUDE_SKILLS" ]; then
    echo "    警告: $CLAUDE_SKILLS がすでに存在します（シンボリックリンクではない）。スキップします" >&2
else
    ln -s "$AGENTS_SKILLS_REL" "$CLAUDE_SKILLS"
    echo "    完了: .claude/skills → ../.agents/skills"
fi

# --------------------------------------------------
# 結果表示
# --------------------------------------------------
echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "  配置先:"
echo "    .agents/skills/  ← OpenCode・Codex 互換スキルディレクトリ"
echo "    .claude/skills   ← Claude Code 互換（.agents/skills/ へのシンボリックリンク）"
echo ""
echo "  スキル一覧:"
for skill_dir in .agents/skills/*/; do
    if [ -f "${skill_dir}SKILL.md" ]; then
        echo "    - $(basename "$skill_dir")"
    fi
done
