# Skill調査まとめ（GitHub Copilot / Claude Code / OpenCode / Codex）

各ツールの「skill関連ファイルの格納場所」と「起動方法」を公式ドキュメントに基づいて整理したものです。

## 各ツールの詳細

### GitHub Copilot

| 区分 | 格納場所 |
|---|---|
| プロジェクト | `.github/skills/<skill-name>/SKILL.md` |
| プロジェクト | `.claude/skills/<skill-name>/SKILL.md` |
| プロジェクト | `.agents/skills/<skill-name>/SKILL.md` |
| 個人 | `~/.copilot/skills/<skill-name>/SKILL.md` |
| 個人 | `~/.agents/skills/<skill-name>/SKILL.md` |

- **起動方法**: 自動（プロンプト内容に応じて Copilot が選択）
- **補足**: カスタムインストラクションは `.github/copilot-instructions.md`、`.github/instructions/**/*.instructions.md`、`AGENTS.md` も使用

### Claude Code

| 区分 | 格納場所 |
|---|---|
| 個人（全プロジェクト） | `~/.claude/skills/<skill-name>/SKILL.md` |
| プロジェクト | `.claude/skills/<skill-name>/SKILL.md` |
| プラグイン | `<plugin>/skills/<skill-name>/SKILL.md` |
| 組織管理 | managed settings 経由 |

- **起動方法**: `/skill-name` で明示起動、またはプロンプトに応じて自動起動
- **補足**: `.claude/commands/deploy.md` と `.claude/skills/deploy/SKILL.md` は同等（`/deploy` を生成）。`.github/skills/` および `.agents/skills/` は **読み込まない**

### OpenCode

| 区分 | 格納場所 |
|---|---|
| プロジェクト（ネイティブ） | `.opencode/skills/<name>/SKILL.md` |
| グローバル（ネイティブ） | `~/.config/opencode/skills/<name>/SKILL.md` |
| プロジェクト（Claude互換） | `.claude/skills/<name>/SKILL.md` |
| グローバル（Claude互換） | `~/.claude/skills/<name>/SKILL.md` |
| プロジェクト（Agent互換） | `.agents/skills/<name>/SKILL.md` |
| グローバル（Agent互換） | `~/.agents/skills/<name>/SKILL.md` |

- **起動方法**: 内部 `skill` ツールで自動ロード、`$skill-name` または `/skill-name` で明示起動
- **補足**: git ワークツリーのルートに向かってディレクトリを遡りながらスキルを探索する

### Codex（OpenAI）

| 区分 | 格納場所 |
|---|---|
| REPO（カレントディレクトリ） | `$CWD/.agents/skills/` |
| REPO（親ディレクトリ） | `$CWD/../.agents/skills/` |
| REPO（リポジトリルート） | `$REPO_ROOT/.agents/skills/` |
| USER（個人） | `$HOME/.agents/skills/` |
| ADMIN（マシン共有） | `/etc/codex/skills/` |
| SYSTEM | Codex 組み込み |

- **起動方法**: プロンプト内で `$skill-name` を使った明示起動、または説明に基づく自動起動
- **AGENTS.md**: `~/.codex/AGENTS.md`（グローバル）、プロジェクト内の `AGENTS.md` / `AGENTS.override.md`（プロジェクト）
- **補足**: `.claude/skills/` および `.github/skills/` は**読み込まない**。`.agents/skills/` のみ対応

---

## ディレクトリ別 対応ツール一覧

| ディレクトリ | GitHub Copilot | Claude Code | OpenCode | Codex |
|---|:---:|:---:|:---:|:---:|
| `.github/skills/` | ✓ | ✗ | ✗ | ✗ |
| `.claude/skills/` | ✓ | ✓ | ✓ | ✗ |
| `.agents/skills/` | ✓ | ✗ | ✓ | ✓ |
| `.opencode/skills/` | ✗ | ✗ | ✓ | ✗ |

**4ツール全カバーには単一ディレクトリでは不可能。**
- `.claude/skills/` → Copilot + Claude Code + OpenCode をカバー（3/4）
- `.agents/skills/` → Copilot + OpenCode + Codex をカバー（3/4）
- **両方に配置する**（または symlink）と全4ツールをカバーできる

---

## 参照元（公式ドキュメント）

- **GitHub Copilot**
  - https://docs.github.com/en/copilot/reference/customization-cheat-sheet
  - https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- **Claude Code**
  - https://code.claude.com/docs/en/skills
  - https://code.claude.com/docs/en/memory
- **OpenCode**
  - https://opencode.ai/docs/en/skills/
- **Codex（OpenAI）**
  - https://developers.openai.com/codex/skills
  - https://developers.openai.com/codex/guides/agents-md
