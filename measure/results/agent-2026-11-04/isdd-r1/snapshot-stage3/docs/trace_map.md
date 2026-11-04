# 対応表（設計 ID とコードの対応）

書式と粒度は isdd の対応表のルールに従う（粒度: function）。要件 ID との対応は詳細設計書の第 11 章にある。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-APP-FACTORY` | `app/__init__.py` | アプリの生成 |
| `DS-FN-CREATE-APP` | `app/__init__.py::create_app` | アプリの生成と DB・秘密鍵の準備 |
| `DS-OP-SECRET-KEY` | `app/__init__.py::load_or_create_secret_key` | 秘密鍵の作成と読み込み |
| `DS-MD-SERVER` | `app/__main__.py` | waitress での起動 |
| `DS-OP-SERVER-THREADS` | `app/__main__.py::main` | スレッド数 8 |
| `DS-MD-CONFIG` | `app/config.py` | 設定の読み込み |
| `DS-FN-LOAD-CONFIG` | `app/config.py::load_config` | 環境変数の読み込み |
| `DS-OP-ENV-CONFIG` | `app/config.py::load_config` | 環境変数の一覧 |
| `DS-MD-DB` | `app/db.py` | SQLite の接続と初期化 |
| `DS-FN-CONNECT-DB` | `app/db.py::connect` | 接続（自動トランザクションを使わない） |
| `DS-FN-INIT-SCHEMA` | `app/db.py::init_schema` | テーブルの作成 |
| `DS-MD-VALIDATION` | `app/validation.py` | 入力の検査 |
| `DS-FN-VALIDATE-LOAN-INPUT` | `app/validation.py::validate_loan_input` | 貸出の入力の検査 |
| `DS-FN-VALIDATE-ACCOUNT-INPUT` | `app/validation.py::validate_account_input` | アカウント入力の検査 |
| `DS-FN-VALIDATE-EQUIPMENT-INPUT` | `app/validation.py::validate_equipment_input` | 備品入力の検査 |
| `DS-MD-ACCOUNTS` | `app/accounts.py` | アカウントの登録と照合 |
| `DS-FN-REGISTER-ACCOUNT` | `app/accounts.py::register_account` | 登録（最初の 1 件は担当者） |
| `DS-FN-AUTHENTICATE-ACCOUNT` | `app/accounts.py::authenticate_account` | 社員番号とパスワードの照合 |
| `DS-MD-EQUIPMENT` | `app/equipment.py` | 備品の処理 |
| `DS-FN-GET-EQUIPMENT-WITH-REVISION` | `app/equipment.py::get_equipment_with_revision` | 1 件の取得（版番号を含む） |
| `DS-FN-CREATE-EQUIPMENT` | `app/equipment.py::create_equipment` | 登録 |
| `DS-FN-UPDATE-EQUIPMENT-IF-CURRENT` | `app/equipment.py::update_equipment_if_current` | 修正（版番号が一致したときだけ。貸出の記録は触らない） |
| `DS-FN-DELETE-EQUIPMENT-IF-NOT-LOANED` | `app/equipment.py::delete_equipment_if_not_loaned` | 貸出中でなければ物理削除 |
| `DS-MD-LOANS` | `app/loans.py` | 貸出の登録・返却・貸出状況の一覧 |
| `DS-FN-REGISTER-LOAN` | `app/loans.py::register_loan` | 空きの備品への貸出の登録（排他） |
| `DS-FN-RETURN-LOAN` | `app/loans.py::return_loan` | 返却（貸出の記録を消す） |
| `DS-FN-LIST-LOAN-STATUS` | `app/loans.py::list_loan_status` | 貸出状況の一覧（管理番号の昇順、貸出の記録と結ぶ） |
| `DS-FN-SHOW-LOAN-FORM` | `app/loans.py::list_borrowers` | 貸出の登録画面の借りる社員の選択肢 |
| `DS-MD-AUTH` | `app/auth.py` | セッションと権限 |
| `DS-FN-LOGIN-USER` | `app/auth.py::login_user` | ログイン |
| `DS-FN-LOGOUT-USER` | `app/auth.py::logout_user` | ログアウト |
| `DS-FN-LOAD-CURRENT-USER` | `app/auth.py::load_current_user` | 制限時間の判定と利用者の判定 |
| `DS-FN-REQUIRE-MANAGER` | `app/auth.py::require_manager` | 担当者の確認 |
| `DS-MD-VIEWS` | `app/views.py` | 画面の要求の受け付け |
| `DS-FN-SHOW-LOAN-STATUS` | `app/views.py::loan_status` | 貸出状況の画面 |
| `DS-FN-SUBMIT-ACCOUNT-REGISTER` | `app/views.py::register_account` | アカウント登録の画面 |
| `DS-FN-SUBMIT-LOGIN` | `app/views.py::login` | ログインの画面 |
| `DS-FN-SUBMIT-LOGOUT` | `app/views.py::logout` | ログアウト |
| `DS-FN-SHOW-EQUIPMENT-FORM` | `app/views.py::equipment_new` | 備品の登録画面 |
| `DS-FN-SHOW-EQUIPMENT-FORM` | `app/views.py::equipment_edit` | 備品の修正画面 |
| `DS-FN-SUBMIT-EQUIPMENT-FORM` | `app/views.py::equipment_new` | 備品の登録の送信 |
| `DS-FN-SUBMIT-EQUIPMENT-FORM` | `app/views.py::equipment_edit` | 備品の修正の送信 |
| `DS-FN-SUBMIT-EQUIPMENT-DELETE` | `app/views.py::equipment_delete` | 備品の削除の送信 |
| `DS-FN-SHOW-LOAN-FORM` | `app/views.py::equipment_loan` | 貸出の登録画面 |
| `DS-FN-SUBMIT-LOAN-FORM` | `app/views.py::equipment_loan` | 貸出の登録の送信 |
| `DS-FN-SUBMIT-RETURN` | `app/views.py::equipment_return` | 返却の送信 |
| `DS-IF-LOAN-REGISTER-SCREEN` | `app/views.py::equipment_loan` | 貸出の登録画面の入口 |
| `DS-IF-LOAN-STATUS-SCREEN` | `app/views.py::loan_status` | 貸出状況の画面の入口 |
| `DS-IF-ACCOUNT-REGISTER-SCREEN` | `app/views.py::register_account` | アカウント登録の画面の入口 |
| `DS-IF-LOGIN-SCREEN` | `app/views.py::login` | ログインの画面の入口 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `app/views.py::equipment_new` | 備品の登録画面の入口 |
| `DS-IF-EQUIPMENT-FORM-SCREEN` | `app/views.py::equipment_edit` | 備品の修正画面の入口 |
| `DS-TS-REGISTER-FIRST-ACCOUNT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_register_first_account` | E2E |
| `DS-TS-REGISTER-SECOND-ACCOUNT-AS-MEMBER` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_register_second_account_as_member` | E2E |
| `DS-TS-REGISTER-ACCOUNT-VALIDATION` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_register_account_validation` | E2E |
| `DS-TS-LOGIN-AND-LOGOUT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_login_and_logout` | E2E |
| `DS-TS-LOGIN-FAILURE-NO-HINT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_login_failure_no_hint` | E2E |
| `DS-TS-AUTO-LOGOUT-AFTER-IDLE` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_auto_logout_after_idle` | E2E |
| `DS-TS-MANAGER-REGISTER-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_manager_register_equipment` | E2E |
| `DS-TS-EQUIPMENT-VALIDATION` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_equipment_validation` | E2E |
| `DS-TS-MANAGER-EDIT-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_manager_edit_equipment` | E2E |
| `DS-TS-MANAGER-DELETE-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_manager_delete_equipment` | E2E |
| `DS-TS-MEMBER-CANNOT-OPERATE-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_member_cannot_operate_equipment` | E2E |
| `DS-TS-GUEST-CANNOT-OPERATE-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_guest_cannot_operate_equipment` | E2E |
| `DS-TS-VIEW-LOAN-STATUS-AS-GUEST` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_view_loan_status_as_guest` | E2E |
| `DS-TS-VIEW-EMPTY-LOAN-STATUS` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_view_empty_loan_status` | E2E |
| `DS-TS-ROLE-BUTTON-VISIBILITY` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_role_button_visibility` | E2E |
| `DS-TS-LIST-RESPONSE-TIME` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_list_response_time` | E2E |
| `DS-TS-REGISTER-LOAN` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_register_loan` | E2E |
| `DS-TS-LOAN-INPUT-VALIDATION` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_loan_input_validation` | E2E |
| `DS-TS-NO-DOUBLE-LOAN` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_no_double_loan` | E2E |
| `DS-TS-RETURN-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_return_equipment` | E2E |
| `DS-TS-NO-DOUBLE-RETURN` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_no_double_return` | E2E |
| `DS-TS-NO-DELETE-LOANED-EQUIPMENT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_no_delete_loaned_equipment` | E2E |
| `DS-TS-EDIT-KEEPS-LOAN` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_edit_keeps_loan` | E2E |
| `DS-TS-EDIT-CONFLICT-REJECT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_edit_conflict_reject` | E2E |
| `DS-TS-MEMBER-AND-GUEST-CANNOT-LOAN-OR-RETURN` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_member_and_guest_cannot_loan_or_return` | E2E |
| `DS-TS-VIEW-LOAN-DETAILS-AS-GUEST` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_view_loan_details_as_guest` | E2E |
| `DS-TS-CONCURRENT-RESPONSE-TIME` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_concurrent_response_time` | E2E |
| `DS-FN-VALIDATE-PASSWORD` | `app/validation.py::validate_password` | パスワードの検査（8 文字以上） |
| `DS-FN-LIST-ACCOUNTS` | `app/accounts.py::list_accounts` | アカウントの一覧（社員番号の昇順） |
| `DS-FN-GET-ACCOUNT` | `app/accounts.py::find_account_by_id` | 内部の識別子で 1 件引く（利用者の引き直し） |
| `DS-FN-CHANGE-ACCOUNT-ROLE` | `app/accounts.py::change_account_role` | 担当者の付け外し（担当者が 1 人だけなら外さない） |
| `DS-FN-RESET-ACCOUNT-PASSWORD` | `app/accounts.py::reset_account_password` | パスワードの再設定 |
| `DS-FN-DELETE-ACCOUNT` | `app/accounts.py::delete_account` | 削除（借りている社員と最後の担当者は削除しない） |
| `DS-FN-SHOW-ACCOUNT-LIST` | `app/views.py::account_list` | アカウントの一覧の画面 |
| `DS-FN-SUBMIT-ACCOUNT-ROLE` | `app/views.py::account_role` | 担当者の付け外しの送信 |
| `DS-FN-SHOW-PASSWORD-RESET` | `app/views.py::account_password` | パスワード再設定の行を開く |
| `DS-FN-SUBMIT-PASSWORD-RESET` | `app/views.py::account_password` | パスワードの再設定の送信 |
| `DS-FN-SUBMIT-ACCOUNT-DELETE` | `app/views.py::account_delete` | アカウントの削除の送信 |
| `DS-IF-ACCOUNT-LIST-SCREEN` | `app/views.py::account_list` | アカウントの一覧の画面の入口 |
| `DS-TS-LIST-ACCOUNTS` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_list_accounts` | E2E |
| `DS-TS-CHANGE-ACCOUNT-ROLE` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_change_account_role` | E2E |
| `DS-TS-KEEP-ONE-MANAGER` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_keep_one_manager` | E2E |
| `DS-TS-RESET-ACCOUNT-PASSWORD` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_reset_account_password` | E2E |
| `DS-TS-DELETE-ACCOUNT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_delete_account` | E2E |
| `DS-TS-NO-DELETE-BORROWING-ACCOUNT` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_no_delete_borrowing_account` | E2E |
| `DS-TS-MEMBER-AND-GUEST-CANNOT-MANAGE-ACCOUNTS` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_member_and_guest_cannot_manage_accounts` | E2E |
| `DS-TS-DEMOTED-MANAGER-LOSES-ACCESS` | `e2e/test_equipment_ledger.py::EquipmentLedgerE2E.test_demoted_manager_loses_access` | E2E |
