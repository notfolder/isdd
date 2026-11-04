# 変更要件定義書: 数字列の分割（splitbyx）の復元

作成日: 2026-11-04（変更フロー。正本 `docs/requirements.md` は書き換えない。実装後に isdd-build が反映する）

## 1. 目的・前提

### 目的

`num2words/utils.py` の `splitbyx` が現在のコードに無く、`lang_*.py` の多くが `from .utils import get_digits, splitbyx` で失敗するため、パッケージを import できない。`splitbyx` を、依頼の文章（REQUEST.md の PRD）のシグネチャとドキュメント文字列のとおりに戻し、数字列を x 桁ごとに分けられるようにする。既存の機能の挙動は変えない。

### 変更の背景

正本 `docs/detail_design.md` と `docs/trace_map.md` には `DS-FN-SPLITBYX` が既にあり、対応要件は既存の `RQ-FT-CONVERT-CARDINAL` である。コードだけが欠けている状態のため、新しい要件は足さず、既存の要件を満たす実装を戻す。

### 用語

| 用語 | 業務上の意味 | 本変更での使用範囲 | 同義語/類義語 |
|---|---|---|---|
| 分割（チャンク） | 数字列を先頭から一定の桁数ごとに切ったもの | 本変更の関数の戻り値 | chunk |
| 先頭の端数 | 桁数が x の倍数でないとき、先頭に残る x 桁未満の部分 | 本変更の関数 | 端数 |

### システムの形態

ライブラリ（変更なし）。利用者は Python から `splitbyx` を呼ぶ（内部の補助関数。変換器の `to_cardinal` などが使う）。

## 2. 業務

### 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。

| RQ-BZ-ID | 業務名 | 業務の範囲 | 担当者 |
|---|---|---|---|
| RQ-BZ-NUMBER-WORDING | 数値の読み上げ | 数値を各言語の読み上げ文字列にして、利用者のプログラムの出力に使う | このライブラリを使う開発者 |

### 2-1. 業務の問題

変更なし。既存要件定義書 `docs/requirements.md` セクション 2-1 を参照（既存システムの問題は「不明」のまま）。

### 2-2. 業務課題一覧

変更なし（既存の `RQ-BK-CARDINAL-WORDING` を使う。新しい業務課題は足さない）。

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| RQ-BK-CARDINAL-WORDING | 数値を基数の読み上げ文字列にする | 2-1 の問題を聞き取れていないため、既存機能の提供を課題として置く | 現状の機能を維持する（既存システムのため数値目標は無い） | RQ-BZ-NUMBER-WORDING |

### 2-3. 見込み経営効果

変更なし。見込み経営効果は算定しない（既存要件定義書 2-3 を参照）。

## 3. 機能要件

### 機能一覧

変更なし（新しい RQ-FT は足さない）。`splitbyx` は既存の RQ-FT-CONVERT-CARDINAL を満たす補助処理として、既存設計 `DS-FN-SPLITBYX` で受ける。

| RQ-ID | 機能名 | 内容 | この機能が無いと何が困るか | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-FT-CONVERT-CARDINAL | 基数の変換 | 整数・小数・Decimal・文字列を読み上げ文字列にする（変更なし。既存要件） | 数値を言葉にできない | RQ-BK-CARDINAL-WORDING |

### 3-1. 帳票・出力ファイル

変更なし。

### 3-1a. 画面・Web API

変更なし（既存要件の参照）。

| RQ-ID | 名称 | 用途 | 入力 | 出力 | 利用者 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-UI-PUBLIC-API | num2words()（Python 関数） | 数値を読み上げ文字列にする（変更なし。既存要件） | number, ordinal, lang, to, **kwargs | 読み上げ文字列（str） | 開発者 | RQ-BK-CARDINAL-WORDING |

### 3-2. 業務ルール

変更なし。分割の規則は既存設計書 `docs/detail_design.md` の `DS-FN-SPLITBYX` の責務（ドキュメント文字列の規則）に従う。

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

変更なし。`RQ-FT-CONVERT-CARDINAL` は既存の `RQ-TS-VERIFY-CARDINAL-READING` が検証する（`e2e/test_baseline_scenarios.py` の基数の場面が、変換器を通して `splitbyx` を使う）。既存の単体テスト `tests/test_utils.py::test_splitbyx` も同じ規則を確かめる。

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-VERIFY-CARDINAL-READING | 基数の読み上げと公開 API の呼び出しを確かめる（変更なし。既存） | num2words を import できる | 言語と整数・小数を指定して num2words() を呼ぶ | 既定の英語と指定言語の読み上げ文字列が期待値と一致する | RQ-FT-CONVERT-CARDINAL, RQ-UI-PUBLIC-API | RQ-BK-CARDINAL-WORDING |

## 8. 変更後の業務課題と要件の対応表

変更なし。既存要件定義書の対応のとおり（RQ-BK-CARDINAL-WORDING → RQ-FT-CONVERT-CARDINAL）。
