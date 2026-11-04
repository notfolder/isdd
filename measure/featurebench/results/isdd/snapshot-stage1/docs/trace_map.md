# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-PACKAGE-INIT` | `mlflow/claude_code/__init__.py` | モジュール |
| `DS-MD-CONFIG-MODULE` | `mlflow/claude_code/config.py` | モジュール |
| `DS-MD-HOOKS-MODULE` | `mlflow/claude_code/hooks.py` | モジュール |
| `DS-MD-CLI-MODULE` | `mlflow/claude_code/cli.py` | モジュール |
| `DS-MD-TRACING-MODULE` | `mlflow/claude_code/tracing.py` | モジュール |
| `DS-CL-TRACING-STATUS` | `mlflow/claude_code/config.py::TracingStatus` | データクラス |
| `DS-IF-AUTOLOG-CLI` | `mlflow/claude_code/cli.py::commands` | コマンドの group |
| `DS-IF-AUTOLOG-CLAUDE-COMMAND` | `mlflow/claude_code/cli.py::claude` | 有効化・状態表示・無効化 |
| `DS-IF-STOP-HOOK` | `mlflow/claude_code/hooks.py::stop_hook_handler` | Stop フックの入口 |
| `DS-IF-SDK-STOP-HOOK` | `mlflow/claude_code/hooks.py::sdk_stop_hook_handler` | SDK の停止コールバック |
| `DS-FN-UPSERT-HOOK` | `mlflow/claude_code/hooks.py::upsert_hook` | フック一覧への登録 |
| `DS-FN-SETUP-HOOKS-CONFIG` | `mlflow/claude_code/hooks.py::setup_hooks_config` | 設定ファイルへの登録 |
| `DS-FN-DISABLE-TRACING-HOOKS` | `mlflow/claude_code/hooks.py::disable_tracing_hooks` | 記録の無効化 |
| `DS-FN-STOP-HOOK-HANDLER` | `mlflow/claude_code/hooks.py::stop_hook_handler` | Stop フックの処理 |
| `DS-FN-SDK-STOP-HOOK-HANDLER` | `mlflow/claude_code/hooks.py::sdk_stop_hook_handler` | SDK の停止の処理 |
| `DS-FN-SETUP-LOGGING` | `mlflow/claude_code/tracing.py::setup_logging` | 動作ログの初期化 |
| `DS-FN-GET-LOGGER` | `mlflow/claude_code/tracing.py::get_logger` | ロガーの取得 |
| `DS-FN-SETUP-MLFLOW` | `mlflow/claude_code/tracing.py::setup_mlflow` | 追跡先の設定 |
| `DS-FN-IS-TRACING-ENABLED` | `mlflow/claude_code/tracing.py::is_tracing_enabled` | 有効判定 |
| `DS-FN-READ-HOOK-INPUT` | `mlflow/claude_code/tracing.py::read_hook_input` | フック入力の読み取り |
| `DS-FN-READ-TRANSCRIPT` | `mlflow/claude_code/tracing.py::read_transcript` | トランスクリプトの読み取り |
| `DS-FN-GET-HOOK-RESPONSE` | `mlflow/claude_code/tracing.py::get_hook_response` | 応答の組み立て |
| `DS-FN-PARSE-TIMESTAMP-TO-NS` | `mlflow/claude_code/tracing.py::parse_timestamp_to_ns` | 時刻の変換 |
| `DS-FN-EXTRACT-TEXT-CONTENT` | `mlflow/claude_code/tracing.py::extract_text_content` | 文章の抽出 |
| `DS-FN-FIND-LAST-USER-MESSAGE-INDEX` | `mlflow/claude_code/tracing.py::find_last_user_message_index` | 最後の利用者の発言の特定 |
| `DS-FN-FIND-FINAL-ASSISTANT-RESPONSE` | `mlflow/claude_code/tracing.py::find_final_assistant_response` | 最後の応答の特定 |
| `DS-FN-PROCESS-TRANSCRIPT` | `mlflow/claude_code/tracing.py::process_transcript` | トレース作成 |
| `DS-TS-ENABLE-PROJECT-TRACING` | `e2e/test_claude_code.py::test_enable_project_tracing` | E2E シナリオ |
| `DS-TS-SHOW-TRACING-STATUS` | `e2e/test_claude_code.py::test_show_tracing_status` | E2E シナリオ |
| `DS-TS-DISABLE-PROJECT-TRACING` | `e2e/test_claude_code.py::test_disable_project_tracing` | E2E シナリオ |
| `DS-TS-REGISTER-HOOK-TWICE` | `e2e/test_claude_code.py::test_register_hook_twice` | E2E シナリオ |
| `DS-TS-STOP-HOOK-RECORD` | `e2e/test_claude_code.py::test_stop_hook_records_trace` | E2E シナリオ |
| `DS-TS-STOP-HOOK-DISABLED` | `e2e/test_claude_code.py::test_stop_hook_disabled_records_nothing` | E2E シナリオ |
| `DS-TS-SDK-STOP-RECORD` | `e2e/test_claude_code.py::test_sdk_stop_records_trace` | E2E シナリオ |
| `DS-TS-TRANSCRIPT-WITHOUT-USER` | `e2e/test_claude_code.py::test_transcript_without_user_no_trace` | E2E シナリオ |
| `DS-TS-TRACING-LOG` | `e2e/test_claude_code.py::test_tracing_log_records_failure` | E2E シナリオ |
| `DS-TS-TRACING-STATUS-VALUE` | `e2e/test_claude_code.py::test_tracing_status_value` | E2E シナリオ |
| `DS-FN-LOAD-CLAUDE-CONFIG` | `mlflow/claude_code/config.py::load_claude_config` | 設定ファイルと環境変数 |
| `DS-FN-SAVE-CLAUDE-CONFIG` | `mlflow/claude_code/config.py::save_claude_config` | 設定ファイルと環境変数 |
| `DS-FN-GET-ENV-VAR` | `mlflow/claude_code/config.py::get_env_var` | 設定ファイルと環境変数 |
| `DS-FN-GET-TRACING-STATUS` | `mlflow/claude_code/config.py::get_tracing_status` | 設定ファイルと環境変数 |
| `DS-FN-SETUP-ENVIRONMENT-CONFIG` | `mlflow/claude_code/config.py::setup_environment_config` | 設定ファイルと環境変数 |
| `DS-TS-LOAD-SAVE-CONFIG` | `e2e/test_claude_code.py::test_load_save_config` | E2E シナリオ |
| `DS-TS-GET-ENV-VAR-PRECEDENCE` | `e2e/test_claude_code.py::test_get_env_var_precedence` | E2E シナリオ |
| `DS-TS-READ-TRACING-STATUS-VALUES` | `e2e/test_claude_code.py::test_read_tracing_status_values` | E2E シナリオ |
| `DS-TS-SETUP-ENVIRONMENT-PRECEDENCE` | `e2e/test_claude_code.py::test_setup_environment_precedence` | E2E シナリオ |
