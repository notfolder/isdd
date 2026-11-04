# タスク: HTML タグの除去（strip_html）、文字列型の判定（is_string）、InvalidInputError の実装し直し

変更要件定義書と変更設計書にもとづく。上から順に実行する。

## 0. 実装開始前の固定タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし（登録の確認）
- 内容: `docs/active_change` の 1 行目が `.history/20261104-restore-strip-html-and-is-string/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `docs/active_change` の指す先が正しいこと。

## 1. 実装タスク

### 1. InvalidInputError の初期化の実装

- 対象の設計 ID: `DS-CL-INVALID-INPUT-ERROR`
- 内容: `string_utils/errors.py` の `InvalidInputError.__init__(self, input_data: Any)` を実装する。受け取った値の型名を含み、期待する型が `str` であることを示すメッセージを作り、`TypeError` の初期化に渡す。
- 完了条件: `InvalidInputError(1)` の文字列表現に `str` と `int` の両方が含まれる。

### 2. 文字列型の判定関数の実装

- 対象の設計 ID: `DS-FN-IS-STRING`
- 内容: `string_utils/validation.py` に `is_string(obj: Any) -> bool` を実装する（変更設計書 4-2 の仕様どおり）。
- 完了条件: 文字列（空文字を含む）は真、それ以外（`None`、数値、バイト列）は偽。例外を送出しない。

### 3. HTML タグ除去関数の実装

- 対象の設計 ID: `DS-FN-STRIP-HTML`
- 内容: `string_utils/manipulation.py` に `strip_html(input_string: str, keep_tag_content: bool=False) -> str` を実装する（変更設計書 4-2 の仕様どおり。`HTML_RE` と `HTML_TAG_ONLY_RE` を使う）。文字列以外は `InvalidInputError`。
- 完了条件: 中身を残さない既定では、タグと中身を除いた文字列を返す。`keep_tag_content=True` では、タグだけを除き中身を残す。文字列以外は `InvalidInputError`。

### 4. 単体テスト・結合テスト全件通過タスク

- 対象の設計 ID: `DS-FN-IS-STRING`、`DS-FN-STRIP-HTML`、`DS-CL-INVALID-INPUT-ERROR`、既存の全関数
- 内容: 作業ディレクトリの `.venv` で `python -m pytest tests` を実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 5. E2E テストの実行

- 対象の設計 ID: `DS-TS-VERIFY-PUBLIC-API-IMPORT`、`DS-TS-VERIFY-VALIDATION-BASICS`、`DS-TS-VERIFY-TEXT-TRANSFORM`
- 内容: `python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。
- 完了条件: FAIL と ERROR が 0 件。

### 6. 対応表（docs/trace_map.md）の確認

- 対象の設計 ID: `DS-FN-IS-STRING`、`DS-FN-STRIP-HTML`、`DS-CL-INVALID-INPUT-ERROR`
- 内容: 既存の行が `string_utils/validation.py::is_string`、`string_utils/manipulation.py::strip_html`、`string_utils/errors.py::InvalidInputError` を指していることを確かめる（行は既にある）。
- 完了条件: `bash scripts/isdd/check.sh` がエラー 0 件。

### 7. 実装後レビュー

- 内容: `isdd-build` の実装後レビューで変更を正本へ反映する（正本の内容は既に一致しているため、確認と `docs/active_change` の削除）。
