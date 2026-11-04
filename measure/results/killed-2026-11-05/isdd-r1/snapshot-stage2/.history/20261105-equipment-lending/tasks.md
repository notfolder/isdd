# 備品の貸出・返却と社員番号 7 桁化 実装タスク（段 2）

変更要件定義書（`change_requirements.md`）と変更設計書（`change_detail_design.md`）にもとづく。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない（反映は実装後レビューが行う）。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` と `scripts/isdd/VERSION` を確かめる。VERSION の値とスキルの `metadata.version` が同じであること。無ければ `isdd-setup` を実行する。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）、認証（あり）、外部連携（なし）が詳細設計書と一致している。

## 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-equipment-lending/` を指していることを確認する。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261105-equipment-lending/change_requirements.md .history/20261105-equipment-lending/change_detail_design.md --base docs/requirements.md` が合格する。

## 1. 社員番号を 7 桁にする（`DS-FN-VALIDATE-ACCOUNT-INPUT-SEVEN-DIGIT`、`DS-IF-ACCOUNT-REGISTER-SCREEN`、`DS-IF-LOGIN-SCREEN`）

- `src/equipment_ledger/validation.py::validate_account_input`: 社員番号の規則を 7 桁の数字にする。文言は「社員番号は 7 桁の数字で入力してください」。
- `src/equipment_ledger/templates/register.html`、`login.html`: 社員番号の表示を「7 桁の数字」に直す。
- 完了条件: 単体テストで 6 桁・8 桁・英字・空を拒否し、7 桁の数字を通すことを確かめる。

## 2. 貸出と版番号のための DB（`DS-SC-EQUIPMENT-TABLE-REVISIONED`、`DS-SC-LOAN-TABLE`、`DS-FN-PREPARE-DATABASE`）

- `src/equipment_ledger/db.py`: 備品テーブルに `revision INTEGER NOT NULL DEFAULT 1` を足す。貸出テーブル `loans`（`equipment_id` 主キー・参照 equipment(id)、`borrower_id` 参照 accounts(id)、`lent_on` テキスト）を作る。`initialize_database` で、既存の備品テーブルに版番号が無ければ `ALTER TABLE` で列を足す。
- 完了条件: 単体テストで、テーブルが無い DB の初期化を 2 回行ってもエラーにならないこと、版番号の列が無い（段 1 の）DB に対して初期化すると列が足され既存の行が残ること、主キーで同じ備品に 2 件の貸出が入らないことを確かめる。

## 3. 貸出状況の一覧と借りる社員の一覧（`DS-FN-LIST-EQUIPMENT-WITH-LENDING`、`DS-FN-LIST-BORROWERS`、`DS-FN-FIND-EQUIPMENT`、`DS-FN-CREATE-EQUIPMENT`）

- `src/equipment_ledger/equipment.py::list_equipment`: 備品と貸出と借りる社員を結合し、管理番号の昇順で返す。状況は「空き」か「貸出中」。
- `src/equipment_ledger/accounts.py::list_borrowers`: 全アカウントを社員番号の昇順で返す（id、社員番号、名前）。
- `find_equipment` は版番号を含む行を返す（`SELECT *`）。`create_equipment` は版番号の既定 1 に任せる。
- 完了条件: 単体テストで、貸出の無い備品は「空き」、貸出中は借りている社員の名前と貸出日、並びが管理番号の昇順であることを確かめる。

## 4. 備品の修正・削除（`DS-FN-UPDATE-EQUIPMENT-CHECKED`、`DS-FN-DELETE-UNLENT-EQUIPMENT`）

- `src/equipment_ledger/equipment.py::update_equipment`: 管理番号と版番号が一致する行を更新し、版番号を 1 増やす。一致しなければ `CONFLICT_MESSAGE`（「他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください」）を返す。一意制約違反は重複の文言。
- `src/equipment_ledger/equipment.py::delete_equipment`: 書き込みロックを取り、貸出があれば `LENT_MESSAGE`（「この備品は貸出中のため削除できません。先に返却を処理してください」）を返して削除しない。対象が無ければ `NOT_FOUND_MESSAGE`。成功なら None。
- 完了条件: 単体テストで、版番号の一致で更新、不一致と削除済みは競合、貸出の記録は修正後も残る、貸出中の削除は拒否、貸出が無ければ削除できることを確かめる。

## 5. 貸出と返却（`DS-MD-LENDING`、`DS-FN-LEND-EQUIPMENT`、`DS-FN-RETURN-EQUIPMENT`、`DS-FN-VALIDATE-LENDING-INPUT`）

- `src/equipment_ledger/lending.py`（新規）:
  - `lend_equipment(conn, equipment_number, borrower_id, lent_on)`: 書き込みロック、備品の存在、借りる社員の存在（無ければ `BORROWER_MISSING_MESSAGE`）、貸出中か（`ALREADY_LENT_MESSAGE`）、行の挿入（主キーの一意制約違反も `ALREADY_LENT_MESSAGE`）、コミット。
  - `return_equipment(conn, equipment_number)`: 書き込みロック、備品の存在、貸出の行の削除（無ければ `ALREADY_RETURNED_MESSAGE`）、コミット。
- `src/equipment_ledger/validation.py`: `validate_lending_input(borrower_id, lent_on, today)`（借りる社員の未選択、貸出日の空欄と形式、未来の日付の文言）と `today_in_japan()`（UTC+9 の今日）。
- 完了条件: 単体テストで、貸出の登録、貸出中の二重の登録の拒否、存在しない借りる社員、返却と二重の返却の拒否、貸出日の境界（今日は可、明日は不可、形式違い）を確かめる。

## 6. 画面（`DS-IF-LENDING-STATUS-SCREEN`、`DS-IF-LENDING-SCREEN`、`DS-IF-RETURN-ACTION`、`DS-IF-EQUIPMENT-EDIT-CHECKED-SCREEN`、`DS-IF-EQUIPMENT-DELETE-UNLENT-ACTION`、`DS-MD-WEB`、`DS-MD-AUTH`）

- `src/equipment_ledger/web.py`:
  - `equipment_status`: 貸出の情報を一覧に出す。担当者の行に「貸出」（空きのとき）または「返却」（貸出中のとき、`window.confirm`）、「修正」「削除」。
  - `lend_equipment`（`/equipment/<管理番号>/lend/`、GET と POST、担当者のみ）: GET で貸出中なら `.message`「この備品は既に貸出中です」、存在しなければ「対象の備品が見つかりません」で戻す。POST で入力を検証し、借りる社員と貸出日の `.field-error` を出す。成功で「貸出を登録しました」。
  - `return_equipment`（`/equipment/<管理番号>/return/`、POST、担当者のみ）: 「返却を処理しました」「この備品は既に返却されています」「対象の備品が見つかりません」。
  - `edit_equipment`: 修正画面に版番号を隠し欄で入れる。保存時に競合なら `.error`（開き直しの文言）、入力値を残す。
  - `delete_equipment`: 貸出中の拒否の文言を `.message` に出す。
  - 担当者の判定は既存の `auth.require_manager` を使う（`DS-FN-REQUIRE-MANAGER` は変更なし）。
- `src/equipment_ledger/templates/status.html`、`equipment_form.html`、新規 `lending_form.html`: 貸出の列、ボタン、`.lending-equipment`、`id_borrower`（select、「名前（社員番号）」）、`id_lent_on`（type=date、既定は今日）、「登録」ボタン、`.field`/`.field-error`、版番号の隠し欄。
- 完了条件: `tests/test_web.py` で、担当者以外の貸出・返却の拒否、ボタンの出し分け（社員と未ログインに「貸出」「返却」は無い）、貸出・返却の文言、修正の競合の `.error`、貸出中の削除の拒否を確かめる。

## 7. 単体・結合テスト（`tests/`）

- 既存の `tests/` の社員番号を 7 桁に直す（6 桁の期待は 7 桁の期待に変える）。
- 新規 `tests/test_lending.py`（貸出・返却、貸出日、同時の二重の貸出と返却を先の処理だけにすることを、接続を分けて確かめる）。
- 完了条件: `.venv/bin/python -m pytest tests -q` が全件通過する。

## 8. E2E テスト（`e2e/`、`DS-TS-*`）

- `e2e/test_accounts.py`: 社員番号を 7 桁に直す。`test_register_account` は 6 桁と重複の文言を確かめる（`DS-TS-REGISTER-ACCOUNT`）。
- `e2e/test_equipment.py`、`e2e/test_performance.py`: 社員番号を 7 桁に直す。既存の場面は変えない。
- 新規 `e2e/test_lending.py`:
  - `test_lend_equipment`（`DS-TS-LEND-EQUIPMENT`）
  - `test_prevent_double_lending`（`DS-TS-PREVENT-DOUBLE-LENDING`。担当者 2 つのブラウザ）
  - `test_return_equipment`（`DS-TS-RETURN-EQUIPMENT`）
  - `test_refuse_delete_lent_equipment`（`DS-TS-REFUSE-DELETE-LENT-EQUIPMENT`）
  - `test_update_equipment_conflict`（`DS-TS-UPDATE-EQUIPMENT-CONFLICT`）
  - `test_restrict_lending_non_manager`（`DS-TS-RESTRICT-LENDING-NON-MANAGER`）
  - `test_view_lending_status`（`DS-TS-VIEW-LENDING-STATUS`）
- `e2e/support.py`: 貸出の操作の補助（社員番号 7 桁の登録、貸出、返却）を足す。
- 完了条件: `.venv/bin/python -m pytest e2e -q --junitxml=e2e/results/e2e.xml` が全件通過する。

## 9. 対応表（`docs/trace_map.md`）更新タスク

- 変更設計書の [追加] の DS-ID を対応表に足し、[削除] の DS-ID（`DS-FN-VALIDATE-ACCOUNT-INPUT`、`DS-FN-LIST-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`、`DS-FN-INITIALIZE-DATABASE`、`DS-IF-EQUIPMENT-STATUS-SCREEN`、`DS-IF-EQUIPMENT-EDIT-SCREEN`、`DS-IF-EQUIPMENT-DELETE-ACTION`、`DS-SC-EQUIPMENT-TABLE`）の行を消す。`DS-MD-LENDING` と新しいファイルの行を足す。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（受け入れ判定を含む。E2E の結果を先に出しておく）。

## 10. README.md 記載タスク

- 「使い方」に貸出状況の見方、貸出の登録（担当者）、返却（担当者）を書く。
- 「初期ユーザー」は変更なし。既存の DB は起動時に自動で更新される旨を「起動」の後に書く。
- 完了条件: README だけで貸出と返却の操作が分かる。

## 11. 起動確認タスク

- `bash run.sh` で起動し、`/`、`/accounts/register/`、`/login/` が応答することを確かめる。
- 完了条件: エラー無く起動する。

## 12. 単体・結合テスト・E2E の全件通過

- 完了条件: `pytest tests` と `pytest e2e`（JUnit XML 出力）が FAIL 0 件。

## 13. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 14. 最終確認タスク

- 変更要件の [追加] の `RQ-FT`・`RQ-UI`・`RQ-TS` と、[追加] の `DS-TS` が受け入れ判定で「実装済み」であることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh --strict` の受け入れ判定が全件「実装済み」、未実行・不合格が 0 件。

## 追加の決め事（変更要件の再確認で変えたもの）

- 無し。
