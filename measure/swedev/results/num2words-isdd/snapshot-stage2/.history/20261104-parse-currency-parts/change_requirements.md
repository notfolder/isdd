# 変更要件定義書: 通貨金額の分解（parse_currency_parts）の復元

作成日: 2026-11-04（変更フロー。正本 `docs/requirements.md` は書き換えない。実装後に isdd-build が反映する）

## 1. 目的・前提

### 目的

`num2words/currency.py` の `parse_currency_parts` が現在のコードに無く、パッケージを import できない。この関数を、依頼の文章（REQUEST.md の PRD）のシグネチャとドキュメント文字列のとおりに追加し、数値・文字列・Decimal の通貨金額を「整数部・セント部・符号」に分解できるようにする。既存の機能の挙動は変えない。

### 変更の背景

正本の `docs/detail_design.md` 第 10 章の既知の欠落を解消する。`num2words/base.py` の `to_currency` と複数の変換器がこの関数を使う。

### 用語

| 用語 | 業務上の意味 | 本変更での使用範囲 | 同義語/類義語 |
|---|---|---|---|
| 分解（パース） | 通貨金額を整数部・セント部・符号に分けること | 本変更の関数 | parse |
| セント部 | 小数点以下 2 桁（0〜99）の整数 | 本変更の関数の戻り値 | 小数部（cents） |
| セントとして扱う整数 | `is_int_with_cents=True` のときの整数入力（例: 1234 は 12.34） | 本変更の関数 | 最小単位の整数 |

### システムの形態

ライブラリ（変更なし）。利用者は Python から `parse_currency_parts` を呼ぶ（内部の補助関数で、公開 API `num2words()` からは `to_currency` 経由で呼ばれる）。

## 2. 業務

### 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。

### 2-1. 業務の問題

変更なし。既存要件定義書 `docs/requirements.md` セクション 2-1 を参照（既存システムの問題は「不明」のまま）。

### 2-2. 業務課題一覧

変更なし（既存の `RQ-BK-CURRENCY-WORDING` を使う。新しい業務課題は足さない）。既存要件定義書 `docs/requirements.md` セクション 2-2 を参照。

### 2-3. 見込み経営効果

変更なし。見込み経営効果は算定しない（既存要件定義書 2-3 を参照）。

## 3. 機能要件

### 機能一覧

| 区分 | RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
|---|---|---|---|---|---|
| [追加] | RQ-FT-PARSE-CURRENCY-PARTS | 機能 | 通貨金額の分解（整数部・セント部・符号） | RQ-BK-CURRENCY-WORDING | パッケージが import できず、通貨金額の読み上げ（RQ-FT-CONVERT-CURRENCY）が一切動かない |

### 3-1. 帳票・出力ファイル

変更なし。既存要件定義書 `docs/requirements.md` セクション 3-1 を参照。

### 3-1a. 画面・Web API

変更なし。既存要件定義書 `docs/requirements.md` セクション 3-1a を参照。

### 3-2. 業務ルール

変更なし。既存要件定義書 `docs/requirements.md` セクション 3-2 を参照。分解の規則（丸め、符号、入力の型ごとの扱い）は RQ-FT-PARSE-CURRENCY-PARTS の内容に書いた。

#### RQ-FT-PARSE-CURRENCY-PARTS の内容（[追加]）

| 項目 | 規則 |
|---|---|
| 整数（int）・`is_int_with_cents=True` | 値をセントとみなす。整数部 = 絶対値 // 100、セント部 = 絶対値 % 100、符号 = 値 < 0 |
| 整数（int）・`is_int_with_cents=False` | 値を整数部とみなす。整数部 = 絶対値、セント部 = 0、符号 = 値 < 0 |
| 文字列（str） | `Decimal` として解釈し、下の小数の規則に従う |
| Decimal（float も同様に `str` 経由で `Decimal` にする） | 小数点以下 2 桁に `ROUND_HALF_UP` で丸める。符号は丸めた後の値の符号、整数部とセント部は丸めた絶対値から得る |
| 不正な文字列 | `Decimal` が投げる例外（decimal.InvalidOperation）をそのまま返す（握りつぶさない） |

違反・エラー時の業務上の扱い: 不正な入力はそのまま例外を返し、呼び出し元で扱う。

対応業務課題ID（RQ-BK-*）: RQ-BK-CURRENCY-WORDING

### 3-3. 外部連携

変更なし（外部連携は無い）。

## 4. データ

### 4-1〜4-5

変更なし。既存要件定義書 `docs/requirements.md` セクション 4 を参照（データは扱わない）。

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 5 を参照。

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 6 を参照。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-VERIFY-PARSE-CURRENCY-PARTS（[追加]） | 通貨金額の分解の規則（セント扱い、符号、丸め、型ごとの扱い）を確かめる | num2words を import できる | `parse_currency_parts` に、整数（セント扱いと整数部扱い）、負の整数、文字列、Decimal、float を渡す | 各入力で `(整数部, セント部, 符号)` が規則どおりになり、不正な文字列は decimal.InvalidOperation を返す | RQ-FT-PARSE-CURRENCY-PARTS | RQ-BK-CURRENCY-WORDING |

既存のシナリオは変更なし。

## 8. 変更後の業務課題と要件の対応表

| 業務課題 | 要件 |
|---|---|
| RQ-BK-CURRENCY-WORDING | RQ-FT-CONVERT-CURRENCY（既存）、RQ-FT-PARSE-CURRENCY-PARTS（追加） |
