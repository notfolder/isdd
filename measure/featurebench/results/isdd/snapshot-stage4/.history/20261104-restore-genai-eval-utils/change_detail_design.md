# 変更設計書（GenAI 評価結果の整形と表示の復元：mlflow/cli/genai_eval_utils.py）

正本: `docs/detail_design.md`。本書は正本を書き換えない。区分は [追加] のみ。
変更要件: `change_requirements.md`。本変更は新しい範囲 `mlflow/cli/genai_eval_utils.py` を正本に足す（実装後レビューで正本へ反映する）。

## 1. 言語・フレームワーク・アーキテクチャの選定

既存コードベースの選定を使う。Python の標準ライブラリ（re）と、既存の依存（pandas、click）と既存の mlflow の内部モジュール（スコアラーの取得、アセスメントのメタデータの鍵）だけを使う。新しい依存は足さない。DB は使わない。

| 項目 | 選定 | 根拠 |
|---|---|---|
| 言語 | Python | 既存コードの言語 |
| ライブラリ | pandas（DataFrame の反復）、click（使用エラー）、既存の mlflow の scorer 登録の仕組み | 既存コードの依存 |
| 実行形態 | `mlflow/cli/eval.py` からの関数呼び出し | 依頼文（呼び出し側は既存） |
| 承認 | 固定回答（ANSWERS.md）と依頼文により承認済み | ANSWERS.md、REQUEST.md |

## 2. システム構成

### 2-1. コンポーネント一覧

| コンポーネント | 役割 | 配置 |
|---|---|---|
| 評価結果の整形モジュール | アセスメントの抽出、表の整形、スコアラーの解決、型の定義 | `mlflow/cli/genai_eval_utils.py` |

### 2-2. 各コンポーネントの役割と機能

- アセスメントの抽出（`extract_assessments_from_results`）: DataFrame の各行から、評価の実行 ID が一致するアセスメントを `Assessment` にする。
- 表の整形（`format_table_output`）: `EvalResult` の並びを `TableOutput` にする。セル文字列は既存の `_format_assessment_cell` を使う。
- スコアラーの解決（`resolve_scorers`）: 組み込み（クラス名・snake_case）を先に、登録済みを後に探す。

### 2-3. コンポーネント間インターフェースとデータフロー

- 入力: 評価結果の DataFrame（`trace_id`、`assessments` の列）と評価の実行 ID。出力は `list[EvalResult]`。
- 表の整形の入力は `list[EvalResult]`、出力は `TableOutput`（ヘッダーとセルの行）。
- スコアラーの解決の入力は名前の一覧と実験 ID、出力は `list[Scorer]`。

### 2-4. ネットワーク構成図

無し（ライブラリ。登録済みスコアラーの探索は既存の仕組みに任せる）。

## 3. データ設計

### 3-1. データモデル

既存の型（変更しない）:

| DS-ID | 種類 | 項目 | 意味 |
|---|---|---|---|
| `DS-CL-ASSESSMENT` | データクラス | name、result、rationale、error | アセスメントの 1 件 |
| `DS-CL-CELL` | データクラス | value、assessment | 表のセル |
| `DS-CL-EVAL-RESULT` | データクラス | trace_id、assessments | トレースごとの結果 |
| `DS-CL-TABLE-OUTPUT` | データクラス | headers、rows | 表 |

### 3-2. トランザクションと排他制御

無し（純粋な変換。共有の状態は持たない）。

### 3-3. 状態遷移

無し。

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者の公開インターフェース（`mlflow.cli.genai_eval_utils` からの import）:

- `extract_assessments_from_results(results_df: pd.DataFrame, evaluation_run_id: str) -> list[EvalResult]`
- `format_table_output(output_data: list[EvalResult]) -> TableOutput`
- `resolve_scorers(scorer_names: list[str], experiment_id: str) -> list[Scorer]`

### 4-2. 内部設計

- 抽出: 各行の `trace_id` 列が無ければ "unknown"。`assessments` 列が無ければ空。各エントリのメタデータの評価の実行 ID が一致するものだけを、`feedback` が辞書なら `value` を結果にして `Assessment` にする。エラーは真なら文字列にする。該当が無ければ既定のエラーを 1 件入れる。
- 表の整形: 名前の集合（None と "N/A" を除く）を昇順にしてヘッダーにする。各セルは同じ名前の最初のアセスメントの `_format_assessment_cell` の結果。値が "N/A" のセルは `assessment=None` にする。
- スコアラーの解決: 組み込みの辞書を、クラス名と snake_case 名の両方で引けるように作る。見つからなければ登録済みの取得を呼び、`MlflowException` は使用エラーに変換する（利用可能な組み込みの名前を含める）。結果が空なら使用エラー。

### 4-3. バッチ設計

無し。

## 5. クラス設計

### 5-1. クラス一覧

既存の 4 つのデータクラス（3-1）。新しいクラスは無い。

### 5-2. クラスの責務・属性

3-1 の表のとおり（既存コードのまま）。

### 5-3. クラス図

無し（データクラスの 4 つの組み合わせ。`EvalResult` は `Assessment` の並び、`TableOutput` は `Cell` の行を持つ）。

### 5-4. 関数の責務

| DS-ID | 関数 | 責務 |
|---|---|---|
| `DS-FN-EXTRACT-ASSESSMENTS-FROM-RESULTS` | `extract_assessments_from_results` | 評価の実行 ID でアセスメントを絞り、トレースごとの結果にする |
| `DS-FN-FORMAT-TABLE-OUTPUT` | `format_table_output` | トレース × アセスメント名の表にする |
| `DS-FN-RESOLVE-SCORERS` | `resolve_scorers` | 名前を組み込みまたは登録済みのスコアラーにする |

### 5-5. クラス図とメッセージ

無し。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

- スコアラーの解決: 登録済みの探索の `MlflowException`（未登録を含む）と、指定が空の場合を `click.UsageError` にする。それ以外の例外は変換しない。
- 外部の形式の不正（`assessments` が None、辞書でない要素など）は正規化せず、Python の通常の例外に任せる。

### 6-2. 認証・認可・監査ログ

無し。

### 6-3. その他のセキュリティ対策

無し。

## 7. コード設計

### 7-1. ディレクトリ構成

```
mlflow/cli/
  genai_eval_utils.py  （評価結果の整形。対象はこのファイルだけ。他のファイルは正本の対象外）
```

### 7-2. ファイルごとの役割

| ファイル | 役割 | 含まれるクラス・公開関数 | 実現する設計 ID |
|---|---|---|---|
| `mlflow/cli/genai_eval_utils.py` | 評価結果の抽出、表の整形、スコアラーの解決 | `extract_assessments_from_results`、`format_table_output`、`resolve_scorers` | `DS-MD-GENAI-EVAL-UTILS-MODULE`、`DS-FN-EXTRACT-ASSESSMENTS-FROM-RESULTS`、`DS-FN-FORMAT-TABLE-OUTPUT`、`DS-FN-RESOLVE-SCORERS` |

### 7-3. 対応表の粒度

`function`（公開関数まで対応表に載せる）。

### 7-4. 依存の規則

依存の規則は無い。

### 7-5. コーディング規約

- Python の既存の規約（リポジトリの pyproject と ruff の設定）に従う。
- コードに要件 ID と設計 ID は書かない。設計 ID とコードの対応は `docs/trace_map.md` で管理する。

## 8. テスト設計

### 8-1. テストの種類と方針

- 総合テスト・E2E: 本書 8-2 のシナリオを `e2e/test_genai_eval_utils.py` で実行する。公開の関数だけを呼び、スコアラーの登録済み探索は置き換えて行う（外部の登録先に依存しない）。
- 既存の `tests/` は変更しない。

### 8-2. E2E テストのシナリオ

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| `DS-TS-EXTRACT-ASSESSMENTS-BY-RUN` | 評価の実行 ID で絞り、該当が無ければ既定のエラーを入れる | 実行 A と B のアセスメントを持つ 2 行 | 実行 A の ID で抽出する | 実行 A のものだけ。該当なしの行は既定のエラー |
| `DS-TS-FORMAT-TABLE-CELLS` | 表の列の並びとセルの文字列 | 値・根拠・エラーの異なるアセスメントを持つ 2 トレース | 表を作り、セルを読む | 列は昇順。error・value・rationale の規則どおり。該当なしは N/A で assessment は None |
| `DS-TS-RESOLVE-SCORERS-NAMES` | 組み込みの 2 つの名前で解決でき、未知の名前と空の指定は使用エラー | 登録済みの探索を失敗させる | 名前を解決する。未知の名前と空の一覧を渡す | 組み込みに解決。未知と空は click.UsageError |

### 8-3. E2E の実行手段

pytest（コンテナ内の Python）。公開の関数を直接呼ぶ。

### 8-4. E2E の実行コマンドと運用

- 実行コマンド: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml'`
- 外部連携は無いため、モックのモードは設けない（登録済み探索の置き換えはテストの中だけで行う）。

## 9. 運用設計

無し（ライブラリの関数のため、起動・バックアップ・監視の設計は無い）。

## 10. ログ・監視・アラート・障害対応設計

無し。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| `DS-MD-GENAI-EVAL-UTILS-MODULE` | `RQ-FT-EXTRACT-ASSESSMENTS-BY-RUN`, `RQ-FT-FORMAT-TABLE-OUTPUT`, `RQ-FT-RESOLVE-SCORERS` |
| `DS-CL-ASSESSMENT` | `RQ-FT-EXTRACT-ASSESSMENTS-BY-RUN`, `RQ-FT-FORMAT-TABLE-OUTPUT` |
| `DS-CL-CELL` | `RQ-FT-FORMAT-TABLE-OUTPUT` |
| `DS-CL-EVAL-RESULT` | `RQ-FT-EXTRACT-ASSESSMENTS-BY-RUN`, `RQ-FT-FORMAT-TABLE-OUTPUT` |
| `DS-CL-TABLE-OUTPUT` | `RQ-FT-FORMAT-TABLE-OUTPUT` |
| `DS-FN-EXTRACT-ASSESSMENTS-FROM-RESULTS` | `RQ-FT-EXTRACT-ASSESSMENTS-BY-RUN` |
| `DS-FN-FORMAT-TABLE-OUTPUT` | `RQ-FT-FORMAT-TABLE-OUTPUT` |
| `DS-FN-RESOLVE-SCORERS` | `RQ-FT-RESOLVE-SCORERS` |
| `DS-TS-EXTRACT-ASSESSMENTS-BY-RUN` | `RQ-TS-EXTRACT-ASSESSMENTS-BY-RUN` |
| `DS-TS-FORMAT-TABLE-CELLS` | `RQ-TS-FORMAT-TABLE-CELLS` |
| `DS-TS-RESOLVE-SCORERS-NAMES` | `RQ-TS-RESOLVE-SCORERS-NAMES` |
