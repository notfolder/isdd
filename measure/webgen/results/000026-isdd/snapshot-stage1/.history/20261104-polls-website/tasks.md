# タスク: 投票サイト（Polls）の実装

対象: `docs/detail_design.md`（新規フロー）。実装は設計の設計 ID だけを作る。`docs/trace_map.md` に対応を登録する。

## 0. isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無を確かめ、無ければ `isdd-setup` を実行する。導入時の入力: 実行形態は「ローカルのサーバー（コンテナ無し）」、認証は「無し」、外部連携は「無し」、対応表の粒度は `function`、依存の規則は `app/` が `tests/`・`e2e/` に依存しないこと（`docs/detail_design.md` 第 7 章の表）。
- 対象の設計 ID: なし（導入のみ）
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致している。

## 1. 依存と起動の基盤

- 対象: `requirements.txt`（Flask 3.1.3、pytest）、`setup.sh`（`.venv` を作り、依存を入れる）、`run.sh`（`.venv/bin/python -m app` を前景で exec する。PORT の既定値は 8000）、`app/__main__.py`（PORT と DATA_DIR を読み、127.0.0.1 で待ち受ける）、`app/__init__.py`（`DS-FN-CREATE-APP`）
- 対象の設計 ID: `DS-MD-REQUIREMENTS`, `DS-MD-SETUP-SCRIPT`, `DS-MD-RUN-SCRIPT`, `DS-MD-SERVER`, `DS-MD-APP-PACKAGE`, `DS-FN-CREATE-APP`, `DS-OP-SETUP-ENVIRONMENT`, `DS-OP-RUN-SERVER`, `DS-OP-ENVIRONMENT-VARIABLES`
- 完了条件: `bash setup.sh` が成功し、`PORT=18080 bash run.sh` で起動して `http://127.0.0.1:18080/` が応答する（確認後にそのプロセスの PID だけを止める）。

## 2. データ層

- 対象: `app/database.py`（DATA_DIR を作り SQLite を開く。テーブルを作る。外部キーを有効にする）、`app/repository.py`（投票・選択肢・票の SQL。票の登録は一意制約違反を区別して返す）
- 対象の設計 ID: `DS-MD-DATABASE`, `DS-FN-OPEN-DATABASE`, `DS-FN-INIT-SCHEMA`, `DS-SC-POLLS-TABLE`, `DS-SC-OPTIONS-TABLE`, `DS-SC-VOTES-TABLE`, `DS-MD-REPOSITORY`, `DS-CL-POLL-REPOSITORY`
- 完了条件: 単体テスト `DS-TS-UNIT-REPOSITORY` の関数が通る（一時 DB）。

## 3. 初期データ

- 対象: `app/sample_data.py`。投票が 0 件のときだけ、3 件の投票（選択肢 3〜4 件）と票を入れる。`create_app` から呼ぶ。
- 対象の設計 ID: `DS-MD-SAMPLE-DATA`, `DS-FN-SEED-SAMPLE-DATA`
- 完了条件: 空の DATA_DIR で起動すると投票が 3 件あり、2 回目の起動で増えない。

## 4. 業務ロジック

- 対象: `app/voting.py`（投票の検証と票の登録、結果の集計。1 投票 1 票は一意制約と既存票の確認で判定する）
- 対象の設計 ID: `DS-MD-VOTING`, `DS-CL-VOTING-SERVICE`, `DS-FN-CAST-VOTE`, `DS-FN-GET-POLL-RESULT`, `DS-FN-GET-ALL-RESULTS`
- 完了条件: 単体テスト `DS-TS-UNIT-VOTING` の関数が通る（未選択・他投票の選択肢・二重投票の拒否、割合の計算、投票 0 件の表示）。

## 5. 画面と経路

- 対象: `app/views.py`（GET `/`、GET `/polls/<id>`、POST `/polls/<id>/vote`、GET `/results`、存在しない投票は 404。利用者識別子 Cookie の作成）、`app/templates/base.html`（ナビゲーション Polls と Results）、`polls.html`、`poll.html`（未投票はフォーム、投票済みは結果）、`results.html`、`app/static/style.css`（背景 #ffffff、部品 #000080、文字は英語）
- 対象の設計 ID: `DS-MD-VIEWS`, `DS-FN-IDENTIFY-VOTER`, `DS-IF-POLLS-PAGE`, `DS-IF-POLL-PAGE`, `DS-IF-VOTE-ACTION`, `DS-IF-RESULTS-PAGE`, `DS-IF-NOT-FOUND`, `DS-IF-PAGE-LAYOUT`, `DS-MD-TEMPLATE-BASE`, `DS-MD-TEMPLATE-POLLS`, `DS-MD-TEMPLATE-POLL`, `DS-MD-TEMPLATE-RESULTS`, `DS-MD-STYLESHEET`
- 完了条件: `DS-IF-*` の経路が設計どおりの応答を返す（手動の HTTP 確認）。

## 6. テスト

- 対象: `tests/`（単体テスト。`DS-TS-UNIT-REPOSITORY`、`DS-TS-UNIT-VOTING`）、`e2e/`（E2E。`DS-TS-BROWSE-POLLS-E2E`、`DS-TS-CAST-VOTE-E2E`、`DS-TS-REJECT-INVALID-VOTE-E2E`、`DS-TS-ONE-VOTE-E2E`、`DS-TS-RESULT-AFTER-VOTE-E2E`、`DS-TS-ALL-RESULTS-E2E`、`DS-TS-NAVIGATION-E2E`、`DS-TS-SAMPLE-DATA-E2E`、`DS-TS-THEME-E2E`、`DS-TS-PUBLIC-ACCESS-E2E`）。E2E は `python -m app` を一時 DATA_DIR と空きポートで子プロセスとして起動し、HTTP で接続する。
- 対象の設計 ID: 上記すべての `DS-TS-*`
- 完了条件: 単体テストは `.venv/bin/python -m pytest tests` で FAIL 0。E2E は `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` で全件通過。

## 7. 対応表（docs/trace_map.md）更新

- 対象: 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は対応表のルールに従う）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 8. 起動確認

- 対象: `bash setup.sh`、`PORT=任意 bash run.sh`。
- 完了条件: 起動がエラーなく完了し、根の URL と各画面（投票の一覧、詳細、結果）が開ける。

## 9. README.md 記載

- 対象: `README.md` に起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、DATA_DIR の説明）を書く。
- 完了条件: README.md を読むだけで初回起動が完結する。

## 10. 実装完了チェック

- 対象: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 11. 変更点の確認（最後）

- 対象: `docs/requirements.md` の全 `RQ-*` と `docs/detail_design.md` の全 `DS-*` が実装されたかを確認する（`RQ-TS` → `DS-TS` → E2E の結果、`DS-*` → 対応表）。
- 完了条件: 未実装の設計 ID が 0 件。

## 設計の修正（P1、案 A）

- 対応表チェッカーが読めないファイル（setup.sh・run.sh・requirements.txt・HTML・CSS）の DS-MD 行と、それを指していた DS-IF-PAGE-LAYOUT と DS-MD-TEMPLATE-* と DS-MD-STYLESHEET を、詳細設計書の第 7 章と第 11 章から外した。
- 直下の server.py を app/__main__.py に移し、DS-MD-SERVER の対象をそれにした。run.sh は `.venv/bin/python -m app` を呼ぶ。
- 理由と経緯は docs/proposals.md の P1 を参照。
