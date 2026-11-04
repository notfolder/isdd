# 変更設計書: Num2Word_Base の欠落メソッドの復元

作成日: 2026-11-04（変更フロー。正本 `docs/detail_design.md` は書き換えない）

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計書 `docs/detail_design.md` セクション 1 を参照（Python、標準ライブラリだけを使う）。

## 2. システム構成

変更なし。既存設計書 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし（保存するデータは無い）。インスタンス属性（`is_title`、`precision`、`exclude_title`、`negword`、`pointword`、`errmsg_*`、`cards`、`MAXVAL`）は `__init__` で初期化する（`__init__` は対応表に載せないダンダーメソッドのため、設計 ID は付けない）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。公開インターフェース（`num2words()`）は変えない。

### 4-2. 内部設計

変更なし。各メソッドの責務は既存設計書の基底の DS-FN 系（対応表の行）の責務に従う。

- `__init__`: 属性を既定値で設定し、`setup()` を呼ぶ。数の語彙（`high_numwords`、`mid_numwords`、`low_numwords`）があれば `cards` を作り、`MAXVAL` を最大の桁から求める。
- `to_cardinal_float`: 数値として扱えない値は TypeError。`float2tuple` で整数部と小数部に分け、整数部は `to_cardinal`、小数部は `precision` の桁数で読む。整数部が 0 で負のときは負の語を前に付ける。
- `pluralize`、`set_high_numwords`、`merge`: 派生クラスで実装する拡張点。基底では NotImplementedError。
- `title`: `is_title` が真のときだけ、`exclude_title` に無い語の先頭を大文字にする。
- `to_ordinal_num`: 値をそのまま返す（基底の既定。派生クラスが上書きする）。
- `to_currency`: CURRENCY_FORMS に無い通貨は NotImplementedError。`adjective` が真で CURRENCY_ADJECTIVES があれば接頭辞を付ける。`parse_currency_parts` で整数部・セント部・符号に分け、`_money_verbose` と `_cents_verbose`（`cents` が偽なら `_cents_terse`）で読み、単位語は `pluralize` で選ぶ。

## 5. クラス設計

変更あり（復元のみ。設計要素は足さない。`__init__` はダンダーメソッドのため対応表には載せず、設計 ID も付けない）。

| 区分 | DS-ID | クラス・関数 | 責務（1 文） |
|---|---|---|---|
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-TO-CARDINAL-FLOAT | `Num2Word_Base.to_cardinal_float` | 小数を読み上げ文字列にする |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-MERGE | `Num2Word_Base.merge` | 派生クラス向けの拡張点（未実装） |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-TITLE | `Num2Word_Base.title` | 見出しの形式にする |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-TO-ORDINAL-NUM | `Num2Word_Base.to_ordinal_num` | 序数の数字表記（基底は既定の値をそのまま返す） |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-PLURALIZE | `Num2Word_Base.pluralize` | 派生クラス向けの拡張点（未実装） |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-SET-HIGH-NUMWORDS | `Num2Word_Base.set_high_numwords` | 派生クラス向けの拡張点（未実装） |
| 変更なし（既存・実装を復元） | DS-FN-NUM2WORD-BASE-TO-CURRENCY | `Num2Word_Base.to_currency` | 通貨金額を読み上げ文字列にする |

既存の関数（`setup`、`to_cardinal`、`float2tuple` など）は変更なし。

## 6. エラーハンドリングとセキュリティ設計

- 数値として扱えない値は TypeError（`to_cardinal_float`）。
- 未実装の拡張点は NotImplementedError。
- 未対応の通貨は NotImplementedError。
- 不正な文字列の通貨金額は `parse_currency_parts` の decimal.InvalidOperation をそのまま返す（既存の規則）。

## 7. コード設計

### ファイル一覧（変更あり）

| 区分 | DS-ID | ファイル | 役割 | 実現する設計 ID |
|---|---|---|---|---|
| 変更あり（復元） | DS-MD-BASE | `num2words/base.py` | 基底クラス | 既存の DS-FN 系（TO-CARDINAL-FLOAT、MERGE、TITLE、TO-ORDINAL-NUM、PLURALIZE、SET-HIGH-NUMWORDS、TO-CURRENCY）の復元 |

### 対応表の粒度

`function`（既存の正本と同じ）。

### 依存の規則

無い（既存の正本と同じ）。

### コーディング規約

既存コードのとおり（`tox.ini` の flake8・isort）。コードには要件 ID・設計 ID を書かない。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存の単体テスト（`tests/test_base.py` など）は変更しない。

### 8-2. E2E テストのシナリオ（変更あり）

変更なし。`DS-TS-VERIFY-CARDINAL-READING` が `to_cardinal_float` を通る小数の読み上げを確かめる。

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
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-TO-CARDINAL-FLOAT | RQ-FT-CONVERT-CARDINAL |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-MERGE | RQ-FT-CONVERT-CARDINAL |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-TITLE | RQ-FT-CONVERT-CARDINAL |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-TO-ORDINAL-NUM | RQ-FT-CONVERT-ORDINAL-NUM |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-PLURALIZE | RQ-FT-CONVERT-CURRENCY |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-SET-HIGH-NUMWORDS | RQ-FT-CONVERT-CARDINAL |
| 変更あり（復元） | DS-FN-NUM2WORD-BASE-TO-CURRENCY | RQ-FT-CONVERT-CURRENCY |
| 変更なし（既存） | DS-MD-BASE | RQ-FT-CONVERT-CARDINAL, RQ-FT-CONVERT-ORDINAL-NUM, RQ-FT-CONVERT-CURRENCY |
| 変更なし（既存） | DS-FN-PARSE-CURRENCY-PARTS | RQ-FT-PARSE-CURRENCY-PARTS |
| 変更なし（既存） | DS-MD-CURRENCY | RQ-FT-CONVERT-CURRENCY, RQ-FT-PARSE-CURRENCY-PARTS |
| 変更なし（既存） | DS-IF-PUBLIC-API | RQ-UI-PUBLIC-API, RQ-FT-SELECT-LANGUAGE |
| 変更なし（既存） | DS-TS-VERIFY-CARDINAL-READING | RQ-TS-VERIFY-CARDINAL-READING |

### 11-1. 除外要件

除外要件は無い。
