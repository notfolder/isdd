# 変更設計書: 空でない文字列の判定と IPv4 判定関数の実装し直し

変更要件定義書 `.history/20261104-restore-full-string-and-ip-v4/change_requirements.md` にもとづく。この変更は既存の設計要素を実装し直すもので、設計要素の追加・削除は無い。

区分の注記: この変更では追加・削除の行は無い（既存の設計要素をそのまま実装する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` 第 1 章を引き継ぐ。

## 2. システム構成

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。`SHALLOW_IP_V4_RE`（`string_utils/_regex.py` の既存の正規表現定数）を `is_ip_v4` が使う。正規表現定数は変えない。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。

### 4-2. 内部設計

変更なし（既存の関数の仕様どおり）。

- `is_full_string`（`DS-FN-IS-FULL-STRING`）: 文字列でなければ偽。文字列なら空白を除いて空でないかを返す。`is_string` で型を確かめる。
- `is_ip_v4`（`DS-FN-IS-IP-V4`）: `is_full_string` で空でない文字列を確かめ、`SHALLOW_IP_V4_RE` で形式を確かめ、各区切りが 0〜255 であるかを確かめる。

### 4-2 補足: バッチ設計

変更なし。

## 5. クラス設計

変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし。両関数は例外を送出せず、不正な入力には偽を返す。

## 7. コード設計

変更なし。対応表の粒度は `function`、依存の規則は無い。両関数は既存ファイル `string_utils/validation.py` に置く。

## 8. テスト設計

変更なし。既存の E2E `e2e/test_scenarios.py` の `DS-TS-VERIFY-VALIDATION-BASICS` と `DS-TS-VERIFY-PUBLIC-API-IMPORT` が、この変更の受け入れに使う。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表（変更分）

この変更で実装し直す設計 ID と要件 ID の対応は、正本の `docs/detail_design.md` 第 11 章と同じ（変更の追加・削除は無い）。

| DS-ID | 対応要件ID |
| --- | --- |
| `DS-FN-IS-FULL-STRING` | `RQ-FT-CHECK-STRING-TYPE` |
| `DS-FN-IS-IP-V4` | `RQ-FT-CHECK-IP-ADDRESS` |
| `DS-TS-VERIFY-VALIDATION-BASICS` | `RQ-TS-VERIFY-VALIDATION-BASICS` |
| `DS-TS-VERIFY-PUBLIC-API-IMPORT` | `RQ-TS-VERIFY-PUBLIC-API-IMPORT` |

### 11-1. 除外要件（変更分）

変更なし（除外要件は無い）。
