# 対応表（設計 ID とコードの対応）

粒度: function（公開関数・メソッドまで）。書式は trace-map-rules.md に従う。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-MAIN` | `app/__main__.py` | 起動の入口 |
| `DS-FN-MAIN` | `app/__main__.py::main` | サーバーを起動する |
| `DS-OP-SERVER-START` | `app/__main__.py::main` | 起動（run.sh から呼ばれる） |
| `DS-MD-CONFIG` | `app/config.py` | 環境変数の読み込み |
| `DS-FN-LOAD-SETTINGS` | `app/config.py::load_settings` | 設定を読む |
| `DS-MD-DATABASE` | `app/db.py` | DB 接続とスキーマ |
| `DS-FN-OPEN-CONNECTION` | `app/db.py::open_connection` | DB に接続する |
| `DS-FN-INITIALIZE-SCHEMA` | `app/db.py::initialize_schema` | スキーマを作る |
| `DS-SC-DATABASE-FILE` | `app/db.py::open_connection` | DB ファイルと接続の設定 |
| `DS-SC-ACCOUNTS` | `app/db.py::initialize_schema` | アカウントの表 |
| `DS-SC-EQUIPMENT` | `app/db.py::initialize_schema` | 備品の表 |
| `DS-SC-LENDING` | `app/db.py::initialize_schema` | 貸出の表 |
| `DS-SC-SESSIONS` | `app/db.py::initialize_schema` | セッションの表 |
| `DS-MD-SECURITY` | `app/security.py` | パスワードとトークン |
| `DS-FN-HASH-PASSWORD` | `app/security.py::hash_password` | パスワードをハッシュにする |
| `DS-FN-VERIFY-PASSWORD` | `app/security.py::verify_password` | パスワードを照合する |
| `DS-FN-NEW-SESSION-TOKEN` | `app/security.py::new_session_token` | セッションのトークンを作る |
| `DS-MD-VALIDATION` | `app/validation.py` | 入力値の検査 |
| `DS-FN-VALIDATE-EMPLOYEE-NUMBER` | `app/validation.py::validate_employee_number` | 社員番号の検査 |
| `DS-FN-VALIDATE-NAME` | `app/validation.py::validate_name` | 名前の検査 |
| `DS-FN-VALIDATE-PASSWORD` | `app/validation.py::validate_password` | パスワードの検査 |
| `DS-FN-VALIDATE-EQUIPMENT-NUMBER` | `app/validation.py::validate_equipment_number` | 管理番号の検査 |
| `DS-FN-VALIDATE-EQUIPMENT-NAME` | `app/validation.py::validate_equipment_name` | 備品名の検査 |
| `DS-FN-VALIDATE-LENT-ON` | `app/validation.py::validate_lent_on` | 貸出日の検査 |
| `DS-MD-ACCOUNTS` | `app/accounts.py` | アカウントの業務 |
| `DS-FN-REGISTER-ACCOUNT` | `app/accounts.py::register_account` | アカウントを登録する |
| `DS-FN-AUTHENTICATE-ACCOUNT` | `app/accounts.py::authenticate_account` | 社員番号とパスワードを照合する |
| `DS-FN-LIST-ACCOUNTS` | `app/accounts.py::list_accounts` | アカウントの一覧 |
| `DS-FN-CHANGE-MANAGER-ROLE` | `app/accounts.py::change_manager_role` | 担当者の付け外し |
| `DS-FN-RESET-PASSWORD` | `app/accounts.py::reset_password` | パスワードを再設定する |
| `DS-FN-DELETE-ACCOUNT` | `app/accounts.py::delete_account` | アカウントを削除する |
| `DS-MD-EQUIPMENT` | `app/equipment.py` | 備品の業務 |
| `DS-FN-CREATE-EQUIPMENT` | `app/equipment.py::create_equipment` | 備品を登録する |
| `DS-FN-UPDATE-EQUIPMENT` | `app/equipment.py::update_equipment` | 備品を修正する |
| `DS-FN-DELETE-EQUIPMENT` | `app/equipment.py::delete_equipment` | 備品を削除する |
| `DS-FN-CHECK-EQUIPMENT-VERSION` | `app/equipment.py::check_equipment_version` | 版番号の検査 |
| `DS-MD-LENDING` | `app/lending.py` | 貸出の業務 |
| `DS-FN-LIST-LENDING-STATUS` | `app/lending.py::list_lending_status` | 貸出状況の一覧 |
| `DS-FN-LEND-EQUIPMENT` | `app/lending.py::lend_equipment` | 貸出を登録する |
| `DS-FN-RETURN-EQUIPMENT` | `app/lending.py::return_equipment` | 返却を登録する |
| `DS-MD-SESSIONS` | `app/sessions.py` | セッションと担当者の検査 |
| `DS-FN-CREATE-SESSION` | `app/sessions.py::create_session` | セッションを作る |
| `DS-FN-RESOLVE-SESSION` | `app/sessions.py::resolve_session` | セッションから利用者を得る |
| `DS-FN-DELETE-SESSION` | `app/sessions.py::delete_session` | セッションを消す |
| `DS-FN-REQUIRE-MANAGER` | `app/sessions.py::require_manager` | 担当者の操作を検査する |
| `DS-MD-WEB` | `app/web.py` | HTTP の振り分けと画面の処理 |
| `DS-CL-REQUEST-HANDLER` | `app/web.py::RequestHandler` | 要求の処理 |
| `DS-CL-REQUEST-HANDLER` | `app/web.py::RequestHandler.do_GET` | GET の振り分け |
| `DS-CL-REQUEST-HANDLER` | `app/web.py::RequestHandler.do_POST` | POST の振り分け |
| `DS-CL-REQUEST-HANDLER` | `app/web.py::RequestHandler.log_message` | アクセスログを出さない |
| `DS-IF-LENDING-STATUS-SCREEN` | `app/web.py::RequestHandler.lending_status_screen` | 貸出状況の画面 |
| `DS-IF-REGISTER-ACCOUNT-SCREEN` | `app/web.py::RequestHandler.register_account_screen` | アカウント登録の画面 |
| `DS-IF-LOGIN-SCREEN` | `app/web.py::RequestHandler.login_screen` | ログインの画面 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `app/web.py::RequestHandler.equipment_form_screen` | 備品の登録・修正の画面 |
| `DS-IF-LENDING-FORM-SCREEN` | `app/web.py::RequestHandler.lending_form_screen` | 貸出の登録の画面 |
| `DS-IF-ACCOUNT-LIST-SCREEN` | `app/web.py::RequestHandler.account_list_screen` | アカウントの一覧の画面 |
| `DS-MD-TEMPLATES` | `app/templates.py` | 画面の HTML |
| `DS-FN-RENDER-PAGE` | `app/templates.py::render_page` | 画面の HTML 全体を返す |
| `DS-TS-REGISTER-ACCOUNTS` | `e2e/test_accounts.py::TestRegisterAccounts.test_register_accounts` | アカウント登録の E2E |
| `DS-TS-REGISTER-ACCOUNTS` | `e2e/test_accounts.py::TestRegisterAccounts.test_register_accounts_limit` | 50 人の上限の E2E |
| `DS-TS-LOGIN-LOGOUT` | `e2e/test_accounts.py::TestLoginLogout.test_login_logout` | ログインとログアウトの E2E |
| `DS-TS-IDLE-LOGOUT` | `e2e/test_accounts.py::TestIdleLogout.test_idle_logout` | 自動ログアウトの E2E |
| `DS-TS-MANAGE-MANAGER-ROLE` | `e2e/test_accounts.py::TestManageAccounts.test_manage_manager_role` | 担当者の付け外しの E2E |
| `DS-TS-RESET-PASSWORD` | `e2e/test_accounts.py::TestManageAccounts.test_reset_password` | パスワード再設定の E2E |
| `DS-TS-DELETE-ACCOUNT` | `e2e/test_accounts.py::TestManageAccounts.test_delete_account` | アカウント削除の E2E |
| `DS-TS-VIEW-LENDING-STATUS` | `e2e/test_equipment.py::TestViewLendingStatus.test_view_lending_status` | 貸出状況の閲覧の E2E |
| `DS-TS-EMPTY-EQUIPMENT-LIST` | `e2e/test_equipment.py::TestEmptyEquipmentList.test_empty_equipment_list` | 備品 0 件の表示の E2E |
| `DS-TS-CREATE-EQUIPMENT` | `e2e/test_equipment.py::TestCreateEquipment.test_create_equipment` | 備品登録の E2E |
| `DS-TS-UPDATE-EQUIPMENT` | `e2e/test_equipment.py::TestUpdateEquipment.test_update_equipment` | 備品修正と同時更新の E2E |
| `DS-TS-DELETE-EQUIPMENT` | `e2e/test_equipment.py::TestDeleteEquipment.test_delete_equipment` | 備品削除の E2E |
| `DS-TS-LEND-EQUIPMENT` | `e2e/test_equipment.py::TestLendEquipment.test_lend_equipment` | 貸出の E2E |
| `DS-TS-RETURN-EQUIPMENT` | `e2e/test_equipment.py::TestReturnEquipment.test_return_equipment` | 返却の E2E |
| `DS-TS-RESTRICT-NON-MANAGER` | `e2e/test_equipment.py::TestRestrictNonManager.test_restrict_non_manager` | 社員と未ログインの操作制限の E2E |
| `DS-TS-KEEP-LENDING-ON-UPDATE` | `e2e/test_equipment.py::TestKeepLendingOnUpdate.test_keep_lending_on_update` | 修正で貸出を引き継ぐ E2E |
| `DS-TS-CONCURRENT-LEND-RETURN` | `e2e/test_equipment.py::TestConcurrentLendReturn.test_concurrent_lend_return` | 同時の貸出と返却の E2E |
| `DS-TS-RESPONSE-TIME` | `e2e/test_nonfunctional.py::TestResponseTime.test_response_time` | 同時 50 件の応答時間 |
| `DS-TS-CONCURRENT-USERS` | `e2e/test_nonfunctional.py::TestConcurrentUsers.test_concurrent_users` | 50 人の同時利用 |
