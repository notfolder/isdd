# tasks.md: Num2Word_Base の欠落メソッドの復元

変更のディレクトリ: `.history/20261104-restore-base-methods/`（`docs/active_change` に登録済み）

## 0. 実装開始前の固定タスク

### 0-1. 進行中の変更の登録確認

- `docs/active_change` の 1 行目が `.history/20261104-restore-base-methods/` であること。正本は書き換えない。

## 1. 実装タスク

### 1-1. Num2Word_Base の 8 個の復元

- 対象ファイル: `num2words/base.py`（既存の関数は変更しない）。
- 実装する設計 ID: 変更設計書 5 のとおり（設計 ID は足さない）。
- 署名とドキュメント文字列は REQUEST.md の PRD のとおり。
- 完了条件: `python -c "import num2words"` が例外なく終わること。`tests/test_base.py` が通ること。

### 1-2. 対応表の確認

- `docs/trace_map.md` に 7 個の基底の DS-FN 系 の行が既にあることを確かめる。
- `__init__` は対応表に載せない（ダンダーメソッド）。行を足さない。
- 完了条件: `bash scripts/isdd/check.sh` の対応表チェックがエラー 0。

## 2. 実装完了確認の固定タスク

1. E2E: `python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。
2. 既存の全単体テスト: `python -m pytest tests -q` を実行する。
3. 正本反映タスク（isdd-build の実装後レビュー）: 正本の書き換えは無し（変更は復元のみ）。`docs/active_change` を消す。
4. 全変更点の確認: 変更点は `num2words/base.py` の 8 個の追加だけであること。
