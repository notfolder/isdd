# タスク一覧: 備品の貸出と返却（段 2、変更フロー）

対象: `change_requirements.md`（[追加] と [削除] の要件）と `change_detail_design.md`（[追加] と [削除] の設計要素）。上から順に実行する。各タスクの「実装する設計 ID」は対応表（`docs/trace_map.md`）に登録する行の手がかり。[削除] の設計要素は、後継の要素を実装したあとに対応表から外す。

## 先頭の固定タスク

### 0. isdd-setup 導入確認タスク

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` と `scripts/isdd/VERSION` が既にあるので、導入は済み。`bash scripts/isdd/check.sh` が実行できることを確かめる。第 7 章の依存の規則（`equipment_ledger/core/` から `flask`・画面の層への依存の禁止）が `scripts/isdd/dependencies.json` にあることを確かめる（既存のまま。変更しない）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（有り）・外部連携（無し）が変更設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 実装する設計 ID: なし
- 内容: `docs/active_change` の 1 行目が `.history/20261104-lending-return/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない（反映は実装後レビューで行う）。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 -I ~/.claude/skills/isdd-build/scripts/rq_ds_link_checker.py`（または isdd-build に同梱の同じチェッカー）を `.history/20261104-lending-return/change_requirements.md .history/20261104-lending-return/change_detail_design.md --base docs/requirements.md` で実行して合格すること。

## 実装タスク

### 1. DB のスキーマと移行（`equipment_ledger/core/db.py`）

- 実装する設計 ID: `DS-FN-INITIALIZE-SCHEMA-WITH-MIGRATION`、`DS-SC-LENDING-TABLE`、`DS-SC-EQUIPMENT-TABLE-WITH-REVISION`（[削除] の `DS-FN-INITIALIZE-SCHEMA`、`DS-SC-EQUIPMENT-TABLE` は対応表から外す）
- 内容: 備品テーブルに `revision INTEGER NOT NULL DEFAULT 0` を入れる。既存の DB で列が無ければ `ALTER TABLE` で足す。貸出テーブル（`equipment_number` 主キー、`employee_number`、`lent_on`）を `CREATE TABLE IF NOT EXISTS` で作る。
- 完了条件: 単体テストで、空の DB に 3 テーブルができ、版番号の無い旧い備品テーブルに列が足され、二度実行しても壊れないことを確かめる。

### 2. 入力チェック（`equipment_ledger/core/validation.py`）

- 実装する設計 ID: `DS-FN-VALIDATE-LENDING-INPUT`
- 内容: 借りる社員の空（「借りる社員を選んでください」、欄は `borrower`）、貸出日の形式（`\d{4}-\d{2}-\d{2}` かつ実在する日付。違うと「貸出日は YYYY-MM-DD の形式で入力してください」）、今日（引数で受け取る）より後（「貸出日に未来の日付は入力できません」）。今日は呼び出し側で日本時間（UTC+9）の日付として渡す。
- 完了条件: 単体テストで、空、形式違い（`2026-2-3`、`2026/11/04`、`2026-02-30`）、今日、昨日、明日の境界と文言を確かめる。

### 3. 借りる社員の候補（`equipment_ledger/core/accounts.py`）

- 実装する設計 ID: `DS-FN-LIST-BORROWER-CANDIDATES`
- 内容: 全アカウントを社員番号の昇順に、社員番号と名前の辞書で返す。
- 完了条件: 単体テストで、0 件、複数件の順序を確かめる。

### 4. 備品の操作の入れ替え（`equipment_ledger/core/equipment.py`）

- 実装する設計 ID: `DS-FN-LIST-EQUIPMENT-STATUS-WITH-LENDING`、`DS-FN-GET-EQUIPMENT-WITH-REVISION`、`DS-FN-UPDATE-EQUIPMENT-IF-UNCHANGED`、`DS-FN-DELETE-EQUIPMENT-IF-NOT-LENT`、`DS-FN-REGISTER-EQUIPMENT`（変更なし。版番号は 0 で入る）
- 内容:
  - 一覧は備品と貸出を LEFT JOIN し、管理番号の昇順。貸出の行があれば「貸出中」、借りている社員の名前（社員アカウントから）と貸出日、無ければ「空き」と空欄。版番号も返す。
  - 取得は管理番号・備品名・版番号を返す。無ければ無し。
  - 修正は `UPDATE ... SET name=?, revision=revision+1 WHERE equipment_number=? AND revision=?`。更新行数 0 は「他の担当者が変えた」（削除された場合も含む）の結果。貸出の行は触らない。
  - 削除は `BEGIN IMMEDIATE` で、貸出の行があれば「貸出中」の結果で終える（削除しない）。無ければ削除し、対象無しは結果で返す。
  - 旧い `list_equipment_status`、`get_equipment`、`update_equipment`、`delete_equipment` は削除する（呼び出し側は 6 で差し替える）。
- 完了条件: 単体テストで、一覧の順序と空き・貸出中の表示、取得、修正の成功と版番号の不一致（削除された場合も）、削除の成功と貸出中の拒否と対象無しを確かめる。

### 5. 貸出と返却（`equipment_ledger/core/lending.py`）

- 実装する設計 ID: `DS-MD-LENDING`、`DS-FN-LEND-EQUIPMENT`、`DS-FN-RETURN-EQUIPMENT`
- 内容:
  - `lend_equipment(conn, equipment_number, employee_number, lent_on)`: `BEGIN IMMEDIATE`。備品が無ければ `LEND_NO_EQUIPMENT`。借りる社員が無ければ `LEND_NO_BORROWER`。貸出の行を INSERT し、一意制約違反なら `LEND_ALREADY_LENT`。COMMIT して `LEND_OK`。
  - `return_equipment(conn, equipment_number)`: `BEGIN IMMEDIATE`。備品が無ければ `RETURN_NO_EQUIPMENT`。貸出の行を DELETE し、行数 0 なら `RETURN_ALREADY`、1 なら `RETURN_OK`。記録は残さない。
  - 結果の定数は同じモジュールに書く。ファイルは `core/` の中だけに依存する。
- 完了条件: 単体テストで、貸出の成功、備品無し、社員無し、貸出中の拒否、返却の成功、返却済みの拒否、返却後に貸出の行が残らないことを確かめる。同時の貸出・返却は別々の接続とスレッドで、1 件だけが成功することを確かめる（`tests/` に書く）。

### 6. 画面（`equipment_ledger/views.py`、テンプレート）

- 実装する設計 ID: `DS-IF-LEND-SCREEN`、`DS-IF-RETURN-EQUIPMENT`、`DS-IF-EQUIPMENT-STATUS-SCREEN`（内容の変更）、`DS-IF-EQUIPMENT-FORM-SCREEN`（版番号の隠し項目と `.error`）、`DS-IF-EQUIPMENT-DELETE`（貸出中の拒否）、`DS-FN-REQUIRE-MANAGER`（貸出と返却に付ける）
- 内容:
  - `/equipment/<管理番号>/lend/`（GET、POST）: `require_manager`。備品が無ければ 404。`.lending-equipment` に「備品: 管理番号 備品名」。`id_borrower` の select（候補は名前（社員番号））、`id_lent_on` の入力欄（既定は日本時間の今日）、「登録」ボタン。検査は 2 の関数。結果は `LEND_NO_BORROWER` を借りる社員の `.field-error`、`LEND_ALREADY_LENT` を貸出状況へのリダイレクトと `.message`「この備品は既に貸出中です」。入力値は残す。
  - `/equipment/<管理番号>/return/`（POST）: `require_manager`。`RETURN_OK` は貸出状況へ。`RETURN_ALREADY` は貸出状況の `.message`「この備品は既に返却されています」。`RETURN_NO_EQUIPMENT` は 404。
  - 貸出状況の画面: 行の状態、借りている社員、貸出日を出す。担当者は空きの行に「貸出」（貸出の画面へのボタン）、貸出中の行に「返却」（確認 `window.confirm` の「はい」で送信）。
  - 修正の画面: 開いた時点の版番号を隠し項目（`revision`）に入れる。保存で版番号が違えば、入力した備品名を残し `.error`「他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください」を出す。
  - 削除の画面（一覧の削除）: `DELETE_IF_NOT_LENT` の結果で貸出中なら `.message`「この備品は貸出中のため削除できません。先に返却を処理してください」。
  - テンプレート `lend.html` を足す。
- 完了条件: `bash run.sh` で起動し、`/`、`/accounts/register/`、`/login/`、`/equipment/new/` が 200 を返すこと（段 1 と同じ）。貸出と返却は E2E（8 番）で確かめる。

### 7. 単体テストと結合テストの全件通過

- 実装する設計 ID: なし（1〜5 のテスト。対応表は要求しない）
- 内容: `tests/` に 1〜5 の単体・結合テストを足し、段 1 のテストも通す。同時の貸出・返却（別の接続とスレッド）を含める。
- 実行: `cd プロジェクトルート && .venv/bin/python -m unittest discover -s tests -t .`
- 完了条件: FAIL と ERROR が 0 件。失敗したら修正と再実行を繰り返す。

### 8. E2E テスト全件通過

- 実装する設計 ID: `DS-TS-LEND-EQUIPMENT-E2E`、`DS-TS-REJECT-INVALID-LEND-E2E`、`DS-TS-RETURN-EQUIPMENT-E2E`、`DS-TS-DENY-DELETE-WHILE-LENT-E2E`、`DS-TS-EDIT-KEEPS-LENDING-E2E`、`DS-TS-REJECT-STALE-EDIT-E2E`、`DS-TS-CONCURRENT-LEND-E2E`、`DS-TS-CONCURRENT-RETURN-E2E`、`DS-TS-DENY-NON-STAFF-LENDING-E2E`（段 1 の 12 本は既存のまま通す）
- 内容: `e2e/test_equipment_ledger.py` に、上の 9 個の関数を 1 DS-TS 1 関数で足す。同時の貸出・返却は、ログイン済みの Cookie を持つ 2 つの HTTP の要求を、スレッドで同時に送る（Playwright の要求の API か標準ライブラリ）。段 1 の関数は変えない。
- 実行: `cd プロジェクトルート && .venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`
- 完了条件: 21 件（段 1 の 12 件と追加の 9 件）の JUnit XML で FAIL と ERROR が 0 件。失敗したら修正と再実行を全件通過まで続ける。

### 9. README.md の更新

- 実装する設計 ID: なし
- 内容: 段 1 の README に、貸出と返却の使い方（担当者が貸出状況の行の「貸出」「返却」で行う）を 1 節足す。既存の起動方法と初回の導入は変えない。
- 完了条件: README を読むだけで、貸出と返却の操作の場所と、担当者だけが行えることが分かること。

## 実装完了確認の必須固定タスク

### 10. 対応表（docs/trace_map.md）更新タスク

- 実装する設計 ID: 上の 1〜6 のすべて。[削除] の設計 ID（`DS-FN-LIST-EQUIPMENT-STATUS`、`DS-FN-GET-EQUIPMENT`、`DS-FN-UPDATE-EQUIPMENT`、`DS-FN-DELETE-EQUIPMENT`、`DS-FN-INITIALIZE-SCHEMA`、`DS-SC-EQUIPMENT-TABLE`）の行は外す。`DS-TS-*-E2E` の 9 行を足す。`DS-MD-LENDING` を `equipment_ledger/core/lending.py` に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

### 11. 起動確認タスク

- 実行形態がサーバー: `bash setup.sh` のあと、`bash run.sh` で起動し、`/` が 200 を返すこと（第 9 章 9-1 の起動方法）。
- 完了条件: 起動がエラーなく完了すること。

### 12. 単体テスト・結合テスト全件通過タスク

- 7 のテストを再実行する。完了条件: FAIL と ERROR が 0 件。

### 13. E2E テスト全件通過タスク

- 8 の E2E を再実行する。完了条件: JUnit XML で FAIL と ERROR が 0 件。

### 14. README.md 記載タスク

- 9 の README を確かめる。完了条件: 起動方法と初回の導入と、貸出・返却の操作が読めること。

### 15. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。完了条件: 全項目が OK であること。

### 16. 変更点の実装確認タスク

- `change_requirements.md` の [追加] の要件（RQ-FT・RQ-UI・RQ-DT・RQ-TS）と、`change_detail_design.md` の [追加] の設計要素（DS-*）が、すべて実装されているか（コードまたは E2E・単体テストのどれかで確かめられるか）を照らし合わせる。実装が原因の差分（設計にあるのに無い、無いのに足した）を直す。完了条件: 差分が 0 件。設計に無い要素が必要になったら実装を止め、isdd-spec に戻す。
