# tasks.md: 数字列の分割（splitbyx）の復元

変更のディレクトリ: `.history/20261104-restore-splitbyx/`（`docs/active_change` に登録済み）

## 0. 実装開始前の固定タスク

### 0-1. isdd-setup 導入確認

- `scripts/isdd/check.sh` が存在し、`scripts/isdd/VERSION`（v2.2.0）がスキルの版と一致すること。
- 完了条件: `bash scripts/isdd/check.sh` が実行できること。

### 0-2. 進行中の変更の登録確認

- `docs/active_change` の 1 行目が `.history/20261104-restore-splitbyx/` であること。正本は書き換えない。
- 完了条件: `rq_ds_link_checker.py .history/20261104-restore-splitbyx/change_requirements.md .history/20261104-restore-splitbyx/change_detail_design.md --base docs/requirements.md` が問題 0 件。

## 1. 実装タスク

### 1-1. splitbyx の実装

- 対象ファイル: `num2words/utils.py`（既存の `get_digits` は変更しない）。
- 実装する設計 ID: `DS-FN-SPLITBYX`（変更設計書 5 の復元。設計 ID は足さない）。
- 署名とドキュメント文字列は REQUEST.md の PRD のとおり。
- 完了条件: `python -c "import num2words"` が例外なく終わること。
- 検証: `.venv/bin/python -m pytest tests -q` で既存の単体テスト（`tests/test_utils.py` を含む）が通ること。

### 1-2. 対応表の確認

- `docs/trace_map.md` に `DS-FN-SPLITBYX` の行が既にあることを確かめる（新しい行は足さない）。
- 完了条件: `bash scripts/isdd/check.sh --strict` の対応表チェックがエラー 0・警告 0。

## 2. 実装完了確認の固定タスク

1. E2E の結果: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行し、`e2e/results/e2e.xml` を更新する。
2. 受け入れ判定: `RQ-FT-CONVERT-CARDINAL` が「実装済み」と判定されること。
3. 正本反映タスク（isdd-build の実装後レビュー）: 正本に `[追加]`・`[削除]` の区分は無い（変更は復元のみ）。`docs/active_change` を消す。
4. 全変更点の確認: 変更点は `num2words/utils.py` の `splitbyx` の追加だけであること。
