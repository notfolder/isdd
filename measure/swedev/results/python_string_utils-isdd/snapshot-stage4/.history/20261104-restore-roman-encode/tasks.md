# タスク: ローマ数字の変換（整数からローマ数字）の実装し直し

変更要件定義書と変更設計書にもとづく。上から順に実行する。

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、`scripts/isdd/completeness.json` の実行形態（library）・認証（なし）・外部連携（なし）が詳細設計書と一致していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし（登録の確認）
- 内容: `docs/active_change` の 1 行目が `.history/20261104-restore-roman-encode/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `docs/active_change` の指す先が正しいこと。

## 1. 実装タスク

### 1. 変換クラスの整数からローマ数字への変換の実装

- 対象の設計 ID: `DS-FN-ROMAN-ENCODE`（変換クラス `__RomanNumbers.encode` を含む。DS-ID なし）
- 内容: `string_utils/manipulation.py` の `__RomanNumbers` に `encode(cls, input_number: Union[str, int]) -> str` を実装する（既存の `__mappings` と `__encode_digit` を使う。`decode` は変えない）。
- 完了条件: 整数と整数の文字列を 1〜3999 で変換し、範囲外・非整数・真偽値は `ValueError`。

### 2. roman_encode の実装

- 対象の設計 ID: `DS-FN-ROMAN-ENCODE`
- 内容: `string_utils/manipulation.py` に `roman_encode(input_number: Union[str, int]) -> str` を実装する（`__RomanNumbers.encode` を呼ぶ。`roman_decode` と同じ形）。
- 完了条件: `roman_encode(37) == 'XXXVIII'`、`roman_encode('2020') == 'MMXX'`。

### 3. 単体テスト・結合テスト全件通過タスク

- 対象の設計 ID: `DS-FN-ROMAN-ENCODE` と既存の全関数
- 内容: 作業ディレクトリの `.venv` で `python -m pytest tests --noconftest` を実行する（ルートの conftest.py は `hunter` を要求するが、この依頼の環境には入っていないため外す）。
- 完了条件: FAIL と ERROR が 0 件。

### 4. E2E テストの実行

- 対象の設計 ID: `DS-TS-VERIFY-COMPRESS-AND-ROMAN`
- 内容: `python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 5. 対応表（docs/trace_map.md）の確認

- 対象の設計 ID: `DS-FN-ROMAN-ENCODE`
- 内容: 既存の行が `string_utils/manipulation.py::roman_encode` を指していることを確かめる（行は既にある）。
- 完了条件: `bash scripts/isdd/check.sh` がエラー 0 件。

### 6. 実装後レビュー

- 内容: `isdd-build` の実装後レビューで変更を正本へ反映する（正本の内容は既に一致しているため、確認と `docs/active_change` の削除）。
