# isdd バックログ

完了・見送りは `BACKLOG-archive.md`、案・記録は `IDEAS.md` にある。

## v2.0.1 と v2.1.0（正本の反映時期、スキル構成の見直し）

概要: .history/2026-11-03-1404-正本反映時期とスキル再構成/summary.md

- [x] (2026-11-03) v2.1.0 の A・B・C（外部連携の責務分割、短い設計 ID、スキル 4 本と質問のまとめ出し）をブランチ `v2.1.0-restructure` に実装し、PR #9 を作成
- [x] (2026-11-03) このPCのユーザーグローバル（Claude Code 用）を v2.1.0（`e393c09`）に入れ替え、旧 8 本を削除
- [ ] v2.1.0 を幾つかの実プロジェクトで試し、問題があれば `v2.1.0-restructure` で直してから PR #9 をマージする（ユーザー作業、追加 2026-11-03、重要 高）
- [ ] PR #9 のマージ後に v2.1.0 を公開し、ユーザーグローバルを `--pin v2.1.0` で入れ直す（追加 2026-11-03、重要 高）
- [ ] 外部連携の設計の段階（ライブラリの採否とモック方式を設計 ID で書く）に Haiku の eval 場面を 1 本足す（追加 2026-11-03、重要 高）
- [ ] マージ済みのブランチ `fix-external-research-change-flow`・`restore-post-impl-canonical` をローカルと GitHub から消す（追加 2026-11-03、重要 低）
- [ ] `evals/isdd-<旧スキル名>/` に残る git 管理外の eval 記録を消す（ユーザー作業、`! rm -rf`。追加 2026-11-03、重要 低）

## 環境・言語の非固定化と ID の入れ方の再検討（ブランチ feature-rethink-env-and-id）

概要: .history/2026-10-18-0312-スキルレビューと重大修正/summary.md

- [ ] 検証 D: microsoft/waza をフォークし、`internal/execution/claudecode.go` に `claude -p --output-format stream-json` を子プロセスで呼ぶエンジンを実装する（追質問は `--resume`、スキルは `.claude/skills` と `--append-system-prompt`）（追加 2026-10-17、重要 低）
- [ ] 検証 D: `cmd/waza/engine_factory.go`・`schemas/eval.schema.json`・`schemas/config.schema.json`・`internal/models` の実行器名の判定に `isdd-claude-sdk` を追加する（追加 2026-10-17、重要 低）
- [ ] 検証 D: 偽の `claude` スクリプトで単体テストを書き、isdd の eval を `executor: isdd-claude-sdk` で実際に回す（追加 2026-10-17、重要 低）
- [ ] 検証 D: フォークのビルド物を `waza-cc` の名前で入れ、`run-all.sh` が環境変数 `WAZA_BIN` で切り替えられるようにする（追加 2026-10-17、重要 低）
- [ ] 検証の題材と範囲（通しフロー用のサンプル案件、インタビュー回答の固定方式、既存 fixture の書き換え時期）を決める（追加 2026-10-17、重要 低）
- [ ] `.env` の旧変数 3 行（`WAZA_CLAUDE_MODEL_PRIMARY`・`WAZA_CLAUDE_MODEL_SECONDARY`・`WAZA_CLAUDE_ESCALATE`）を削除する（ユーザー作業。残っていても動作に影響なし）（追加 2026-10-18、重要 低）
- [ ] 実行基盤の固まり（2026-10-18 の eval で 2 回。Copilot CLI がモデル応答待ちのまま 22〜40 分停止、転記ファイル未作成）が再発したら、Copilot CLI の更新か検証 D を優先する。2026-11-03 までの eval では再発なし（追加 2026-10-18、重要 低）
- [ ] ローカルブランチ `feature-equipment-lending-management`（2026-10-19、main に無いコミット 7 件。備品管理・貸出管理アプリを題材に、最新のスキルで要件定義・詳細設計・実装まで通した記録とみられる）の扱いを決める。残すなら目的をここに書き、不要なら削除する（追加 2026-10-25、重要 低）
