# 変更設計書: ローマ数字の変換（整数からローマ数字）の実装し直し

変更要件定義書 `.history/20261104-restore-roman-encode/change_requirements.md` にもとづく。この変更は既存の設計要素を実装し直すもので、設計要素の追加・削除は無い。

区分の注記: この変更では追加・削除の行は無い（既存の設計要素をそのまま実装する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` 第 1 章を引き継ぐ。

## 2. システム構成

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。変換クラス `__RomanNumbers` の既存の対応表 `__mappings`（単位・十・百・千の記号）を使う。対応表は変えない。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。

### 4-2. 内部設計

変更なし（既存の関数・メソッドの仕様どおり）。

- `roman_encode`（`DS-FN-ROMAN-ENCODE`）: 変換クラス `__RomanNumbers.encode` を呼んで結果を返す。
- `__RomanNumbers.encode`（変換クラスの内部。DS-ID なし。`docs/detail_design.md` の変換クラスの図と `decode` に対応）: 入力が文字列なら `is_integer` で整数の形式を確かめて整数にする。入力が整数（真偽値を除く）ならそのまま使う。それ以外は `ValueError`。1〜3999 の範囲外は `ValueError`。千・百・十・一の各桁を、既存の `__encode_digit` で記号にして、大きい桁から順に連結する。

### 4-2 補足: バッチ設計

変更なし。

## 5. クラス設計

変更なし。`__RomanNumbers` の `encode` を実装し直す（`decode` と `__mappings` は変えない）。

## 6. エラーハンドリングとセキュリティ設計

変更なし。不正な入力（非整数、真偽値、範囲外）は `ValueError` を送出する。

## 7. コード設計

変更なし。対応表の粒度は `function`、依存の規則は無い。`roman_encode` は既存ファイル `string_utils/manipulation.py` に置く。

## 8. テスト設計

変更なし。既存の E2E `e2e/test_scenarios.py::test_compress_and_roman`（`DS-TS-VERIFY-COMPRESS-AND-ROMAN`）が、この変更の受け入れに使う。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表（変更分）

この変更で実装し直す設計 ID と要件 ID の対応は、正本の `docs/detail_design.md` 第 11 章と同じ（変更の追加・削除は無い）。

| DS-ID | 対応要件ID |
| --- | --- |
| `DS-FN-ROMAN-ENCODE` | `RQ-FT-ROMAN-NUMERAL` |
| `DS-TS-VERIFY-COMPRESS-AND-ROMAN` | `RQ-TS-VERIFY-COMPRESS-AND-ROMAN` |

### 11-1. 除外要件（変更分）

変更なし（除外要件は無い）。
