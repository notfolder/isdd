# タスク一覧: アカウントの管理（段 3、変更フロー）

対象: `change_requirements.md`（[追加] の要件）と `change_detail_design.md`（[追加] の設計要素）。上から順に実行する。各タスクの「実装する設計 ID」は対応表（`docs/trace_map.md`）に登録する行の手がかり。変更は既存の段 1・2 の機能を壊さないこと（段 1・2 のテストと E2E は変えずに通す）。

## 先頭の固定タスク

### 0. isdd-setup 導入確認タスク

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` と `scripts/isdd/VERSION` が既にあるので、導入は済み。`bash scripts/isdd/check.sh` が実行できることを確かめる。第 7 章の依存の規則（`equipment_ledger/core/` から `flask`・画面の層への依存の禁止）が `scripts/isdd/dependencies.json` にあることを確かめる（既存のまま。変更しない）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（有り）・外部連携（無し）が変更設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 実装する設計 ID: なし
- 内容: `docs/active_change` の 1 行目が `.history/20261104-account-management/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない（反映は実装後レビューで行う）。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-account-management/change_requirements.md .history/20261104-account-management/change_detail_design.md --base docs/requirements.md` が合格すること。

## 実装タスク

### 1. 入力チェック（`equipment_ledger/core/validation.py`）

- 実装する設計 ID: `DS-FN-VALIDATE-PASSWORD-INPUT`
- 内容: 再設定の新しいパスワードを検査する関数を足す。8 文字未満は「パスワードは 8 文字以上で入力してください」（欄は `new_password`）を返す。既存の関数は変えない。
- 完了条件: 単体テストで、7 文字（エラー）、8 文字（問題なし）、空（エラー）を確かめる。

### 2. アカウントの管理の関数（`equipment_ledger/core/accounts.py`）

- 実装する設計 ID: `DS-FN-LIST-ACCOUNTS`、`DS-FN-CHANGE-ACCOUNT-ROLE`、`DS-FN-RESET-PASSWORD`、`DS-FN-DELETE-ACCOUNT`
- 内容:
  - `list_accounts`: 全アカウントを社員番号の昇順で、社員番号・名前・権限を返す（ハッシュは返さない）。
  - `change_account_role`: `BEGIN IMMEDIATE`。対象が無ければ `ROLE_NO_ACCOUNT`。担当者を社員にする場合は担当者の数を数え、1 人以下なら `ROLE_LAST_MANAGER`。それ以外は権限を書き換えて `ROLE_CHANGE_OK`。コミットする。
  - `reset_password`: 1 件の UPDATE でハッシュを置き換える。行数 0 なら `RESET_NO_ACCOUNT`、1 なら `RESET_OK`（Werkzeug の `generate_password_hash`）。
  - `delete_account`: `BEGIN IMMEDIATE`。対象が無ければ `DELETE_NO_ACCOUNT`。貸出の行（`lending` の社員番号）があれば `DELETE_LENT`。担当者で、担当者の数が 1 人以下なら `DELETE_LAST_MANAGER`。それ以外は行を削除して `DELETE_OK`。
  - 結果の定数は同じモジュールに書く。
- 完了条件: `tests/` の単体テストで、一覧の順序と項目、権限の付け外し（2 人から 1 人への外しは成功、1 人の外しは拒否）、再設定後の照合（古いパスワードは失敗、新しいパスワードは成功）、削除の成功、貸出中の拒否、最後の担当者の拒否、対象無しの結果を確かめる。同時の付け外しと削除は別々の接続とスレッドで、担当者が 0 人にならないことを確かめる（`tests/` に書く）。

### 3. 要求ごとのセッションの同期（`equipment_ledger/auth.py`）

- 実装する設計 ID: `DS-FN-SYNC-SESSION-WITH-ACCOUNT`
- 内容: `sync_session_user(conn)`: セッションに社員がいれば、社員番号で DB のアカウントを読む。無ければセッションを消す。あれば、名前と権限をセッションに入れ直す。セッションが無ければ何もしない。既存の `current_user`、`require_manager` は変えない。
- 完了条件: 単体の結合（Flask のテストクライアント、`tests/` に書く）で、権限を担当者から社員に変えた後の次の要求が拒否され、削除した後の次の要求が未ログインとして扱われることを確かめる。

### 4. 画面（`equipment_ledger/views.py`、テンプレート）

- 実装する設計 ID: `DS-IF-ACCOUNT-LIST-SCREEN`、`DS-IF-ACCOUNT-ROLE-CHANGE`、`DS-IF-ACCOUNT-PASSWORD-RESET`、`DS-IF-ACCOUNT-DELETE`、`DS-MD-VIEWS` の要求ごとの同期（`bp.before_request` で `sync_session_user` を呼ぶ）、`DS-FN-REQUIRE-MANAGER`（新しい 4 つの経路に付ける）
- 内容:
  - `/accounts/`（GET）: 担当者だけ。一覧の表（`tbody tr`、`data-employee-number`、3 列目「担当者」か「社員」）。各行に、担当者の行は「担当者から外す」、社員の行は「担当者にする」（どちらも確認 `window.confirm`）、「パスワード再設定」（GET で `?reset=社員番号`、その行に `input[name=new_password]` と「確定」）、「削除」（確認）。再設定の行の `.field-error` と入力値の保持。`.message` の知らせ。貸出状況の画面の担当者向けに「アカウントの一覧」リンクを出す。
  - `/accounts/<社員番号>/role/`（POST、欄 `role`）、`/accounts/<社員番号>/password/`（POST、欄 `new_password`）、`/accounts/<社員番号>/delete/`（POST）: 結果に応じて一覧へ戻す。`ROLE_LAST_MANAGER` と `DELETE_LAST_MANAGER` は「担当者が 1 人もいなくなるため、この操作はできません」、`DELETE_LENT` は「この社員は備品を借りているため削除できません。先に返却を処理してください」を `.message` に出す。対象が無ければ 404。自分自身を削除したときはログアウトして貸出状況へ戻す。
  - テンプレート `accounts.html` を足す。`equipment_status.html` に担当者向けの「アカウントの一覧」リンクを足す。
- 完了条件: `bash run.sh` で起動し、`/`、`/accounts/register/`、`/login/`、`/equipment/new/` が 200 を返すこと。`/accounts/` は未ログインでログイン画面へ、社員で貸出状況へ戻ること（E2E の 8 番で確かめる）。

### 5. 単体テストと結合テストの全件通過

- 実装する設計 ID: なし（1〜4 のテスト。対応表は要求しない）
- 内容: 1〜3 のテストを `tests/` に足し、段 1・2 のテストも通す。
- 実行: `cd プロジェクトルート && .venv/bin/python -m unittest discover -s tests -t .`
- 完了条件: FAIL と ERROR が 0 件。失敗したら修正と再実行を繰り返す。

### 6. E2E テスト（追加分）

- 実装する設計 ID: `DS-TS-VIEW-ACCOUNT-LIST-E2E`、`DS-TS-CHANGE-ROLE-E2E`、`DS-TS-KEEP-ONE-STAFF-E2E`、`DS-TS-CONCURRENT-DEMOTE-E2E`、`DS-TS-RESET-PASSWORD-E2E`、`DS-TS-DELETE-ACCOUNT-E2E`、`DS-TS-DENY-DELETE-LENT-BORROWER-E2E`、`DS-TS-DENY-NON-STAFF-ACCOUNT-E2E`
- 内容: `e2e/test_equipment_ledger.py` に 8 個の関数を 1 DS-TS 1 関数で足す（`change_requirements.md` 第 7 章の 8 本に対応）。同時の付け外しは、ログイン済みの Cookie を持つ 2 つの HTTP 要求を、スレッドで同時に送る（段 2 と同じ方法）。段 1・2 の関数は変えない。
- 完了条件: 段 1・2 の E2E と合わせて全件（21 件に 8 件を足した数）の JUnit XML で FAIL と ERROR が 0 件。

### 7. README.md の更新

- 実装する設計 ID: なし
- 内容: 担当者が貸出状況の「アカウントの一覧」から、担当者の付け外し、パスワードの再設定、削除を行うことを 1 節足す。担当者が 1 人だけのときは外せず削除もできないこと、借りている社員は削除できないことを書く。既存の起動方法と初回の導入は変えない。
- 完了条件: README を読むだけで、アカウントの管理の場所と、担当者だけが行えることが分かること。

## 実装完了確認の必須固定タスク

### 8. 対応表（docs/trace_map.md）更新タスク

- 実装する設計 ID: 上の 1〜4 のすべて（`DS-FN-VALIDATE-PASSWORD-INPUT`、`DS-FN-LIST-ACCOUNTS`、`DS-FN-CHANGE-ACCOUNT-ROLE`、`DS-FN-RESET-PASSWORD`、`DS-FN-DELETE-ACCOUNT`、`DS-FN-SYNC-SESSION-WITH-ACCOUNT`、`DS-IF-ACCOUNT-LIST-SCREEN`、`DS-IF-ACCOUNT-ROLE-CHANGE`、`DS-IF-ACCOUNT-PASSWORD-RESET`、`DS-IF-ACCOUNT-DELETE`）の行を足す。`DS-TS-*-E2E` の 8 行を足す。関数の追加は `equipment_ledger/core/accounts.py::...` のように関数単位で結ぶ（粒度は function）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

### 9. 起動確認タスク

- 実行形態がサーバー: `bash setup.sh` のあと、`bash run.sh` で起動し、`/`、`/accounts/` が応答すること（`/accounts/` は未ログインならログイン画面へのリダイレクト）。
- 完了条件: 起動がエラーなく完了すること。

### 10. 単体テスト・結合テスト全件通過タスク

- 5 のテストを再実行する。完了条件: FAIL と ERROR が 0 件。

### 11. E2E テスト全件通過タスク

- 6 の E2E を再実行する。完了条件: JUnit XML（`e2e/results/e2e.xml`）で FAIL と ERROR が 0 件。実行は `cd プロジェクトルート && .venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`。

### 12. README.md 記載タスク

- 7 の README を確かめる。完了条件: 起動方法と初回の導入と、アカウントの管理の操作が読めること。

### 13. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。完了条件: 全項目が OK であること。

### 14. 変更点の実装確認タスク

- `change_requirements.md` の [追加] の要件（RQ-FT・RQ-UI・RQ-TS）と、`change_detail_design.md` の [追加] の設計要素（DS-*）が、すべて実装されているか（コードまたは E2E・単体テストのどれかで確かめられるか）を照らし合わせる。実装が原因の差分を直す。完了条件: 差分が 0 件。設計に無い要素が必要になったら実装を止め、isdd-spec に戻す。
