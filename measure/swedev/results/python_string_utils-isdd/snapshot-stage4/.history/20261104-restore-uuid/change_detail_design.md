# 変更設計書: UUID の判定（is_uuid）と生成（uuid）の実装し直し

変更要件定義書 `.history/20261104-restore-uuid/change_requirements.md` にもとづく。この変更は既存の設計要素を実装し直すもので、設計要素の追加・削除は無い。

区分の注記: この変更では追加・削除の行は無い（既存の設計要素をそのまま実装する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` 第 1 章を引き継ぐ。

## 2. システム構成

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。UUID の形式判定は既存の正規表現定数 `UUID_RE`（ハイフンあり）と `UUID_HEX_OK_RE`（ハイフンの有無を許す）を使う。定数は変えない。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。

### 4-2. 内部設計

変更なし（既存の関数の仕様どおり）。

- `is_uuid`（`DS-FN-IS-UUID`）: 入力が文字列でなければ文字列に変換する。`allow_hex` が偽なら `UUID_RE` で、真なら `UUID_HEX_OK_RE` で判定し、一致すれば真、しなければ偽を返す。
- `uuid`（`DS-FN-UUID`）: 標準ライブラリの `uuid4()` で UUID v4 を生成する。`as_hex` が真なら `.hex`（ハイフンなしの 16 進）、偽なら `str()`（標準表記）の文字列を返す。

### 4-2 補足: バッチ設計

変更なし。

## 5. クラス設計

変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし。判定関数は不正な入力に対して例外を送出せず偽を返す。

## 7. コード設計

変更なし。対応表の粒度は `function`、依存の規則は無い。`is_uuid` は既存ファイル `string_utils/validation.py`、`uuid` は既存ファイル `string_utils/generation.py` に置く。

## 8. テスト設計

変更なし。既存の E2E `e2e/test_scenarios.py::test_validation_basics`（`DS-TS-VERIFY-VALIDATION-BASICS`）と `test_generation`（`DS-TS-VERIFY-GENERATION`）が、この変更の受け入れに使う。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表（変更分）

この変更で実装し直す設計 ID と要件 ID の対応は、正本の `docs/detail_design.md` 第 11 章と同じ（変更の追加・削除は無い）。

| DS-ID | 対応要件ID |
| --- | --- |
| `DS-FN-IS-UUID` | `RQ-FT-CHECK-UUID` |
| `DS-FN-UUID` | `RQ-FT-GENERATE-UUID` |
| `DS-TS-VERIFY-VALIDATION-BASICS` | `RQ-TS-VERIFY-VALIDATION-BASICS` |
| `DS-TS-VERIFY-GENERATION` | `RQ-TS-VERIFY-GENERATION` |

### 11-1. 除外要件（変更分）

変更なし（除外要件は無い）。
