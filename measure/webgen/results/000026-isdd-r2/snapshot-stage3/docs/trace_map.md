# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER` | `src/server.py` | 実行の入口 |
| `DS-FN-CREATE-APP` | `src/server.py::create_app` | アプリ作成と初期化 |
| `DS-OP-START-SERVER` | `src/server.py::main` | PORT で 127.0.0.1 に起動 |
| `DS-MD-DB` | `src/db.py` | SQLite 接続とテーブル作成 |
| `DS-FN-GET-DB` | `src/db.py::get_db` | DATA_DIR の polls.db へ接続 |
| `DS-FN-INIT-DB` | `src/db.py::init_db` | テーブルを作る（無ければ） |
| `DS-MD-POLLS` | `src/polls.py` | 投票テーマの参照・投票・集計 |
| `DS-CL-VOTE-ERROR` | `src/polls.py::VoteError` | 投票の拒否理由（code） |
| `DS-FN-LIST-POLLS` | `src/polls.py::list_polls` | 投票テーマの一覧 |
| `DS-FN-GET-POLL` | `src/polls.py::get_poll` | 投票テーマと選択肢 |
| `DS-FN-HAS-VOTED` | `src/polls.py::has_voted` | 投票済みか |
| `DS-FN-CAST-VOTE` | `src/polls.py::cast_vote` | 検査と保存 |
| `DS-FN-GET-RESULTS` | `src/polls.py::get_results` | 票数と割合 |
| `DS-FN-LIST-POLL-SUMMARIES` | `src/polls.py::list_poll_summaries` | 結果一覧用の合計票数 |
| `DS-MD-VOTER` | `src/voter.py` | 投票用 Cookie |
| `DS-FN-GET-VOTER-TOKEN` | `src/voter.py::get_voter_token` | Cookie の読み取り |
| `DS-FN-ISSUE-VOTER-TOKEN` | `src/voter.py::issue_voter_token` | 新しい投票者識別子 |
| `DS-MD-SAMPLE-DATA` | `src/sample_data.py` | サンプルの投入 |
| `DS-OP-SAMPLE-DATA` | `src/sample_data.py::seed_sample_data` | 空のときだけ投入 |
| `DS-MD-WEB` | `src/web.py` | 画面と投票の受付 |
| `DS-IF-ROOT-REDIRECT` | `src/web.py::root_redirect` | `/` → `/surveys` |
| `DS-IF-POLL-LIST-SCREEN` | `src/web.py::poll_list_page` | 投票一覧 |
| `DS-IF-POLL-VOTE-SCREEN` | `src/web.py::poll_detail_page` | 投票詳細と投票フォーム（投票済みは選択肢と Vote を無効化） |
| `DS-IF-CAST-VOTE-ACTION` | `src/web.py::cast_vote_action` | 投票の受付（POST） |
| `DS-IF-POLL-RESULTS-SCREEN` | `src/web.py::poll_results_page` | 投票結果 |
| `DS-IF-RESULTS-LIST-SCREEN` | `src/web.py::results_list_page` | 結果一覧 |
| `DS-IF-LEGACY-POLL-REDIRECT` | `src/web.py::legacy_poll_redirect` | 旧 `/polls` 系のパスを `/surveys` 系へ 302 で転送 |
| `DS-TS-BROWSE-POLLS-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_browse_polls_flow` | 一覧から詳細まで |
| `DS-TS-CAST-VOTE-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_cast_vote_flow` | 投票と結果への反映 |
| `DS-TS-ONE-VOTE-RULE-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_one_vote_rule` | 同じブラウザの 2 回目の投票を拒否 |
| `DS-TS-VALIDATE-VOTE-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_validate_vote` | 未選択・不正な選択肢を拒否 |
| `DS-TS-VIEW-RESULTS-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_view_results` | 結果の票数と割合 |
| `DS-TS-RESULTS-LIST-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_results_list` | 結果一覧からの移動 |
| `DS-TS-NAVIGATION-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_navigation` | ナビゲーション |
| `DS-TS-VERIFY-VOTE-LOCK-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_verify_vote_lock` | 投票済みの操作の無効化と直接の 2 回目の投票の拒否 |
| `DS-TS-VERIFY-COLOR-THEME-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_verify_color_theme` | 全画面の配色（背景と部品の色） |
| `DS-TS-VERIFY-SURVEY-WORDING-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_verify_survey_wording` | 利用者の画面に poll の語が無いこと、ナビゲーションが Surveys であること |
| `DS-TS-VERIFY-LEGACY-URL-E2E` | `e2e/test_polls_e2e.py::PollsEndToEndTest.test_verify_legacy_url` | 旧パスが新しいパスへ転送されること |
