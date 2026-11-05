# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER-MODULE` | `src/server.py` | HTTP サーバーと画面・API の振り分け |
| `DS-MD-STORE-MODULE` | `src/store.py` | SQLite の保存と取得 |
| `DS-MD-DRAW-MODULE` | `src/draw.py` | 重み付き抽選 |
| `DS-MD-PAGES-SCRIPT` | `src/web/app.js` | 画面の描画とルーレット |
| `DS-CL-WHEEL-REQUEST-HANDLER` | `src/server.py::WheelRequestHandler` | HTTP 要求の処理 |
| `DS-CL-STORE` | `src/store.py::Store` | 景品と当選記録の保存 |
| `DS-FN-PICK-PRIZE` | `src/draw.py::pick_prize` | 重みに比例した景品の選択 |
| `DS-FN-HANDLE-SPIN` | `src/server.py::WheelRequestHandler.handle_spin` | 抽選 API |
| `DS-FN-HANDLE-PRIZES` | `src/server.py::WheelRequestHandler.handle_prizes` | 景品一覧 API |
| `DS-FN-HANDLE-WINNINGS` | `src/server.py::WheelRequestHandler.handle_winnings` | 当選記録一覧 API |
| `DS-FN-SEED-SAMPLE-PRIZES` | `src/store.py::Store.seed_sample_prizes` | サンプル景品の初期投入 |
| `DS-FN-LIST-PRIZES` | `src/store.py::Store.list_prizes` | 景品一覧の取得 |
| `DS-FN-ADD-WINNING` | `src/store.py::Store.add_winning` | 当選記録の追加 |
| `DS-FN-LIST-WINNINGS` | `src/store.py::Store.list_winnings` | 利用者ごとの当選記録の取得 |
| `DS-FN-BUILD-SERVER` | `src/server.py::build_server` | サーバーの組み立て（DB 初期化、127.0.0.1 で待ち受け） |
| `DS-FN-MAIN` | `src/server.py::main` | 起動（PORT・DATA_DIR の読み込み） |
| `DS-FN-SPIN-WHEEL-ANIMATION` | `src/web/app.js::spinWheelTo` | ルーレットの回転 |
| `DS-FN-DRAW-WHEEL` | `src/web/app.js::drawWheel` | ルーレットの描画 |
| `DS-IF-SPIN-PAGE` | `src/web/app.js::renderSpinPage` | Spin 画面 |
| `DS-IF-PRIZES-PAGE` | `src/web/app.js::renderPrizesPage` | Prizes 画面 |
| `DS-IF-MY-WINNINGS-PAGE` | `src/web/app.js::renderMyWinningsPage` | My Winnings 画面 |
| `DS-IF-NAV-MENU` | `src/web/app.js::renderNavigation` | 共通メニュー |
| `DS-TS-EMPTY-DATA-START` | `e2e/test_wheel.py::WheelScenarios.test_empty_data_start` | 空データで起動 |
| `DS-TS-SPIN-AND-RECORD` | `e2e/test_wheel.py::WheelScenarios.test_spin_and_record` | 回して記録 |
| `DS-TS-BROWSE-PRIZES` | `e2e/test_wheel.py::WheelScenarios.test_browse_prizes` | 景品一覧 |
| `DS-TS-VIEW-OWN-WINNINGS` | `e2e/test_wheel.py::WheelScenarios.test_view_own_winnings` | 自分の当選記録 |
| `DS-TS-NAVIGATE-MENU` | `e2e/test_wheel.py::WheelScenarios.test_navigate_menu` | メニュー |
| `DS-TS-PLAYER-NAME-RULE` | `e2e/test_wheel.py::WheelScenarios.test_player_name_rule` | 表示名の規則 |
| `DS-TS-NO-PRIZE-NOT-RECORDED` | `e2e/test_wheel.py::WheelScenarios.test_no_prize_not_recorded` | ハズレは記録しない |
| `DS-TS-WEIGHTED-DRAW` | `e2e/test_wheel.py::WheelScenarios.test_weighted_draw` | 重み付き抽選 |
| `DS-TS-RESPONSE-TIME` | `e2e/test_wheel.py::WheelScenarios.test_response_time` | 応答時間 |
| `DS-TS-CONCURRENT-SPINS` | `e2e/test_wheel.py::WheelScenarios.test_concurrent_spins` | 同時の抽選 |
