# 実装タスク: 備品の貸出管理

対象: `docs/requirements.md`・`docs/detail_design.md`（新規フロー。変更フローではない）。上から順に進める。

## 0. isdd-setup 導入確認（固定）

- 対象: `scripts/isdd/` の導入（`check.sh`、チェッカー、`dependencies.json`、`completeness.json`）
- 実行形態 `server`、認証あり（`--auth`）、外部連携なし（`--no-external`）、対応表の粒度 `class`、ソースディレクトリ `src`、E2E ディレクトリ `e2e`
- 依存の規則（設計書 第 7 章）を `scripts/isdd/dependencies.json` に書き写す
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`completeness.json` の実行形態・認証・外部連携が詳細設計書と一致する

## 1. 起動と準備の基盤（DS-OP-START-AND-INIT、DS-OP-NETWORK-ACCESS、DS-MD-MAIN、DS-MD-DATA-DATABASE、DS-CL-DATABASE、DS-SC-USERS-TABLE、DS-SC-EQUIPMENT-TABLE、DS-SC-LENDINGS-TABLE、DS-FN-MAIN、DS-FN-BUILD-SERVICES、DS-FN-LOAD-SECRET-KEY）

- `setup.sh`（`.venv` を作り、`requirements.txt` を入れ、`python3 -m playwright install chromium`）、`run.sh`（`.venv/bin/python src/main.py`）、`requirements.txt`
- `src/data/database.py`: `Database` クラス。接続、`users`・`equipment`・`lendings` のテーブル作成（`lendings.equipment_id` は主キー）、`BEGIN IMMEDIATE` のトランザクション
- `src/main.py`: `PORT`（既定 8000）、`DATA_DIR`（既定 `./data`、無ければ作る）、`0.0.0.0` で待ち受け。`load_secret_key`（`DATA_DIR/secret_key` を作るか読む）、`build_services`
- 完了条件: `bash setup.sh` が成功し、`bash run.sh` で起動して `/` が応答する。`DATA_DIR` に `app.db` ができ、備品とアカウントは 0 件

## 2. 業務層（DS-CL-ACCOUNT-SERVICE、DS-CL-EQUIPMENT-SERVICE、DS-CL-LENDING-SERVICE、DS-CL-SERVICE-ERROR、DS-CL-PERMISSION-DENIED、DS-CL-DUPLICATE-ERROR、DS-CL-USER-REPOSITORY、DS-CL-EQUIPMENT-REPOSITORY、DS-CL-LENDING-REPOSITORY、DS-FN-VALIDATE-ACCOUNT-FIELDS、DS-FN-VALIDATE-EQUIPMENT-FIELDS、DS-FN-VALIDATE-LENDING-FIELDS、DS-FN-REQUIRE-MANAGER、DS-FN-TODAY-JST、DS-MD-DATA-REPOSITORIES、DS-MD-SERVICE-*）

- `src/data/repositories.py`: 3 つのリポジトリと `DuplicateError`（一意制約の違反を変換）
- `src/service/errors.py`: `ServiceError`（欄の名前と文言）
- `src/service/permissions.py`: `PermissionDenied`、`require_manager`
- `src/service/clock.py`: `today_jst`（Asia/Tokyo）
- `src/service/validation.py`: 社員番号（6 桁の半角数字）、名前（前後の空白を除いて 1〜30 文字、空白だけ不可）、パスワード（8 文字以上）、管理番号（半角英数字とハイフン、1〜20 文字）、備品名（1〜50 文字）、貸出日（YYYY-MM-DD、今日以前）、借りる社員の必須
- `src/service/accounts.py`: `AccountService.register`（`BEGIN IMMEDIATE` で 0 件なら担当者）、`authenticate`（`hashlib.scrypt`、`hmac.compare_digest`）、`find_by_id`
- `src/service/equipment.py`: `EquipmentService.list_status`（管理番号の昇順、貸出中は名前と日付）、`register`、`update`、`delete`（貸出中は拒否）
- `src/service/lending.py`: `LendingService.lend`（`BEGIN IMMEDIATE`、貸出中は拒否）、`return_equipment`（貸出記録が無ければ拒否）
- 単体テスト `tests/`: 入力の検査の境界値、初回登録の役割、貸出中の拒否と削除の拒否、担当者以外の拒否、パスワードのハッシュ（元の文字列が保存されない）
- 完了条件: `python3 -m pytest tests -q` が全件通過

## 3. 画面（DS-MD-WEB-APP、DS-MD-WEB-AUTH、DS-MD-WEB-VIEWS、DS-CL-*、DS-IF-*、DS-FN-CREATE-APP、DS-FN-HANDLE-PERMISSION-DENIED、DS-FN-CURRENT-USER、DS-FN-START-SESSION、DS-FN-END-SESSION）

- `src/web/app.py`: `create_app`（サービスを受け取る。`PermissionDenied` を 403 の画面に変換）
- `src/web/auth.py`: `current_user`、`start_session`、`end_session`
- `src/web/views.py`: 9 つの画面の関数（`status_page`、`register_account_page`、`login_page`、`logout`、`equipment_new_page`、`equipment_edit_page`、`equipment_delete`、`lending_new_page`、`lending_return`）
- `src/web/templates/`: `base.html`（`.current-user`、「ログイン」「アカウント登録」リンク、「ログアウト」ボタン、`.error`、`.message`）、各画面。入力欄は `<div class="field">` に入れ、`.field-error` を置く。送った値は残す。操作ボタンはログイン状態と役割で出し分ける
- `src/web/static/style.css`
- 契約の id・文言・ボタン文言・URL を守る（contract.md）
- 完了条件: 画面を手で開いて確かめられる（`bash run.sh` で `/`、`/login/`、`/accounts/register/`、`/equipment/new/` が表示される）

## 4. E2E テスト（DS-TS-* の 19 本）

- `e2e/test_accounts.py`、`e2e/test_equipment.py`、`e2e/test_lending.py`、`e2e/test_status.py`、`e2e/test_nonfunctional.py`
- 各テストは一時の `DATA_DIR` でサーバーを起動する。Playwright（Chromium）で操作する
- 関数名は `DS-TS` の行と対応する（対応表の `e2e/<ファイル>::<関数名>`）
- `DS-TS-STATUS-RESPONSE-TIME` は備品 500 件と利用者 50 人を DB に直接入れる（前処理）
- `DS-TS-INTERNAL-ACCESS-REACHABLE` は、取れる場合は機の非ループバック IP でも開く
- 完了条件: `python3 -m pytest e2e -q --junitxml=e2e/results/e2e.xml` が全件通過

## 5. README.md（固定の一部）

- 準備（`setup.sh`）、起動（`run.sh`）、`PORT` と `DATA_DIR`、最初の登録は担当者になること、社内ネットワーク限定の運用（DS-OP-NETWORK-ACCESS）
- 完了条件: README.md だけで初回起動まで進める

## 6. 対応表（固定）

- `docs/trace_map.md`: 設計書 第 7 章の粒度 `class` で、ファイル、クラス、設計で名前を付けた関数、画面の関数（DS-IF）、E2E の DS-TS の行を登録する（書式は trace-map-rules.md）
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件

## 7. 完了確認（固定）

- `python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が問題 0 件
- `python3 scripts/isdd/implementation_completeness_checker.py .` が全項目 OK
- 単体・結合テスト（`python3 -m pytest tests -q`）が全件通過
- E2E（`python3 -m pytest e2e -q --junitxml=e2e/results/e2e.xml`）が全件通過
- 起動確認（`bash run.sh` で起動し、`/` が応答する）
- コードに `要件ID:` `設計ID:` `RQ-` `DS-` を含むコメントが無い
