#!/usr/bin/env bash
# install.sh
# スキルを各 AI エージェントの互換パスに展開するスクリプト
#
# 処理概要:
#   0. skills/ の共通ファイルの複製が shared/ の正本と一致するかを確かめる（gh skill publish で配る中身と揃えるため）
#   1. skills/ の各スキル（SKILL.md があるディレクトリ）を .agents/skills/<スキル>/ に、過不足なくコピーする
#      （OpenCode・Codex・Copilot・Gemini CLI 互換）。以前の版の isdd-common が残っていれば削除する
#   2. .claude/skills → ../.agents/skills のシンボリックリンクを作成する（Claude Code 互換）
#
# gh skill install と同じく、スキルのディレクトリ単位で展開する。skills/ 直下のスキル以外のファイルは展開しない。
set -euo pipefail

# スクリプトが置かれているディレクトリ（プロジェクトルート）を基準にする
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== install.sh: スキルディレクトリのセットアップ ==="

if [ ! -d "skills" ]; then
    echo "    エラー: skills/ ディレクトリが見つかりません" >&2
    exit 1
fi

# --------------------------------------------------
# 0. 複製が正本と一致するかの確認
# --------------------------------------------------
echo ""
echo "[0/2] skills/ の共通ファイルが shared/ と一致するかを確認中..."
if ! python3 tools/build_skills.py --check; then
    echo "    エラー: 複製が古いか手で編集されています。python3 tools/build_skills.py を実行してから再実行してください" >&2
    exit 1
fi

# --------------------------------------------------
# 1. skills/<スキル>/ → .agents/skills/<スキル>/ にコピー
# --------------------------------------------------
echo ""
echo "[1/2] skills/ の各スキルを .agents/skills/ にコピー中..."

mkdir -p .agents/skills
for skill_dir in skills/*/; do
    [ -f "${skill_dir}SKILL.md" ] || continue
    name="$(basename "$skill_dir")"
    mkdir -p ".agents/skills/$name"
    # --delete: 以前の版にあって今の版に無いファイルを残さない（gh skill install の結果と揃える）
    rsync -a --delete --exclude "__pycache__" --exclude ".DS_Store" "$skill_dir" ".agents/skills/$name/"
    echo "    完了: $skill_dir → .agents/skills/$name/"
done

# v1 系までの共通スキル。今は各スキルに共通ファイルを同梱しているので不要
if [ -d ".agents/skills/isdd-common" ]; then
    rm -rf ".agents/skills/isdd-common"
    echo "    削除: .agents/skills/isdd-common（旧版の共通スキル）"
fi

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
echo "    .agents/skills/  ← OpenCode・Codex・Copilot・Gemini CLI 互換スキルディレクトリ"
echo "    .claude/skills   ← Claude Code 互換（.agents/skills/ へのシンボリックリンク）"
echo ""
echo "  スキル一覧:"
for skill_dir in .agents/skills/*/; do
    if [ -f "${skill_dir}SKILL.md" ]; then
        echo "    - $(basename "$skill_dir")"
    fi
done
