# tasks.md: 備品台帳と貸出状況の閲覧（段 1）

詳細設計書 `docs/detail_design.md` のとおりに実装する。上から順に進める。

## 0. isdd-setup 導入確認タスク（先頭）

- 内容: `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。実行形態 `server`、認証あり（`--auth`）、外部連携なし（`--no-external`）、対応表の粒度 `function`、ソースディレクトリ `app`。第 7 章の依存の規則（無し）を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致する。

## 1. 基盤（設定・DB・アプリの作成）

- 設計 ID: `DS-MD-APP-INIT`, `DS-FN-CREATE-APP`, `DS-FN-LOAD-SETTINGS`, `DS-MD-DB`, `DS-FN-GET-DB`, `DS-FN-INIT-DB`, `DS-FN-CLOSE-DB`, `DS-SC-ACCOUNT-TABLE`, `DS-SC-EQUIPMENT-TABLE`, `DS-OP-ENV-SETTINGS`
- 内容: `app/__init__.py`（create_app、load_settings）、`app/db.py`（SQLite の接続、WAL、待ち 5 秒、テーブルと秘密鍵の初期化）。
- 完了条件: `DATA_DIR` を空にして `create_app` を呼ぶと、テーブルと `secret_key` ができる。単体テストで確かめる。

## 2. アカウント（登録・認証）

- 設計 ID: `DS-MD-ACCOUNTS`, `DS-FN-HASH-PASSWORD`, `DS-FN-VALIDATE-REGISTRATION`, `DS-FN-REGISTER-ACCOUNT`, `DS-FN-GET-ACCOUNT`, `DS-FN-AUTHENTICATE-ACCOUNT`
- 内容: `app/accounts.py`。入力検査（6 桁の数字、名前 1〜30 文字で空不可、パスワード 8 文字以上）。0 件なら担当者、それ以外は社員。BEGIN IMMEDIATE で直列化。社員番号の重複は一意制約で検出。認証は失敗時に理由を区別しない。
- 完了条件: `tests/test_accounts.py` が通る（最初の登録が担当者、2 件目が社員、重複、形式違い、認証の成否）。

## 3. 備品（検査・登録・修正・削除・一覧）

- 設計 ID: `DS-MD-EQUIPMENT`, `DS-FN-VALIDATE-EQUIPMENT`, `DS-FN-CREATE-EQUIPMENT`, `DS-FN-UPDATE-EQUIPMENT`, `DS-FN-DELETE-EQUIPMENT`, `DS-FN-GET-EQUIPMENT`, `DS-FN-LIST-LOAN-STATUS`
- 内容: `app/equipment.py`。管理番号は半角の英数字とハイフン 20 文字以内、備品名は 50 文字以内で空不可。重複は一意制約で検出。一覧は管理番号の昇順、状態は「空き」固定。
- 完了条件: `tests/test_equipment.py` が通る。

## 4. セッションとロール

- 設計 ID: `DS-MD-AUTH`, `DS-FN-LOGIN-ACCOUNT`, `DS-FN-LOGOUT-ACCOUNT`, `DS-FN-CURRENT-ACCOUNT`, `DS-FN-CHECK-IDLE-TIMEOUT`, `DS-FN-MANAGER-REQUIRED`
- 内容: `app/auth.py`。最後の操作から設定秒数を超えたらセッションを消す。`manager_required` は未ログインをログイン画面へ、社員を一覧へ戻して `.message`「この操作は担当者だけが行えます」。
- 完了条件: `tests/test_auth.py`（期限の境界、担当者判定）が通る。

## 5. 画面と操作（views）

- 設計 ID: `DS-MD-VIEWS`, `DS-IF-LOAN-STATUS-PAGE`, `DS-IF-REGISTER-PAGE`, `DS-IF-LOGIN-PAGE`, `DS-IF-LOGOUT-ACTION`, `DS-IF-EQUIPMENT-FORM-PAGE`, `DS-IF-EQUIPMENT-EDIT-PAGE`, `DS-IF-EQUIPMENT-DELETE-ACTION`
- 内容: `app/views.py` の 7 つの関数。テンプレート（`app/templates/`）と CSS（`app/static/`）。入力の id・ボタンの文言・リンクの文言・`.field`/`.field-error`・`.error`・`.message`・`.current-user`・`tbody tr[data-equipment-number]` は契約（contract.md）のとおり。削除は `window.confirm`。
- 完了条件: Flask のテストクライアントで各画面が 200 を返し、契約の要素が出る（`tests/test_views.py`）。

## 6. 起動

- 設計 ID: `DS-MD-APP-MAIN`, `DS-FN-START-SERVER`, `DS-OP-RUN-SCRIPT`, `DS-OP-SETUP-SCRIPT`, `DS-OP-FIRST-MANAGER-PROCEDURE`
- 内容: `app/__main__.py`（Waitress で `0.0.0.0:PORT`）、`run.sh`、`setup.sh`、`requirements.txt`。README.md に起動方法と初回の担当者登録の手順を書く。
- 完了条件: `bash setup.sh` の後、`bash run.sh` で起動し、`/` が 200 を返す。

## 7. 単体・結合テスト全件通過

- 内容: `.venv/bin/python -m pytest tests -q` を全件実行する。
- 完了条件: FAIL が 0 件。失敗は修正と再実行を繰り返す。

## 8. E2E テスト全件通過

- 設計 ID: `DS-TS-REGISTER-FIRST-ACCOUNT`, `DS-TS-REGISTER-VALIDATION`, `DS-TS-REGISTER-SECOND-ACCOUNT`, `DS-TS-LOGIN-AND-FAILURE`, `DS-TS-LOGOUT`, `DS-TS-IDLE-TIMEOUT`, `DS-TS-CREATE-EQUIPMENT`, `DS-TS-CREATE-EQUIPMENT-VALIDATION`, `DS-TS-UPDATE-EQUIPMENT`, `DS-TS-DELETE-EQUIPMENT`, `DS-TS-LOAN-STATUS-ANONYMOUS`, `DS-TS-ROLE-CONTROL`, `DS-TS-LOAN-STATUS-PERFORMANCE`
- 内容: `e2e/conftest.py`（一時の DATA_DIR と空きポートで Waitress を起動）と `e2e/test_scenarios.py`（13 関数、各 DS-TS に 1 対 1）。対応表の `DS-TS` 行は `e2e/test_scenarios.py::test_...`。
- 完了条件: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件通過する。

## 9. 対応表（docs/trace_map.md）の更新

- 内容: 実装したファイル・クラス（なし）・公開関数・`DS-MD`・`DS-IF`・`DS-TS` を `docs/trace_map.md` に登録する（書式は trace-map-rules.md）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 10. 起動確認

- 完了条件: `bash run.sh` で起動し、エラーなく待ち受ける（タスク 6 と同じ確認を最終状態で行う）。

## 11. README.md 記載

- 完了条件: README.md を読むだけで `bash setup.sh`、`bash run.sh`、初回の担当者登録まで完結できる。

## 12. 実装完了チェック

- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 13. 要件の全件確認（最後）

- 内容: 設計書 `DS-*` の全件が対応表にあること、要件 `RQ-FT`・`RQ-UI`・`RQ-NF-RESPONSE-3S` の受け入れが E2E で通ること（受け入れ判定）を確かめる。
- 完了条件: `rq_ds_link_checker.py` が問題 0 件、受け入れ判定が「実装済み」。

## 変更点の確認

- 段 1 の要件・設計の全 ID（`RQ-FT-*` 9 件、`RQ-UI-*` 4 件、`RQ-DT-*` 3 件、`RQ-NF-*` 5 件、`RQ-OP-*` 2 件、`RQ-TS-*` 13 件）を、上の各タスクに割り当てたことを確かめる。
- 完了条件: 割り当て漏れが無い。
