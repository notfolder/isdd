# タスク一覧: 備品台帳と貸出状況の閲覧（新規開発）

実装は上から順に行う。各タスクの「実装する設計 ID」は対応表（`docs/trace_map.md`）に登録する行の手がかり。

## 先頭の固定タスク

### 0. isdd-setup 導入確認タスク

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が無ければ `isdd-setup` で対応表チェックを導入する。導入時は詳細設計書の実行形態（サーバー）、認証（有り）、外部連携（無し）、対応表の粒度（function、第 7 章）を渡す。依存の規則は「無い」ではなく第 7 章 7-4 の表を `scripts/isdd/dependencies.json` に書き写す（core から web 層と flask への依存の禁止）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（有り）・外部連携（無し）が詳細設計書と一致していること。

## 実装タスク

### 1. プロジェクトの土台（依存・起動スクリプト・パッケージ）

- 実装する設計 ID: `DS-MD-PACKAGE-INIT`、`DS-MD-CORE-PACKAGE-INIT`、`DS-OP-RUN-SCRIPT`、`DS-OP-SETUP-SCRIPT`、`DS-OP-ENVIRONMENT-CONFIG`
- 内容: `requirements.txt`（flask、waitress、playwright をバージョン固定）、`setup.sh`（`.venv` の作成、依存の導入、`python -m playwright install chromium`）、`run.sh`（`.venv` の Python で `python -m equipment_ledger`）、空の `__init__.py` 2 つ。
- 完了条件: `bash setup.sh` が 1 回でエラーなく終わる。

### 2. 設定とDB（`equipment_ledger/core/config.py`、`db.py`）

- 実装する設計 ID: `DS-MD-CONFIG`、`DS-FN-LOAD-SETTINGS`、`DS-MD-DB`、`DS-FN-OPEN-CONNECTION`、`DS-FN-INITIALIZE-SCHEMA`、`DS-SC-EQUIPMENT-TABLE`、`DS-SC-ACCOUNT-TABLE`
- 内容: 環境変数 `PORT`（既定 8000）、`HOST`（既定 0.0.0.0）、`DATA_DIR`（既定 `./data`）、`SESSION_IDLE_TIMEOUT_SECONDS`（既定 1800）を読む。SQLite を開くとき WAL と busy timeout 5 秒を設定する。2 テーブル（equipment: 主キー管理番号と備品名、account: 社員番号・名前・ハッシュ・role の CHECK）を無ければ作る。秘密鍵ファイルを `DATA_DIR` に無ければ作る（これは `equipment_ledger/app.py` で使う）。
- 完了条件: 単体テストで、設定の既定値と環境変数の上書き、スキーマの二重作成が無害なことを確かめる。

### 3. 入力チェック（`core/validation.py`）

- 実装する設計 ID: `DS-MD-VALIDATION`、`DS-FN-VALIDATE-ACCOUNT-INPUT`、`DS-FN-VALIDATE-EQUIPMENT-INPUT`
- 内容: 社員番号（6 桁の数字）、名前（前後の空白を除いて 1 文字以上、30 文字以内）、パスワード（8 文字以上）。管理番号（半角英数字とハイフン、1〜20 文字）、備品名（1〜50 文字）。文言は契約の完全一致の文言を使う。
- 完了条件: 単体テストで境界値（5/6/7 桁、29/30/31 文字、7/8 文字、20/21 文字、50/51 文字）と文言を確かめる。

### 4. アカウントの登録と照合（`core/accounts.py`）

- 実装する設計 ID: `DS-MD-ACCOUNTS`、`DS-FN-REGISTER-ACCOUNT`、`DS-FN-AUTHENTICATE`
- 内容: 登録は `BEGIN IMMEDIATE` のトランザクションで件数を見て、0 件なら manager、それ以外は member。社員番号の重複は一意制約の違反を重複の結果として返す。パスワードは Werkzeug の `generate_password_hash`。照合は社員番号が無くても同じ経路でハッシュ照合（ダミー）を行い、失敗の文言を同じにする。
- 完了条件: 単体テストで、1 件目 manager・2 件目 member、重複、照合の成功と失敗（社員番号違い・パスワード違いが同じ結果）を確かめる。

### 5. 備品の操作（`core/equipment.py`）

- 実装する設計 ID: `DS-MD-EQUIPMENT`、`DS-FN-LIST-EQUIPMENT-STATUS`、`DS-FN-GET-EQUIPMENT`、`DS-FN-REGISTER-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`
- 内容: 一覧は管理番号の昇順、行ごとに空き（借りた社員名と貸出日は空欄）。登録の重複は結果で返す。修正は備品名のみ。削除は 1 件を物理削除（履歴を残さない）。
- 完了条件: 単体テストで、一覧の順序、0 件、登録・重複、修正、削除、対象無しの結果を確かめる。

### 6. 認証のセッションと要求の拒否（`equipment_ledger/auth.py`）

- 実装する設計 ID: `DS-MD-AUTH`、`DS-FN-LOG-IN-USER`、`DS-FN-LOG-OUT-USER`、`DS-FN-CURRENT-USER`、`DS-FN-REQUIRE-MANAGER`
- 内容: セッションに社員番号と最終操作時刻を入れる。`current_user` は社員番号と役割を返す。`require_manager` は担当者でなければ、未ログインはログイン画面へ、社員は貸出状況へリダイレクトし、どちらも `.message` に「この操作は担当者だけが行えます」を出す（未ログインはログイン画面）。
- 完了条件: 単体の結合（Flask のテストクライアント）で、未ログイン・社員・担当者それぞれの拒否と通過を確かめる。

### 7. アプリ本体と無操作の自動ログアウト（`equipment_ledger/app.py`、`__main__.py`）

- 実装する設計 ID: `DS-MD-APP`、`DS-FN-CREATE-APP`、`DS-FN-CHECK-IDLE-TIMEOUT`、`DS-MD-MAIN`、`DS-FN-START-SERVER`、`DS-MD-DB` の接続を利用
- 内容: `create_app` で設定を読み、秘密鍵を作り（無ければ）、スキーマを初期化し、セッション Cookie の SameSite を Lax にする。`before_request` で無操作時間を確かめ、設定秒数を超えたらセッションを消す。`__main__` は waitress で `HOST` と `PORT` を待ち受ける。
- 完了条件: `bash run.sh` で待ち受けを始め、`/` が 200 を返す。

### 8. 画面（`equipment_ledger/views.py`、テンプレート、CSS）

- 実装する設計 ID: `DS-MD-VIEWS`、`DS-IF-EQUIPMENT-STATUS-SCREEN`、`DS-IF-ACCOUNT-REGISTER-SCREEN`、`DS-IF-LOGIN-SCREEN`、`DS-IF-EQUIPMENT-FORM-SCREEN`、`DS-IF-LOGOUT`、`DS-IF-EQUIPMENT-DELETE`、`DS-FN-GET-EQUIPMENT`
- 内容: 契約の URL、id（`id_employee_number`、`id_name`、`id_password`、`id_equipment_number`）、文言（「登録」「ログイン」「ログアウト」「保存」「修正」「削除」「備品を登録」）、クラス（`.field`、`.field-error`、`.error`、`.message`、`.current-user`）を契約どおりに出す。貸出状況の表は `tbody tr` と `data-equipment-number` を持つ。削除の行は `window.confirm` の確認で「はい」のときだけ送信する。担当者以外に行ボタンを出さない。ログイン中だけ名前とログアウトを出す。入力値は残す。
- 完了条件: E2E（後の 9 番）で確かめる。ここでは `/`、`/accounts/register/`、`/login/`、`/equipment/new/` が 200 を返すことを手で確かめる。

### 9. 単体テストと結合テストの全件通過

- 実装する設計 ID: `DS-TS-REGISTER-FIRST-ACCOUNT-E2E` 以下の単体で確かめる範囲（タスク 2〜7 のテスト）
- 内容: `tests/` に unittest を書き、`.venv/bin/python -m unittest discover -s tests -t .` で全件を実行する。
- 完了条件: 結果に FAIL と ERROR が 0 件。失敗したら修正と再実行を繰り返す。

### 10. E2E テスト全件通過

- 実装する設計 ID: `DS-TS-REGISTER-FIRST-ACCOUNT-E2E`、`DS-TS-REJECT-ACCOUNT-INPUT-E2E`、`DS-TS-LOGIN-LOGOUT-E2E`、`DS-TS-AUTO-LOGOUT-E2E`、`DS-TS-REGISTER-EQUIPMENT-E2E`、`DS-TS-REJECT-EQUIPMENT-INPUT-E2E`、`DS-TS-UPDATE-EQUIPMENT-E2E`、`DS-TS-DELETE-EQUIPMENT-E2E`、`DS-TS-VIEW-STATUS-WITHOUT-LOGIN-E2E`、`DS-TS-VIEW-EMPTY-STATUS-E2E`、`DS-TS-DENY-NON-STAFF-E2E`、`DS-TS-PERFORMANCE-E2E`
- 内容: `e2e/test_equipment_ledger.py` に上の 12 関数を書く（1 DS-TS 1 関数）。Playwright の Chromium で、テスト用の一時 `DATA_DIR` と空きポートで `python -m equipment_ledger` を起動して操作する。自動ログアウトのテストは `SESSION_IDLE_TIMEOUT_SECONDS=2` で起動する。実行コマンドは `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`（pytest と pytest-playwright の導入を `requirements.txt` に含める）。
- 完了条件: JUnit XML で FAIL と ERROR が 0 件。失敗したら修正と再実行を全件通過まで繰り返す。

### 11. README.md 記載タスク

- 実装する設計 ID: `DS-OP-FIRST-ACCOUNT-SETUP`
- 内容: 「起動方法」（`bash setup.sh`、`bash run.sh`、`PORT` などの環境変数）と「初回の導入」（社員に URL を知らせる前に担当者が最初のアカウントを登録する。最初の登録者が担当者になる）。パスワードを画面に再表示する点の注意を書く。
- 完了条件: README を読むだけで、初回起動から最初の担当者登録まで完結できること。

### 12. 対応表（docs/trace_map.md）更新タスク

- 実装する設計 ID: 上の実装タスクのすべての `DS-*`（`DS-MD-*` は各ファイルの行、`DS-FN-*`・`DS-IF-*` は公開関数や画面の関数の行、`DS-SC-*` は DB の初期化関数の行に結ぶ）。`DS-TS-*` は `e2e/test_equipment_ledger.py::関数名` の行。
- 内容: 書式は trace-map-rules.md。粒度は function。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

### 13. 起動確認タスク

- 実装する設計 ID: `DS-OP-RUN-SCRIPT`
- 内容: `bash run.sh` で起動し、`/` が 200 を返すことを確かめて止める。
- 完了条件: 起動がエラーなく完了する。

### 14. 実装完了チェックタスク

- 実装する設計 ID: すべて
- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。`rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` も合格させる。
- 完了条件: 全項目が OK。
