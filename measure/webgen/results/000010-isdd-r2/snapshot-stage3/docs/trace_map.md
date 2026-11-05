# 対応表（設計 ID とコードの対応）

粒度: function。書式は isdd の trace-map-rules に従う。要件 ID との対応は詳細設計書 第 11 章で持つ。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-MAIN` | `app/__main__.py` | 起動モジュール |
| `DS-FN-MAIN` | `app/__main__.py::main` | 環境変数の読み取り、部品の組み立て、サーバーの起動 |
| `DS-MD-SERVER` | `app/server.py` | HTTP 層 |
| `DS-CL-WHEEL-REQUEST-HANDLER` | `app/server.py::WheelRequestHandler` | 1 件の HTTP 要求の振り分けと応答 |
| `DS-FN-CREATE-SERVER` | `app/server.py::create_server` | 待ち受けサーバーの作成 |
| `DS-FN-ROUTE-REQUEST` | `app/server.py::WheelRequestHandler.do_GET` | GET の振り分け |
| `DS-FN-ROUTE-REQUEST` | `app/server.py::WheelRequestHandler.do_POST` | POST の振り分け |
| `DS-IF-SPIN-SCREEN-NAME-FIELD` | `app/server.py::WheelRequestHandler.serve_page` | `/` の画面（web/index.html を返す。名前の入力欄と Spin ボタンは同じ行） |
| `DS-IF-REWARD-LIST-SCREEN` | `app/server.py::WheelRequestHandler.serve_page` | `/rewards` の画面（web/rewards.html を返す。旧い `/prizes` は `/rewards` へ 301 で転送。`_send_redirect` を使う） |
| `DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` | `app/server.py::WheelRequestHandler.serve_page` | `/my-winnings` の画面（web/my-winnings.html を返す。表の列は Player、Reward、Date won） |
| `DS-IF-NAVIGATION-MENU` | `app/server.py::WheelRequestHandler.serve_page` | 各 HTML のナビゲーション |
| `DS-IF-STATIC-ASSETS` | `app/server.py::WheelRequestHandler.serve_static` | web/static の JavaScript と CSS の配信（範囲外は 404） |
| `DS-IF-THEME-STYLESHEET` | `app/server.py::WheelRequestHandler.serve_static` | web/static/style.css（配色。背景 ivory、部品 dark green） |
| `DS-IF-PRIZES-API` | `app/server.py::WheelRequestHandler.handle_prizes` | GET /api/prizes |
| `DS-IF-SPINS-API` | `app/server.py::WheelRequestHandler.handle_spin` | POST /api/spins |
| `DS-IF-WINNINGS-API-WITH-NAME` | `app/server.py::WheelRequestHandler.handle_winnings` | GET /api/winnings（各行に名前を含む） |
| `DS-MD-SERVICE` | `app/service.py` | 業務ロジック |
| `DS-CL-SPIN-SERVICE` | `app/service.py::SpinService` | 抽選と取得 |
| `DS-CL-REQUEST-ERROR` | `app/service.py::RequestError` | 利用者に見せるエラー |
| `DS-FN-SPIN-WHEEL` | `app/service.py::SpinService.spin` | 名前の検査、等確率の抽選、当選記録 |
| `DS-FN-GET-PRIZE-LIST` | `app/service.py::SpinService.get_prizes` | 景品一覧 |
| `DS-FN-GET-OWN-WINNINGS` | `app/service.py::SpinService.get_winnings` | 名前で絞り込んだ当選記録 |
| `DS-FN-VALIDATE-PLAYER-NAME` | `app/service.py::validate_player_name` | 名前の検査（空、30 文字超） |
| `DS-MD-DATABASE` | `app/database.py` | データ層 |
| `DS-CL-DATABASE` | `app/database.py::Database` | SQLite の窓口 |
| `DS-FN-INITIALIZE-DATABASE` | `app/database.py::Database.initialize` | 表の作成と初期データ |
| `DS-FN-LIST-PRIZES` | `app/database.py::Database.list_prizes` | 景品の一覧（表示順） |
| `DS-FN-ADD-WINNING-RECORD` | `app/database.py::Database.add_winning_record` | 当選記録の追加 |
| `DS-FN-LIST-WINNINGS-WITH-NAME` | `app/database.py::Database.list_winnings_by_name` | 名前の完全一致（大文字小文字を区別しない）、新しい順。各行に名前を含む |
| `DS-TS-SPIN-AND-RECORD` | `e2e/test_wheel_site.py::WheelSiteTest.test_spin_and_record` | E2E |
| `DS-TS-REQUIRE-PLAYER-NAME` | `e2e/test_wheel_site.py::WheelSiteTest.test_spin_requires_valid_name` | E2E |
| `DS-TS-PRIZE-LIST-SHOWS-ALL` | `e2e/test_wheel_site.py::WheelSiteTest.test_prize_list_shows_all_prizes` | E2E |
| `DS-TS-OWN-WINNINGS-FILTER` | `e2e/test_wheel_site.py::WheelSiteTest.test_own_winnings_filtered_and_newest_first` | E2E |
| `DS-TS-PRIZE-SELECTION-RULE` | `e2e/test_wheel_site.py::WheelSiteTest.test_every_prize_is_drawn` | E2E |
| `DS-TS-NAVIGATION-ALL-PAGES` | `e2e/test_wheel_site.py::WheelSiteTest.test_navigation_links_on_every_page` | E2E |
| `DS-TS-THEME-IVORY-GREEN` | `e2e/test_wheel_site.py::WheelSiteTest.test_theme_ivory_and_dark_green` | E2E |
| `DS-TS-SPIN-NAME-FIELD` | `e2e/test_wheel_site.py::WheelSiteTest.test_spin_name_field_is_required_next_to_spin` | E2E |
| `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE` | `e2e/test_wheel_site.py::WheelSiteTest.test_record_shows_name_prize_and_date` | E2E |
| `DS-TS-START-WITH-SAMPLE-DATA` | `e2e/test_wheel_site.py::WheelSiteTest.test_empty_data_dir_gets_samples` | E2E |
