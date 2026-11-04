# isdd バックログ

完了・見送りは `BACKLOG-archive.md`、案・記録は `IDEAS.md` にある。

## v2.0.1 と v2.1.0（正本の反映時期、スキル構成の見直し）

概要: .history/2026-11-03-1404-正本反映時期とスキル再構成/summary.md

- [ ] 公開後、試用中のプロジェクトで `--pin v2.2.0` で入れ直して `isdd-setup` を再実行する（チェッカーの複製と `check.sh`・`.gitignore` の `e2e/results/` を更新。v2.1.0 は飛ばしてよい。ユーザー作業、追加 2026-11-03、v2.2.0 に更新 2026-11-04、重要 高）
- [ ] 対応表の粒度 `class` を Haiku で確かめる eval 場面を 1 本足す（依存の規則と `DS-TS` の行は remap の場面で確かめ済み。追加 2026-11-03、重要 低）
- [ ] 外部連携の設計の段階（ライブラリの採否とモック方式を設計 ID で書く）に Haiku の eval 場面を 1 本足す（追加 2026-11-03、重要 高）
- [ ] `evals/isdd-<旧スキル名>/` に残る git 管理外の eval 記録を消す（ユーザー作業、`! rm -rf`。追加 2026-11-03、重要 低）

## isdd の効果の計測（isdd あり・なしの比較）

概要: .history/2026-11-04-1031-v2.2.0公開と計測1試運転/summary.md（計測 1 の試運転の結果。考え方は 2026-11-03 夜の検討）。考え方: 公開ベンチマークの 1 課題の隠しテストを機能のまとまりで 3 つに分け、段階 1 を要件、段階 2・3 を変更要求として毎回新しいセッションで与える。対照群は同じ分割・同じ順序をスキルなしのエージェントに与える。測るのは最終の通過率、段階ごとの通過率、退行数（前段階で通ったテストが後で落ちた数）、作りすぎ、トークンと往復数。順序はユーザー決定（2026-11-03）。計測 1 のブラインドの受け入れテストと要件ごとの判定は v2.2 の P1（受け入れ判定スクリプト、JUnit XML）を使うので、着手は v2.2 の公開後（2026-11-04 整理）

- [ ] 計測 1 の試運転で見つかった仕組みの直し: (1) 契約（contract.md）が全段の画面を含むため両群とも段 1 で全部作り、段 2・3 が検証だけになった → 契約も段ごとに分け、段 2・3 に退行を起こしうる変更を入れる。(2) `run.py`（`claude -p` の無人実行）は全権限を外す指定が自動モードの分類器に止められた → `evals/run-claude-code.py` と同じ権限指定（`acceptEdits` ＋ 許可ツールの列挙、依頼は標準入力）に直す。(3) 隠しテストの契約の抜け（「備品を登録」の入口、リダイレクトのクエリ文字列）を直した版が `measure/hidden/` の正。結果は `measure/results/REPORT.md`（追加 2026-11-04、重要 高）
- [ ] 計測 2: SWE-Dev（NeurIPS 2025、機能説明 ＋ 既存コード ＋ 単体テスト）の易しい split から 10〜20 件で、逆引き → 変更フロー × 3 の isdd あり・なしを比べる。既存リポジトリが大きいので「変更に関わるディレクトリだけ逆引きする」入口が要るかを確かめる。データと Docker 環境は github.com/DorothyDUUU/SWE-Dev。hard split は Claude 3.7 Sonnet で Pass@3 22% なので easy split を使う。機能説明（PRD）は LLM 生成で曖昧という指摘あり（追加 2026-11-03、重要 高）
- [ ] 計測 3: FeatureBench（ICLR 2026、最高 11%）から 5〜10 件で、要件をサブ機能に分けて段階的に積めば Haiku でも実装できるかを試す（isdd の評価とは別の、仕様の分割という手法の評価。github.com/LiberCoders/FeatureBench は PyPI の `featurebench` CLI でエージェント枠組みに Claude Code を選べる＝isdd のスキルをそのまま載せられる見込み。Claude 4.5 Opus で 11% なので Haiku では差が出ないおそれ。追加 2026-11-03、重要 高）
- [ ] 計測 4: WebGen-Bench（NeurIPS 2025、ブラウザ操作エージェントで採点）で新規フロー → 変更 × 2 の作りすぎと通過率を測る。採点環境の構築が先。採点は WebVoyager 型の UI エージェントで、論文は Qwen2.5-VL-32B を使う（GPU か API が要る。Docker の手順は未確認）（追加 2026-11-03、重要 低）
- [ ] P7 計測の手順を `evals/` と同じ基盤（waza、固定回答）に載せ、版を上げるたびに isdd あり・なしの差を出せるようにする（計測 1 の後。追加 2026-11-03、重要 高）

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
