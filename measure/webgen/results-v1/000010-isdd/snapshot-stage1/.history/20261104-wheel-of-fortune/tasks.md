# 実装タスク: 抽選ホイール Web サイト

対象: `docs/detail_design.md`（設計 ID は各タスクに書く）。タスクは上から順に実行する。
対応表は `docs/trace_map.md`（function 粒度）。コードには要件 ID・設計 ID を書かない。

## 0. isdd-setup 導入確認タスク（先頭）

- 対象設計 ID: なし（導入）
- 内容: `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。渡す値: 実行形態 = サーバー（前景）、認証 = 無し、外部連携 = 無し、対応表の粒度 = function、依存の規則 = 無い。E2E の実行器（`scripts/isdd/unittest_junit.py`）を導入する。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が設計書と一致する。

## 1. 起動スクリプトと環境の確認

- 対象設計 ID: `DS-MD-SETUP-SCRIPT`、`DS-OP-SETUP-ENVIRONMENT`、`DS-MD-RUN-SCRIPT`、`DS-OP-START-SERVER`、`DS-MD-MAIN`
- 内容: `setup.sh`（Python 3.9 以上の確認と、依存が無い旨の表示）、`run.sh`（`PORT` 既定 8000、`DATA_DIR` 既定 `data`、`python3 -m app` を前景で起動）、`app/__main__.py`（環境変数を読み、DB を開き、HTTP サーバーを起動する。待ち受けは 127.0.0.1）。
- 完了条件: `bash setup.sh` が成功する。`PORT=8123 bash run.sh` が前景で起動し、`curl -s http://127.0.0.1:8123/` が HTML を返す。

## 2. データベースと初期データ

- 対象設計 ID: `DS-MD-DB`、`DS-FN-OPEN-DATABASE`、`DS-SC-PRIZE-TABLE`、`DS-SC-SPIN-RECORD-TABLE`、`DS-OP-SAMPLE-DATA-SEED`
- 内容: `DATA_DIR` を作る。`wheel.sqlite3` が無いときだけスキーマを作り、初期データ 6 件を入れる。ファイルが既にあれば初期データは入れない。
- 完了条件: 空の `DATA_DIR` で起動すると景品が 6 件ある。2 回目の起動で件数が増えない。単体テストが通る（タスク 7）。

## 3. 業務ロジック（抽選・利用者名の検証）

- 対象設計 ID: `DS-MD-DRAW`、`DS-FN-DRAW-PRIZE`、`DS-MD-VALIDATION`、`DS-FN-VALIDATE-PLAYER-NAME`
- 内容: `draw_prize` は景品の一覧から `secrets` で一様に 1 件を選ぶ（景品が 0 件のときの扱いは呼び出し側が 409 にする）。`validate_player_name` は前後の空白を除き、1〜30 文字を確かめる。
- 完了条件: 単体テストが通る（タスク 7）。

## 4. データアクセス

- 対象設計 ID: `DS-MD-REPOSITORY`、`DS-FN-LIST-PRIZES`、`DS-FN-INSERT-SPIN-RECORD`、`DS-FN-FIND-RECORDS-BY-NAME`
- 内容: 景品の一覧（`id` 昇順）、抽選記録の追加（`spun_at` は UTC の ISO 8601）、利用者名の完全一致による検索（`spun_at` の新しい順）。SQL は引数で渡す。
- 完了条件: 一時 DB を使う単体テストが通る（タスク 7）。

## 5. HTTP サーバーと API

- 対象設計 ID: `DS-MD-SERVER`、`DS-FN-HANDLE-SPIN`、`DS-IF-STATIC-PAGE`、`DS-IF-PRIZES-API`、`DS-IF-SPIN-API`、`DS-IF-RECORDS-API`
- 内容: `GET /api/prizes`、`POST /api/spin`（400・409・500 の仕様は設計書 4-1 のとおり）、`GET /api/records?player_name=`（400 の仕様どおり）。`/` と `/app.js`・`/style.css` の静的配信。それ以外は 404。応答は JSON（UTF-8）。
- 完了条件: `curl` で各 API の正常系と 400・409 の応答を確かめられる。

## 6. 画面（HTML・CSS・JavaScript）

- 対象設計 ID: `DS-MD-INDEX-HTML`、`DS-MD-APP-JS`、`DS-MD-STYLE-CSS`、`DS-FN-SHOW-VIEW`、`DS-FN-RENDER-WHEEL`、`DS-FN-REMEMBER-PLAYER-NAME`
- 内容: 共通メニュー（Spin、Prizes、My Records）。Spin 画面は利用者名の入力、Spin ボタン、ホイール（景品数の等角の区画、景品の順）、結果表示。ホイール回転中は Spin ボタンを押せない。Prizes 画面は景品の表（名前と説明）。My Records 画面は利用者名で検索し、新しい順に表示。利用者名はブラウザに保存して初期値にする。文言は英語（設計書 4-1 のエラー文言どおり）。背景は薄いグレー、部品は濃い赤。DOM へは `textContent` で入れる。
- 完了条件: Chromium で 3 画面を開き、抽選・景品一覧・記録の確認・メニュー移動ができる（起動確認で目視）。

## 7. 単体テスト・結合テスト

- 対象設計 ID: 設計書 8-1 の単体・結合テスト（`DS-FN-DRAW-PRIZE`、`DS-FN-VALIDATE-PLAYER-NAME`、`DS-FN-LIST-PRIZES`、`DS-FN-INSERT-SPIN-RECORD`、`DS-FN-FIND-RECORDS-BY-NAME`、`DS-FN-OPEN-DATABASE`）
- 内容: `tests/` に `unittest` で書く。実行コマンド `python3 -m unittest discover -s tests`。
- 完了条件: テスト結果に FAIL が 0 件。失敗したら修正と再実行を全件通過まで繰り返す。

## 8. E2E テスト

- 対象設計 ID: `DS-TS-SPIN-AND-RECORD-E2E`、`DS-TS-VALIDATE-PLAYER-NAME-E2E`、`DS-TS-VIEW-PRIZE-LIST-E2E`、`DS-TS-VIEW-OWN-RECORDS-E2E`、`DS-TS-NAVIGATE-MENU-E2E`、`DS-TS-EMPTY-PRIZES-E2E`、`DS-TS-FIRST-START-AND-THEME-E2E`
- 内容: `e2e/test_e2e.py` に 7 本のテストを書く。一時 `DATA_DIR` と空きポートで `python3 -m app` を起動して HTTP で確かめる。`DS-TS-EMPTY-PRIZES-E2E` は DB から景品を全件削除した状態で確かめる。
- 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` の結果に FAIL が 0 件。失敗したら修正と再実行を全件通過まで繰り返す。

## 9. README.md 記載

- 対象設計 ID: `DS-OP-START-SERVER`、`DS-OP-SETUP-ENVIRONMENT`
- 内容: 起動方法（`bash setup.sh`、`PORT=任意 bash run.sh`）、環境変数（`PORT`、`DATA_DIR`）、3 画面の説明。初期ユーザーは無い。
- 完了条件: README.md だけを読んで初回起動できる。

## 10. 対応表（docs/trace_map.md）更新

- 対象設計 ID: 実装したすべての `DS-MD-*`、`DS-FN-*`、`DS-SC-*`、`DS-IF-*`、`DS-OP-*`、`DS-TS-*`
- 内容: 設計 ID とファイル・関数の対応を `docs/trace_map.md` に登録する（書式は trace-map-rules.md）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通る。

## 11. 起動確認

- 対象設計 ID: `DS-OP-START-SERVER`
- 内容: 空の `DATA_DIR` で `bash setup.sh`、`PORT=任意 bash run.sh` を実行し、Chromium で 3 画面を開く。
- 完了条件: 起動がエラーなく続き、3 画面が開ける。

## 12. 実装完了チェック

- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 13. 変更点の全件確認（最後）

- 内容: 設計書 11 章のすべての設計 ID が実装・テスト・対応表のいずれかに現れることを確かめる。要件 `RQ-FT`・`RQ-UI`・`RQ-EX` すべてが E2E の対応する `DS-TS` で確かめられていることを確かめる。
- 完了条件: 欠落が 0 件。

## 補足

- 要件の追加・変更・除外は無い（設計の途中で要件に不足は見つかっていない）。
