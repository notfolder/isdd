# tasks.md: 備品台帳と貸出状況の閲覧

対象: `docs/requirements.md`、`docs/detail_design.md`（新規フロー）。isdd-build が上から順に実行する。

## 実装前の固定タスク

### 0. isdd-setup 導入確認タスク

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が無ければ isdd-setup を実行して対応表チェックを導入する。詳細設計書の実行形態（直接起動のサーバー）、認証あり、外部連携なし、対応表の粒度 `function` を渡す。依存の規則は「無い」なので `scripts/isdd/dependencies.json` は規則なしの雛形のままにする。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（直接起動）・認証（あり）・外部連携（なし）が詳細設計書と一致している。

## 実装タスク

### 1. 基盤（設定・データベース・時刻）

- 実装する設計 ID: `DS-MD-APP-INIT`、`DS-FN-CREATE-APP`、`DS-MD-CONFIG`、`DS-FN-LOAD-CONFIG`、`DS-FN-LOAD-SECRET-KEY`、`DS-MD-DB`、`DS-FN-CONNECT-DATABASE`、`DS-FN-INIT-SCHEMA`、`DS-SC-DATABASE-FILE`、`DS-SC-ACCOUNT-TABLE`、`DS-SC-EQUIPMENT-TABLE`、`DS-SC-LOAN-TABLE`、`DS-SC-SESSION-TABLE`、`DS-MD-TIMEUTIL`、`DS-FN-TODAY-JST`、`DS-MD-ERRORS`、`DS-CL-RULE-VIOLATION`、`DS-OP-SETTINGS`
- 内容: 設定の読み取り（PORT、DATA_DIR、SESSION_IDLE_TIMEOUT_SECONDS の既定値）、秘密鍵の生成と保存、SQLite の接続（外部キー、busy_timeout 5 秒、WAL）、表の作成（詳細設計書 3-1 の 4 表）、日本時間の今日、業務ルール違反の例外。
- 完了条件: 単体テスト（`tests/test_db.py`、`tests/test_config.py`）が通る。空の DATA_DIR で表が作られる。

### 2. 検証と認証の部品

- 実装する設計 ID: `DS-MD-VALIDATION`、`DS-FN-VALIDATE-ACCOUNT-INPUT`、`DS-FN-VALIDATE-PASSWORD`、`DS-FN-VALIDATE-EQUIPMENT-INPUT`、`DS-FN-VALIDATE-LENT-ON`、`DS-MD-AUTH`、`DS-FN-CREATE-SESSION`、`DS-FN-RESOLVE-SESSION-USER`、`DS-FN-DELETE-SESSION`、`DS-FN-REQUIRE-MANAGER`
- 内容: 詳細設計書 4-1 の入力の検証（文言は完全一致）、セッションの作成・解決（無操作の判定と最終操作時刻の更新）・削除、担当者の判定（担当者でなければ貸出状況の画面へ戻し「この操作は担当者だけが行えます」、未ログインはログイン画面へ）。
- 完了条件: `tests/test_validation.py`、`tests/test_auth.py` が通る。

### 3. アカウントの業務処理

- 実装する設計 ID: `DS-MD-ACCOUNTS`、`DS-FN-REGISTER-ACCOUNT`、`DS-FN-AUTHENTICATE`、`DS-FN-LIST-ACCOUNTS`、`DS-FN-SET-MANAGER-ROLE`、`DS-FN-RESET-PASSWORD`、`DS-FN-DELETE-ACCOUNT`
- 内容: 登録（最初の 1 件は担当者、以降は社員。BEGIN IMMEDIATE で判定と挿入を 1 トランザクションに）、認証（社員番号が無い場合も同じ照合を行い、区別しない）、一覧、担当者の付け外し（担当者 0 人を拒否）、パスワード再設定（scrypt のハッシュ）、削除（貸出中の社員は拒否、削除前にそのセッションを消す）。
- 完了条件: `tests/test_accounts.py` が通る。

### 4. 備品と貸出の業務処理

- 実装する設計 ID: `DS-MD-EQUIPMENT`、`DS-FN-CREATE-EQUIPMENT`、`DS-FN-GET-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`、`DS-FN-LIST-LENDING-STATUS`、`DS-MD-LOANS`、`DS-FN-LEND-EQUIPMENT`、`DS-FN-RETURN-EQUIPMENT`
- 内容: 備品の登録、取得、修正（版番号の一致を確かめて更新し版番号を 1 増やす）、削除（貸出中は拒否、版番号の一致）、貸出状況の一覧（管理番号の昇順）、貸出（版番号の一致、既に貸出中は拒否）、返却（版番号の一致、貸出の行の削除、既に返却済みは拒否）。
- 完了条件: `tests/test_equipment.py`、`tests/test_loans.py` が通る。同時更新の競合（版番号の不一致、既に貸出中）が単体テストで確かめられる。

### 5. 画面（経路と画面の部品）

- 実装する設計 ID: `DS-MD-VIEWS`、`DS-IF-LENDING-STATUS-SCREEN`、`DS-IF-ACCOUNT-REGISTER-SCREEN`、`DS-IF-LOGIN-SCREEN`、`DS-IF-LOGOUT-ACTION`、`DS-IF-EQUIPMENT-NEW-SCREEN`、`DS-IF-EQUIPMENT-EDIT-SCREEN`、`DS-IF-EQUIPMENT-DELETE-ACTION`、`DS-IF-LEND-SCREEN`、`DS-IF-RETURN-ACTION`、`DS-IF-ACCOUNT-LIST-SCREEN`、`DS-IF-ACCOUNT-MANAGER-ACTION`、`DS-IF-ACCOUNT-PASSWORD-ACTION`、`DS-IF-ACCOUNT-DELETE-ACTION`、`DS-MD-TPL-BASE`、`DS-MD-TPL-STATUS`、`DS-MD-TPL-LOGIN`、`DS-MD-TPL-ACCOUNT-REGISTER`、`DS-MD-TPL-ACCOUNT-LIST`、`DS-MD-TPL-EQUIPMENT-FORM`、`DS-MD-TPL-LEND-FORM`
- 内容: 詳細設計書 4-1 の経路と画面（`.message`、`.error`、`.field`、`.field-error`、`.current-user`、`tbody tr` の `data-*` 属性、ボタンの文言、確認ダイアログは `onsubmit` の `confirm`）。画面の文言と id は contract.md に完全一致させる。すべての POST は担当者の判定を通す。
- 完了条件: アプリを起動して各画面の HTML に contract.md の id・文言が出る（isdd-build の起動確認で確かめる）。

### 6. 起動スクリプトと依存

- 実装する設計 ID: `DS-OP-SETUP-SCRIPT`、`DS-OP-RUN-SCRIPT`、`DS-OP-INITIAL-MANAGER-PROCEDURE`
- 内容: `setup.sh`（Python 3.12 で `.venv` を作り `requirements.txt` の固定版を入れる）、`run.sh`（PORT 既定 8000、DATA_DIR 既定 `data`、`SESSION_IDLE_TIMEOUT_SECONDS` 既定 1800、waitress を 0.0.0.0 でスレッド 16 で起動）、`requirements.txt`（flask==3.1.3、waitress==3.0.2）、README.md の起動方法と導入手順（最初の担当者の登録）。
- 完了条件: `bash setup.sh` と `PORT=8785 DATA_DIR=/tmp/isdd-r1-data bash run.sh` でアプリが起動し、`/` が 200 を返す。

### 7. 単体テストと結合テストの全件通過

- 実装する設計 ID: 単体テスト（`tests/`）は設計の 8-1。対応表には載せない（テストファイルは `DS-TS` の行でだけ載せるため）。
- 内容: 8-1 の実行コマンド `.venv/bin/python -m pytest tests` を実行する。
- 完了条件: 失敗が 0 件。失敗は修正と再実行を繰り返す。

### 8. E2E テストの実装と全件通過

- 実装する設計 ID: `DS-TS-REGISTER-FIRST-MANAGER`、`DS-TS-REGISTER-ACCOUNT-VALIDATION`、`DS-TS-LOGIN-LOGOUT`、`DS-TS-IDLE-LOGOUT`、`DS-TS-ROLE-CHECK`、`DS-TS-REGISTER-EQUIPMENT`、`DS-TS-EDIT-EQUIPMENT`、`DS-TS-DELETE-EQUIPMENT`、`DS-TS-LEND-RETURN`、`DS-TS-VIEW-LENDING-STATUS`、`DS-TS-ACCOUNT-LIST-MANAGE`、`DS-TS-PERFORMANCE-50-USERS`
- 内容: `e2e/requirements-e2e.txt`（pytest==9.2.0、playwright==1.64.1）。`e2e/` の pytest テストは、一時の PORT と DATA_DIR で waitress を起動して Playwright で操作する。`DS-TS-IDLE-LOGOUT` は SESSION_IDLE_TIMEOUT_SECONDS=3 で別の起動をする。`DS-TS-PERFORMANCE-50-USERS` は 50 並列で表示時間を計る。`e2e/results/` は git 管理外（.gitignore に追加）。
- 完了条件: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` で FAIL が 0 件。`DS-TS` の行が対応表にあり、テスト関数に結ばれている。

### 9. 対応表（docs/trace_map.md）更新タスク

- 実装する設計 ID: 上の全設計 ID（`DS-MD`、`DS-FN`、`DS-CL`、`DS-IF`、`DS-TS` の行）
- 内容: 実装したファイル・クラス・公開関数を docs/trace_map.md に登録する（書式は trace-map-rules.md。粒度は `function`）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通る。

### 10. 起動確認タスク

- 実装する設計 ID: `DS-OP-RUN-SCRIPT`、`DS-OP-SETUP-SCRIPT`
- 内容: `bash setup.sh`、`PORT=8785 DATA_DIR=/tmp/isdd-r1-data bash run.sh` で起動し、契約の URL（`/`、`/accounts/register/`、`/login/`、`/equipment/new/`、`/accounts/`）が開くこと、画面の id と文言を確かめる。確かめたら停止する。
- 完了条件: 起動とすべての画面の確認がエラーなく完了する。

### 11. 実装完了チェック

- 実装する設計 ID: なし（確認）
- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 変更点の確認

- すべての変更点（設計書の DS-ID）が実装されたことを確認する。対象は `docs/trace_map.md` の行と、要件の受け入れ判定（`scripts/isdd/acceptance_checker.py` の出力）。
- 完了条件: 要件定義書 第 7 章の全 `RQ-TS` が「実装済み」になる。
