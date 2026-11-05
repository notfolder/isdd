# 対応表: 設計 ID とコードの対応

粒度: class（ファイルとクラスまで。設計書にある DS-IF は、その入口のメソッドに結ぶ）。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER` | `app/server.py` | モジュール |
| `DS-MD-CONFIG` | `app/config.py` | モジュール |
| `DS-MD-DATABASE` | `app/db.py` | モジュール |
| `DS-MD-POLLS` | `app/polls.py` | モジュール |
| `DS-MD-SEED` | `app/seed.py` | モジュール |
| `DS-MD-VIEWS` | `app/views.py` | モジュール（HTML と CSS） |
| `DS-CL-HTTP-SERVER` | `app/server.py::PollsHTTPServer` | クラス |
| `DS-CL-REQUEST-HANDLER` | `app/server.py::PollsRequestHandler` | クラス |
| `DS-CL-POLL-SERVICE` | `app/polls.py::PollService` | クラス |
| `DS-CL-DATABASE` | `app/db.py::Database` | クラス |
| `DS-CL-SAMPLE-SEEDER` | `app/seed.py::SampleSeeder` | クラス |
| `DS-IF-ROOT-REDIRECT` | `app/server.py::PollsRequestHandler.do_GET` | GET / の入口 |
| `DS-IF-POLL-LIST-SCREEN` | `app/server.py::PollsRequestHandler.do_GET` | GET /polls の入口 |
| `DS-IF-POLL-VOTE-SCREEN` | `app/server.py::PollsRequestHandler.do_GET` | GET /polls/{id} の入口 |
| `DS-IF-POLL-VOTE-SUBMIT` | `app/server.py::PollsRequestHandler.do_POST` | POST /polls/{id}/vote の入口 |
| `DS-IF-POLL-RESULTS-SCREEN` | `app/server.py::PollsRequestHandler.do_GET` | GET /polls/{id}/results の入口 |
| `DS-IF-RESULTS-LIST-SCREEN` | `app/server.py::PollsRequestHandler.do_GET` | GET /results の入口 |
| `DS-TS-BROWSE-AND-VOTE-E2E` | `e2e/test_site.py::test_browse_and_vote_e2e` | E2E |
| `DS-TS-VOTE-WITHOUT-SELECTION-E2E` | `e2e/test_site.py::test_vote_without_selection_e2e` | E2E |
| `DS-TS-ONE-VOTE-E2E` | `e2e/test_site.py::test_one_vote_per_browser_e2e` | E2E |
| `DS-TS-RESULTS-LIST-E2E` | `e2e/test_site.py::test_results_list_e2e` | E2E |
| `DS-TS-UNKNOWN-POLL-E2E` | `e2e/test_site.py::test_unknown_poll_e2e` | E2E |
| `DS-TS-VISUAL-STYLE-E2E` | `e2e/test_site.py::test_visual_style_e2e` | E2E |
| `DS-TS-EMPTY-RESULTS-E2E` | `e2e/test_site.py::test_empty_poll_results_e2e` | E2E |
| `DS-TS-UNIT-POLL-SERVICE` | `e2e/test_polls_unit.py` | 単体テスト |
