# 変更要件定義書: Num2Word_Base の欠落メソッドの復元

作成日: 2026-11-04（変更フロー。正本 `docs/requirements.md` は書き換えない。実装後に isdd-build が反映する）

## 1. 目的・前提

### 目的

`num2words/base.py` の `Num2Word_Base` から、依頼の文章（REQUEST.md の PRD）に挙がった 8 個の関数・メソッド（`__init__`、`to_cardinal_float`、`pluralize`、`set_high_numwords`、`title`、`to_ordinal_num`、`merge`、`to_currency`）が削除されている。PRD のシグネチャとドキュメント文字列のとおりに戻し、既存の変換器（`lang_*.py`）と既存の基底処理（`to_cardinal`、`to_splitnum`、`clean` など）が呼び出せる状態にする。既存の他の機能の挙動は変えない。

### 変更の背景

正本 `docs/detail_design.md` と `docs/trace_map.md` には 8 個すべての 基底の DS-FN 系 が既にあり、対応要件は既存の RQ（`RQ-FT-CONVERT-CARDINAL`、`RQ-FT-CONVERT-ORDINAL-NUM`、`RQ-FT-CONVERT-CURRENCY` など）である。コードだけが欠けている状態のため、新しい要件は足さず、既存の要件を満たす実装を戻す（`splitbyx` の復元と同じ扱い）。

### 用語

| 用語 | 業務上の意味 | 本変更での使用範囲 | 同義語/類義語 |
|---|---|---|---|
| 基底クラス | 言語ごとの変換器が継承する `Num2Word_Base` | 本変更の対象 | base class |
| 未実装の拡張点 | 派生クラスで実装することを前提にした `NotImplementedError` を出すメソッド | `pluralize`、`set_high_numwords`、`merge`、`to_currency`（既定の CURRENCY_FORMS が空の場合） | hook |

### システムの形態

ライブラリ（変更なし）。利用者は Python から `num2words()` を呼ぶ。本変更の 8 個は変換器の内部で使われる（`to_cardinal` が `to_cardinal_float` を、`to_currency` が `pluralize` などを呼ぶ）。

## 2. 業務

### 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。

| RQ-BZ-ID | 業務名 | 業務の範囲 | 担当者 |
|---|---|---|---|
| RQ-BZ-NUMBER-WORDING | 数値の読み上げ | 数値を各言語の読み上げ文字列にして、利用者のプログラムの出力に使う | このライブラリを使う開発者 |

### 2-1. 業務の問題

変更なし（既存要件定義書 2-1 を参照。既存システムの問題は「不明」のまま）。

### 2-2. 業務課題一覧

変更なし。既存の業務課題を使う（RQ-BK-CARDINAL-WORDING、RQ-BK-ORDINAL-WORDING、RQ-BK-CURRENCY-WORDING）。新しい業務課題は足さない。

### 2-3. 見込み経営効果

変更なし。見込み経営効果は算定しない。

## 3. 機能要件

### 機能一覧

変更なし（新しい RQ-FT は足さない）。8 個の関数・メソッドは既存の次の要件を満たす処理として、既存設計の 基底の DS-FN 系 で受ける。

| RQ-ID | 機能名 | 内容 | この機能が無いと何が困るか | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-FT-CONVERT-CARDINAL | 基数の変換 | 整数・小数・Decimal・文字列を読み上げ文字列にする（小数は `to_cardinal_float` が担う。変更なし。既存要件） | 小数と負の数の読み上げが作れない | RQ-BK-CARDINAL-WORDING |
| RQ-FT-CONVERT-ORDINAL-NUM | 序数の数字表記 | 整数に序数の接尾辞を付けた数字表記を作る（基底の `to_ordinal_num` は値をそのまま返す。変更なし。既存要件） | 数字表記の序数が作れない | RQ-BK-ORDINAL-WORDING |
| RQ-FT-CONVERT-CURRENCY | 通貨金額の変換 | 通貨コードと金額から、通貨の読み上げ文字列を作る（基底の `to_currency` は CURRENCY_FORMS に無い通貨で NotImplementedError。変更なし。既存要件） | 金額の読み上げが作れない | RQ-BK-CURRENCY-WORDING |

### 3-1. 帳票・出力ファイル

変更なし（帳票・出力ファイルは無い）。

### 3-1a. 画面・Web API

変更なし。RQ-UI-PUBLIC-API（`num2words()`）を既存のとおり使う。

### 3-2. 業務ルール

変更なし。既存の RQ-FT-PARSE-CURRENCY-PARTS の規則を `to_currency` が `parse_currency_parts` 経由で使う。

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

変更なし。既存のシナリオを使う（`RQ-TS-VERIFY-CARDINAL-READING` が小数と基数を、既存の `RQ-TS-*` の通貨・序数の場面が残りを確かめる）。基底クラスの直接の振る舞い（`tests/test_base.py`）は既存の単体テストが確かめる。

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-VERIFY-CARDINAL-READING | 基数（小数を含む）の読み上げと公開 API の呼び出しを確かめる（変更なし。既存） | num2words を import できる | 言語と整数・小数を指定して num2words() を呼ぶ | 読み上げ文字列が期待値と一致する | RQ-FT-CONVERT-CARDINAL, RQ-UI-PUBLIC-API | RQ-BK-CARDINAL-WORDING |

## 8. 変更後の業務課題と要件の対応表

変更なし。既存要件定義書の対応のとおり。
