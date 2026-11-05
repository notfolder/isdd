# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-APP` | `src/app.py` | モジュール |
| `DS-FN-MAIN` | `src/app.py::main` | 起動の入口 |
| `DS-MD-WEB` | `src/web.py` | モジュール |
| `DS-CL-POLL-REQUEST-HANDLER` | `src/web.py::PollRequestHandler` | HTTP リクエストの処理 |
| `DS-FN-DISPATCH-GET-REQUEST` | `src/web.py::PollRequestHandler.do_GET` | GET の経路の振り分け |
| `DS-FN-DISPATCH-POST-REQUEST` | `src/web.py::PollRequestHandler.do_POST` | POST の経路の振り分け |
| `DS-IF-POLL-LIST-PAGE` | `src/web.py::PollRequestHandler.handle_poll_list` | 投票テーマ一覧（`/`） |
| `DS-IF-POLL-RESULT-PAGE` | `src/web.py::PollRequestHandler.handle_poll_results` | 投票テーマの結果画面（`/polls/<id>/results`） |
| `DS-IF-ALL-RESULTS-PAGE` | `src/web.py::PollRequestHandler.handle_all_results` | 全体の結果画面（`/results`） |
| `DS-FN-CREATE-SERVER` | `src/web.py::create_server` | HTTP サーバーの作成 |
| `DS-MD-POLL-SERVICE` | `src/poll_service.py` | モジュール |
| `DS-CL-POLL-SERVICE` | `src/poll_service.py::PollService` | 業務処理 |
| `DS-CL-POLL-NOT-FOUND-ERROR` | `src/poll_service.py::PollNotFoundError` | 投票テーマが無い |
| `DS-CL-NO-OPTION-SELECTED-ERROR` | `src/poll_service.py::NoOptionSelectedError` | 選択肢が未選択・不正 |
| `DS-FN-SERVICE-LIST-POLLS` | `src/poll_service.py::PollService.list_polls` | 投票テーマ一覧 |
| `DS-FN-SERVICE-GET-POLL` | `src/poll_service.py::PollService.get_poll` | 投票テーマと選択肢 |
| `DS-FN-SERVICE-GET-POLL-RESULTS` | `src/poll_service.py::PollService.get_poll_results` | 投票テーマの結果 |
| `DS-FN-SERVICE-GET-ALL-RESULTS` | `src/poll_service.py::PollService.get_all_results` | 全体の結果 |
| `DS-MD-STORAGE` | `src/storage.py` | モジュール |
| `DS-FN-OPEN-DATABASE` | `src/storage.py::open_database` | DB を開き、スキーマと初期データを準備する |
| `DS-SC-DATABASE-FILE` | `src/storage.py::open_database` | DATA_DIR の polls.db |
| `DS-FN-SEED-SAMPLE-DATA` | `src/storage.py::seed_sample_data` | 初期データの投入 |
| `DS-FN-LIST-POLLS-WITH-TOTALS` | `src/storage.py::list_polls_with_totals` | 投票テーマと合計票数 |
| `DS-FN-FIND-POLL` | `src/storage.py::find_poll` | 投票テーマの取得 |
| `DS-SC-POLL-TABLE` | `src/storage.py::find_poll` | polls テーブル |
| `DS-FN-LIST-OPTIONS-WITH-COUNTS` | `src/storage.py::list_options_with_counts` | 選択肢と票数 |
| `DS-FN-FIND-OPTION` | `src/storage.py::find_option` | 投票テーマに属する選択肢の取得 |
| `DS-SC-OPTION-TABLE` | `src/storage.py::find_option` | options テーブル |
| `DS-SC-VOTE-TABLE` | `src/storage.py::record_vote_once` | votes テーブル |
| `DS-MD-VIEWS` | `src/views.py` | モジュール |
| `DS-FN-RENDER-LAYOUT` | `src/views.py::render_layout` | 共通のページ枠 |
| `DS-IF-NAVIGATION-MENU` | `src/views.py::render_navigation_menu` | 案内メニュー |
| `DS-FN-RENDER-POLL-LIST` | `src/views.py::render_poll_list` | 投票テーマ一覧の画面 |
| `DS-FN-RENDER-POLL-RESULTS` | `src/views.py::render_poll_results` | 投票テーマの結果画面 |
| `DS-FN-RENDER-ALL-RESULTS` | `src/views.py::render_all_results` | 全体の結果画面 |
| `DS-FN-RENDER-NOT-FOUND` | `src/views.py::render_not_found` | 404 画面 |
| `DS-TS-BROWSE-POLLS-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_browse_polls` | E2E |
| `DS-TS-VOTE-FOR-OPTION-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_vote_for_option` | E2E |
| `DS-TS-REJECT-EMPTY-VOTE-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_reject_empty_vote` | E2E |
| `DS-TS-VIEW-ALL-RESULTS-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_view_all_results` | E2E |
| `DS-TS-OPEN-UNKNOWN-POLL-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_open_unknown_poll` | E2E |
| `DS-TS-ANONYMOUS-ACCESS-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_anonymous_access` | E2E |
| `DS-TS-SEED-SAMPLE-DATA-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_seed_sample_data` | E2E |
| `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | `src/web.py::PollRequestHandler.handle_vote_page` | 投票画面（投票済みの無効化と通知） |
| `DS-IF-VOTE-SUBMIT-ONE-VOTE` | `src/web.py::PollRequestHandler.handle_vote_submit` | 投票の送信（投票済みは記録せず再表示） |
| `DS-FN-READ-VOTER-COOKIE` | `src/web.py::PollRequestHandler.voter_id` | cookie のブラウザ識別子の読み取りと発行 |
| `DS-IF-COLOR-THEME` | `src/views.py::render_layout` | 配色（共通の CSS） |
| `DS-SC-BALLOT-TABLE` | `src/storage.py::find_ballot` | ballots テーブル（投票済み記録） |
| `DS-FN-FIND-BALLOT` | `src/storage.py::find_ballot` | 投票済みの検索 |
| `DS-FN-RECORD-VOTE-ONCE` | `src/storage.py::record_vote_once` | 投票と投票済み記録の 1 トランザクション追加 |
| `DS-CL-ALREADY-VOTED-ERROR` | `src/poll_service.py::AlreadyVotedError` | 投票済みの例外 |
| `DS-FN-SERVICE-HAS-VOTED` | `src/poll_service.py::PollService.has_voted` | 投票済みの判定 |
| `DS-FN-SERVICE-CAST-VOTE-ONCE` | `src/poll_service.py::PollService.cast_vote_once` | 投票者付きの投票の記録 |
| `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | `src/views.py::render_vote_page` | 投票済みの状態を受ける投票画面 |
| `DS-TS-ONE-VOTE-PER-POLL-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_one_vote_per_poll_per_browser` | E2E |
| `DS-TS-THEME-COLORS-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_theme_colors` | E2E |
| `DS-TS-SURVEY-TERMINOLOGY-E2E` | `e2e/test_polls_e2e.py::PollsE2ETest.test_survey_terminology` | E2E |
