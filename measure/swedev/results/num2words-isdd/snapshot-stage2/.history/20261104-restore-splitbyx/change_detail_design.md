# 変更設計書: 数字列の分割（splitbyx）の復元

作成日: 2026-11-04（変更フロー。正本 `docs/detail_design.md` は書き換えない）

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計書 `docs/detail_design.md` セクション 1 を参照（Python、標準ライブラリだけを使う）。

## 2. システム構成

変更なし。既存設計書 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし（保存するデータは無い）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし（公開インターフェースは変えない。`splitbyx` は `num2words/utils.py` の補助関数で、`DS-IF-PUBLIC-API` の対象ではない）。

### 4-2. 内部設計

変更なし。既存設計書 `DS-FN-SPLITBYX` の責務（数字列を x 桁ごとに分ける。先頭に x 桁未満の端数を先に出し、その後は x 桁ずつ。format_int が真なら整数、偽なら文字列で出す）に従う。

## 5. クラス設計

変更あり（復元のみ。設計要素は足さない）。

| 区分 | DS-ID | クラス・関数 | 責務（1 文） |
|---|---|---|---|
| 変更なし（既存・実装を復元） | DS-FN-SPLITBYX | `num2words/utils.py::splitbyx` | 数字列を x 桁ごとに分ける |

`DS-FN-GET-DIGITS` と既存の関数は変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし。

## 7. コード設計

### ファイル一覧（変更あり）

| 区分 | DS-ID | ファイル | 役割 | 実現する設計 ID |
|---|---|---|---|---|
| 変更なし（既存・実装を復元） | DS-MD-UTILS | `num2words/utils.py` | 数字列の分割などの補助関数 | DS-FN-SPLITBYX（復元）、DS-FN-GET-DIGITS（既存） |

### 対応表の粒度

`function`（既存の正本と同じ。isdd-setup の `--granularity function`）。

### 依存の規則

無い（既存の正本と同じ）。

### コーディング規約

既存コードのとおり（`tox.ini` の flake8・isort）。コードには要件 ID・設計 ID を書かない。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存の単体テスト（`tests/test_utils.py`）は変更しない。

### 8-2. E2E テストのシナリオ（変更あり）

変更なし。`DS-TS-VERIFY-CARDINAL-READING` が `DS-FN-SPLITBYX` を通る基数の読み上げを確かめる。

### 8-3. E2E の実行手段

変更なし（pytest。E2E は `e2e/` に置く）。

### 8-4. E2E の実行コマンドと運用

変更なし（`python -m pytest e2e --junitxml=e2e/results/e2e.xml`）。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| 変更なし（既存・実装を復元） | DS-FN-SPLITBYX | RQ-FT-CONVERT-CARDINAL |
| 変更なし（既存） | DS-FN-GET-DIGITS | RQ-FT-CONVERT-CARDINAL |
| 変更なし（既存） | DS-MD-UTILS | RQ-FT-CONVERT-CARDINAL |
| 変更なし（既存） | DS-IF-PUBLIC-API | RQ-UI-PUBLIC-API, RQ-FT-SELECT-LANGUAGE |
| 変更なし（既存） | DS-TS-VERIFY-CARDINAL-READING | RQ-TS-VERIFY-CARDINAL-READING |

### 11-1. 除外要件

除外要件は無い。
