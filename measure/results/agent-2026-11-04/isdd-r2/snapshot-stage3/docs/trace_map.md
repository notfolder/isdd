# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-PACKAGE-INIT` | `equipment_ledger/__init__.py` | パッケージの印 |
| `DS-MD-CORE-PACKAGE-INIT` | `equipment_ledger/core/__init__.py` | パッケージの印 |
| `DS-MD-MAIN` | `equipment_ledger/__main__.py` | 起動の入口 |
| `DS-FN-START-SERVER` | `equipment_ledger/__main__.py::main` | 設定を読み waitress で待ち受ける |
| `DS-OP-RUN-SCRIPT` | `equipment_ledger/__main__.py::main` | 起動（run.sh から呼ばれる入口） |
| `DS-MD-APP` | `equipment_ledger/app.py` | アプリの作成 |
| `DS-FN-CREATE-APP` | `equipment_ledger/app.py::create_app` | Flask アプリを作る |
| `DS-MD-VIEWS` | `equipment_ledger/views.py` | 画面と操作の受け口 |
| `DS-IF-EQUIPMENT-STATUS-SCREEN` | `equipment_ledger/views.py::status` | 貸出状況の画面 |
| `DS-IF-ACCOUNT-REGISTER-SCREEN` | `equipment_ledger/views.py::register` | アカウント登録 |
| `DS-IF-LOGIN-SCREEN` | `equipment_ledger/views.py::login` | ログイン |
| `DS-IF-LOGOUT` | `equipment_ledger/views.py::logout` | ログアウト |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `equipment_ledger/views.py::equipment_new` | 備品の登録画面 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `equipment_ledger/views.py::equipment_edit` | 備品の修正画面 |
| `DS-IF-EQUIPMENT-DELETE` | `equipment_ledger/views.py::equipment_delete` | 備品の削除 |
| `DS-MD-AUTH` | `equipment_ledger/auth.py` | ログイン状態と担当者の拒否 |
| `DS-FN-CHECK-IDLE-TIMEOUT` | `equipment_ledger/auth.py::check_idle_timeout` | 無操作の自動ログアウト |
| `DS-FN-LOG-IN-USER` | `equipment_ledger/auth.py::log_in_user` | ログイン状態を作る |
| `DS-FN-LOG-OUT-USER` | `equipment_ledger/auth.py::log_out_user` | ログイン状態を消す |
| `DS-FN-CURRENT-USER` | `equipment_ledger/auth.py::current_user` | ログイン中の社員を返す |
| `DS-FN-REQUIRE-MANAGER` | `equipment_ledger/auth.py::require_manager` | 担当者以外の要求を拒否する |
| `DS-OP-ENVIRONMENT-CONFIG` | `equipment_ledger/core/config.py::load_settings` | 環境変数の一覧（HOST、PORT、DATA_DIR、SESSION_IDLE_TIMEOUT_SECONDS） |
| `DS-MD-CONFIG` | `equipment_ledger/core/config.py` | 環境変数の読み込み |
| `DS-FN-LOAD-SETTINGS` | `equipment_ledger/core/config.py::load_settings` | 設定を読む |
| `DS-MD-DB` | `equipment_ledger/core/db.py` | DB 接続とスキーマ |
| `DS-MD-LENDING` | `equipment_ledger/core/lending.py` | 貸出と返却 |
| `DS-FN-OPEN-CONNECTION` | `equipment_ledger/core/db.py::open_connection` | DB を開く（WAL と busy timeout） |
| `DS-SC-ACCOUNT-TABLE` | `equipment_ledger/core/db.py::initialize_schema` | アカウントテーブルの定義（SCHEMA_SQL） |
| `DS-MD-VALIDATION` | `equipment_ledger/core/validation.py` | 入力チェック |
| `DS-FN-VALIDATE-ACCOUNT-INPUT` | `equipment_ledger/core/validation.py::validate_account_input` | アカウント入力の検査 |
| `DS-FN-VALIDATE-EQUIPMENT-INPUT` | `equipment_ledger/core/validation.py::validate_equipment_input` | 備品入力の検査 |
| `DS-MD-ACCOUNTS` | `equipment_ledger/core/accounts.py` | アカウントの登録と照合 |
| `DS-FN-REGISTER-ACCOUNT` | `equipment_ledger/core/accounts.py::register_account` | 登録（最初の 1 件は担当者） |
| `DS-FN-AUTHENTICATE` | `equipment_ledger/core/accounts.py::authenticate` | 社員番号とパスワードの照合 |
| `DS-MD-EQUIPMENT` | `equipment_ledger/core/equipment.py` | 備品の操作 |
| `DS-FN-REGISTER-EQUIPMENT` | `equipment_ledger/core/equipment.py::register_equipment` | 登録 |
| `DS-TS-REGISTER-FIRST-ACCOUNT-E2E` | `e2e/test_equipment_ledger.py::test_register_first_account_as_staff` | E2E |
| `DS-TS-REJECT-ACCOUNT-INPUT-E2E` | `e2e/test_equipment_ledger.py::test_reject_account_input` | E2E |
| `DS-TS-LOGIN-LOGOUT-E2E` | `e2e/test_equipment_ledger.py::test_login_and_logout` | E2E |
| `DS-TS-AUTO-LOGOUT-E2E` | `e2e/test_equipment_ledger.py::test_auto_logout_after_idle` | E2E |
| `DS-TS-REGISTER-EQUIPMENT-E2E` | `e2e/test_equipment_ledger.py::test_register_equipment_as_staff` | E2E |
| `DS-TS-REJECT-EQUIPMENT-INPUT-E2E` | `e2e/test_equipment_ledger.py::test_reject_equipment_input` | E2E |
| `DS-TS-UPDATE-EQUIPMENT-E2E` | `e2e/test_equipment_ledger.py::test_update_equipment` | E2E |
| `DS-TS-DELETE-EQUIPMENT-E2E` | `e2e/test_equipment_ledger.py::test_delete_equipment` | E2E |
| `DS-TS-VIEW-STATUS-WITHOUT-LOGIN-E2E` | `e2e/test_equipment_ledger.py::test_view_status_without_login` | E2E |
| `DS-TS-VIEW-EMPTY-STATUS-E2E` | `e2e/test_equipment_ledger.py::test_view_empty_status` | E2E |
| `DS-TS-DENY-NON-STAFF-E2E` | `e2e/test_equipment_ledger.py::test_deny_non_staff` | E2E |
| `DS-TS-PERFORMANCE-E2E` | `e2e/test_equipment_ledger.py::test_performance_within_limit` | E2E |
| `DS-FN-LIST-EQUIPMENT-STATUS-WITH-LENDING` | `equipment_ledger/core/equipment.py::list_equipment_status` | 一覧（貸出の行を結ぶ、管理番号の昇順） |
| `DS-FN-GET-EQUIPMENT-WITH-REVISION` | `equipment_ledger/core/equipment.py::get_equipment` | 1 件の取得（版番号つき） |
| `DS-FN-UPDATE-EQUIPMENT-IF-UNCHANGED` | `equipment_ledger/core/equipment.py::update_equipment` | 版番号が一致するときだけ備品名の修正 |
| `DS-FN-DELETE-EQUIPMENT-IF-NOT-LENT` | `equipment_ledger/core/equipment.py::delete_equipment` | 貸出中でなければ削除（記録は残さない） |
| `DS-FN-INITIALIZE-SCHEMA-WITH-MIGRATION` | `equipment_ledger/core/db.py::initialize_schema` | 3 テーブルを作り、版番号の列を移行する |
| `DS-SC-EQUIPMENT-TABLE-WITH-REVISION` | `equipment_ledger/core/db.py::initialize_schema` | 備品テーブルの定義（SCHEMA_SQL、版番号の列） |
| `DS-SC-LENDING-TABLE` | `equipment_ledger/core/db.py::initialize_schema` | 貸出テーブルの定義（SCHEMA_SQL） |
| `DS-FN-LEND-EQUIPMENT` | `equipment_ledger/core/lending.py::lend_equipment` | 貸出の登録（先の 1 件だけ記録） |
| `DS-FN-RETURN-EQUIPMENT` | `equipment_ledger/core/lending.py::return_equipment` | 返却（記録は残さない） |
| `DS-FN-VALIDATE-LENDING-INPUT` | `equipment_ledger/core/validation.py::validate_lending_input` | 貸出入力の検査 |
| `DS-FN-LIST-BORROWER-CANDIDATES` | `equipment_ledger/core/accounts.py::list_borrower_candidates` | 借りる社員の候補 |
| `DS-IF-LEND-SCREEN` | `equipment_ledger/views.py::equipment_lend` | 貸出の登録画面 |
| `DS-IF-RETURN-EQUIPMENT` | `equipment_ledger/views.py::equipment_return` | 返却 |
| `DS-TS-LEND-EQUIPMENT-E2E` | `e2e/test_equipment_ledger.py::test_lend_equipment_as_staff` | E2E |
| `DS-TS-REJECT-INVALID-LEND-E2E` | `e2e/test_equipment_ledger.py::test_reject_invalid_lend` | E2E |
| `DS-TS-RETURN-EQUIPMENT-E2E` | `e2e/test_equipment_ledger.py::test_return_equipment_as_staff` | E2E |
| `DS-TS-DENY-DELETE-WHILE-LENT-E2E` | `e2e/test_equipment_ledger.py::test_deny_delete_while_lent` | E2E |
| `DS-TS-EDIT-KEEPS-LENDING-E2E` | `e2e/test_equipment_ledger.py::test_edit_keeps_lending` | E2E |
| `DS-TS-REJECT-STALE-EDIT-E2E` | `e2e/test_equipment_ledger.py::test_reject_stale_edit` | E2E |
| `DS-TS-CONCURRENT-LEND-E2E` | `e2e/test_equipment_ledger.py::test_concurrent_lend_only_first_recorded` | E2E |
| `DS-TS-CONCURRENT-RETURN-E2E` | `e2e/test_equipment_ledger.py::test_concurrent_return_only_first_processed` | E2E |
| `DS-TS-DENY-NON-STAFF-LENDING-E2E` | `e2e/test_equipment_ledger.py::test_deny_non_staff_lending` | E2E |
| `DS-FN-VALIDATE-PASSWORD-INPUT` | `equipment_ledger/core/validation.py::validate_password_input` | 再設定の新しいパスワードの検査 |
| `DS-FN-LIST-ACCOUNTS` | `equipment_ledger/core/accounts.py::list_accounts` | 全アカウントの一覧（パスワードは返さない） |
| `DS-FN-CHANGE-ACCOUNT-ROLE` | `equipment_ledger/core/accounts.py::change_account_role` | 権限の付け外し（最後の担当者は外さない） |
| `DS-FN-RESET-PASSWORD` | `equipment_ledger/core/accounts.py::reset_password` | パスワードのハッシュを置き換える |
| `DS-FN-DELETE-ACCOUNT` | `equipment_ledger/core/accounts.py::delete_account` | 借りていない、最後の担当者でないときだけ物理削除 |
| `DS-FN-SYNC-SESSION-WITH-ACCOUNT` | `equipment_ledger/auth.py::sync_session_user` | 要求ごとにセッションを DB の権限と存在に合わせる |
| `DS-IF-ACCOUNT-LIST-SCREEN` | `equipment_ledger/views.py::accounts` | アカウントの一覧の画面（/accounts/） |
| `DS-IF-ACCOUNT-ROLE-CHANGE` | `equipment_ledger/views.py::account_role` | 担当者の付け外し |
| `DS-IF-ACCOUNT-PASSWORD-RESET` | `equipment_ledger/views.py::account_password` | パスワードの再設定 |
| `DS-IF-ACCOUNT-DELETE` | `equipment_ledger/views.py::account_delete` | アカウントの削除 |
| `DS-TS-VIEW-ACCOUNT-LIST-E2E` | `e2e/test_equipment_ledger.py::test_view_account_list_as_staff` | E2E |
| `DS-TS-CHANGE-ROLE-E2E` | `e2e/test_equipment_ledger.py::test_change_role` | E2E |
| `DS-TS-KEEP-ONE-STAFF-E2E` | `e2e/test_equipment_ledger.py::test_keep_one_staff` | E2E |
| `DS-TS-CONCURRENT-DEMOTE-E2E` | `e2e/test_equipment_ledger.py::test_concurrent_demote_keeps_one_staff` | E2E |
| `DS-TS-RESET-PASSWORD-E2E` | `e2e/test_equipment_ledger.py::test_reset_password` | E2E |
| `DS-TS-DELETE-ACCOUNT-E2E` | `e2e/test_equipment_ledger.py::test_delete_account` | E2E |
| `DS-TS-DENY-DELETE-LENT-BORROWER-E2E` | `e2e/test_equipment_ledger.py::test_deny_delete_lent_borrower` | E2E |
| `DS-TS-DENY-NON-STAFF-ACCOUNT-E2E` | `e2e/test_equipment_ledger.py::test_deny_non_staff_account` | E2E |
