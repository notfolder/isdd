# 実装タスク: アカウントの管理（段 3）の変更

変更要件定義書: `.history/20261104-account-management/change_requirements.md`。変更設計書: `.history/20261104-account-management/change_detail_design.md`。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない。

## 0. 導入確認と登録確認（固定）

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は存在する。`scripts/isdd/completeness.json` の実行形態（server）・認証（true）・外部連携（false）が詳細設計書と一致することを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、completeness.json が詳細設計書と一致する。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-account-management/` を指すことを確認する。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-account-management/change_requirements.md .history/20261104-account-management/change_detail_design.md --base docs/requirements.md` が合格する。

## 1. 受け入れテストの追加（RQ-TS-ACCESS-ENDS-ON-RESET-AND-DELETE、変更設計 0 と 8-2）

- 1-1. テスト: `e2e/test_accounts.py::TestManageAccounts.test_access_ends_on_reset_and_delete` を追加する（DS-TS-ACCESS-ENDS-ON-RESET-AND-DELETE）。社員 A のパスワードを再設定し古いパスワードでログインできないこと、社員 B を削除しログインできず貸出の登録の社員の一覧に出ないことを確かめる。
- 完了条件: このテストが通る。コードの変更は要らない（通らなければ止めて報告する）。

## 1-2. 担当者の画面の入口の文言（変更設計 0。ID は増えない）

- 1-2-1. 実装: `app/templates.py` のヘッダーで、担当者の入口の文言を「備品の登録」から「備品を登録」に直す（リンク先 `/equipment/new/` は変えない）。
- 1-2-2. テスト: `e2e/test_accounts.py::TestManageAccounts.test_manage_manager_role` の先頭に、担当者で `/` を開き「備品を登録」が出ることの確認を足す。
- 完了条件: このテストが通る。

## 2. 既存の機能の確認（変更なし）

- 2-1. アカウントの一覧、担当者の付け外し、パスワード再設定、削除、借りている社員の削除の禁止、担当者 0 人の禁止は既存の実装で満たすことを、既存の E2E（`e2e/test_accounts.py`）と単体テスト・結合テストで確かめる。コードの変更は要らない。
- 完了条件: 既存テストが通る。

## 3. 対応表の登録

- 3-1. 対応表（`docs/trace_map.md`）に DS-TS-ACCESS-ENDS-ON-RESET-AND-DELETE の行を、`e2e/test_accounts.py::TestManageAccounts.test_access_ends_on_reset_and_delete` で登録する（isdd-build の実装後の対応表の書式）。
- 完了条件: `bash scripts/isdd/check.sh --strict` で対応表チェックの未登録の警告が出ない。

## 4. 実装完了の確認（固定）

1. **対応表（docs/trace_map.md）更新タスク**: 3-1 のとおり。完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。
2. **起動確認タスク**: `bash setup.sh` のあと `PORT=8797 DATA_DIR=/private/tmp/claude-501/-Users-notfolder-Documents-isdd/49090259-0412-4808-99fc-5bedf53f2f86/scratchpad/work/isdd-r2-data3 bash run.sh` で起動し、契約の URL と要素を確かめる。完了条件: 起動がエラーなく完了し、契約の画面と要素が出る。
3. **単体テスト・結合テスト全件通過タスク**: `python3 -m unittest discover -s tests/unit`。完了条件: FAIL が 0 件。
4. **E2E テスト全件通過タスク**: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`。完了条件: FAIL が 0 件。
5. **README.md 記載タスク**: 変更なし（起動方法と初期登録の手順は既存）。完了条件: 既存の README が起動方法と初期登録を書いていることを確かめる。
6. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。

## 5. 条件付きタスクの扱い

- 外部連携の接続確認・連携ライブラリ・モック: 対象外（外部連携は無い）。
- 正本への反映（docs/requirements.md・docs/detail_design.md・docs/trace_map.md の更新と docs/active_change の削除）: 実装後レビュー（isdd-build の build-review.md）で行う。実装の段階では行わない。
