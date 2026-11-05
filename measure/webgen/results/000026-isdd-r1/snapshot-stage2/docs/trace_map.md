# 対応表（設計 ID とコードの対応）

粒度: function。書式は isdd の対応表ルールに従う。要件 ID との対応は `docs/detail_design.md` の 11 章を見る。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-MAIN` | `src/main.py` | 起動処理 |
| `DS-FN-READ-SETTINGS` | `src/main.py::read_settings` | PORT と DATA_DIR を読む |
| `DS-FN-MAIN` | `src/main.py::main` | DB 初期化、初期データ、サーバー起動 |
| `DS-MD-STORE` | `src/store/db.py` | SQLite の保存処理 |
| `DS-FN-INIT-DB` | `src/store/db.py::init_db` | テーブル作成 |
| `DS-FN-SEED-SAMPLE-POLLS` | `src/store/db.py::seed_sample_polls` | 空のときだけ初期データ |
| `DS-FN-LIST-POLLS` | `src/store/db.py::list_polls` | 一覧と総票数 |
| `DS-FN-GET-POLL` | `src/store/db.py::get_poll` | 詳細と票数・割合 |
| `DS-FN-HAS-VOTED` | `src/store/db.py::has_voted` | 投票済みかの判定 |
| `DS-FN-CAST-VOTE-ONCE` | `src/store/db.py::cast_vote` | 投票者ごとに 1 トランザクションで 1 票（投票済みなら記録しない） |
| `DS-MD-APP` | `src/web/app.py` | Flask の画面 |
| `DS-FN-CREATE-APP` | `src/web/app.py::create_app` | ルートとエラー処理の登録 |
| `DS-IF-NAVIGATION-MENU` | `src/web/app.py::provide_navigation` | 共通メニュー |
| `DS-IF-POLL-LIST-SCREEN` | `src/web/app.py::show_poll_list` | GET / |
| `DS-IF-POLL-DETAIL-SCREEN` | `src/web/app.py::show_poll_detail` | GET /polls/<id> |
| `DS-IF-VOTE-SUBMIT-ONCE` | `src/web/app.py::submit_vote` | POST /polls/<id>/vote（投票済みは 409） |
| `DS-IF-ALREADY-VOTED-STATE` | `src/web/app.py::show_poll_detail` | 投票済みの詳細画面（投票の操作を無効にする） |
| `DS-FN-READ-VOTER-COOKIE` | `src/web/app.py::read_voter_cookie` | Cookie の投票者 ID を読む |
| `DS-FN-SET-VOTER-COOKIE` | `src/web/app.py::set_voter_cookie` | 投票者 ID の Cookie を付ける |
| `DS-IF-POLL-RESULTS-SCREEN` | `src/web/app.py::show_poll_results` | GET /polls/<id>/results |
| `DS-IF-RESULTS-OVERVIEW-SCREEN` | `src/web/app.py::show_results_overview` | GET /results |
| `DS-FN-HANDLE-NOT-FOUND` | `src/web/app.py::handle_not_found` | 404 の画面 |
| `DS-TS-BROWSE-POLL-LIST` | `e2e/test_site.py::PollsSiteTest.test_browse_poll_list` | E2E |
| `DS-TS-VIEW-POLL-OPTIONS` | `e2e/test_site.py::PollsSiteTest.test_view_poll_options` | E2E |
| `DS-TS-CAST-VOTE-ONCE-PER-POLL` | `e2e/test_site.py::PollsSiteTest.test_cast_vote_once_per_poll` | E2E |
| `DS-TS-REJECT-INVALID-VOTE` | `e2e/test_site.py::PollsSiteTest.test_reject_invalid_vote` | E2E |
| `DS-TS-VIEW-ALL-RESULTS` | `e2e/test_site.py::PollsSiteTest.test_view_all_results` | E2E |
| `DS-TS-NAVIGATE-MENU` | `e2e/test_site.py::PollsSiteTest.test_navigate_menu` | E2E |
| `DS-TS-COLOR-THEME` | `e2e/test_site.py::PollsSiteTest.test_color_theme` | E2E |
| `DS-TS-SAMPLE-DATA-ON-EMPTY-START` | `e2e/test_site.py::PollsSiteTest.test_sample_data_on_empty_start` | E2E |
