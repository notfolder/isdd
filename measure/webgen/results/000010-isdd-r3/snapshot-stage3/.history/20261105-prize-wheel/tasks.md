# tasks.md: 景品ルーレット Web サイトの実装タスク

設計: `docs/detail_design.md`。要件: `docs/requirements.md`。上から順に進める。コードに要件 ID・設計 ID は書かない。対応は `docs/trace_map.md` に登録する。

## 0. 固定: isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無、`scripts/isdd/completeness.json`（実行形態 server、認証なし、外部連携なし）、`scripts/isdd/dependencies.json`（第 7 章の依存の規則）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`completeness.json` の実行形態・認証・外部連携が詳細設計書と一致している。

## 1. データ層（DB、リポジトリ、初期データ）

- 実装: `src/store/database.py`（`DS-MD-DATABASE`、`DS-CL-DATABASE`、`DS-SC-PRIZES-TABLE`、`DS-SC-WINNING-RECORDS-TABLE`）、`src/store/repositories.py`（`DS-MD-REPOSITORIES`、`DS-CL-PRIZE-REPOSITORY`、`DS-CL-RECORD-REPOSITORY`）、`src/store/seed.py`（`DS-MD-SEED-DATA`、`DS-FN-SEED-SAMPLE-DATA`、`DS-SC-SAMPLE-DATA-SET`）。
- 内容: 設計 8 章 3-1 の景品 7 件と「Sample Player」の当選記録 2 件。景品が 0 件のときだけ投入する。
- 完了条件: `tests/unit/` の該当テストが通る（一時ファイルの SQLite。投入は 2 回目で増えない）。

## 2. サービス層（利用者名の検証、抽選、当選記録）

- 実装: `src/service/validation.py`（`DS-MD-NAME-VALIDATION`、`DS-CL-PLAYER-NAME-ERROR`、`DS-FN-VALIDATE-PLAYER-NAME`）、`src/service/wheel.py`（`DS-MD-WHEEL-SERVICE`、`DS-CL-WHEEL-SERVICE`、`DS-FN-CHOOSE-SEGMENT-BY-WEIGHT`）。
- 内容: 利用者名は前後の空白を除いて 1〜20 文字。抽選は重みの累計で選ぶ。はずれは記録しない。
- 完了条件: 単体テストで、空・空白・20 文字・21 文字、重みの境界（乱数を固定）、はずれで記録が増えないことを確かめ、結合テストで抽選と記録が一致することを確かめる。

## 3. HTTP 層（起動の入口、ルーティング、API）

- 実装: `src/server.py`（`DS-MD-SERVER-ENTRY`、関数 `main`）、`src/web/router.py`（`DS-MD-HTTP-ROUTER`、`DS-CL-REQUEST-HANDLER`、`DS-IF-PAGE-ROUTES`）、`src/web/api.py`（`DS-MD-API-HANDLERS`、`DS-IF-PRIZES-API`、`DS-IF-SPIN-API`、`DS-IF-RECORDS-API`）。
- 内容: `PORT`（既定 8000、不正なら終了コード 1）と `DATA_DIR`（既定はリポジトリ直下の `data`、無ければ作る）を読む。待ち受けは 127.0.0.1。`/`、`/prizes`、`/records`、`/static/...` の配信（`src/web/static/` の外は 404）。API は設計 4-1 の表どおり。
- 完了条件: 起動し、`curl` で `/api/prizes` が 7 件を返し、`/api/spin` が 200 か 400 を返す。

## 4. 画面（HTML、CSS、JavaScript）

- 実装: `src/web/static/index.html`、`prizes.html`、`records.html`、`styles.css`、`js/common.js`（`DS-MD-COMMON-JS`）、`js/wheel.js`（`DS-MD-WHEEL-JS`、`initSpinPage` が `DS-IF-SPIN-SCREEN`、`startSpin` が `DS-FN-START-SPIN`）、`js/prizes.js`（`DS-MD-PRIZES-JS`、`initPrizesPage` が `DS-IF-PRIZES-SCREEN`、`renderPrizeTable` が `DS-FN-RENDER-PRIZE-TABLE`）、`js/records.js`（`DS-MD-RECORDS-JS`、`initRecordsPage` が `DS-IF-RECORDS-SCREEN`、`loadRecords` が `DS-FN-LOAD-RECORDS`）。
- 内容: 共通メニュー（Spin Wheel、Prize List、My Winning Records）。背景 #D3D3D3、部品 #8B0000。文言は英語。利用者名は `localStorage` の `wheel.playerName` に保存。抽選中はボタンを無効にする。利用者名の表示は必ずエスケープする。
- 完了条件: 3 画面がブラウザで開け、抽選の回転が止まって結果が出る。Chrome のヘッドレス実行でスクリーンショットを取り、配色とメニューを目で確かめる。

## 5. 起動スクリプト

- 実装: `setup.sh`（`DS-OP-SETUP-SCRIPT`）、`run.sh`（`DS-OP-RUN-SCRIPT`）。
- 内容: `setup.sh` は Python 3 と sqlite3 の確認、`DATA_DIR` の作成。`run.sh` は `PORT` と `DATA_DIR` を読み、`exec python3 src/server.py`。
- 完了条件: `bash setup.sh` が 0 で終わり、`PORT=任意 bash run.sh` で起動する。

## 6. 単体テスト・結合テスト

- 実装: `tests/unit/`（`test_*.py`、標準ライブラリの `unittest`）。
- 実行コマンド: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
- 完了条件: 全件通過。FAIL が 0 件。

## 7. E2E テスト

- 実装: `e2e/test_wheel_e2e.py`（テストクラス `WheelE2ETest`、標準ライブラリの `unittest` と `urllib`）。各テストは一時 `DATA_DIR` で `src/server.py` を子プロセスとして起動し、終了時にその子プロセスだけを終了する。
- 対応: 設計 8-2 の `DS-TS-*` を対応表で次のテストメソッドに結ぶ。`DS-TS-SPIN-AND-RECORD-E2E` → `test_spin_and_record`、`DS-TS-NAME-VALIDATION-E2E` → `test_name_validation`、`DS-TS-VIEW-PRIZES-E2E` → `test_view_prizes`、`DS-TS-VIEW-OWN-RECORDS-E2E` → `test_view_own_records`、`DS-TS-NAVIGATION-E2E` → `test_navigation`、`DS-TS-SEED-DATA-E2E` → `test_seed_data`。
- 実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
- 完了条件: 全件通過。FAIL が 0 件。

## 8. README.md

- 内容: 起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、ブラウザで `http://127.0.0.1:8000`）と、3 画面の説明。認証は無いため初期ユーザーは書かない。

## 9. 対応表（docs/trace_map.md）更新

- 実装したファイル・クラス・公開関数を粒度 `class` で登録する（`DS-MD-*`、`DS-CL-*`、`DS-FN-*`、`DS-IF-*` の行と、`DS-TS-*` は `e2e/test_wheel_e2e.py::テストメソッド` の行）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 10. 起動確認

- 完了条件: `bash setup.sh` の後、`PORT=任意 bash run.sh` で起動し、3 画面が開く。確認後に起動したプロセスを PID で止める。

## 11. 実装完了チェック

- 完了条件: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。
- 完了条件（全件）: 単体・結合テスト、E2E テストが全件通過。`rq_ds_link_checker.py` と `rq_integrity_checker.py` が問題 0 件。

## 12. 要件の網羅確認（すべての変更点の実装確認）

- `docs/requirements.md` の `RQ-FT-*`（7 件）、`RQ-UI-*`（3 件）、`RQ-DT-*`（4 件）、`RQ-NF-*`（3 件）、`RQ-OP-*`（2 件）が、実装か E2E テストのどちらかで確かめられていることを確認する。
