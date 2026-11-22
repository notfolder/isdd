# 対応表: 設計 ID とコードの対応

粒度: `class`（設計書 第 7 章）。ファイル、クラス、設計で名前を付けた関数・画面・テストを載せる。要件 ID との対応は設計書 第 11 章で持つ。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-MAIN` | `src/main.py` | 起動の入口 |
| `DS-MD-WEB-APP` | `src/web/app.py` | Flask アプリの組み立てと例外の画面 |
| `DS-MD-WEB-AUTH` | `src/web/auth.py` | ログイン状態の取り出しとセッション |
| `DS-MD-WEB-VIEWS` | `src/web/views.py` | 画面のルーティングと描画 |
| `DS-MD-SERVICE-ACCOUNTS` | `src/service/accounts.py` | 利用者の登録と認証 |
| `DS-MD-SERVICE-EQUIPMENT` | `src/service/equipment.py` | 備品の管理と一覧 |
| `DS-MD-SERVICE-LENDING` | `src/service/lending.py` | 貸出と返却 |
| `DS-MD-SERVICE-ERRORS` | `src/service/errors.py` | 業務エラー |
| `DS-MD-SERVICE-VALIDATION` | `src/service/validation.py` | 入力の検査 |
| `DS-MD-SERVICE-PERMISSIONS` | `src/service/permissions.py` | 担当者の権限 |
| `DS-MD-SERVICE-CLOCK` | `src/service/clock.py` | 日本時間 |
| `DS-MD-DATA-DATABASE` | `src/data/database.py` | SQLite の接続とトランザクション |
| `DS-MD-DATA-REPOSITORIES` | `src/data/repositories.py` | 3 つの表の読み書き |
| `DS-CL-SERVICES-BUNDLE` | `src/main.py::Services` | 業務層の入れ物 |
| `DS-FN-MAIN` | `src/main.py::main` | 設定を読み、起動する |
| `DS-FN-BUILD-SERVICES` | `src/main.py::build_services` | データベースと業務層を組み立てる |
| `DS-FN-LOAD-SECRET-KEY` | `src/main.py::load_secret_key` | セッションの秘密の値を読むか作る |
| `DS-FN-CREATE-APP` | `src/web/app.py::create_app` | Flask アプリを作る |
| `DS-FN-HANDLE-PERMISSION-DENIED` | `src/web/app.py::handle_permission_denied` | 403 の画面 |
| `DS-FN-CURRENT-USER` | `src/web/auth.py::current_user` | ログイン中の利用者 |
| `DS-FN-START-SESSION` | `src/web/auth.py::start_session` | ログインの開始 |
| `DS-FN-END-SESSION` | `src/web/auth.py::end_session` | ログアウト |
| `DS-CL-ACCOUNT-SERVICE` | `src/service/accounts.py::AccountService` | 利用者の登録と認証 |
| `DS-CL-USER-VALUE` | `src/service/accounts.py::User` | 利用者の値 |
| `DS-CL-EQUIPMENT-SERVICE` | `src/service/equipment.py::EquipmentService` | 備品の管理と一覧 |
| `DS-CL-EQUIPMENT-STATUS` | `src/service/equipment.py::EquipmentStatus` | 一覧の 1 行 |
| `DS-CL-EQUIPMENT-ITEM` | `src/service/equipment.py::EquipmentItem` | 備品 1 件の値 |
| `DS-CL-LENDING-SERVICE` | `src/service/lending.py::LendingService` | 貸出と返却 |
| `DS-CL-SERVICE-ERROR` | `src/service/errors.py::ServiceError` | 業務エラー |
| `DS-CL-NOT-FOUND-ERROR` | `src/service/errors.py::NotFoundError` | 対象が無い |
| `DS-FN-VALIDATE-ACCOUNT-FIELDS` | `src/service/validation.py::validate_account_fields` | 利用者の入力の検査 |
| `DS-FN-VALIDATE-EQUIPMENT-FIELDS` | `src/service/validation.py::validate_equipment_fields` | 備品の入力の検査 |
| `DS-FN-VALIDATE-LENDING-FIELDS` | `src/service/validation.py::validate_lending_fields` | 貸出の入力の検査 |
| `DS-CL-PERMISSION-DENIED` | `src/service/permissions.py::PermissionDenied` | 権限が無い |
| `DS-FN-REQUIRE-MANAGER` | `src/service/permissions.py::require_manager` | 担当者の確認 |
| `DS-FN-TODAY-JST` | `src/service/clock.py::today_jst` | 日本時間の今日 |
| `DS-CL-DATABASE` | `src/data/database.py::Database` | SQLite の接続とトランザクション |
| `DS-CL-USER-REPOSITORY` | `src/data/repositories.py::UserRepository` | 利用者の表 |
| `DS-CL-EQUIPMENT-REPOSITORY` | `src/data/repositories.py::EquipmentRepository` | 備品の表 |
| `DS-CL-LENDING-REPOSITORY` | `src/data/repositories.py::LendingRepository` | 貸出記録の表 |
| `DS-CL-DUPLICATE-ERROR` | `src/data/repositories.py::DuplicateError` | 一意制約の違反 |
| `DS-IF-STATUS-PAGE` | `src/web/views.py::status_page` | 貸出状況（`/`） |
| `DS-IF-REGISTER-ACCOUNT-PAGE` | `src/web/views.py::register_account_page` | アカウント登録 |
| `DS-IF-LOGIN-PAGE` | `src/web/views.py::login_page` | ログイン |
| `DS-IF-LOGOUT` | `src/web/views.py::logout` | ログアウト |
| `DS-IF-EQUIPMENT-NEW-PAGE` | `src/web/views.py::equipment_new_page` | 備品の登録 |
| `DS-IF-EQUIPMENT-EDIT-PAGE` | `src/web/views.py::equipment_edit_page` | 備品の修正 |
| `DS-IF-EQUIPMENT-DELETE` | `src/web/views.py::equipment_delete` | 備品の削除 |
| `DS-IF-LENDING-NEW-PAGE` | `src/web/views.py::lending_new_page` | 貸出の登録 |
| `DS-IF-LENDING-RETURN` | `src/web/views.py::lending_return` | 返却 |
| `DS-TS-FIRST-ACCOUNT-IS-MANAGER` | `e2e/test_accounts.py::test_first_account_is_manager` | 最初の登録者は担当者 |
| `DS-TS-SECOND-ACCOUNT-IS-MEMBER` | `e2e/test_accounts.py::test_second_account_is_member` | 2 人目以降は社員 |
| `DS-TS-REJECT-INVALID-ACCOUNT` | `e2e/test_accounts.py::test_reject_invalid_account` | 不正な登録の拒否 |
| `DS-TS-LOGIN-LOGOUT` | `e2e/test_accounts.py::test_login_logout` | ログインとログアウト |
| `DS-TS-LOGIN-FAILURE` | `e2e/test_accounts.py::test_login_failure` | ログインの失敗 |
| `DS-TS-REGISTER-EQUIPMENT` | `e2e/test_equipment.py::test_register_equipment` | 備品の登録 |
| `DS-TS-REJECT-INVALID-EQUIPMENT` | `e2e/test_equipment.py::test_reject_invalid_equipment` | 不正な備品の拒否 |
| `DS-TS-EDIT-EQUIPMENT` | `e2e/test_equipment.py::test_edit_equipment` | 備品の修正 |
| `DS-TS-DELETE-EQUIPMENT` | `e2e/test_equipment.py::test_delete_equipment` | 備品の削除 |
| `DS-TS-REFUSE-DELETE-LENT` | `e2e/test_equipment.py::test_refuse_delete_lent` | 貸出中の削除の拒否 |
| `DS-TS-LEND-EQUIPMENT` | `e2e/test_lending.py::test_lend_equipment` | 貸出の登録 |
| `DS-TS-REJECT-INVALID-LENDING` | `e2e/test_lending.py::test_reject_invalid_lending` | 不正な貸出と貸出中への貸出の拒否 |
| `DS-TS-RETURN-EQUIPMENT` | `e2e/test_lending.py::test_return_equipment` | 返却 |
| `DS-TS-VIEW-STATUS-ANONYMOUS` | `e2e/test_status.py::test_view_status_anonymous` | 未ログインの閲覧 |
| `DS-TS-VIEW-EMPTY-STATUS` | `e2e/test_status.py::test_view_empty_status` | 備品 0 件 |
| `DS-TS-MEMBER-CANNOT-OPEN-MANAGER-SCREEN` | `e2e/test_status.py::test_member_cannot_open_manager_screen` | 社員の担当者画面の拒否 |
| `DS-TS-STATUS-RESPONSE-TIME` | `e2e/test_nonfunctional.py::test_status_response_time` | 2 秒以内の表示 |
| `DS-TS-PASSWORD-NOT-STORED-PLAIN` | `e2e/test_nonfunctional.py::test_password_not_stored_plain` | パスワードの非保存 |
| `DS-TS-INTERNAL-ACCESS-REACHABLE` | `e2e/test_nonfunctional.py::test_internal_access_reachable` | 全インターフェースでの待ち受け |
