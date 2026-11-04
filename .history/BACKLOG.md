# isdd バックログ

完了・見送りは `BACKLOG-archive.md`、案・記録は `IDEAS.md` にある。

## v2.0.1 と v2.1.0（正本の反映時期、スキル構成の見直し）

概要: .history/2026-11-03-1404-正本反映時期とスキル再構成/summary.md

- [ ] 公開後、試用中のプロジェクトで `--pin v2.2.0` で入れ直して `isdd-setup` を再実行する（チェッカーの複製と `check.sh`・`.gitignore` の `e2e/results/` を更新。v2.1.0 は飛ばしてよい。ユーザー作業、追加 2026-11-03、v2.2.0 に更新 2026-11-04、重要 高）
- [ ] 対応表の粒度 `class` を Haiku で確かめる eval 場面を 1 本足す（依存の規則と `DS-TS` の行は remap の場面で確かめ済み。追加 2026-11-03、重要 低）
- [ ] 外部連携の設計の段階（ライブラリの採否とモック方式を設計 ID で書く）に Haiku の eval 場面を 1 本足す（追加 2026-11-03、重要 高）
- [ ] `evals/isdd-<旧スキル名>/` に残る git 管理外の eval 記録を消す（ユーザー作業、`! rm -rf`。追加 2026-11-03、重要 低）

## isdd の効果の計測（isdd あり・なしの比較）

概要: `measure/results/REPORT.md`（2026-11-04 の本計測。計測 1・2・4 の結果と問題 10 件）。試運転は `measure/results/trial-2026-11-04/`。考え方: 公開ベンチマークの 1 課題の隠しテストを機能のまとまりで 3 つに分け、段階 1 を要件、段階 2・3 を変更要求として毎回新しいセッションで与える。対照群は同じ分割・同じ順序をスキルなしのエージェントに与える。測るのは最終の通過率、段階ごとの通過率、退行数、作りすぎ、トークンと往復数。結果の要点: 退行は全系列 0、差が出たのは受け入れ基準が曖昧な WebGen-Bench だけ（isdd 48/50 対 43.5/50）、備品管理と SWE-Dev easy は同点、isdd のコストはトークン 3.4〜4.6 倍・時間 6〜10 倍（2026-11-04）

- [ ] isdd-build が「設計の直し方の判断」で止まる問題: 案 A（文書の規則）で `shared/references/design-chapters.md` 7 章と `trace-map-rules.md` に「DS-MD はチェッカーが走査するプログラム言語のファイルだけ。起動スクリプトは DS-OP、テンプレート・CSS は DS-IF の説明に含める。実行の入口は --src の中に置く」を書いた（2026-11-04、ユーザー決定 A）。残り: isdd-spec の設計の場面の差分 eval（`evals/run-claude-code.py` か 12-01 以降の waza）と、設計書に非コードの DS-MD があるときに警告ではなく「対応表の対象外」と扱えるかの確認、eval 場面を 1 本足す（重要 高）
- [x] (2026-11-05) 依頼に無い決め事の見える化（ユーザー決定）: hearing-rules.md に「依頼文に無い決め事」の節と洗い出しの表、requirements-chapters.md に「1-2. 依頼に無く自分で決めた項目（必須）」、rq_integrity_checker に節の有無の検査、isdd-spec の報告に表をそのまま貼る規則を足した。fixture 23 本に節を追加。eval 場面 `req-decided-items.yaml` を新設し、Claude Code 経路で 4 回直して 1 回目合格（落ちた原因: 空ファイルの問いの抜け、報告で表を箇条書きに崩す、問いの先送り）
- [ ] 計測の対照群の文脈を直す: Agent ツール方式は cwd がこのリポジトリなので両群に CLAUDE.md が読まれる。別の cwd のセッションから回すか、`measure/run.py`（`claude -p`）の起動を許す権限規則を足す（REPORT.md 問題 1。追加 2026-11-04、重要 高）
- [ ] 計測 4（WebGen-Bench）を 5 課題以上に広げ、isdd 群の差（3 課題で +4.5 点）が再現するかを見る。採点の揺れ（色の判定、確認の知らせ）は WebGen-Bench 同梱の人手採点器で検算する（REPORT.md 問題 6。追加 2026-11-04、重要 高）
- [x] (2026-11-05) 対応表チェッカーの範囲指定: `--src` にファイルも書けるようにし、`trace_map_checker.py` に `--exclude <相対パスのグロブ>` を足した（dependency_checker・acceptance_checker・isdd_setup も同じ扱い）。単体テスト 3 本追加、5 版で合格。計測 3 の作業ディレクトリで 2 ファイルだけを対象にして `--strict` が通ることを確認。残り: 文書の規則（trace-map-rules.md）を変えたので isdd-setup / isdd-reverse-engineering の差分 eval（API 上限の回復後）
- [x] (2026-11-04) 計測 3: FeatureBench fast の mlflow 4 課題を段として積んで実施（Docker は OrbStack でデータは SSD にあり、容量の問題は無かった）。結果は `measure/results/REPORT.md`
- [ ] 退行を測る依頼を足す: 段 2・3 に既存のテスト済みの挙動を変える依頼（例: 社員番号を 6 桁 → 7 桁）と、段ごとに差し替える隠しテストを入れる。今は全系列で退行 0（REPORT.md 問題 10。追加 2026-11-04、重要 中）
- [ ] 作りすぎの指標を公開関数の数から機能の単位（画面・URL・操作の数）に替える。isdd 群はモジュール分割で関数が増えるため今の指標は設計の粒度を測っている（REPORT.md 問題 7。追加 2026-11-04、重要 中）
- [ ] SWE-Dev は easy で両群 100%（天井）。差を見るなら hard split か FeatureBench lv1。`swedev.py prepare` の正解の複製（build/lib、modified_testcases）の削除は hard でも要る（追加 2026-11-04、重要 低）
- [ ] P7 計測の手順を `evals/` と同じ基盤（waza、固定回答）に載せ、版を上げるたびに isdd あり・なしの差を出せるようにする（Agent ツール方式の制約〔cwd、無人実行の分類器〕を先に解いてから。追加 2026-11-03、重要 中）
- [x] (2026-11-04) 計測 1 の仕組みの直し（契約と固定回答を段ごとに分けた、`run.py` の権限指定を直した〔分類器に止められるのは変わらず〕、`stage.py` に snapshot と直列の採点を足した）と本計測（2 群 × 2 回 × 3 段）
- [x] (2026-11-04) 計測 2: SWE-Dev easy 3 パッケージ 10 課題を逆引き → 変更フローで積む形で実施。両群 100%
- [x] (2026-11-04) 計測 4: WebGen-Bench 3 課題を新規 → 変更 × 2 で実施（採点は Haiku ＋ Playwright）。isdd 48/50、対照 43.5/50

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
