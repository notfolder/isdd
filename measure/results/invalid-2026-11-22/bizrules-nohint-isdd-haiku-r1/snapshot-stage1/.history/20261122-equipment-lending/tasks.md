# 実装タスク: 備品の貸出管理

対象の設計: `docs/detail_design.md`。要件: `docs/requirements.md`。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時は、実行形態 `server`、認証あり、外部連携なし、対応表の粒度 `function`、ソースディレクトリ `src`、E2E ディレクトリ `e2e` を渡す。
- 依存の規則（設計書 7-2 の表）を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が設計書と一致していること。

## 1. プロジェクト骨格

- 作るもの: `src/manage.py`、`src/config/__init__.py`、`src/config/settings.py`、`src/config/urls.py`（最初は空の割り当て）、`src/config/wsgi.py`。
- 設計 ID: `DS-MD-MANAGE-ENTRY`、`DS-MD-CONFIG-INIT`、`DS-MD-CONFIG-SETTINGS`、`DS-MD-CONFIG-URLS`、`DS-MD-CONFIG-WSGI`、`DS-SC-DATABASE`、`DS-OP-SETTINGS-ENV`。
- 要点: DB は `$DATA_DIR/lending.sqlite3`（`DATA_DIR` 既定は `./data`）。`ALLOWED_HOSTS` は環境変数、既定 `localhost,127.0.0.1`。`AUTH_USER_MODEL` は `accounts.Account`。パスワード検査は空（`AUTH_PASSWORD_VALIDATORS = []`）。`TIME_ZONE = 'Asia/Tokyo'`、`USE_TZ = True`。秘密鍵は環境変数 `DJANGO_SECRET_KEY`、無ければ `$DATA_DIR/secret_key` を作って使う。
- 完了条件: `python3 src/manage.py check` が問題 0 件。

## 2. アカウント（モデル）

- 作るもの: `src/accounts/__init__.py`（空）、`src/accounts/models.py`、`src/accounts/migrations/__init__.py`（空）、`src/accounts/migrations/0001_initial.py`（`makemigrations` で生成）。
- 設計 ID: `DS-MD-ACCOUNTS-INIT`、`DS-MD-ACCOUNTS-MODELS`、`DS-MD-ACCOUNTS-MIGRATIONS-INIT`、`DS-MD-ACCOUNTS-MIGRATION-0001`、`DS-CL-ACCOUNT-USER`、`DS-CL-ACCOUNT-USER-MANAGER`、`DS-SC-ACCOUNT-TABLE`、`DS-SC-ROLE-VALUES`。
- 要点: `employee_number`（6 桁の数字、一意）を `USERNAME_FIELD`。`name`（30 文字）、`role`（`M` 担当者 / `E` 社員）。`set_password` は Django 既定のハッシュ。マネージャーの作成関数は社員番号・名前・パスワードを受け、役割は呼び出し側が決める。
- 完了条件: `python3 src/manage.py makemigrations --check` が差分無し。

## 3. アカウント登録とログイン

- 作るもの: `src/accounts/forms.py`、`src/accounts/services.py`、`src/accounts/views.py`、テンプレート（`src/templates/base.html`、`accounts/register.html`、`accounts/login.html`）、`src/config/urls.py` の割り当て。
- 設計 ID: `DS-MD-ACCOUNTS-FORMS`、`DS-MD-ACCOUNTS-SERVICES`、`DS-MD-ACCOUNTS-VIEWS`、`DS-CL-REGISTER-FORM`、`DS-CL-LOGIN-FORM`、`DS-FN-REGISTER-ACCOUNT`、`DS-FN-REGISTER-VIEW`、`DS-FN-LOGIN-VIEW`、`DS-FN-LOGOUT-VIEW`、`DS-IF-REGISTER-SCREEN`、`DS-IF-LOGIN-SCREEN`、`DS-IF-LOGOUT-ACTION`。
- 要点: 登録の判定と作成は `transaction.atomic` の中で行い、件数 0 なら担当者、1 以上なら社員。SQLite の書き込みトランザクションを即時開始にする。成功時は `/login/` へ転送し「登録しました。ログインしてください」を `.message` に出す。ログイン失敗は `.error` に「社員番号またはパスワードが違います」（社員番号の有無を区別しない）。ログイン成功でトップへ。ログアウトは POST のみ。エラーは `.field`・`.field-error`、入力値を残す。
- 完了条件: 単体テストで、登録の成功・失敗、最初の登録者の担当者化、ログインの成否を確かめて通る。

## 4. 権限

- 作るもの: `src/accounts/permissions.py`。
- 設計 ID: `DS-MD-ACCOUNTS-PERMISSIONS`、`DS-FN-MANAGER-REQUIRED`。
- 要点: 未ログインは `/login/` へ転送。社員は 403（`handler403` の画面に `.error`「この操作は担当者だけができます」）。
- 完了条件: 単体テストで、未ログイン・社員・担当者の各ケースを確かめて通る。

## 5. 備品と貸出（モデル）

- 作るもの: `src/equipment/__init__.py`（空）、`src/equipment/models.py`、`src/equipment/migrations/__init__.py`（空）、`src/equipment/migrations/0001_initial.py`（生成）。
- 設計 ID: `DS-MD-EQUIPMENT-INIT`、`DS-MD-EQUIPMENT-MODELS`、`DS-MD-EQUIPMENT-MIGRATIONS-INIT`、`DS-MD-EQUIPMENT-MIGRATION-0001`、`DS-CL-EQUIPMENT`、`DS-CL-LENDING`、`DS-SC-EQUIPMENT-TABLE`、`DS-SC-LENDING-TABLE`。
- 要点: `Equipment.equipment_number`（20 文字、一意、大文字と小文字を区別）、`name`（50 文字）。`Lending` は `equipment`（一意の外部キー、PROTECT）、`borrower`（アカウントへの外部キー、PROTECT）、`lent_on`（日付）。貸出の有無で状態を決める。
- 完了条件: `makemigrations --check` が差分無し。

## 6. 備品と貸出の業務処理

- 作るもの: `src/equipment/services.py`。
- 設計 ID: `DS-MD-EQUIPMENT-SERVICES`、`DS-FN-DELETE-EQUIPMENT`、`DS-FN-LEND-EQUIPMENT`、`DS-FN-RETURN-EQUIPMENT`、`DS-CL-BUSINESS-RULE-ERROR`、`DS-SC-LENDING-TABLE`（遷移の処理に関わる）。
- 要点: どれも `transaction.atomic` の中で備品の行をロックし、貸出の記録の有無を確かめてから書く。貸出は、既に貸出中なら `BusinessRuleError`（「この備品は貸出中です」）。返却は、貸出中で無ければ `BusinessRuleError`（「この備品は貸出中ではありません」）。削除は、貸出中なら `BusinessRuleError`（「貸出中の備品は削除できません。先に返却してください」）。
- 完了条件: 単体テストで、3 つの業務処理の正常系と業務エラーの両方が、DB の状態を変えないことまで確かめて通る。

## 7. 備品と貸出の入力検証

- 作るもの: `src/equipment/forms.py`。
- 設計 ID: `DS-MD-EQUIPMENT-FORMS`、`DS-CL-EQUIPMENT-FORM`、`DS-CL-LENDING-FORM`。
- 要点: 管理番号は半角英数字とハイフン 1〜20 文字（大文字と小文字を区別）、一意（修正時は自分を除く）。備品名は必須 50 文字以内。貸出は借りる社員（登録済みの全アカウント、表示は「名前（社員番号）」）、貸出日（既定は今日（日本時間）、今日より後は入力エラー）。
- 完了条件: 単体テストで、境界値（20 文字・21 文字、50 文字・51 文字、今日・明日）を確かめて通る。

## 8. 備品と貸出の画面

- 作るもの: `src/equipment/views.py`、テンプレート（`equipment/status.html`、`equipment/equipment_form.html`、`equipment/lending_form.html`、`equipment/forbidden.html`）、`src/static/app.css`、`src/config/urls.py` の割り当て（`handler403` を含む）。
- 設計 ID: `DS-MD-EQUIPMENT-VIEWS`、`DS-FN-STATUS-VIEW`、`DS-FN-EQUIPMENT-NEW-VIEW`、`DS-FN-EQUIPMENT-EDIT-VIEW`、`DS-FN-EQUIPMENT-DELETE-VIEW`、`DS-FN-LENDING-NEW-VIEW`、`DS-FN-LENDING-RETURN-VIEW`、`DS-IF-STATUS-SCREEN`、`DS-IF-EQUIPMENT-NEW-SCREEN`、`DS-IF-EQUIPMENT-EDIT-SCREEN`、`DS-IF-EQUIPMENT-DELETE-ACTION`、`DS-IF-LENDING-NEW-SCREEN`、`DS-IF-LENDING-RETURN-ACTION`。
- 要点: 貸出状況は管理番号の昇順、列は管理番号・備品名・状態（「空き」「貸出中」）・借りている社員の名前・貸出日（YYYY-MM-DD）。行は `<tr data-equipment-number="...">`。ボタンは担当者にだけ描画（修正、削除、空きは「貸出」、貸出中は「返却」）。0 件は「備品は登録されていません」。削除と返却は `window.confirm` を通す POST のフォーム。貸出の登録成功は `/` へ転送。ヘッダーに `.current-user`。担当者には「備品を登録」（`/equipment/new/`）。
- 完了条件: 単体テストと結合テストで、画面の要素（id、クラス、文言）と権限ごとの表示を確かめて通る。

## 9. 単体・結合テスト

- 作るもの: `pytest.ini`（`DJANGO_SETTINGS_MODULE = config.settings`、`pythonpath = src`）、`tests/` 配下のテスト。
- 設計 ID: なし（テストファイルは対応表に載せない。`DS-TS` の行はテスト関数に結ばない）。
- 要点: 8-1 の方針。`RQ-NF-PASSWORD-HASH`（保存値が平文でない）と `RQ-NF-INTERNAL-ACCESS`（`ALLOWED_HOSTS` 既定値）も確かめる。
- 完了条件: `python3 -m pytest tests -q` が全件通る。

## 10. 起動スクリプトと依存

- 作るもの: `run.sh`、`setup.sh`、`requirements.txt`（Django 5.2.19、gunicorn 27.0.1、pytest 9.2.0、pytest-django、playwright 1.65.2 を固定）、`README.md` の起動方法（11 章の後）。
- 設計 ID: `DS-OP-START-SCRIPT`、`DS-OP-SETUP-SCRIPT`。
- 要点: `setup.sh` は `.venv` を作り依存を入れ、`python3 -m playwright install chromium` を実行。`run.sh` は `DATA_DIR` を作り、秘密鍵を用意し、`migrate` を行い、`exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --chdir src config.wsgi:application`。
- 完了条件: `bash setup.sh` が成功し、`PORT=18080 DATA_DIR=<一時> bash run.sh` で `/` が 200 を返す（確認後、起動したプロセスだけを停止する）。

## 11. E2E テスト

- 作るもの: `e2e/conftest.py`（起動と停止）、`e2e/test_*.py`（10 本）。
- 設計 ID: `DS-TS-REGISTER-FIRST-ACCOUNT-E2E`、`DS-TS-REGISTER-SECOND-ACCOUNT-E2E`、`DS-TS-LOGIN-LOGOUT-E2E`、`DS-TS-REGISTER-EQUIPMENT-E2E`、`DS-TS-UPDATE-EQUIPMENT-E2E`、`DS-TS-DELETE-EQUIPMENT-E2E`、`DS-TS-LEND-EQUIPMENT-E2E`、`DS-TS-RETURN-EQUIPMENT-E2E`、`DS-TS-VIEW-STATUS-PUBLIC-E2E`、`DS-TS-EMPLOYEE-CANNOT-OPERATE-E2E`。
- 要点: テストごとに空の `DATA_DIR` と空きポートで `bash run.sh` を起動し、終了時に起動したプロセスの PID だけを停止する（`pkill` や `killall` は使わない）。Playwright の同期 API。確認ダイアログは `page.once("dialog")` で受ける。
- 完了条件: `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件通る。

## 12. 対応表とチェックの実行

- 作るもの: `docs/trace_map.md`（実装したファイル、クラス、公開関数を登録）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。`rq_ds_link_checker.py` の問題 0 件（完了条件は build-implement.md の完了条件に従う）。

## 13. 起動確認タスク

- 実行形態 `server`。詳細設計書 9 章の起動方法（`bash setup.sh` の後に `bash run.sh`）どおりに起動できることを確かめる。
- 完了条件: 起動がエラーなく完了し、`/` が開けること。

## 14. 単体・結合テスト全件通過タスク

- `python3 -m pytest tests -q` を実行する。
- 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返す。

## 15. E2E テスト全件通過タスク

- `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する（mock モードは無い）。
- 完了条件: FAIL が 0 件。失敗したら修正と再実行を繰り返し、全件通過まで継続する。

## 16. README.md 記載タスク

- README.md に「起動方法」（`bash setup.sh`、`bash run.sh`、環境変数、既定ポート 8000）と「初期ユーザー」（無し。最初に登録した人が担当者になる）を書く。
- 完了条件: README.md を読むだけで初回起動が完結すること。

## 17. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。
