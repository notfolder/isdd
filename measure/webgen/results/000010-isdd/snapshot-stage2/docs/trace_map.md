# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-MAIN` | `app/__main__.py` | モジュール |
| `DS-MD-SERVER` | `app/server.py` | モジュール |
| `DS-MD-REPOSITORY` | `app/repository.py` | モジュール |
| `DS-MD-DB` | `app/db.py` | モジュール |
| `DS-MD-DRAW` | `app/draw.py` | モジュール |
| `DS-MD-VALIDATION` | `app/validation.py` | モジュール |
| `DS-MD-INDEX-HTML` | `static/index.html` | モジュール |
| `DS-MD-APP-JS` | `static/app.js` | モジュール |
| `DS-MD-STYLE-CSS` | `static/style.css` | モジュール |
| `DS-OP-START-SERVER` | `app/__main__.py::main` | 起動の入口 |
| `DS-OP-SAMPLE-DATA-SEED` | `app/db.py::open_database` | 初期データの投入 |
| `DS-SC-PRIZE-TABLE` | `app/db.py::open_database` | 景品テーブル（スキーマ） |
| `DS-SC-SPIN-RECORD-TABLE` | `app/db.py::open_database` | 抽選記録テーブル（スキーマ） |
| `DS-FN-OPEN-DATABASE` | `app/db.py::open_database` | |
| `DS-FN-LIST-PRIZES` | `app/repository.py::list_prizes` | |
| `DS-FN-INSERT-SPIN-RECORD` | `app/repository.py::insert_spin_record` | |
| `DS-FN-FIND-RECORDS-BY-NAME` | `app/repository.py::find_records_by_name` | |
| `DS-FN-DRAW-PRIZE` | `app/draw.py::draw_prize` | |
| `DS-FN-VALIDATE-PLAYER-NAME` | `app/validation.py::validate_player_name` | |
| `DS-FN-HANDLE-SPIN` | `app/server.py::handle_spin` | |
| `DS-IF-STATIC-PAGE` | `app/server.py::serve_static` | |
| `DS-IF-PRIZES-API` | `app/server.py::handle_prizes` | |
| `DS-IF-SPIN-API` | `app/server.py::handle_spin` | |
| `DS-IF-RECORDS-API` | `app/server.py::handle_records` | |
| `DS-IF-ADD-PRIZE-API` | `app/server.py::handle_add_prize` | |
| `DS-IF-DELETE-PRIZE-API` | `app/server.py::handle_delete_prize` | |
| `DS-FN-SHOW-VIEW-AND-RELOAD` | `static/app.js::showViewAndReload` | 画面の切り替えと景品の読み直し |
| `DS-FN-RENDER-MANAGE-PRIZES` | `static/app.js::renderManagePrizes` | 景品の管理の表 |
| `DS-FN-INSERT-PRIZE` | `app/repository.py::insert_prize` | |
| `DS-FN-DELETE-PRIZE` | `app/repository.py::delete_prize` | |
| `DS-FN-VALIDATE-PRIZE-NAME` | `app/validation.py::validate_prize_name` | |
| `DS-FN-HANDLE-ADD-PRIZE` | `app/server.py::handle_add_prize` | |
| `DS-FN-HANDLE-DELETE-PRIZE` | `app/server.py::handle_delete_prize` | |
| `DS-FN-RENDER-WHEEL` | `static/app.js::renderWheel` | |
| `DS-FN-REMEMBER-PLAYER-NAME` | `static/app.js::rememberPlayerName` | |
| `DS-TS-SPIN-AND-RECORD-E2E` | `e2e/test_e2e.py::E2EScenarios.test_spin_and_record` | E2E |
| `DS-TS-VALIDATE-PLAYER-NAME-E2E` | `e2e/test_e2e.py::E2EScenarios.test_validate_player_name` | E2E |
| `DS-TS-VIEW-PRIZE-LIST-E2E` | `e2e/test_e2e.py::E2EScenarios.test_view_prize_list` | E2E |
| `DS-TS-VIEW-OWN-RECORDS-E2E` | `e2e/test_e2e.py::E2EScenarios.test_view_own_records` | E2E |
| `DS-TS-NAVIGATE-MENU-E2E` | `e2e/test_e2e.py::E2EScenarios.test_navigate_menu` | E2E |
| `DS-TS-EMPTY-PRIZES-E2E` | `e2e/test_e2e.py::E2EScenarios.test_empty_prizes` | E2E |
| `DS-TS-FIRST-START-AND-THEME-E2E` | `e2e/test_e2e.py::E2EScenarios.test_first_start_and_theme` | E2E |
| `DS-TS-MANAGE-PRIZES-E2E` | `e2e/test_e2e.py::E2EScenarios.test_manage_prizes` | E2E |
| `DS-TS-VALIDATE-PRIZE-NAME-E2E` | `e2e/test_e2e.py::E2EScenarios.test_validate_prize_name` | E2E |
| `DS-TS-REMOVE-PRIZE-KEEPS-RECORDS-E2E` | `e2e/test_e2e.py::E2EScenarios.test_remove_prize_keeps_records` | E2E |
