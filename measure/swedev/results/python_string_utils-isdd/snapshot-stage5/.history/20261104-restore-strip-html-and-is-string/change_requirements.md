# 変更要件定義書: HTML タグの除去（strip_html）、文字列型の判定（is_string）、InvalidInputError の実装し直し

既存の要件定義書 `docs/requirements.md` に対する変更。`strip_html`、`is_string`、`InvalidInputError.__init__` は既存コードから削られたため、この変更で実装を戻す。要件そのものは既存の正本に既に定義されている。区分は [追加] と [削除] だけで書く。この変更では [追加] と [削除] の要件は無い（既存の要件を実装し直すだけ）。

## 1. 目的・前提

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照。

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。対応する業務課題は `RQ-BK-VALIDATE-STRING-FORMAT`（文字列の形式判定）、`RQ-BK-TRANSFORM-STRING`（文字列の加工・変換）。

## 3. 機能要件

### 利用者向けインターフェース（公開関数）

変更なし。`strip_html` は `manipulation` の、`is_string` は `validation` の公開関数の一覧（`__all__`）に既に載っており、利用者向けの形は変わらない。`InvalidInputError` は既存の例外クラスで、呼び出し方は変わらない。

### 3-1. 帳票・出力ファイル

変更なし。

### 3-2. 業務ルール

変更なし（既存の業務ルールを守って実装し直す）。

- `strip_html(input_string, keep_tag_content=False)`: 入力が文字列でなければ `InvalidInputError` を送出する。`keep_tag_content` が偽なら、タグとタグの中身を取り除く。真なら、タグだけを取り除き、中身は残す。タグの判定は既存の正規表現定数 `HTML_RE`（中身も除く）と `HTML_TAG_ONLY_RE`（タグだけ）を使う。
- `is_string(obj)`: 引数がどの型でも例外を送出せず、文字列の型かどうかを真偽値で返す。空文字も文字列として真とする（空でないかは `is_full_string` の役目）。
- `InvalidInputError`: 生成時に受け取った値の型を含み、期待する型が `str` であることを示すメッセージを作り、`TypeError` の初期化に渡す。

### 3-3. 外部連携

変更なし（外部連携は無い）。

### 機能一覧

変更なし。この変更が実装し直す既存の要件は次のとおり。いずれも `docs/requirements.md` の機能一覧と非機能要件に既にある。

| RQ-ID | 実装し直す要素 | 既存の内容 |
| --- | --- | --- |
| `RQ-FT-STRIP-HTML` | `strip_html` | HTML・XML タグの除去（中身の残し方を指定可） |
| `RQ-FT-CHECK-STRING-TYPE` | `is_string`（空でない判定 `is_full_string` と併せて） | 文字列型・空でない文字列の判定 |
| `RQ-FT-REJECT-NON-STRING-INPUT` | `InvalidInputError.__init__` | 文字列以外の入力を `InvalidInputError` で知らせる |

## 4. データ

変更なし（既存要件定義書 セクション 4 を参照。永続化するデータは無い）。

## 5. 非機能要件

変更なし。標準ライブラリだけで実装する（既存の `re` と既存の正規表現定数 `HTML_RE`・`HTML_TAG_ONLY_RE` を使う）。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

変更なし。既存のシナリオ `RQ-TS-VERIFY-PUBLIC-API-IMPORT`（文字列以外の入力の扱い）、`RQ-TS-VERIFY-VALIDATION-BASICS`（文字列型の判定）、`RQ-TS-VERIFY-TEXT-TRANSFORM`（タグ除去）が、この変更の受け入れに使う。既存の E2E `e2e/test_scenarios.py` の対応する場面がそのまま確かめる。

## 8. 業務課題と要件の対応（変更後）

変更なし。既存の `docs/requirements.md` セクション 8 のとおり。

| RQ-BK-ID | 対応する要件（変更後） |
|---|---|
| `RQ-BK-VALIDATE-STRING-FORMAT` | `RQ-FT-CHECK-STRING-TYPE`、`RQ-TS-VERIFY-VALIDATION-BASICS`、`RQ-TS-VERIFY-PUBLIC-API-IMPORT` |
| `RQ-BK-TRANSFORM-STRING` | `RQ-FT-STRIP-HTML`、`RQ-FT-REJECT-NON-STRING-INPUT`、`RQ-TS-VERIFY-TEXT-TRANSFORM`、`RQ-TS-VERIFY-PUBLIC-API-IMPORT` |
