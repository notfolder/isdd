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
| `DS-IF-PRIZES-API` | `src/web/api.py::handle_list_prizes` | GET /api/rewards |
| `DS-IF-SPIN-API` | `src/web/api.py::handle_spin` | POST /api/spin |
| `DS-IF-RECORDS-API-WITH-PLAYER` | `src/web/api.py::handle_list_records` | GET /api/records（各記録に利用者名を含む） |
| `DS-MD-WHEEL-SERVICE` | `src/service/wheel.py` | モジュール |
| `DS-CL-WHEEL-SERVICE` | `src/service/wheel.py::WheelService` | クラス |
| `DS-FN-CHOOSE-SEGMENT-BY-WEIGHT` | `src/service/wheel.py::choose_segment_by_weight` | 重みによる区分の選択 |
| `DS-MD-NAME-VALIDATION` | `src/service/validation.py` | モジュール |
| `DS-CL-PLAYER-NAME-ERROR` | `src/service/validation.py::PlayerNameError` | 例外クラス |
| `DS-FN-VALIDATE-PLAYER-NAME` | `src/service/validation.py::validate_player_name` | 利用者名の検証 |
| `DS-MD-DATABASE` | `src/store/database.py` | モジュール |
| `DS-CL-DATABASE` | `src/store/database.py::Database` | クラス |
| `DS-SC-PRIZES-TABLE` | `src/store/database.py::Database` | 報酬のテーブル定義（`init_schema` が作る） |
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
| `DS-IF-SPIN-SCREEN-NAME-FIELD` | `src/web/static/js/wheel.js::initSpinPage` | 報酬ルーレット画面（利用者名欄と抽選ボタンの行） |
| `DS-FN-START-SPIN-WITH-NAME-CHECK` | `src/web/static/js/wheel.js::startSpin` | 利用者名の検査と抽選の開始、結果の表示 |
| `DS-FN-DRAW-WHEEL-THEMED` | `src/web/static/js/wheel.js::drawWheel` | ルーレットの描画（dark green と白の区分） |
| `DS-FN-DRAW-SEGMENT-LABEL` | `src/web/static/js/wheel.js::drawSegmentLabel` | 区分の文字の描画 |
| `DS-FN-ANIMATE-WHEEL-TO` | `src/web/static/js/wheel.js::animateWheelTo` | 停止位置へ回転させるアニメーション |
| `DS-MD-PRIZES-JS` | `src/web/static/js/rewards.js` | モジュール（報酬一覧画面） |
| `DS-IF-PRIZES-SCREEN` | `src/web/static/js/rewards.js::initRewardsPage` | 報酬一覧画面（`/rewards`） |
| `DS-FN-RENDER-PRIZE-TABLE` | `src/web/static/js/rewards.js::renderRewardTable` | 報酬の表の描画 |
| `DS-MD-RECORDS-JS` | `src/web/static/js/records.js` | モジュール |
| `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `src/web/static/js/records.js::initRecordsPage` | 当選履歴画面（利用者名・報酬名・当選日時の列） |
| `DS-FN-LOAD-RECORDS-WITH-PLAYER` | `src/web/static/js/records.js::loadRecords` | 当選履歴の読み込みと表示（利用者名を含む行） |
| `DS-TS-SPIN-AND-RECORD-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_spin_and_record` | E2E |
| `DS-TS-SPIN-NAME-REQUIRED-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_spin_name_required` | E2E |
| `DS-TS-VIEW-PRIZES-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_view_prizes` | E2E |
| `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_view_records_with_player` | E2E |
| `DS-TS-NAVIGATION-THEME-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_navigation_and_theme` | E2E |
| `DS-TS-SEED-DATA-E2E` | `e2e/test_wheel_e2e.py::WheelE2ETest.test_seed_data` | E2E |
