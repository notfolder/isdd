# 実装タスク（NPMI の 2 関数の復元：mlflow/store/analytics/trace_correlation.py）

前提: `docs/active_change` が本変更（`.history/20261104-restore-npmi-functions/`）を指している。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない（反映は実装後レビュー）。
対象の変更設計 ID: `DS-MD-TRACE-CORRELATION-MODULE`、`DS-MD-ANALYTICS-PACKAGE-INIT`、`DS-CL-TRACE-CORRELATION-COUNTS`、`DS-CL-NPMI-RESULT`、`DS-FN-CALCULATE-NPMI-FROM-COUNTS`、`DS-FN-CALCULATE-SMOOTHED-NPMI`、`DS-TS-NPMI-UNSMOOTHED-VALUES`、`DS-TS-NPMI-INCONSISTENT-COUNTS`、`DS-TS-NPMI-PERFECT-COOCCURRENCE`、`DS-TS-SMOOTHED-NPMI-JEFFREYS`。

## タスク

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は存在する（導入済み）。`scripts/isdd/completeness.json` の実行形態（cli）・認証（無し）・外部連携（無し）が、正本の詳細設計書と一致していることを確かめる。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、上記が一致していること。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261104-restore-npmi-functions` を指していることを確認する。正本には変更を反映しない。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 /Users/notfolder/.claude/skills/isdd-spec/scripts/rq_ds_link_checker.py .history/20261104-restore-npmi-functions/change_requirements.md .history/20261104-restore-npmi-functions/change_detail_design.md --base docs/requirements.md` が合格すること。

1. **相関分析モジュールの実装**（`DS-FN-CALCULATE-NPMI-FROM-COUNTS`、`DS-FN-CALCULATE-SMOOTHED-NPMI`、`DS-MD-TRACE-CORRELATION-MODULE`、`DS-CL-TRACE-CORRELATION-COUNTS`、`DS-CL-NPMI-RESULT`）
   - `mlflow/store/analytics/trace_correlation.py` に `calculate_npmi_from_counts(joint_count, filter1_count, filter2_count, total_count) -> NPMIResult` と `calculate_smoothed_npmi(joint_count, filter1_count, filter2_count, total_count, smoothing: float = JEFFREYS_PRIOR) -> float` を書く。引数名・順序・既定値・戻り値の型は依頼文の Interface Description どおり。
   - 既存の `JEFFREYS_PRIOR`、`TraceCorrelationCounts`、`NPMIResult` は変えない。
   - 設計書 5-4 の詳細規則（順序 1〜6）と 4-2 の式に従う。例外を投げない。例外の型検査はしない。
   - 完了条件: 依頼文の Interface Description の例（(10,20,15,100)、(0,50,50,100)、(0,0,50,100)）で、素の値・平滑化の値が仕様どおり返ること（タスク 4 の E2E で確かめる）。

2. **パッケージの公開一覧の import 追加**（`DS-MD-ANALYTICS-PACKAGE-INIT`）
   - `mlflow/store/analytics/__init__.py` の import 行に `calculate_npmi_from_counts`、`calculate_smoothed_npmi` を足す（`__all__` は既存のまま）。
   - 完了条件: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -c "from mlflow.store.analytics import calculate_npmi_from_counts, calculate_smoothed_npmi, NPMIResult"'` がエラーなく終わること。

3. **検査の対象に新しい範囲を足す**（isdd の検査のみ。プロダクトのコードは変えない）
   - `scripts/isdd/check.sh` の 3 つの呼び出し（`trace_map_checker.py`、`dependency_checker.py`、`acceptance_checker.py`）の `mlflow/claude_code` の並びに `mlflow/store/analytics` を足す。各チェッカーは複数のソースディレクトリを受け付ける（引数の順は `mlflow/claude_code` の後ろに足す）。
   - 完了条件: `bash scripts/isdd/check.sh` の出力で、両方のディレクトリが対象になっていること。

4. **E2E テストの実装**（`DS-TS-NPMI-UNSMOOTHED-VALUES`、`DS-TS-NPMI-INCONSISTENT-COUNTS`、`DS-TS-NPMI-PERFECT-COOCCURRENCE`、`DS-TS-SMOOTHED-NPMI-JEFFREYS`）
   - `e2e/test_trace_correlation.py` を新規に作る。公開インターフェース（`mlflow.store.analytics` からの import）だけを使い、設計書 8-2 の 4 シナリオを、それぞれ 1 つのテスト関数に書く（関数名は DS-TS の名前を小文字・アンダースコアにした形、例 `test_npmi_unsmoothed_values`）。既存の `e2e/test_claude_code.py` は変えない。
   - 完了条件: タスク 6 の実行で、対応する 4 関数が通ること。
   - 対応表の行（タスク 5）で各 DS-TS をテスト関数に結ぶ。

5. **対応表（docs/trace_map.md）更新タスク**
   - 変更設計書 7-2 の 5 つの DS-MD・DS-CL・DS-FN と、4 つの DS-TS の行を足す。書式は trace-map-rules.md（修飾名は `mlflow/store/analytics/trace_correlation.py::calculate_npmi_from_counts` の形。`DS-MD` はファイルパス、`DS-CL` は `::TraceCorrelationCounts` の形、`DS-TS` は `e2e/test_trace_correlation.py::test_...` の形）。
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること（タスク 3 の検査対象の変更を含めて）。

6. **E2E テスト全件通過タスク**
   - 実行コマンド（設計書 8-4）: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml'`
   - 完了条件: 結果に FAIL が 0 件。失敗したら修正と再実行を全件通過まで繰り返す。

7. **単体テスト・結合テスト全件通過タスク**
   - 本変更で単体テストは追加しない（設計書 8-1）。既存の単体テストで、このモジュールに触れるものを実行して FAIL が無いことを確かめる: `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest tests/store/analytics'`（テストが無ければ「テスト無し」と報告する）。
   - 完了条件: 実行したテストに FAIL が 0 件。

8. **起動確認タスク**: 対象外（理由: ライブラリで、詳細設計書 9-1 に起動方法が無い。import の確認はタスク 2 で行う）。

9. **README.md 記載タスク**: 対象外（理由: ライブラリの起動方法が無く、既存の README を変えない）。

10. **変更の全件確認タスク**（変更要件・変更設計書の全項目を実装したかの確認）
    - 変更設計書の 5-4 の 2 関数、7-2 の 2 ファイル（`__init__.py`・`trace_correlation.py`）、8-2 の 4 シナリオ、11 章の全設計 ID に対応する実装とテストがあることを確かめる。
    - 完了条件: 漏れが無いこと。

11. **実装完了チェックタスク**
    - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
    - 完了条件: 全項目が OK であること（対象外の項目は理由を報告に書く）。

## 修正が要る場合の扱い

- 実装中に設計に無い設計要素が要ることが分かったら、実装を止めて `isdd-spec` での見直しに戻す（設計 ID を実装中に作らない）。

## 依頼の範囲外の既存の不具合

- 依頼の範囲外の既存の不具合は直さず、正本に現状として書く（報告に含める）。
