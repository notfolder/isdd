# 変更設計書: 通貨金額の分解（parse_currency_parts）の復元

作成日: 2026-11-04（変更フロー。正本 `docs/detail_design.md` は書き換えない）

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計書 `docs/detail_design.md` セクション 1 を参照（Python、標準ライブラリの decimal を使う。新しい依存は足さない）。

## 2. システム構成

変更なし。既存設計書 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし（DB は無く、保存するデータも無い）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし（公開インターフェースは追加しない。`parse_currency_parts` は `num2words/currency.py` の補助関数で、`DS-IF-PUBLIC-API` は変えない）。

### 4-2. 内部設計

処理の規則は次のとおり（要件定義書 RQ-FT-PARSE-CURRENCY-PARTS の 3-2 の表と同じ）。

```mermaid
flowchart TD
    A[value を受け取る] --> B{int か}
    B -->|はい・is_int_with_cents=True| C[セントとして分ける: 絶対値 // 100, 絶対値 % 100]
    B -->|はい・False| D[整数部 = 絶対値、セント部 = 0]
    B -->|いいえ| E{str か}
    E -->|はい| F[Decimal にする]
    E -->|いいえ・float| G[str を経由して Decimal にする]
    F --> H[小数点以下 2 桁に ROUND_HALF_UP で丸める]
    G --> H
    H --> I[符号 = 値 < 0、整数部とセント部を絶対値から得る]
    C --> R[(整数部, セント部, 符号) を返す]
    D --> R
    I --> R
```

各処理の役割: `DS-FN-PARSE-CURRENCY-PARTS` が上の全体を行う。バッチは無い。

## 5. クラス設計

変更あり（追加のみ）。

| 区分 | DS-ID | クラス・関数 | 責務（1 文） |
|---|---|---|---|
| [追加] | DS-FN-PARSE-CURRENCY-PARTS | `num2words/currency.py::parse_currency_parts` | 通貨金額を整数部・セント部・符号の 3 要素に分解する |

クラス・既存の関数（`prefix_currency`）は変更なし。

## 6. エラーハンドリングとセキュリティ設計

### エラーハンドリング

| 想定エラー | 扱い | 利用者への見え方 | ログ | 処理 |
|---|---|---|---|---|
| 不正な文字列（数値として読めない） | `Decimal` の変換例外をそのまま返す | decimal.InvalidOperation | 無し | 中止 |

### 認証・認可・監査ログ

変更なし（認証・認可・監査ログは無い）。

### その他のセキュリティ対策

変更なし。

## 7. コード設計

### ファイル一覧（変更あり）

| 区分 | DS-ID | ファイル | 役割 | 実現する設計 ID |
|---|---|---|---|---|
| [追加] | DS-MD-CURRENCY | `num2words/currency.py` | 通貨名の補助と、通貨金額の分解 | [追加] DS-FN-PARSE-CURRENCY-PARTS（既存: DS-FN-PREFIX-CURRENCY） |

### 対応表の粒度

`function`（既存の正本と同じ。isdd-setup の `--granularity function`）。

### 依存の規則

無い（既存の正本と同じ。新しい依存は足さない）。

### コーディング規約

既存コードのとおり（`tox.ini` の flake8・isort）。コードには要件 ID・設計 ID を書かない。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存の単体テスト（`tests/`）は変更しない。

### 8-2. E2E テストのシナリオ（変更あり）

| 区分 | DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] | DS-TS-VERIFY-PARSE-CURRENCY-PARTS | 分解の規則を確かめる | num2words を import できる | `parse_currency_parts` に、int（セント扱い・整数部扱い）、負の int、str、Decimal、float を渡す | 規則どおりの `(整数部, セント部, 符号)`。不正な str は decimal.InvalidOperation |

### 8-3. E2E の実行手段

変更なし（pytest。E2E は `e2e/` に置く）。

### 8-4. E2E の実行コマンドと運用

変更なし（`python3 -m pytest e2e --junitxml=e2e/results/e2e.xml`）。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計書 `docs/detail_design.md` 第 10 章の「既知の欠落」は、この変更で解消する（実装後に isdd-build が正本から削除する）。

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [追加] | DS-FN-PARSE-CURRENCY-PARTS | RQ-FT-PARSE-CURRENCY-PARTS |
| [追加] | DS-TS-VERIFY-PARSE-CURRENCY-PARTS | RQ-TS-VERIFY-PARSE-CURRENCY-PARTS |
| 変更なし（既存） | DS-MD-CURRENCY | RQ-FT-CONVERT-CURRENCY |
| 変更なし（既存） | DS-FN-PREFIX-CURRENCY | RQ-FT-CONVERT-CURRENCY |
| 変更なし（既存） | DS-IF-PUBLIC-API | RQ-UI-PUBLIC-API, RQ-FT-SELECT-LANGUAGE |

### 11-1. 除外要件

除外要件は無い。
