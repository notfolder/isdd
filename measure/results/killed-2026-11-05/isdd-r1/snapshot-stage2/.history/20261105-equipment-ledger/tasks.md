# 備品台帳・貸出状況 実装タスク

詳細設計書（`docs/detail_design.md`）と要件定義書（`docs/requirements.md`）にもとづく。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行して対応表チェックを導入する。導入時の値は次のとおり。
  - ソースディレクトリ `--src src`
  - 実行形態 `--runtime server`
  - 認証あり `--auth`
  - 外部連携なし `--no-external`
  - 対応表の粒度 `--granularity function`
  - 依存の規則: 無い（`scripts/isdd/dependencies.json` は `"rules": []`）
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態が server、認証あり、外部連携なし。

## 1. 導入ファイルの作成

- `requirements.txt`（Flask 3.1.3、Waitress 3.0.2）、`requirements-dev.txt`（pytest 9.2.0、Playwright 1.64.1）を作る。
- `setup.sh` を作る: `.venv` の作成、両方の依存の導入、`python -m playwright install chromium`。
- `run.sh` を作る: `.venv` が無ければ案内して終了。あれば `PYTHONPATH=src` で `python -m equipment_ledger` を起動する。
- `.gitignore` に `.venv/`、`data/`、`e2e/results/`、`__pycache__/` を足す。
- 完了条件: `bash setup.sh` が正常終了する。

## 2. 設定と DB（`DS-MD-CONFIG`、`DS-MD-DB`、`DS-FN-LOAD-CONFIG`、`DS-FN-CONNECT-DATABASE`、`DS-FN-INITIALIZE-DATABASE`、`DS-SC-EQUIPMENT-TABLE`、`DS-SC-ACCOUNT-TABLE`）

- `src/equipment_ledger/config.py`: `load_config` で `PORT`、`HOST`、`DATA_DIR`、`SESSION_IDLE_TIMEOUT_SECONDS` を読む（既定は 8000、0.0.0.0、`./data`、1800）。
- `src/equipment_ledger/db.py`: `connect_database`（一意制約と外部キーを有効にした接続）、`initialize_database`（備品・アカウントのテーブルを作る。管理番号と社員番号に一意制約）。
- 完了条件: テーブルが無い DB に対して初期化を 2 回行ってもエラーにならない（単体テスト）。

## 3. 入力の検証（`DS-MD-VALIDATION`、`DS-FN-VALIDATE-ACCOUNT-INPUT`、`DS-FN-VALIDATE-EQUIPMENT-INPUT`）

- `src/equipment_ledger/validation.py`: 前後の空白を除いて判定する。アカウントは社員番号 6 桁、名前 1〜30 文字、パスワード 8 文字以上。備品は管理番号の半角英数字とハイフン 1〜20 文字、備品名 1〜50 文字。文言は契約（contract.md）と要件 1-2 のとおり。
- 完了条件: 単体テストで各境界（5/6/7 桁、30/31 文字、7/8 文字、20/21 文字、50/51 文字）と空欄を確かめる。

## 4. アカウント（`DS-MD-ACCOUNTS`、`DS-FN-REGISTER-ACCOUNT`、`DS-FN-FIND-ACCOUNT`、`DS-FN-AUTHENTICATE-ACCOUNT`）

- `src/equipment_ledger/accounts.py`:
  - `register_account`: `BEGIN IMMEDIATE` のトランザクションで件数を数え、0 件なら `manager`、それ以外は `employee`。パスワードはハッシュ化して保存。社員番号の重複は一意制約違反として文言を返す。
  - `find_account`: 社員番号で 1 件探す。
  - `authenticate_account`: 社員番号とパスワードを照合する。どちらが違うかは返さない。
- 完了条件: 単体テストで、最初の登録者が担当者、2 件目が社員、重複の拒否、パスワードが平文で保存されないこと、照合の成否を確かめる。

## 5. 備品（`DS-MD-EQUIPMENT`、`DS-FN-LIST-EQUIPMENT`、`DS-FN-FIND-EQUIPMENT`、`DS-FN-CREATE-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`）

- `src/equipment_ledger/equipment.py`:
  - `list_equipment`: 管理番号の昇順で全件。状況は「空き」、借りている社員・貸出日は空。
  - `find_equipment`: 管理番号で 1 件探す。
  - `create_equipment`、`update_equipment`: 一意制約違反を重複の結果として返す。更新は対象の存在を同じトランザクションで確かめる。
  - `delete_equipment`: 対象を削除する。記録は残さない。
- 完了条件: 単体テストで一覧の順序、登録・修正の重複、修正の対象が無い場合、削除の成否を確かめる。

## 6. セッションと権限（`DS-MD-AUTH`、`DS-FN-LOG-IN`、`DS-FN-LOG-OUT`、`DS-FN-CURRENT-ACCOUNT`、`DS-FN-EXPIRE-IDLE-SESSION`、`DS-FN-REQUIRE-MANAGER`）

- `src/equipment_ledger/auth.py`:
  - `log_in`: セッションにアカウントの識別子と最後の操作の時刻を入れる。
  - `log_out`: セッションを空にする。
  - `current_account`: セッションのアカウントを DB から読む（無ければ None）。
  - `expire_idle_session`: 最後の操作から期限を過ぎていればセッションを捨て、期限切れを示す。ログイン中なら最後の操作の時刻を更新する。
  - `require_manager`: 担当者以外の要求を、未ログインはログイン画面、社員は貸出状況へ転送し、`.message`「この操作は担当者だけが行えます」を出す。
- 完了条件: 単体テストで期限切れ（秒数を短くして確かめる）、担当者の判定を確かめる。

## 7. Web アプリ（`DS-MD-WEB`、`DS-FN-CREATE-APP` と各 `DS-IF-*`）

- `src/equipment_ledger/web.py`: `create_app` で Flask アプリを作る。Cookie は HttpOnly、SameSite=Lax。署名鍵は `DATA_DIR/secret_key`（無ければ生成し、権限は所有者だけ読めるように）。
  - ルート: `/`（`equipment_status`）、`/accounts/register/`（`register_account`）、`/login/`（`login`）、`/logout/`（`logout`、POST）、`/equipment/new/`（`new_equipment`）、`/equipment/<管理番号>/edit/`（`edit_equipment`）、`/equipment/<管理番号>/delete/`（`delete_equipment`、POST）。
  - 要求ごとに `expire_idle_session` を先に行う。
- `src/equipment_ledger/templates/` と `src/equipment_ledger/static/style.css`: 4-1 の画面仕様どおり。id と文言は contract.md のとおり（`id_employee_number`、`id_name`、`id_password`、`id_equipment_number`、ボタン「登録」「ログイン」「ログアウト」「保存」「修正」「削除」、リンク「ログイン」「アカウント登録」「備品を登録」、クラス `.field`、`.field-error`、`.error`、`.message`、`.current-user`、行の `data-equipment-number`）。
- 削除ボタンは `onclick="return confirm(...)"` で確認する。
- 完了条件: 単体・結合テスト（`tests/test_web.py`）で、各画面の応答、担当者以外の要求の拒否、ボタンの出し分けを確かめる。

## 8. 起動の入口（`DS-MD-ENTRYPOINT`、`DS-FN-START-SERVER`）

- `src/equipment_ledger/__main__.py`: `main` で設定を読み、DB を初期化し、Waitress で `HOST`:`PORT` を待ち受ける。
- 完了条件: `bash run.sh` で起動し、`curl -s http://127.0.0.1:8000/` が 200 を返す。

## 9. 単体・結合テスト（`tests/`）

- `tests/test_validation.py`、`tests/test_accounts.py`、`tests/test_equipment.py`、`tests/test_auth.py`、`tests/test_web.py` を作る。
- 完了条件: `.venv/bin/python -m pytest tests -q` が全件通過する。

## 10. E2E テスト（`e2e/`、`DS-TS-*`）

- `e2e/conftest.py`: 空きポートと一時の `DATA_DIR` で `python -m equipment_ledger` を起動し、Playwright の Chromium を用意する。終了時に停止する。
- `e2e/test_accounts.py`: `test_register_account`（DS-TS-REGISTER-ACCOUNT）、`test_login_logout`（DS-TS-LOGIN-LOGOUT）、`test_idle_logout`（DS-TS-IDLE-LOGOUT。`SESSION_IDLE_TIMEOUT_SECONDS=2`）。
- `e2e/test_equipment.py`: `test_view_status`（DS-TS-VIEW-STATUS）、`test_create_equipment`（DS-TS-CREATE-EQUIPMENT）、`test_update_equipment`（DS-TS-UPDATE-EQUIPMENT）、`test_delete_equipment`（DS-TS-DELETE-EQUIPMENT）、`test_restrict_non_manager`（DS-TS-RESTRICT-NON-MANAGER）。
- `e2e/test_performance.py`: `test_response_time`（DS-TS-RESPONSE-TIME。備品 500 件、3 秒以内）。
- 完了条件: `.venv/bin/python -m pytest e2e -q --junitxml=e2e/results/e2e.xml` が全件通過する。

## 11. README.md 記載タスク

- 「起動方法」: `bash setup.sh`、`bash run.sh`、環境変数の表。
- 「初期ユーザー」: 初期ユーザーは無い。導入の手順として、社員に URL を知らせる前に担当者が最初のアカウントを登録する（最初の登録者が担当者になる）。
- 「社内ネットワークからだけ開く」の手順（前段のファイアウォールで制限）。
- 完了条件: README だけで初回起動と初期の担当者登録が完結する。

## 12. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（function 粒度）。`DS-MD-*` は各ソースファイルに 1 行。`DS-TS-*` は e2e のテスト関数に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0・警告 0 件。

## 13. 起動確認タスク

- `bash run.sh` で起動し、`/`、`/accounts/register/`、`/login/` が応答することを確かめる。
- 完了条件: エラー無く起動する。

## 14. 単体・結合テスト・E2E の全件通過

- 完了条件: `pytest tests` と `pytest e2e`（JUnit XML 出力）が FAIL 0 件。

## 15. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 16. 最終確認タスク

- 設計書の全 `DS-ID` と要件の全 `RQ-FT`・`RQ-UI`・`RQ-NF` が実装され、受け入れ判定が「実装済み」であることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh --strict` の受け入れ判定が全件「実装済み」、未実行・不合格が 0 件。
