# 変更要件定義書: 空でない文字列の判定と IPv4 判定関数の実装し直し

既存の要件定義書 `docs/requirements.md` に対する変更。`is_full_string` と `is_ip_v4` は既存コードから削られたため、この変更で実装を戻す。要件そのものは既存の正本に既に定義されている。区分は [追加] と [削除] だけで書く。この変更では [追加] と [削除] の要件は無い（既存の要件を実装し直すだけ）。

## 1. 目的・前提

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照。

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 を参照。対応する業務課題は `RQ-BK-VALIDATE-STRING-FORMAT`（文字列の形式判定）。

## 3. 機能要件

### 利用者向けインターフェース（公開関数）

変更なし。既存要件定義書 `docs/requirements.md` セクション 3 の利用者向けインターフェースを参照。`is_full_string` と `is_ip_v4` は既存の公開関数の一覧（`__all__` の `is_full_string`、`is_ip_v4`）に既に載っており、利用者向けの形は変わらない。

### 3-1. 帳票・出力ファイル

変更なし。

### 3-2. 業務ルール

変更なし（既存の業務ルールを守って実装し直す）。

### 3-3. 外部連携

変更なし（外部連携は無い）。

### 機能一覧

変更なし。この変更が実装し直す既存の要件は次のとおり。いずれも `docs/requirements.md` の機能一覧に既にある。

| RQ-ID | 実装し直す関数 | 既存の内容 |
| --- | --- | --- |
| `RQ-FT-CHECK-STRING-TYPE` | `is_full_string` | 文字列型・空でない文字列の判定 |
| `RQ-FT-CHECK-IP-ADDRESS` | `is_ip_v4` | IPv4・IPv6・両方の IP アドレスの判定（IPv4 側） |

## 4. データ

変更なし（既存要件定義書 セクション 4 を参照。永続化するデータは無い）。

## 5. 非機能要件

変更なし。標準ライブラリだけで実装する。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

変更なし。既存のシナリオ `RQ-TS-VERIFY-VALIDATION-BASICS`（`RQ-FT-CHECK-STRING-TYPE`、`RQ-FT-CHECK-IP-ADDRESS` を検証する）と、既存の E2E `e2e/test_scenarios.py` がこの変更の受け入れに使う。

## 8. 業務課題と要件の対応（変更後）

変更なし。既存の `docs/requirements.md` セクション 8 のとおり。実装し直す要件の業務課題は次のとおり。

| RQ-BK-ID | 対応する要件（変更後） |
|---|---|
| `RQ-BK-VALIDATE-STRING-FORMAT` | `RQ-FT-CHECK-STRING-TYPE`、`RQ-FT-CHECK-IP-ADDRESS`、`RQ-TS-VERIFY-VALIDATION-BASICS` |
