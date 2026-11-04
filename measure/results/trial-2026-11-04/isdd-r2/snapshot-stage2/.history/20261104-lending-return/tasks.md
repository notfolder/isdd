# 実装タスク: 貸出と返却（段 2）の変更

変更要件定義書: `.history/20261104-lending-return/change_requirements.md`。変更設計書: `.history/20261104-lending-return/change_detail_design.md`。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない。

## 0. 導入確認と登録確認（固定）

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は存在する。`scripts/isdd/completeness.json` の実行形態（server）・認証（true）・外部連携（false）が詳細設計書と一致することを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、completeness.json が詳細設計書と一致する。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-lending-return/` を指すことを確認する。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-lending-return/change_requirements.md .history/20261104-lending-return/change_detail_design.md --base docs/requirements.md` が合格する。

## 1. 修正での貸出の引き継ぎ（RQ-FT-RULE-KEEP-LENDING-ON-UPDATE）

- 1-1. 実装: 既存の DS-FN-UPDATE-EQUIPMENT が貸出の行に触れないことを確かめる。コードの変更は要らない（変えたら、変更設計 0 の前提が崩れるので止めて報告する）。
- 1-2. テスト: `e2e/test_equipment.py` に `TestKeepLendingOnUpdate.test_keep_lending_on_update` を追加する（DS-TS-KEEP-LENDING-ON-UPDATE）。貸出中の備品を修正し、貸出状況の借りている社員の名前と貸出日が変わらないことを確かめる。
- 完了条件: このテストが通る。

## 2. 同時の貸出と返却（RQ-FT-RULE-CONCURRENT-LEND-RETURN）

- 2-1. 実装: 既存の DS-FN-LEND-EQUIPMENT と DS-FN-RETURN-EQUIPMENT（BEGIN IMMEDIATE の直列化）で満たすことを確かめる。コードの変更は要らない。
- 2-2. テスト: `e2e/test_equipment.py` に `TestConcurrentLendReturn.test_concurrent_lend_return` を追加する（DS-TS-CONCURRENT-LEND-RETURN）。2 つの接続（別スレッド）から同時に貸出を送って一方だけが記録されること、同時に返却を送って一方だけが処理されることを確かめる。
- 完了条件: このテストが通る。

## 3. 対応表の登録

- 3-1. `docs/trace_map.md` に DS-TS-KEEP-LENDING-ON-UPDATE と DS-TS-CONCURRENT-LEND-RETURN の行を、それぞれのテスト関数で登録する（isdd-build の実装後の対応表の書式）。
- 完了条件: `bash scripts/isdd/check.sh --strict` で対応表チェックの未登録の警告が出ない。

## 4. 実装完了の確認（固定）

1. **対応表（docs/trace_map.md）更新タスク**: 3-1 のとおり。完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。
2. **起動確認タスク**: `bash setup.sh` のあと `PORT=8796 DATA_DIR=/tmp/isdd-r2-data2 bash run.sh` で起動し、契約の URL が開けること。完了条件: 起動がエラーなく完了する。
3. **単体テスト・結合テスト全件通過タスク**: `python3 -m unittest discover -s tests/unit`。完了条件: FAIL が 0 件。
4. **E2E テスト全件通過タスク**: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`。完了条件: FAIL が 0 件（新しい 2 件を含む）。
5. **README.md 記載タスク**: 変更なし（起動方法と初期ユーザーの手順は既存）。完了条件: 既存の README が起動方法と初期登録を書いていることを確かめる。
6. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。

## 5. 条件付きタスクの扱い

- 外部連携の接続確認・連携ライブラリ・モック: 対象外（外部連携は無い）。
- 正本への反映（docs/requirements.md・docs/detail_design.md・docs/trace_map.md の更新と docs/active_change の削除）: 実装後レビュー（isdd-build の build-review.md）で行う。実装の段階では行わない。
