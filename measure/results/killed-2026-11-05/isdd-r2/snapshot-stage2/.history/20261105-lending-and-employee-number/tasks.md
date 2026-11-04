# 実装タスク（社員番号の 7 桁化と、備品の貸出・返却）

入力: `change_requirements.md`、`change_detail_design.md`（正本 `docs/requirements.md`・`docs/detail_design.md` に重ねる。有効な設計は「正本 ＋ [追加]」）。上から順に進める。正本と変更文書は書き換えない（反映は実装後レビュー）。

## 0. 導入確認と登録確認

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は導入済み。`scripts/isdd/completeness.json` の実行形態（server）・認証（あり）・外部連携（なし）が詳細設計書と一致していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、completeness.json の値が正本の 1 章と一致する。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261105-lending-and-employee-number/` を指していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261105-lending-and-employee-number/change_requirements.md .history/20261105-lending-and-employee-number/change_detail_design.md --base docs/requirements.md` が合格する。

## 1. 社員番号の 7 桁化（RQ-FT-EMPLOYEE-NUMBER-7-DIGITS）

1. `src/validation.py`（`DS-MD-VALIDATION`、`DS-FN-VALIDATE-ACCOUNT-INPUT`）: 社員番号の形式を `[0-9]{7}` にし、文言を「社員番号は 7 桁の数字で入力してください」にする。
   - 完了条件: 単体テストで 6 桁が形式違い、7 桁（先頭 0 を含む）が合格する。

## 2. 貸出の表（RQ-DT-LENDING-ENTITY）

2. `src/db.py`（`DS-SC-LENDING-TABLE`、`init_schema` の中）: `lendings` 表を作る（主キー `equipment_number`、`equipment` を `ON UPDATE CASCADE` で参照、`employee_number` は `accounts` を参照、`lent_on`）。
   - 完了条件: 一時 DB で表が作られ、既存の DB に対して再実行しても壊れない。外部キーの連動更新で、備品の管理番号を変えると貸出の行も付いてくる。

## 3. 貸出・返却（RQ-FT-LEND-EQUIPMENT、RQ-FT-LEND-ONLY-AVAILABLE、RQ-FT-RETURN-EQUIPMENT、RQ-FT-RETURN-ONLY-LENT）

3. `src/lending.py`（`DS-MD-LENDING`）を作る。
   - `today_jst`（`DS-FN-TODAY-JST`）: 日本時間（固定オフセット +9）の今日の日付を返す。引数 now を受けられる。
   - `lend_equipment`（`DS-FN-LEND-EQUIPMENT`）: `BEGIN IMMEDIATE` の中で、備品の存在、貸出の有無、借りる社員の存在を確かめ、挿入する。戻り値は（エラー、状態）。状態は ok・not_found・already_lent・invalid。
   - `return_equipment`（`DS-FN-RETURN-EQUIPMENT`）: `BEGIN IMMEDIATE` の中で、備品の存在を確かめ、貸出の行を削除する。戻り値は状態（ok・not_found・not_lent）。
   - 完了条件: 単体テストで、貸出→貸出中の再貸出は already_lent、返却→空きへの再返却は not_lent、未知の備品は not_found、借りる社員が無いと invalid。
4. `src/validation.py`（`DS-FN-VALIDATE-LENDING-INPUT`）: 借りる社員の未選択（「借りる社員を選んでください」）、貸出日の形式違い（「貸出日は YYYY-MM-DD の形で入力してください」）、未来（「貸出日に未来の日付は入力できません」）を項目ごとに返す。
   - 完了条件: 単体テストで、今日と過去は合格、明日は未来として拒否される（今日の日付は引数で与える）。
5. `src/accounts.py`（`DS-FN-LIST-BORROWERS`）: 全アカウントを社員番号の昇順で、名前と社員番号の辞書のリストで返す。
   - 完了条件: 単体テストで並びと件数を確かめる。
6. 同時の貸出・返却: 2 つの接続で同じ備品を続けて貸すと、2 回目は already_lent になる（単体テストで、別々の接続（同じ一時 DB）を使う）。返却も同様に not_lent。
   - 完了条件: テストが通る。

## 4. 備品の一覧・修正・削除（RQ-FT-VIEW-EQUIPMENT-STATUS、RQ-FT-UPDATE-CONFLICT-CHECK、RQ-FT-UPDATE-KEEPS-LENDING、RQ-FT-DELETE-BLOCKED-WHEN-LENT）

7. `src/equipment.py`:
   - `list_equipment`（`DS-FN-LIST-EQUIPMENT`）: 貸出の行を左外部結合し、借りている社員の名前（`accounts` を結合）、貸出日、状態（貸出中か）を返す。管理番号の昇順。
   - `get_equipment`（`DS-FN-GET-EQUIPMENT`）: 更新時刻（`updated_at`）を返す。
   - `update_equipment`（`DS-FN-UPDATE-EQUIPMENT`）: 引数に読み込み時の更新時刻を足す。備品が無い、または更新時刻が違う → 状態 conflict。新しい番号が既にある → 重複（既存の文言）。更新で `updated_at` を新しくする。
   - `delete_equipment`（`DS-FN-DELETE-EQUIPMENT`）: 貸出の行があれば削除せず状態 lent を返す。
   - 完了条件: 単体テストで、一覧の貸出の結合、取得の更新時刻、競合（更新時刻の違い、削除後）の拒否、貸出中の削除の拒否、管理番号の変更で貸出が付いてくることを確かめる。既存のテストは新しい引数に合わせて直す。

## 5. 画面・操作（DS-IF-LENDING-FORM-SCREEN、DS-IF-RETURN-ACTION、DS-IF-EQUIPMENT-STATUS-SCREEN、DS-IF-EQUIPMENT-FORM-SCREEN、DS-IF-EQUIPMENT-DELETE-ACTION）

8. `src/web.py`:
   - `equipment_lend`（`DS-IF-LENDING-FORM-SCREEN`、`/equipment/<管理番号>/lend/`）: 担当者の判定（`_guard_manager`）。GET は画面（`.lending-equipment`、借りる社員の選択肢、既定の貸出日は今日）。POST は検査、`lend_equipment` の結果に応じて転送（ok → `lent`、already_lent → `already_lent`、not_found → `not_found`）。入力のエラーは `.field-error`。
   - `equipment_return`（`DS-IF-RETURN-ACTION`、`/equipment/<管理番号>/return/`、POST）: 担当者の判定。`return_equipment` の結果に応じて転送（ok → `returned`、not_lent → `already_returned`、not_found → `not_found`）。
   - `equipment_status`（`DS-IF-EQUIPMENT-STATUS-SCREEN`）: 一覧に状態、借りている社員、貸出日を出す。担当者には空きの行に「貸出」、貸出中の行に「返却」（`window.confirm`）、全行に「修正」「削除」。知らせの種類を増やす。
   - `equipment_edit`（`DS-IF-EQUIPMENT-FORM-SCREEN`）: 隠し項目 `loaded_updated_at` を持つ。保存で競合なら `.error` に「他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください」を出し、入力値は残す。
   - `equipment_delete`（`DS-IF-EQUIPMENT-DELETE-ACTION`）: 貸出中（`lent`）は `.message` に「この備品は貸出中のため削除できません。先に返却を処理してください」。
9. テンプレート: `src/templates/status.html`（列と操作）、`src/templates/equipment_form.html`（`.error` と隠し項目）、`src/templates/lending_form.html`（新規。`.lending-equipment`、`id_borrower` の select（選択肢は「名前（社員番号）」）、`id_lent_on`、「登録」、貸出状況へ戻るリンク）。
   - 完了条件: 結合テスト（Flask のテストクライアント）で、社員と未ログインの要求が拒否され、既存の画面が壊れないことを確かめる。

## 6. テスト（単体・結合）

10. `tests/` を更新する: 社員番号の 7 桁（`test_validation.py`、`test_accounts.py`）、一覧・取得・修正・削除の変更（`test_equipment.py`）、新しい `tests/test_lending.py`（3 の完了条件）、結合（`test_web.py`）の貸出・返却の経路。
   - 完了条件: `.venv/bin/python -m unittest discover -s tests -t .` の FAIL と ERROR が 0 件。

## 7. E2E テスト（DS-TS-*）

11. `e2e/support.py`、`e2e/test_accounts.py`、`e2e/test_equipment.py` の社員番号を 7 桁にし、非機能のシナリオに 100 件の貸出を足す（`DS-TS-NONFUNCTIONAL-LOAD-E2E`）。
12. 新しい `e2e/test_lending.py` に、8-2 の新しい DS-TS を 1 対 1 で書く（テスト関数名は対応表の `DS-TS` 行と一致させる）。`DS-TS-EMPLOYEE-NUMBER-7-DIGITS-E2E` は `e2e/test_accounts.py` に置く。
    - 同時の場面（`DS-TS-LEND-ALREADY-LENT-E2E`、`DS-TS-RETURN-ALREADY-RETURNED-E2E`、`DS-TS-UPDATE-CONFLICT-E2E`）は、同じ BrowserContext で 2 つのページを開き、古いページから操作する。
    - 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で全件通過。

## 8. 対応表と README

13. `docs/trace_map.md` を更新する（同じ作業の中で）: 新しい `src/lending.py` とその公開関数、`DS-SC-LENDING-TABLE`、`DS-FN-VALIDATE-LENDING-INPUT`、`DS-FN-LIST-BORROWERS`、`DS-IF-LENDING-FORM-SCREEN`、`DS-IF-RETURN-ACTION` の行を足す。新しい `DS-TS` の行を `e2e/test_lending.py` などの関数に結ぶ。既存の `DS-FN-*` の行は、変わらない関数名（`list_equipment` などの既存の関数）のまま残す。
    - 完了条件: `bash scripts/isdd/check.sh --strict` でエラー 0 件・警告 0 件。
14. `README.md` の社員番号（7 桁）、初期ユーザーの手順、貸出・返却の画面の説明を書き換える。
    - 完了条件: README の起動方法と初期ユーザーの手順が 7 桁で読める。

## 9. 完了確認（固定タスク）

15. **対応表更新タスク**: 上の 13 を確かめる。完了条件: `bash scripts/isdd/check.sh --strict` が通る。
16. **起動確認タスク**: `bash run.sh` で起動し、`PORT` で応答することを確かめる（空の DATA_DIR から起動する）。完了条件: エラーなく起動する。
17. **単体・結合テスト全件通過タスク**: 6 の完了条件。
18. **E2E テスト全件通過タスク**: 7 の完了条件。失敗したら修正と再実行を繰り返す。
19. **README 記載タスク**: 14 の完了条件。
20. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。
21. **要件・設計の対応の最終確認**: `rq_ds_link_checker.py`（変更の組み合わせ）と `rq_integrity_checker.py`（変更要件定義書）が合格。

## 追加の決め事（変更要件 1-2 のとおり。エージェントが決めた）

- 貸出の対象の社員は全アカウント（担当者を含む）。
- 貸出日の形式違いと、貸出・返却の成功の知らせは契約に無い文言で、変更要件 1-2 のとおり。
- 既存の 6 桁のアカウントは移行しない（依頼どおり）。
