# 変更要件定義書: UUID の判定（is_uuid）と生成（uuid）の実装し直し

既存の要件定義書 `docs/requirements.md` に対する変更。`is_uuid` と `uuid` は既存コードから削られたため、この変更で実装し直す。要件そのものは既存の正本に既に定義されている。区分は [追加] と [削除] だけで書く。この変更では [追加] と [削除] の要件は無い（既存の要件を実装し直すだけ）。

## 1. 目的・前提

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照。

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。対応する業務課題は `RQ-BK-VALIDATE-STRING-FORMAT`（文字列の形式判定）と `RQ-BK-GENERATE-STRING-VALUE`（文字列や値の生成）。

## 3. 機能要件

### 利用者向けインターフェース（公開関数）

変更なし。`is_uuid` は `validation` の、`uuid` は `generation` の公開関数の一覧（`__all__`）に既に載っており、利用者向けの形は変わらない。

### 3-1. 帳票・出力ファイル

変更なし。

### 3-2. 業務ルール

変更なし（既存の業務ルールを守って実装し直す）。判定は RFC 4122 の UUID 形式（ハイフンあり）を正とし、`allow_hex` が真のときだけハイフンなしの 16 進表記も真とする。判定の入力が文字列でなければ文字列に変換してから判定する。生成は `uuid4` による UUID v4 とし、`as_hex` が真のときは 16 進表記（ハイフンなし）で返す。

### 3-3. 外部連携

変更なし（外部連携は無い）。

### 機能一覧

変更なし。この変更が実装し直す既存の要件は次のとおり。いずれも `docs/requirements.md` の機能一覧に既にある。

| RQ-ID | 実装し直す関数 | 既存の内容 |
| --- | --- | --- |
| `RQ-FT-CHECK-UUID` | `is_uuid` | UUID の判定（ハイフンなし形式を許可する指定を含む） |
| `RQ-FT-GENERATE-UUID` | `uuid` | UUID（v4）の生成（16 進表記を選べる） |

## 4. データ

変更なし（既存要件定義書 セクション 4 を参照。永続化するデータは無い）。

## 5. 非機能要件

変更なし。標準ライブラリだけで実装する（`uuid` モジュールと既存の正規表現定数 `UUID_RE`・`UUID_HEX_OK_RE` を使う）。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

変更なし。既存のシナリオ `RQ-TS-VERIFY-VALIDATION-BASICS`（UUID の判定を含む）と `RQ-TS-VERIFY-GENERATION`（UUID の生成を含む）と、既存の E2E `e2e/test_scenarios.py::test_validation_basics`・`test_generation` がこの変更の受け入れに使う。

## 8. 業務課題と要件の対応（変更後）

変更なし。既存の `docs/requirements.md` セクション 8 のとおり。

| RQ-BK-ID | 対応する要件（変更後） |
|---|---|
| `RQ-BK-VALIDATE-STRING-FORMAT` | `RQ-FT-CHECK-UUID`、`RQ-TS-VERIFY-VALIDATION-BASICS` |
| `RQ-BK-GENERATE-STRING-VALUE` | `RQ-FT-GENERATE-UUID`、`RQ-TS-VERIFY-GENERATION` |
