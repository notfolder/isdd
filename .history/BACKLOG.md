# isdd バックログ

完了・見送りは `BACKLOG-archive.md`、案・記録は `IDEAS.md` にある。

## v2.0.1 と v2.1.0（正本の反映時期、スキル構成の見直し）

概要: .history/2026-11-03-1404-正本反映時期とスキル再構成/summary.md

- [ ] 公開後、試用中のプロジェクトで `--pin v2.2.0` で入れ直して `isdd-setup` を再実行する（チェッカーの複製と `check.sh`・`.gitignore` の `e2e/results/` を更新。v2.1.0 は飛ばしてよい。ユーザー作業、追加 2026-11-03、v2.2.0 に更新 2026-11-04、重要 高）
- [ ] 対応表の粒度 `class` を Haiku で確かめる eval 場面を 1 本足す（依存の規則と `DS-TS` の行は remap の場面で確かめ済み。追加 2026-11-03、重要 低）
- [ ] 外部連携の設計の段階（ライブラリの採否とモック方式を設計 ID で書く）に Haiku の eval 場面を 1 本足す（追加 2026-11-03、重要 高）
- [ ] `evals/isdd-<旧スキル名>/` に残る git 管理外の eval 記録を消す（ユーザー作業、`! rm -rf`。追加 2026-11-03、重要 低）

## isdd の効果の計測（isdd あり・なしの比較）

概要: .history/2026-11-05-1101-計測のやり直しと決め事の見える化/summary.md（結果は `measure/results/REPORT.md`。前半が 2026-11-04 の計測 1〜4、後半が 2026-11-05 のやり直しの途中結果）

- [ ] 計測のやり直しの再開: 段階 3（Web サイト 5 課題 × 2 群 × 3 回のうち残り 17 本）、段階 4（計測 5 の生成 8 本と判定 16 本）、段階 5（報告書の書き直し）。手順は summary.md の「次にやること」と `measure/results/timeline.txt` 末尾（追加 2026-11-05、重要 高）
- [ ] 評価の題材の見直し: お題 1 で既存機能の変更（桁数の変更、用語の改称）を入れても両群の差は出なかった。変更箇所が明文化されない依頼や、より大きなコードベースでの変更で、isdd の追跡（対応表）が効くかを測る設計を作る（追加 2026-11-05、重要 高）
- [ ] 無人実行の isdd 群が Skill ツールを使わず SKILL.md を直接読んで進める件: Skill ツール経由と結果が同じかを 1 回確かめる（追加 2026-11-05、重要 低）
- [ ] 計測で起きた外部からの停止（SIGTERM で isdd 群 3 本が落ちた）の原因を切り分ける（エージェントの pkill か、背景実行の後始末か）（追加 2026-11-05、重要 低）
- [ ] SWE-Dev は easy で両群 100%（天井）。差を見るなら hard split か FeatureBench lv1（追加 2026-11-04、重要 低）
- [ ] P7 計測の手順を `evals/` と同じ基盤（waza、固定回答）に載せ、版を上げるたびに isdd あり・なしの差を出せるようにする（無人実行の実行器 `measure/run.py` ができたので、固定回答の場面は載せられる。追加 2026-11-03、重要 中）

## 環境・言語の非固定化と ID の入れ方の再検討（ブランチ feature-rethink-env-and-id）

概要: .history/2026-10-18-0312-スキルレビューと重大修正/summary.md

- [ ] waza（`run-all.sh claude`）で v2.2.0 公開前の最後の 3 場面（build の未マッピング、spec の外部連携の接続テスト、ヒアリングの作法）を回し直し、Claude Code 経路（`evals/run-claude-code.py`）の結果と食い違わないことを確かめる（Anthropic API の上限が戻る 2026-12-01 以降。追加 2026-11-04、重要 低）
- [ ] 検証 D: microsoft/waza をフォークし、`internal/execution/claudecode.go` に `claude -p --output-format stream-json` を子プロセスで呼ぶエンジンを実装する（追質問は `--resume`、スキルは `.claude/skills` と `--append-system-prompt`）（追加 2026-10-17、重要 低）
- [ ] 検証 D: `cmd/waza/engine_factory.go`・`schemas/eval.schema.json`・`schemas/config.schema.json`・`internal/models` の実行器名の判定に `isdd-claude-sdk` を追加する（追加 2026-10-17、重要 低）
- [ ] 検証 D: 偽の `claude` スクリプトで単体テストを書き、isdd の eval を `executor: isdd-claude-sdk` で実際に回す（追加 2026-10-17、重要 低）
- [ ] 検証 D: フォークのビルド物を `waza-cc` の名前で入れ、`run-all.sh` が環境変数 `WAZA_BIN` で切り替えられるようにする（追加 2026-10-17、重要 低）
- [ ] 検証の題材と範囲（通しフロー用のサンプル案件、インタビュー回答の固定方式、既存 fixture の書き換え時期）を決める（追加 2026-10-17、重要 低）
- [ ] `.env` の旧変数 3 行（`WAZA_CLAUDE_MODEL_PRIMARY`・`WAZA_CLAUDE_MODEL_SECONDARY`・`WAZA_CLAUDE_ESCALATE`）を削除する（ユーザー作業。残っていても動作に影響なし）（追加 2026-10-18、重要 低）
- [ ] 実行基盤の固まり（2026-10-18 の eval で 2 回。Copilot CLI がモデル応答待ちのまま 22〜40 分停止、転記ファイル未作成）が再発したら、Copilot CLI の更新か検証 D を優先する。2026-11-03 までの eval では再発なし（追加 2026-10-18、重要 低）
- [ ] ローカルブランチ `feature-equipment-lending-management`（2026-10-19、main に無いコミット 7 件。備品管理・貸出管理アプリを題材に、最新のスキルで要件定義・詳細設計・実装まで通した記録とみられる）の扱いを決める。残すなら目的をここに書き、不要なら削除する（追加 2026-10-25、重要 低）
