# isdd バックログ

## 環境・言語の非固定化と ID の入れ方の再検討（ブランチ feature-rethink-env-and-id）

概要: .history/2026-10-18-0312-スキルレビューと重大修正/summary.md（最新）。決定事項の経緯は同ディレクトリの session.md

決定事項（2026-10-17 ヒアリング）:
- 技術選定は要件定義で制約（既存コードの言語・配備先・チームの技術・ライセンスとコスト・規模性能・利用者種別と SSO）を集め、設計スキルが候補を提案してユーザー承認を取る。
- design-chapters.md から製品名（Python・FastAPI・Vue・Streamlit・SQLite・PostgreSQL）の既定値を消し、判断軸だけにする。選定時のインターネット調査を必須にする。
- docker compose と Playwright の前提は今回は据え置く。→ 2026-10-18 に撤回: 実行形態・認証・外部連携を `scripts/isdd/completeness.json` に記録し、要否を切り替える方式に変更。
- コードには ID を入れない。仕様書・設計書は今まで通り ID を付ける。要件と関数名の対応表を別ファイルで持ち、コード変更時に対応表のチェックを強制する。
- 対応表のキーは DS-ID と修飾名（ファイルパス + クラス + 関数）。RQ は設計書の DS と RQ の対応から導く。
- 対応表に載せる粒度はクラスと公開関数（アンダースコア始まりの内部関数とダンダーメソッドは除外）。
- 強制は 3 層（AGENTS.md と CLAUDE.md のルール、エージェントのフック、git pre-commit）。フックは特定エージェントに固定しない。
- チェックの時点は応答終了時と pre-commit。ファイル編集のたびには動かさない。
- インターネット調査ができない環境では「調査できない」と報告して止まり、ユーザーの許可か情報を待つ。
- 設計書の DS-ID の長さは受け入れる（ID 短縮は今回はしない）。
- 対応表は要件書・設計書の外の独立ファイル `docs/trace_map.md`（Markdown の表。列は DS-ID、修飾名、備考）に置く。要件 ID と設計 ID の対応は設計 ID の末尾略称で表す現状のまま。
- エージェントのフックはエージェント自身に自分の環境向けに作らせる。応答終了時のイベントやフック機能が無ければ作らず報告だけする。isdd 側にエージェントごとの処理は持たない。
- フックと pre-commit の導入は新しい小さなスキル（isdd-setup）が担い、各スキルは未導入なら先に実行するよう案内する。
- pre-commit は「対応表が指す関数がコードに無い（壊れた参照）」だけエラーで止め、「コードにあって対応表に無い（未登録）」は警告に留める。isdd-traceable-coding の完了条件は両方ゼロ。スキルを持たない人の変更によるずれは isdd-post-implementation-review で取り戻す。
- チェッカー本体は isdd-setup がプロジェクト内の `scripts/isdd/` に複製して git 管理対象にする。再実行で上書き更新する。
- CI の雛形は生成しない。

- [x] (2026-10-17) 検証方法を検討する — 決定: A「waza の copilot-sdk 実行器の BYOK で Anthropic API を使う」と D「waza をフォークして Claude Code 実行器を自作する」の両方で進める。Max プランの月次 API クレジット（Claude API 対象）を A に充てる
- 検証の実行環境はこの Mac mini。Go、waza（本家）、Copilot CLI をこのマシンに入れる（2026-10-17 決定）。
- 検証のモデルは Claude Haiku 5.5（`claude-haiku-5-5`）のみ（2026-10-17 決定、同日に昇格を廃止）。失敗した eval は同じモデルで 1 回だけ再試行し、1 回目で落ちたらスキルの質の問題として SKILL.md を直す。Sonnet への昇格は使わない。D のエンジンでも同じ運用にする。
- 検証 D のエンジン名は `isdd-claude-sdk`（フォーク固有の名前にして本家の将来の名前と衝突させない）。
- [x] (2026-10-17) 検証の環境構築（一部）: waza 0.38.10 を `~/bin/waza` に導入。BYOK では `copilot login` 不要と waza のソースで確認。Go は D の着手時に入れる
- [x] (2026-10-17) 検証 A: Claude Console の組織を Max プランに紐づけて API キーを発行し、`.env` の `ANTHROPIC_API_KEY` に置く（ユーザー作業、投入済み）
- [x] (2026-10-17) 検証 A: `evals/run-all.sh` に `claude` モードを実装（Haiku → Haiku 再試行 → Sonnet 昇格、結果表、`WAZA_CLAUDE_ESCALATE=0` で昇格停止、`WAZA_BIN` でフォーク版切替）。擬似 waza で 4 シナリオの流れを確認済み
- [x] (2026-10-17) 検証 A: 最小 eval（isdd-setup）を 1 本回して実測。Haiku 5.5 で約 30 秒、入力 26 万トークン（うちキャッシュ読込が大半）、出力 2.6 千トークン。waza の AI Credits 表示は BYOK では 0 のまま
- [x] (2026-10-17) 検証 A: waza 0.38.10 同梱の Copilot ランタイム 1.0.85 は Haiku 5.5 に `thinking.type=enabled` を送って 400 になる。`evals/install-copilot-cli.sh` で Copilot CLI 1.0.98 を `evals/.copilot-cli/` に入れ、`run-all.sh claude` が `COPILOT_CLI_PATH` として自動使用するようにした
- [x] (2026-10-17) 検証 A: 全 9 スキルの eval を Haiku 5.5 で実行し全て合格。1 回目で落ちたのは isdd-post-implementation-review の case3（要件定義書の ID 表は更新したがデータ章の「固定文字列を出力するのみ」が残った）だけ。スキルの手順 4・7・セルフレビューに「全章通読して旧仕様の本文を書き換える」を追加し、再試行で合格
- [x] (2026-10-17) 検証 A: 全体 1 周の消費は入力約 990 万トークン（うちキャッシュ読込 860 万）、出力約 22 万トークン（PIR の再試行込み）。Haiku のみで約 20 分（20:38〜20:58）
- [x] (2026-10-17) 注意: `run-all.sh` は実行中に編集しない（bash が途中から読み直して結果表の出力で落ちた）。編集は実行完了を待ってから行う
- [ ] 検証 D: microsoft/waza をフォークし、`internal/execution/claudecode.go` に `claude -p --output-format stream-json` を子プロセスで呼ぶエンジンを実装する（追質問は `--resume`、スキルは `.claude/skills` と `--append-system-prompt`）
- [ ] 検証 D: `cmd/waza/engine_factory.go`・`schemas/eval.schema.json`・`schemas/config.schema.json`・`internal/models` の実行器名の判定に `isdd-claude-sdk` を追加する
- [ ] 検証 D: 偽の `claude` スクリプトで単体テストを書き、isdd の eval を `executor: isdd-claude-sdk` で実際に回す
- [ ] 検証 D: フォークのビルド物を `waza-cc` の名前で入れ、`run-all.sh` が環境変数 `WAZA_BIN` で切り替えられるようにする
- [ ] 検証の題材と範囲（通しフロー用のサンプル案件、インタビュー回答の固定方式、既存 fixture の書き換え時期）を決める
- [x] (2026-10-17) 要件定義の章構成に「1-1. 技術制約」を追加し、isdd-requirements と isdd-change-req のヒアリング方式に確認を義務化
- [x] (2026-10-17) design-chapters.md 第 1 章・第 3 章を判断軸ベースに書き換え。インターネット調査と出典・確認日・ユーザー承認を必須化。調査不能時は止まって報告
- [x] (2026-10-17) 対応表の書式（trace-map-rules.md）と trace_map_checker.py を実装。trace_comment_coverage_checker.py は削除
- [x] (2026-10-17) isdd-setup スキルと isdd_setup.py を実装（scripts/isdd/ への複製、check.sh、pre-commit、AGENTS.md と CLAUDE.md の規則ブロック、エージェント自身のフック指示）
- [x] (2026-10-17) isdd-traceable-coding・isdd-reverse-engineering・isdd-post-implementation-review・isdd-design・isdd-change-design を対応表方式に改訂。全スキル v1.0.15。eval の fixture とグレーダーも更新し、mock モードで YAML 解析を確認
- [x] (2026-10-18) スキル全体のレビューと 19 件の修正（重大 4 件: 変更フローの正本反映、逆引きの正本確定、チェッカーの言語拡張、環境固定の解消。中程度 11 件、軽微 4 件）。Haiku のみの eval で 8 スキル合格。3 コミット
- [x] (2026-10-18) `run-all.sh` から Sonnet 昇格を削除（`WAZA_CLAUDE_MODEL` に統一）。`.env` が環境変数を上書きする不具合を修正。`timeout_seconds` を実測の約 3 倍（600〜900 秒）に短縮し、local モードは `WAZA_LOCAL_TIMEOUT_SCALE`（既定 10）倍で実行
- [-] (2026-10-18) 落ちた eval を Sonnet で自動再実行する運用 — ユーザー指示で廃止。Haiku で落ちたらスキルの質の問題として直す
- [ ] `.env` の旧変数 3 行（`WAZA_CLAUDE_MODEL_PRIMARY`・`WAZA_CLAUDE_MODEL_SECONDARY`・`WAZA_CLAUDE_ESCALATE`）を削除する（ユーザー作業。残っていても動作に影響なし）
- [ ] 実行基盤の固まり（2026-10-18 の eval で 2 回。Copilot CLI がモデル応答待ちのまま 22〜40 分停止、転記ファイル未作成）の再発を観察し、再発するなら Copilot CLI の更新か検証 D を優先する
- [ ] v1.0.15 を `gh skill publish ./skills --tag v1.0.15` で公開する（README の変更履歴を読み直してから）
