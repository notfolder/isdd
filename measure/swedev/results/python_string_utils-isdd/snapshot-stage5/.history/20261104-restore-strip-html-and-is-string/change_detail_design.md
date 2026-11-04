# 変更設計書: HTML タグの除去（strip_html）、文字列型の判定（is_string）、InvalidInputError の実装し直し

変更要件定義書 `.history/20261104-restore-strip-html-and-is-string/change_requirements.md` にもとづく。この変更は既存の設計要素を実装し直すもので、設計要素の追加・削除は無い。

区分の注記: この変更では追加・削除の行は無い（既存の設計要素をそのまま実装する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` 第 1 章を引き継ぐ。

## 2. システム構成

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。`strip_html` は既存の正規表現定数 `HTML_RE`（タグと中身）と `HTML_TAG_ONLY_RE`（タグだけ）を使う。定数は変えない。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。

### 4-2. 内部設計

変更なし（既存の関数の仕様どおり）。

- `is_string`（`DS-FN-IS-STRING`）: 引数の型が `str`（その派生を含む）なら真、それ以外は偽を返す。例外は送出しない。空文字も真とする。
- `strip_html`（`DS-FN-STRIP-HTML`）: 入力が文字列でなければ `is_string` の判定を経て `InvalidInputError` を送出する。`keep_tag_content` が偽なら `HTML_RE` で一致する部分（タグと中身）を空文字に置き換える。真なら `HTML_TAG_ONLY_RE` で一致する部分（タグだけ）を空文字に置き換える。置き換えた文字列を返す。

### 4-2 補足: バッチ設計

バッチは無い。

## 5. クラス設計

### 変更なし（クラス設計の要素は既存のまま）

- `InvalidInputError`（`DS-CL-INVALID-INPUT-ERROR`）: 責務は既存のまま「文字列以外の入力を表す例外を作る」。`__init__(input_data)` は次のとおり実装する。受け取った値の型名を取り、期待する型 `str` と実際の型名を含むメッセージを作り、`TypeError` の初期化に渡す。送出時の例外の種類と、利用者への見え方（`TypeError` の派生）は変えない。

クラス図は既存の図（`docs/detail_design.md` 第 5 章）のとおり。

### システム内メッセージ一覧と役割

変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし。`strip_html` は文字列以外に `InvalidInputError` を送出する（既存の表どおり）。`is_string` は例外を送出しない。

## 7. コード設計

変更なし。対応表の粒度は `function`、依存の規則は無い。

- `strip_html` は既存ファイル `string_utils/manipulation.py` に置く。依存は `string_utils/errors.py::InvalidInputError` と `string_utils/validation.py::is_string`（既存の依存の向き: 加工モジュールは判定モジュールに依存してよい）。
- `is_string` は既存ファイル `string_utils/validation.py` に置く。
- `InvalidInputError.__init__` は既存ファイル `string_utils/errors.py` に置く。

## 8. テスト設計

変更なし。既存の E2E `e2e/test_scenarios.py` の `test_validation_basics`（`DS-TS-VERIFY-VALIDATION-BASICS`）、`test_text_transform`（`DS-TS-VERIFY-TEXT-TRANSFORM`）、`test_public_api_import`（`DS-TS-VERIFY-PUBLIC-API-IMPORT`）が、この変更の受け入れに使う。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表（変更分）

この変更で実装し直す設計 ID と要件 ID の対応は、正本の `docs/detail_design.md` 第 11 章と同じ（変更の追加・削除は無い）。

| DS-ID | 対応要件ID |
| --- | --- |
| `DS-FN-STRIP-HTML` | `RQ-FT-STRIP-HTML` |
| `DS-FN-IS-STRING` | `RQ-FT-CHECK-STRING-TYPE` |
| `DS-CL-INVALID-INPUT-ERROR` | `RQ-FT-REJECT-NON-STRING-INPUT` |
| `DS-TS-VERIFY-PUBLIC-API-IMPORT` | `RQ-TS-VERIFY-PUBLIC-API-IMPORT` |
| `DS-TS-VERIFY-VALIDATION-BASICS` | `RQ-TS-VERIFY-VALIDATION-BASICS` |
| `DS-TS-VERIFY-TEXT-TRANSFORM` | `RQ-TS-VERIFY-TEXT-TRANSFORM` |

### 11-1. 除外要件（変更分）

変更なし（除外要件は無い）。
