# tasks.md: 景品ルーレット Web サイト

対象: `docs/requirements.md`・`docs/detail_design.md`（新規フロー）。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。`--src src`、`--runtime server`、`--no-auth`、`--no-external`、`--granularity class`、`--e2e-dir e2e` を渡す。
- 第 7 章の依存の規則（無し）を `scripts/isdd/dependencies.json` の `"rules": []` と一致させる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致していること。

## 1. 基盤（DB・抽選・サーバー起動）

- 対象設計 ID: `DS-MD-STORE-MODULE`、`DS-CL-STORE`、`DS-FN-SEED-SAMPLE-PRIZES`、`DS-FN-LIST-PRIZES`、`DS-FN-ADD-WINNING`、`DS-FN-LIST-WINNINGS`、`DS-SC-PRIZE-TABLE`、`DS-SC-WINNING-RECORD-TABLE`、`DS-MD-DRAW-MODULE`、`DS-FN-PICK-PRIZE`、`DS-MD-SERVER-MODULE`、`DS-FN-MAIN`
- 作業: `src/store.py`、`src/draw.py`、`src/server.py`（起動部分）を作る。SQLite の初期化、サンプル景品 8 件（設計書 4-2）、重み付き抽選。
- 完了条件: `python3 -m unittest discover -s tests -v`（単体テスト）が通ること（テストは `tests/test_draw.py`、`tests/test_store.py`）。

## 2. 抽選 API と一覧 API

- 対象設計 ID: `DS-CL-WHEEL-REQUEST-HANDLER`、`DS-FN-HANDLE-SPIN`、`DS-FN-HANDLE-PRIZES`、`DS-FN-HANDLE-WINNINGS`
- 作業: `POST /api/spin`（表示名の規則、Cookie `wof_player` の発行、ハズレは記録しない）、`GET /api/prizes`、`GET /api/winnings`。`ThreadingHTTPServer` で処理する。
- 完了条件: 単体テストと結合の確認（`e2e/` の API 系シナリオ）が通ること。

## 3. 画面（Spin・Prizes・My Winnings とメニュー）

- 対象設計 ID: `DS-MD-PAGES-SCRIPT`、`DS-IF-SPIN-PAGE`、`DS-IF-PRIZES-PAGE`、`DS-IF-MY-WINNINGS-PAGE`、`DS-IF-NAV-MENU`、`DS-FN-DRAW-WHEEL`、`DS-FN-SPIN-WHEEL-ANIMATION`
- 作業: `src/web/index.html`、`src/web/style.css`（背景 #E6E6E6、部品 #8B0000）、`src/web/app.js`（ハッシュで画面を切り替え、上部にメニュー）。
- 完了条件: 画面の HTML が `/`、`/#/prizes`、`/#/my-winnings` で表示できること（E2E の `DS-TS-NAVIGATE-MENU` で確かめる）。

## 4. 起動スクリプトと README

- 対象設計 ID: `DS-OP-START-SCRIPTS`
- 作業: `setup.sh`（Python と Node の確認、DATA_DIR の作成）、`run.sh`（`PORT` 既定 8000、`DATA_DIR` 既定 `./data`、`127.0.0.1` で待ち受け）。`README.md` に起動方法を書く。
- 完了条件: `bash setup.sh` が成功し、`PORT=<任意> bash run.sh` で起動すること。

## 5. E2E テスト

- 対象設計 ID: `DS-TS-EMPTY-DATA-START`、`DS-TS-SPIN-AND-RECORD`、`DS-TS-BROWSE-PRIZES`、`DS-TS-VIEW-OWN-WINNINGS`、`DS-TS-NAVIGATE-MENU`、`DS-TS-PLAYER-NAME-RULE`、`DS-TS-NO-PRIZE-NOT-RECORDED`、`DS-TS-WEIGHTED-DRAW`、`DS-TS-RESPONSE-TIME`、`DS-TS-CONCURRENT-SPINS`
- 作業: `e2e/test_wheel.py` に `WheelScenarios` クラスを作り、各シナリオを `test_<シナリオ名>` で書く（設計書 8-2）。
- 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` で全件通過すること。

## 6. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は trace-map-rules.md）。`DS-TS` の行は `e2e/test_wheel.py::WheelScenarios.test_<名前>` で結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

## 7. 起動確認タスク

- 設計書 第 9 章のとおり `PORT=<任意> bash run.sh` で起動し、画面を開けること。
- 完了条件: 起動がエラーなく完了し、`/` が HTML を返すこと。

## 8. 単体テスト・結合テスト全件通過タスク

- 実行コマンド: `python3 -m unittest discover -s tests -v`
- 完了条件: FAIL が 0 件。

## 9. E2E テスト全件通過タスク

- 実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`
- 完了条件: FAIL が 0 件。失敗した場合は修正と再実行を繰り返す。

## 10. README.md 記載タスク

- README.md に「起動方法」（`bash setup.sh`、`PORT=8000 bash run.sh`、`DATA_DIR`）を書く。認証は無いので初期ユーザーは書かない。
- 完了条件: README だけで初回起動できること。

## 11. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK であること。

## 12. 要件・設計への全変更点の確認タスク

- 設計書の全設計 ID（11 章）が実装され、`docs/trace_map.md` に載っていること。`docs/requirements.md` の全 `RQ-FT`・`RQ-UI`・`RQ-NF` が E2E で確かめられていること。
- 完了条件: 上の確認の結果がすべて合格。

## 変更点（tasks.md の末尾）

- 要件・設計の修正は無し。
