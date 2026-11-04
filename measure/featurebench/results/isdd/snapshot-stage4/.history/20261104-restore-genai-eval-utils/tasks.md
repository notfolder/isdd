# 実装タスク（GenAI 評価結果の整形と表示の復元：mlflow/cli/genai_eval_utils.py）

前提: `docs/active_change` が本変更を指す。実装中は正本を書き換えない（反映は実装後レビューで行い、反映後に `docs/active_change` を削除する）。
対象の変更設計 ID: `DS-MD-GENAI-EVAL-UTILS-MODULE`、`DS-CL-ASSESSMENT`、`DS-CL-CELL`、`DS-CL-EVAL-RESULT`、`DS-CL-TABLE-OUTPUT`、`DS-FN-EXTRACT-ASSESSMENTS-FROM-RESULTS`、`DS-FN-FORMAT-TABLE-OUTPUT`、`DS-FN-RESOLVE-SCORERS`、`DS-TS-EXTRACT-ASSESSMENTS-BY-RUN`、`DS-TS-FORMAT-TABLE-CELLS`、`DS-TS-RESOLVE-SCORERS-NAMES`。

1. 3 関数の実装（`DS-FN-EXTRACT-ASSESSMENTS-FROM-RESULTS`、`DS-FN-FORMAT-TABLE-OUTPUT`、`DS-FN-RESOLVE-SCORERS`）。依頼文の Interface Description どおりのシグネチャ。既存の型と `_format_assessment_cell` は変えない。
   - 完了条件: `from mlflow.cli.genai_eval_utils import ...` が通ること。
2. E2E テストの実装（`e2e/test_genai_eval_utils.py`、3 関数）。
   - 完了条件: 3 件が通ること。
3. 対応表・正本の更新（`docs/trace_map.md`、`docs/detail_design.md`、`docs/requirements.md`）。mlflow/cli は検査の走査範囲に入れない（ANSWERS.md）。
   - 完了条件: `rq_ds_link_checker.py` が欠落・不整合 0 件。
4. E2E 全件の実行（`e2e/results/e2e.xml`）と `bash scripts/isdd/check.sh` の確認。mlflow/cli の「ファイルが見つかりません」は既知の制約。
