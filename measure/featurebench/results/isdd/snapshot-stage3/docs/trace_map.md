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
| `DS-MD-ANALYTICS-PACKAGE-INIT` | `mlflow/store/analytics/__init__.py` | モジュール |
| `DS-MD-TRACE-CORRELATION-MODULE` | `mlflow/store/analytics/trace_correlation.py` | モジュール |
| `DS-CL-TRACE-CORRELATION-COUNTS` | `mlflow/store/analytics/trace_correlation.py::TraceCorrelationCounts` | データクラス |
| `DS-CL-NPMI-RESULT` | `mlflow/store/analytics/trace_correlation.py::NPMIResult` | データクラス |
| `DS-FN-CALCULATE-NPMI-FROM-COUNTS` | `mlflow/store/analytics/trace_correlation.py::calculate_npmi_from_counts` | 素の値と平滑化の値 |
| `DS-FN-CALCULATE-SMOOTHED-NPMI` | `mlflow/store/analytics/trace_correlation.py::calculate_smoothed_npmi` | 平滑化の値 |
| `DS-TS-NPMI-UNSMOOTHED-VALUES` | `e2e/test_trace_correlation.py::test_npmi_unsmoothed_values` | E2E シナリオ |
| `DS-TS-NPMI-INCONSISTENT-COUNTS` | `e2e/test_trace_correlation.py::test_npmi_inconsistent_counts` | E2E シナリオ |
| `DS-TS-NPMI-PERFECT-COOCCURRENCE` | `e2e/test_trace_correlation.py::test_npmi_perfect_cooccurrence` | E2E シナリオ |
| `DS-TS-SMOOTHED-NPMI-JEFFREYS` | `e2e/test_trace_correlation.py::test_smoothed_npmi_jeffreys` | E2E シナリオ |
| `DS-MD-SERVER-SECURITY-MODULE` | `mlflow/server/security.py` | モジュール |
| `DS-MD-SERVER-SECURITY-UTILS-MODULE` | `mlflow/server/security_utils.py` | モジュール |
| `DS-FN-GET-ALLOWED-HOSTS` | `mlflow/server/security.py::get_allowed_hosts` | 許可ホストの取得 |
| `DS-FN-GET-ALLOWED-ORIGINS` | `mlflow/server/security.py::get_allowed_origins` | 許可オリジンの取得 |
| `DS-FN-INIT-SECURITY-MIDDLEWARE` | `mlflow/server/security.py::init_security_middleware` | Flask への安全策の登録 |
| `DS-FN-IS-ALLOWED-HOST-HEADER` | `mlflow/server/security_utils.py::is_allowed_host_header` | Host の照合 |
| `DS-FN-GET-ALLOWED-HOSTS-FROM-ENV` | `mlflow/server/security_utils.py::get_allowed_hosts_from_env` | 環境変数の許可ホスト |
| `DS-FN-GET-ALLOWED-ORIGINS-FROM-ENV` | `mlflow/server/security_utils.py::get_allowed_origins_from_env` | 環境変数の許可オリジン |
| `DS-FN-GET-LOCALHOST-ADDRESSES` | `mlflow/server/security_utils.py::get_localhost_addresses` | localhost 系のアドレス |
| `DS-FN-GET-PRIVATE-IP-PATTERNS` | `mlflow/server/security_utils.py::get_private_ip_patterns` | プライベート範囲のパターン |
| `DS-FN-GET-DEFAULT-ALLOWED-HOSTS` | `mlflow/server/security_utils.py::get_default_allowed_hosts` | 既定の許可ホスト |
| `DS-FN-IS-API-ENDPOINT` | `mlflow/server/security_utils.py::is_api_endpoint` | API 経路の判定 |
| `DS-FN-IS-LOCALHOST-ORIGIN` | `mlflow/server/security_utils.py::is_localhost_origin` | localhost のオリジンの判定 |
| `DS-FN-SHOULD-BLOCK-CORS-REQUEST` | `mlflow/server/security_utils.py::should_block_cors_request` | CORS 遮断の判定 |
| `DS-TS-SECURITY-ALLOWED-HOSTS-AND-ORIGINS` | `e2e/test_security_middleware.py::test_security_allowed_hosts_and_origins` | E2E |
| `DS-TS-SECURITY-HOST-VALIDATION` | `e2e/test_security_middleware.py::test_security_host_validation` | E2E |
| `DS-TS-SECURITY-CORS-BLOCKING` | `e2e/test_security_middleware.py::test_security_cors_blocking` | E2E |
| `DS-TS-SECURITY-RESPONSE-HEADERS` | `e2e/test_security_middleware.py::test_security_response_headers` | E2E |
| `DS-TS-SECURITY-DISABLED` | `e2e/test_security_middleware.py::test_security_disabled` | E2E |
