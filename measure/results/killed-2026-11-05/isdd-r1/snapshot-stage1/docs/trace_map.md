# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-ENTRYPOINT` | `src/equipment_ledger/__main__.py` | 起動の入口 |
| `DS-FN-START-SERVER` | `src/equipment_ledger/__main__.py::main` | 設定を読み、Waitress で待ち受ける |
| `DS-MD-CONFIG` | `src/equipment_ledger/config.py` | 設定の読み込み |
| `DS-FN-LOAD-CONFIG` | `src/equipment_ledger/config.py::load_config` | 環境変数から設定を読む |
| `DS-MD-DB` | `src/equipment_ledger/db.py` | SQLite の接続と初期化 |
| `DS-FN-CONNECT-DATABASE` | `src/equipment_ledger/db.py::connect_database` | SQLite へ接続する |
| `DS-FN-CONNECT-DATABASE` | `src/equipment_ledger/db.py::get_db` | リクエストごとの接続を開く（connect_database を使う） |
| `DS-FN-CONNECT-DATABASE` | `src/equipment_ledger/db.py::close_db` | リクエストの終わりに接続を閉じる |
| `DS-FN-INITIALIZE-DATABASE` | `src/equipment_ledger/db.py::initialize_database` | テーブルを作る |
| `DS-SC-EQUIPMENT-TABLE` | `src/equipment_ledger/db.py::initialize_database` | 備品テーブルの定義（SCHEMA） |
| `DS-SC-ACCOUNT-TABLE` | `src/equipment_ledger/db.py::initialize_database` | アカウントテーブルの定義（SCHEMA） |
| `DS-MD-VALIDATION` | `src/equipment_ledger/validation.py` | 入力の検証 |
| `DS-FN-VALIDATE-ACCOUNT-INPUT` | `src/equipment_ledger/validation.py::validate_account_input` | アカウント入力の検証 |
| `DS-FN-VALIDATE-EQUIPMENT-INPUT` | `src/equipment_ledger/validation.py::validate_equipment_input` | 備品入力の検証 |
| `DS-MD-ACCOUNTS` | `src/equipment_ledger/accounts.py` | アカウントの登録と認証 |
| `DS-FN-REGISTER-ACCOUNT` | `src/equipment_ledger/accounts.py::register_account` | 登録（最初の登録者は担当者） |
| `DS-FN-FIND-ACCOUNT` | `src/equipment_ledger/accounts.py::find_account` | 社員番号で探す |
| `DS-FN-AUTHENTICATE-ACCOUNT` | `src/equipment_ledger/accounts.py::authenticate_account` | 社員番号とパスワードの照合 |
| `DS-MD-EQUIPMENT` | `src/equipment_ledger/equipment.py` | 備品の一覧・登録・修正・削除 |
| `DS-FN-LIST-EQUIPMENT` | `src/equipment_ledger/equipment.py::list_equipment` | 管理番号の昇順で一覧 |
| `DS-FN-FIND-EQUIPMENT` | `src/equipment_ledger/equipment.py::find_equipment` | 管理番号で 1 件探す |
| `DS-FN-CREATE-EQUIPMENT` | `src/equipment_ledger/equipment.py::create_equipment` | 登録 |
| `DS-FN-UPDATE-EQUIPMENT` | `src/equipment_ledger/equipment.py::update_equipment` | 修正 |
| `DS-FN-DELETE-EQUIPMENT` | `src/equipment_ledger/equipment.py::delete_equipment` | 削除（記録は残さない） |
| `DS-MD-AUTH` | `src/equipment_ledger/auth.py` | セッション、権限、期限切れ |
| `DS-FN-LOG-IN` | `src/equipment_ledger/auth.py::log_in` | ログイン（セッションを作る） |
| `DS-FN-LOG-OUT` | `src/equipment_ledger/auth.py::log_out` | ログアウト |
| `DS-FN-CURRENT-ACCOUNT` | `src/equipment_ledger/auth.py::current_account` | ログイン中のアカウント |
| `DS-FN-EXPIRE-IDLE-SESSION` | `src/equipment_ledger/auth.py::expire_idle_session` | 無操作の期限切れ |
| `DS-FN-REQUIRE-MANAGER` | `src/equipment_ledger/auth.py::require_manager` | 担当者だけの画面・操作 |
| `DS-MD-WEB` | `src/equipment_ledger/web.py` | Web アプリと画面 |
| `DS-FN-CREATE-APP` | `src/equipment_ledger/web.py::create_app` | Flask アプリの作成 |
| `DS-IF-EQUIPMENT-STATUS-SCREEN` | `src/equipment_ledger/web.py::equipment_status` | 貸出状況（`/`） |
| `DS-IF-ACCOUNT-REGISTER-SCREEN` | `src/equipment_ledger/web.py::register_account` | アカウント登録（`/accounts/register/`） |
| `DS-IF-LOGIN-SCREEN` | `src/equipment_ledger/web.py::login` | ログイン（`/login/`） |
| `DS-IF-LOGOUT-ACTION` | `src/equipment_ledger/web.py::logout` | ログアウト（`/logout/`） |
| `DS-IF-EQUIPMENT-NEW-SCREEN` | `src/equipment_ledger/web.py::new_equipment` | 備品の登録（`/equipment/new/`） |
| `DS-IF-EQUIPMENT-EDIT-SCREEN` | `src/equipment_ledger/web.py::edit_equipment` | 備品の修正 |
| `DS-IF-EQUIPMENT-DELETE-ACTION` | `src/equipment_ledger/web.py::delete_equipment` | 備品の削除 |
| `DS-TS-REGISTER-ACCOUNT` | `e2e/test_accounts.py::test_register_account` | E2E |
| `DS-TS-LOGIN-LOGOUT` | `e2e/test_accounts.py::test_login_logout` | E2E |
| `DS-TS-IDLE-LOGOUT` | `e2e/test_accounts.py::test_idle_logout` | E2E |
| `DS-TS-VIEW-STATUS` | `e2e/test_equipment.py::test_view_status` | E2E |
| `DS-TS-CREATE-EQUIPMENT` | `e2e/test_equipment.py::test_create_equipment` | E2E |
| `DS-TS-UPDATE-EQUIPMENT` | `e2e/test_equipment.py::test_update_equipment` | E2E |
| `DS-TS-DELETE-EQUIPMENT` | `e2e/test_equipment.py::test_delete_equipment` | E2E |
| `DS-TS-RESTRICT-NON-MANAGER` | `e2e/test_equipment.py::test_restrict_non_manager` | E2E |
| `DS-TS-RESPONSE-TIME` | `e2e/test_performance.py::test_response_time` | E2E |
