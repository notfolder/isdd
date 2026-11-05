# 対応表（設計 ID とコードの対応）

粒度: class（ファイル、クラス、設計書にある公開関数）。書式は trace-map-rules.md に従う。要件 ID との対応は設計書の第 11 章にある。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER-ENTRY` | `src/server.py` | モジュール（起動の入口） |
| `DS-FN-READ-PORT` | `src/server.py::read_port` | 環境変数 PORT の読み取り |
| `DS-MD-HTTP-ROUTER` | `src/web/router.py` | モジュール |
| `DS-CL-REQUEST-HANDLER` | `src/web/router.py::RequestHandler` | クラス |
| `DS-IF-PAGE-ROUTES` | `src/web/router.py::RequestHandler` | 画面と静的ファイルの配信 |
| `DS-MD-API-HANDLERS` | `src/web/api.py` | モジュール |
| `DS-IF-PRIZES-API` | `src/web/api.py::handle_list_prizes` | GET /api/prizes |
| `DS-IF-SPIN-API` | `src/web/api.py::handle_spin` | POST /api/spin |
| `DS-IF-RECORDS-API` | `src/web/api.py::handle_list_records` | GET /api/records |
| `DS-MD-WHEEL-SERVICE` | `src/service/wheel.py` | モジュール |
| `DS-CL-WHEEL-SERVICE` | `src/service/wheel.py::WheelService` | クラス |
| `DS-FN-CHOOSE-SEGMENT-BY-WEIGHT` | `src/service/wheel.py::choose_segment_by_weight` | 重みによる区分の選択 |
| `DS-MD-NAME-VALIDATION` | `src/service/validation.py` | モジュール |
| `DS-CL-PLAYER-NAME-ERROR` | `src/service/validation.py::PlayerNameError` | 例外クラス |
| `DS-FN-VALIDATE-PLAYER-NAME` | `src/service/validation.py::validate_player_name` | 利用者名の検証 |
| `DS-MD-DATABASE` | `src/store/database.py` | モジュール |
| `DS-CL-DATABASE` | `src/store/database.py::Database` | クラス |
| `DS-SC-PRIZES-TABLE` | `src/store/database.py::Database` | 景品のテーブル定義（`init_schema` が作る） |
| `DS-SC-WINNING-RECORDS-TABLE` | `src/store/database.py::Database` | 当選記録のテーブル定義（`init_schema` が作る） |
| `DS-MD-REPOSITORIES` | `src/store/repositories.py` | モジュール |
| `DS-CL-PRIZE-REPOSITORY` | `src/store/repositories.py::PrizeRepository` | クラス |
| `DS-CL-RECORD-REPOSITORY` | `src/store/repositories.py::RecordRepository` | クラス |
| `DS-MD-SEED-DATA` | `src/store/seed.py` | モジュール |
| `DS-FN-SEED-SAMPLE-DATA` | `src/store/seed.py::seed_sample_data` | 初期データの投入 |
| `DS-SC-SAMPLE-DATA-SET` | `src/store/seed.py::seed_sample_data` | 初期データの内容（定数） |
| `DS-MD-COMMON-JS` | `src/web/static/js/common.js` | モジュール |
| `DS-FN-FETCH-JSON` | `src/web/static/js/common.js::fetchJson` | API の呼び出し |
| `DS-FN-ESCAPE-HTML` | `src/web/static/js/common.js::escapeHtml` | HTML へ入れる前のエスケープ |
| `DS-MD-WHEEL-JS` | `src/web/static/js/wheel.js` | モジュール |
| `DS-IF-SPIN-SCREEN` | `src/web/static/js/wheel.js::initSpinPage` | 景品ルーレット画面 |
| `DS-FN-START-SPIN` | `src/web/static/js/wheel.js::startSpin` | 抽選の開始と結果の表示 |
| `DS-FN-DRAW-WHEEL` | `src/web/static/js/wheel.js::drawWheel` | ルーレットの描画 |
| `DS-FN-DRAW-SEGMENT-LABEL` | `src/web/static/js/wheel.js::drawSegmentLabel` | 区分の文字の描画 |
| `DS-FN-ANIMATE-WHEEL-TO` | `src/web/static/js/wheel.js::animateWheelTo` | 停止位置へ回転させるアニメーション |
| `DS-MD-PRIZES-JS` | `src/web/static/js/prizes.js` | モジュール |
| `DS-IF-PRIZES-SCREEN` | `src/web/static/js/prizes.js::initPrizesPage` | 景品一覧画面 |
| `DS-FN-RENDER-PRIZE-TABLE` | `src/web/static/js/prizes.js::renderPrizeTable` | 景品の表の描画 |
| `DS-MD-RECORDS-JS` | `src/web/static/js/records.js` | モジュール |
| `DS-IF-RECORDS-SCREEN` | `src/web/static/js/records.js::initRecordsPage` | 当選履歴画面 |
| `DS-FN-LOAD-RECORDS` | `src/web/static/js/records.js::loadRecords` | 当選履歴の読み込みと表示 |
| `DS-TS-SPIN-AND-RECORD-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_spin_and_record` | E2E |
| `DS-TS-NAME-VALIDATION-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_name_validation` | E2E |
| `DS-TS-VIEW-PRIZES-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_view_prizes` | E2E |
| `DS-TS-VIEW-OWN-RECORDS-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_view_own_records` | E2E |
| `DS-TS-NAVIGATION-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_navigation` | E2E |
| `DS-TS-SEED-DATA-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_seed_data` | E2E |
