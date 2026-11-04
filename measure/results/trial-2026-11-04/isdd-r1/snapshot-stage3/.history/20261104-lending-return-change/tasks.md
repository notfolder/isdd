# tasks.md: 貸出と返却（修正時の貸出の引き継ぎ）

対象: `change_requirements.md`、`change_detail_design.md`（変更フロー。`docs/active_change` が指す）。isdd-build が上から順に実行する。

## 実装タスク

### 1. 確認の E2E テストを足す

- 実装する設計 ID: `DS-TS-EDIT-KEEPS-LOAN`（追加）、`DS-FN-UPDATE-EQUIPMENT`（既存。対応を追加）
- 内容: `e2e/test_scenarios.py` に `test_edit_keeps_loan` を足す。担当者が備品 EQ-1 を社員に貸し出し、修正の画面で管理番号を EQ-2 に変えて保存し、EQ-2 の行が「貸出中」で借りている社員の名前と貸出日を保つこと、EQ-1 の行が無いことを確かめる。
- 完了条件: テスト関数が追加され、E2E を回して通る。

### 2. 対応表に行を足す

- 実装する設計 ID: `DS-TS-EDIT-KEEPS-LOAN`
- 内容: `docs/trace_map.md` の `DS-TS` の節に `DS-TS-EDIT-KEEPS-LOAN` → `e2e/test_scenarios.py::test_edit_keeps_loan`（E2E）の行を足す。アプリのコードは変えない（`update_equipment` は既に貸出の付け替えを行い、単体テスト `test_rename_moves_active_loan` で確かめられている）。
- 完了条件: `bash scripts/isdd/check.sh --strict` の対応表チェックが合格する。

### 3. 全件の確認

- 内容: `.venv/bin/python -m pytest tests`（単体）と `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`（E2E）を回す。`bash scripts/isdd/check.sh --strict` を実行する。
- 完了条件: 単体・E2E の失敗が 0 件。check.sh がエラー 0 件・警告 0 件（変更中は「進行中の変更」の行を含む）。

## 変更点の確認

- 完了条件: `docs/active_change` を指す変更の [追加] の要件（`RQ-FT-RULE-KEEP-LOAN-ON-EDIT`、`RQ-TS-EDIT-KEEPS-LOAN`）と設計要素（`DS-TS-EDIT-KEEPS-LOAN`、`DS-FN-UPDATE-EQUIPMENT` の対応）が実装・テストされている。
