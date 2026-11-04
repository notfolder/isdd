# 対応表（設計 ID とコードの対応）

粒度: function（ファイル・公開関数・メソッドまで）。書式は trace-map-rules.md に従う。要件との対応は詳細設計書の第 11 章にある。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-PACKAGE-INIT` | `src/__init__.py` | モジュール |
| `DS-MD-MAIN` | `src/main.py` | モジュール |
| `DS-FN-MAIN` | `src/main.py::main` | 起動の入口 |
| `DS-MD-CONFIG` | `src/config.py` | モジュール |
| `DS-FN-LOAD-SETTINGS` | `src/config.py::load_settings` | 環境変数の読み取り |
| `DS-MD-DB` | `src/db.py` | モジュール |
| `DS-FN-CONNECT` | `src/db.py::connect` | DB 接続 |
| `DS-FN-INIT-SCHEMA` | `src/db.py::init_schema` | スキーマ作成 |
| `DS-SC-ACCOUNT-TABLE` | `src/db.py::init_schema` | accounts テーブルの定義（スキーマ文字列） |
| `DS-SC-EQUIPMENT-TABLE` | `src/db.py::init_schema` | equipment テーブルの定義 |
| `DS-SC-SESSION-TABLE` | `src/db.py::init_schema` | sessions テーブルの定義 |
| `DS-MD-VALIDATION` | `src/validation.py` | モジュール |
| `DS-FN-VALIDATE-ACCOUNT-INPUT` | `src/validation.py::validate_account_input` | アカウント入力の検査 |
| `DS-FN-VALIDATE-EQUIPMENT-INPUT` | `src/validation.py::validate_equipment_input` | 備品入力の検査 |
| `DS-MD-ACCOUNTS` | `src/accounts.py` | モジュール |
| `DS-FN-HASH-PASSWORD` | `src/accounts.py::hash_password` | パスワードのハッシュ化 |
| `DS-FN-REGISTER-ACCOUNT` | `src/accounts.py::register_account` | アカウント登録（最初は担当者） |
| `DS-FN-VERIFY-LOGIN` | `src/accounts.py::verify_login` | ログインの照合 |
| `DS-MD-SESSIONS` | `src/sessions.py` | モジュール |
| `DS-FN-CREATE-SESSION` | `src/sessions.py::create_session` | セッションの作成 |
| `DS-FN-RESOLVE-SESSION` | `src/sessions.py::resolve_session` | セッションの確認と期限 |
| `DS-FN-DELETE-SESSION` | `src/sessions.py::delete_session` | セッションの削除 |
| `DS-MD-AUTH` | `src/auth.py` | モジュール |
| `DS-FN-CURRENT-USER` | `src/auth.py::current_user` | 現在の利用者 |
| `DS-FN-REQUIRE-MANAGER` | `src/auth.py::require_manager` | 担当者の判定 |
| `DS-MD-EQUIPMENT` | `src/equipment.py` | モジュール |
| `DS-FN-LIST-EQUIPMENT` | `src/equipment.py::list_equipment` | 備品の一覧 |
| `DS-FN-GET-EQUIPMENT` | `src/equipment.py::get_equipment` | 備品の取得 |
| `DS-FN-CREATE-EQUIPMENT` | `src/equipment.py::create_equipment` | 備品の登録 |
| `DS-FN-UPDATE-EQUIPMENT` | `src/equipment.py::update_equipment` | 備品の修正 |
| `DS-FN-DELETE-EQUIPMENT` | `src/equipment.py::delete_equipment` | 備品の削除 |
| `DS-MD-WEB` | `src/web.py` | モジュール |
| `DS-FN-CREATE-APP` | `src/web.py::create_app` | Flask アプリの作成 |
| `DS-IF-EQUIPMENT-STATUS-SCREEN` | `src/web.py::equipment_status` | 貸出状況の画面 |
| `DS-IF-ACCOUNT-REGISTER-SCREEN` | `src/web.py::account_register` | アカウント登録の画面 |
| `DS-IF-LOGIN-SCREEN` | `src/web.py::login` | ログインの画面 |
| `DS-IF-LOGOUT-ACTION` | `src/web.py::logout` | ログアウトの操作 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `src/web.py::equipment_new` | 備品の登録の画面 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `src/web.py::equipment_edit` | 備品の修正の画面 |
| `DS-IF-EQUIPMENT-DELETE-ACTION` | `src/web.py::equipment_delete` | 備品の削除の操作 |
| `DS-TS-REGISTER-FIRST-ACCOUNT-E2E` | `e2e/test_accounts.py::AccountE2E.test_register_first_account` | E2E |
| `DS-TS-REGISTER-SECOND-ACCOUNT-E2E` | `e2e/test_accounts.py::AccountE2E.test_register_second_account_is_employee` | E2E |
| `DS-TS-ACCOUNT-INPUT-VALIDATION-E2E` | `e2e/test_accounts.py::AccountE2E.test_account_input_validation` | E2E |
| `DS-TS-LOGIN-E2E` | `e2e/test_accounts.py::AccountE2E.test_login_success_and_failure` | E2E |
| `DS-TS-LOGOUT-E2E` | `e2e/test_accounts.py::AccountE2E.test_logout` | E2E |
| `DS-TS-AUTO-LOGOUT-E2E` | `e2e/test_accounts.py::AutoLogoutE2E.test_auto_logout_after_idle` | E2E |
| `DS-TS-REGISTER-EQUIPMENT-E2E` | `e2e/test_equipment.py::RegisterEquipmentE2E.test_register_equipment` | E2E |
| `DS-TS-EQUIPMENT-INPUT-VALIDATION-E2E` | `e2e/test_equipment.py::RegisterEquipmentE2E.test_equipment_input_validation` | E2E |
| `DS-TS-UPDATE-EQUIPMENT-E2E` | `e2e/test_equipment.py::ManageEquipmentE2E.test_update_equipment` | E2E |
| `DS-TS-DELETE-EQUIPMENT-E2E` | `e2e/test_equipment.py::ManageEquipmentE2E.test_delete_equipment_needs_confirmation` | E2E |
| `DS-TS-VIEW-STATUS-ANONYMOUS-E2E` | `e2e/test_equipment.py::ViewEquipmentE2E.test_view_status_anonymous` | E2E |
| `DS-TS-VIEW-STATUS-EMPTY-E2E` | `e2e/test_equipment.py::ViewEquipmentE2E.test_view_status_empty` | E2E |
| `DS-TS-EMPLOYEE-CANNOT-OPERATE-E2E` | `e2e/test_equipment.py::PermissionE2E.test_employee_cannot_operate` | E2E |
| `DS-TS-ANONYMOUS-CANNOT-OPERATE-E2E` | `e2e/test_equipment.py::PermissionE2E.test_anonymous_cannot_operate` | E2E |
| `DS-TS-NONFUNCTIONAL-LOAD-E2E` | `e2e/test_equipment.py::NonFunctionalLoadE2E.test_status_page_responds_within_three_seconds` | E2E（非機能） |
