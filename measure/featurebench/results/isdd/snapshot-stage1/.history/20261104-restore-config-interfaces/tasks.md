# 実装タスク（設定ファイルと環境変数の 5 インターフェースの復元）

前提: `docs/active_change` が本変更を指している。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない（反映は実装後レビュー）。

## タスク

1. `mlflow/claude_code/config.py` に 5 関数を追加する（`load_claude_config`・`save_claude_config`・`get_env_var`・`get_tracing_status`・`setup_environment_config`）。シグネチャと戻り値は REQUEST.md の Interface Description どおり。既存の定数と `TracingStatus` は変えない。
2. 呼び出し側の import 行を足す（承認済み）: `hooks.py` に `load_claude_config`・`save_claude_config`、`cli.py` に `setup_environment_config`・`get_tracing_status`、`tracing.py` に `get_env_var`。処理は変えない。
3. `docs/trace_map.md` に、5 関数の DS-ID（`DS-FN-LOAD-CLAUDE-CONFIG`・`DS-FN-SAVE-CLAUDE-CONFIG`・`DS-FN-GET-ENV-VAR`・`DS-FN-GET-TRACING-STATUS`・`DS-FN-SETUP-ENVIRONMENT-CONFIG`）の行を、変更設計書の「修飾名」で足す。
4. `e2e/test_claude_code.py` に、4 つの DS-TS（`DS-TS-LOAD-SAVE-CONFIG`・`DS-TS-GET-ENV-VAR-PRECEDENCE`・`DS-TS-READ-TRACING-STATUS-VALUES`・`DS-TS-SETUP-ENVIRONMENT-PRECEDENCE`）に対応するテスト関数を書き、対応表の DS-TS の行に結ぶ。
5. 完了条件（実装）: 既存の単体テスト `docker exec fb-isdd bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest tests/claude_code'` が、既存の 19 合格を保つ（既存の status テストは直る）。E2E `pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。`bash scripts/isdd/check.sh --strict` を実行する。
6. 実装後レビュー（isdd-build）で、変更を正本へ反映し、`docs/active_change` を消す。
