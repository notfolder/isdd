# tasks.md: アカウントの管理（備品の登録への入口の文言）

対象: `change_requirements.md`、`change_detail_design.md`（変更フロー。`docs/active_change` が指す）。isdd-build が上から順に実行する。

## 実装タスク

### 1. 貸出状況の画面の文言を直す

- 実装する設計 ID: `DS-MD-TPL-STATUS`（既存。`docs/trace_map.md` で `app/templates/status.html` に対応）
- 内容: `app/templates/status.html` の担当者向けリンクの文言を「備品の登録」から「備品を登録」にする。リンクの行き先は変えない。
- 完了条件: 担当者でログインした貸出状況の画面に、リンク「備品を登録」が出る。

### 2. E2E の確認を足す

- 実装する設計 ID: `DS-TS-ROLE-CHECK`（既存。手順を足す）
- 内容: `e2e/test_scenarios.py::test_role_check` の末尾で、100001 でログインし、貸出状況の画面にリンク「備品を登録」が 1 件出ることを確かめる。社員の画面で「備品の登録」が出ないことは既存の確認のまま直す。
- 完了条件: E2E の `test_role_check` が通る。

### 3. 全件の確認

- 内容: `.venv/bin/python -m pytest tests`（単体）と `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`（E2E）を回す。`bash scripts/isdd/check.sh --strict` を実行する。
- 完了条件: 単体・E2E の失敗が 0 件。check.sh がエラー 0 件・警告 0 件（変更中は「進行中の変更」の行を含む）。

## 変更点の確認

- 完了条件: `docs/active_change` を指す変更の文言の修正（`change_requirements.md` の 3 章）が、コードと E2E に反映されている。
