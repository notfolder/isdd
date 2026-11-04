# tasks.md: 通貨金額の分解（parse_currency_parts）の復元

変更のディレクトリ: `.history/20261104-parse-currency-parts/`（`docs/active_change` に登録済み）

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が存在すること（isdd-setup 導入済み）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（library）・認証（なし）・外部連携（なし）が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261104-parse-currency-parts/` であること。正本（`docs/requirements.md`・`docs/detail_design.md`）は書き換えない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-parse-currency-parts/change_requirements.md .history/20261104-parse-currency-parts/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 実装タスク

### 1-1. parse_currency_parts の実装

- 対象ファイル: `num2words/currency.py`（既存の `prefix_currency` は変更しない）。
- 実装する設計 ID: `DS-FN-PARSE-CURRENCY-PARTS`（change_detail_design.md 4-2 の処理の規則に従う）。
- 関数の署名とドキュメント文字列は REQUEST.md の PRD のとおり。`decimal` の `Decimal` と `ROUND_HALF_UP` を使う（既に import 済み）。
- 完了条件: `python3 -c "import num2words"` が例外なく終わること。
- 検証: `python3 -m pytest tests -q` を実行し、既存のテストの結果を確かめる（既存の失敗が無くなること。失敗が残るなら原因を報告）。

### 1-2. E2E テストの作成

- 対象: `e2e/test_parse_currency_parts.py`（新規。`tests/` は変更しない）。
- 実装する設計 ID: `DS-TS-VERIFY-PARSE-CURRENCY-PARTS`（テスト関数 `e2e/test_parse_currency_parts.py::test_verify_parse_currency_parts` の形で対応表に結ぶ）。
- 内容: int（セント扱い・整数部扱い）、負の int、str、Decimal、float を渡し、`(整数部, セント部, 符号)` を確かめる。不正な str は `decimal.InvalidOperation` を確かめる。
- 完了条件: `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件合格し、`e2e/results/e2e.xml` ができること。

### 1-3. 対応表の更新

- `docs/trace_map.md` に次の行を足す（書式は trace-map-rules.md）。
  - `DS-FN-PARSE-CURRENCY-PARTS` | `num2words/currency.py::parse_currency_parts` | メソッドではなくモジュール関数
  - `DS-TS-VERIFY-PARSE-CURRENCY-PARTS` | `e2e/test_parse_currency_parts.py::test_verify_parse_currency_parts`
- 完了条件: `bash scripts/isdd/check.sh --strict` でエラー 0・警告 0。

## 2. 実装完了確認の固定タスク

1. **対応表（docs/trace_map.md）更新タスク**
   - 上の 1-3 で登録済みであること。
   - 完了条件: `bash scripts/isdd/check.sh --strict` が合格（エラー・警告 0）。
2. **受け入れ判定タスク**
   - `e2e/results/e2e.xml` の結果で `RQ-FT-PARSE-CURRENCY-PARTS` が「実装済み」と判定されること（受け入れ判定の表を応答に載せる）。
3. **正本反映タスク（isdd-build の実装後レビュー）**
   - 変更設計書の内容を `docs/requirements.md`・`docs/detail_design.md` に反映し、`docs/active_change` を消す。
   - 完了条件: `docs/active_change` が無い。正本の 2 文書の中に `[追加]`・`[削除]` の区分が残らない。
4. **全変更点の確認タスク**
   - 変更設計書の [追加] の設計 ID（`DS-FN-PARSE-CURRENCY-PARTS`・`DS-TS-VERIFY-PARSE-CURRENCY-PARTS`）が、コードと対応表にあること。既存の `prefix_currency` と他の関数が変わっていないこと（`git diff` 相当で確かめる。git の履歴が無い場合は、変更前との差分が `num2words/currency.py` の追加だけであることを確かめる）。
   - 完了条件: 変更点の一覧と対応表の突き合わせ結果を報告する。
