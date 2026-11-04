# 変更設計書（設定ファイルと環境変数の 5 インターフェースの復元）

正本: `docs/detail_design.md`。本書は正本を書き換えない。区分は [追加] のみ（変更の対象の設計要素は既存の設計 ID を変えず、関数の中身を復元する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。設定ファイルの構造は変更しない。

## 4. アーキテクチャ設計

変更なし。既存設計 `docs/detail_design.md` セクション 4 を参照。

## 5. クラス設計

### 5-1. クラス一覧

変更なし。

### 5-4. 関数の責務

| 区分 | DS-ID | 関数 | 責務（1 文） |
|---|---|---|---|
| [追加] | `DS-FN-LOAD-CLAUDE-CONFIG` | 設定ファイルを読み、解析結果を返す（無い・読めない・JSON として壊れている場合は空の辞書。内容の検査はしない） | 設定の読み込み |
| [追加] | `DS-FN-SAVE-CLAUDE-CONFIG` | 設定を、親ディレクトリを作ったうえで UTF-8 の 2 桁インデント JSON として上書き保存する | 設定の保存 |
| [追加] | `DS-FN-GET-ENV-VAR` | OS の環境変数、次に設定ファイルの環境欄の順に値を探し、無ければ既定値を返す。設定ファイルの読み取りの例外は握りつぶして既定値を返す | 環境変数の取得 |
| [追加] | `DS-FN-GET-TRACING-STATUS` | 設定ファイルから記録の状態の値を作る（ファイルが無ければ理由つきの無効、記録フラグが true のときだけ有効） | 記録の状態の取得 |
| [追加] | `DS-FN-SETUP-ENVIRONMENT-CONFIG` | 記録フラグを true にし、追跡 URI は真のときだけ書き、実験 ID が真なら実験名を消して実験 ID を書き、実験 ID が偽で実験名が真なら実験名を書く。保存する | 記録の環境設定 |

### 5-5. クラス図とメッセージ

変更なし。ただし、既存のメッセージの呼び出し先に、上の 5 関数が加わる（既存の呼び出し元 `hooks.py`・`cli.py`・`tracing.py` は呼び出し方を変えず、import 行だけを足す）。

## 6. エラーハンドリングとセキュリティ設計

変更なし。ただし次を加える。`DS-FN-LOAD-CLAUDE-CONFIG` は、ファイル読み取りの失敗と JSON の失敗を空の辞書にする（既存の要件どおり）。`DS-FN-GET-ENV-VAR` は、設定ファイルの読み取りで起きた例外を既定値に置き換える。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。

### 7-2. ファイルごとの役割

| 区分 | ファイル | 役割 | 含まれるクラス・公開関数 | 実現する設計 ID |
|---|---|---|---|---|
| [追加] | `mlflow/claude_code/config.py` | 記録の状態の型、設定の定数、設定の読み書きと環境変数の取得、記録の環境設定、記録の状態の取得 | `load_claude_config`、`save_claude_config`、`get_env_var`、`get_tracing_status`、`setup_environment_config` | `DS-FN-LOAD-CLAUDE-CONFIG`、`DS-FN-SAVE-CLAUDE-CONFIG`、`DS-FN-GET-ENV-VAR`、`DS-FN-GET-TRACING-STATUS`、`DS-FN-SETUP-ENVIRONMENT-CONFIG` |
| 変更なし（既存） | `mlflow/claude_code/hooks.py` | 既存のとおり。import 行に `load_claude_config`・`save_claude_config` を足す | 既存のとおり | 既存のとおり |
| 変更なし（既存） | `mlflow/claude_code/cli.py` | 既存のとおり。import 行に `setup_environment_config`・`get_tracing_status` を足す | 既存のとおり | 既存のとおり |
| 変更なし（既存） | `mlflow/claude_code/tracing.py` | 既存のとおり。import 行に `get_env_var` を足す | 既存のとおり | 既存のとおり |

対応表の粒度: `function`（変更なし）。依存の規則: 無い（変更なし）。

### 7-3. コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存の単体テスト `tests/claude_code/` は変更しない。

### 8-2. E2E テストのシナリオ

| 区分 | DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] | `DS-TS-LOAD-SAVE-CONFIG` | 保存と読み込みが往復し、壊れた・無い設定は空になる | 空のディレクトリ、壊れた JSON | 保存して読む。壊れたものと無いものを読む | 往復で同じ内容。壊れた・無いものは空 |
| [追加] | `DS-TS-GET-ENV-VAR-PRECEDENCE` | 環境変数の探索順を確かめる | OS と設定ファイルに同名の値 | OS あり・無しで読む | OS 優先、次に設定ファイル、最後に既定値 |
| [追加] | `DS-TS-READ-TRACING-STATUS-VALUES` | 記録の状態の値が設定ファイルどおりに求まる | 無し・無効・有効の設定 | 状態を求める | 無しは理由つき無効、無効は無効、有効は追跡先などを含む |
| [追加] | `DS-TS-SETUP-ENVIRONMENT-PRECEDENCE` | 実験 ID が実験名に優先し、他の設定を保つ | 他の環境変数と実験名を持つ設定 | 実験 ID と実験名を両方与える | 記録フラグ true、実験 ID あり、実験名は消え、他は残る |

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。テスト関数は `e2e/test_claude_code.py` に追加する（対応表で結ぶ）。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [追加] | `DS-FN-LOAD-CLAUDE-CONFIG` | `RQ-FT-LOAD-SAVE-CLAUDE-CONFIG` |
| [追加] | `DS-FN-SAVE-CLAUDE-CONFIG` | `RQ-FT-LOAD-SAVE-CLAUDE-CONFIG` |
| [追加] | `DS-FN-GET-ENV-VAR` | `RQ-FT-GET-ENV-VAR` |
| [追加] | `DS-FN-GET-TRACING-STATUS` | `RQ-FT-READ-TRACING-STATUS` |
| [追加] | `DS-FN-SETUP-ENVIRONMENT-CONFIG` | `RQ-FT-SETUP-ENVIRONMENT-CONFIG` |
| [追加] | `DS-TS-LOAD-SAVE-CONFIG` | `RQ-TS-LOAD-SAVE-CONFIG` |
| [追加] | `DS-TS-GET-ENV-VAR-PRECEDENCE` | `RQ-TS-GET-ENV-VAR-PRECEDENCE` |
| [追加] | `DS-TS-READ-TRACING-STATUS-VALUES` | `RQ-TS-READ-TRACING-STATUS-VALUES` |
| [追加] | `DS-TS-SETUP-ENVIRONMENT-PRECEDENCE` | `RQ-TS-SETUP-ENVIRONMENT-PRECEDENCE` |

### 11-1. 除外要件

除外要件は無い。
