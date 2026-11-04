# 対応表（設計 ID とコードの対応）

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER` | `app/__main__.py` | 起動の入口（python -m app） |
| `DS-OP-RUN-SERVER` | `app/__main__.py::main` | 127.0.0.1 で前景起動 |
| `DS-OP-ENVIRONMENT-VARIABLES` | `app/__main__.py::main` | PORT と DATA_DIR の読み取り |
| `DS-MD-APP-PACKAGE` | `app/__init__.py` | アプリの組み立て |
| `DS-FN-CREATE-APP` | `app/__init__.py::create_app` | アプリの生成と初期化 |
| `DS-MD-DATABASE` | `app/database.py` | DB の接続と初期化 |
| `DS-FN-OPEN-DATABASE` | `app/database.py::open_database` | SQLite を開く |
| `DS-FN-INIT-SCHEMA` | `app/database.py::init_schema` | テーブルを作る |
| `DS-SC-POLLS-TABLE` | `app/database.py::init_schema` | polls テーブル（SCHEMA の定義を作る） |
| `DS-SC-OPTIONS-TABLE` | `app/database.py::init_schema` | options テーブル（SCHEMA の定義を作る） |
| `DS-SC-VOTES-TABLE` | `app/database.py::init_schema` | votes テーブル（SCHEMA の定義を作る） |
| `DS-MD-SAMPLE-DATA` | `app/sample_data.py` | 初期データ |
| `DS-FN-SEED-SAMPLE-DATA` | `app/sample_data.py::seed_sample_data` | 投票が無いときだけ初期データを入れる |
| `DS-MD-REPOSITORY` | `app/repository.py` | SQL の発行 |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository` | 投票・選択肢・票の読み書き |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.insert_poll` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.insert_option` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.count_polls` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.list_polls` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.get_poll` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.list_options` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.get_option` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.find_vote` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.insert_vote` | メソッド |
| `DS-CL-POLL-REPOSITORY` | `app/repository.py::PollRepository.count_votes_by_option` | メソッド |
| `DS-MD-VOTING` | `app/voting.py` | 投票の業務ロジック |
| `DS-CL-VOTING-SERVICE` | `app/voting.py::VotingService` | 投票の検証と集計 |
| `DS-FN-CAST-VOTE` | `app/voting.py::VotingService.cast_vote` | 1 投票 1 票と選択肢の検証 |
| `DS-FN-CAST-VOTE` | `app/voting.py::PollNotFound` | 投票が無いときの例外 |
| `DS-FN-CAST-VOTE` | `app/voting.py::InvalidVote` | 選択肢の不備の例外 |
| `DS-FN-GET-POLL-RESULT` | `app/voting.py::VotingService.get_poll_result` | 投票ごとの票数と割合 |
| `DS-FN-GET-ALL-RESULTS` | `app/voting.py::VotingService.get_all_results` | 全投票の結果 |
| `DS-MD-VIEWS` | `app/views.py` | 経路と画面 |
| `DS-FN-IDENTIFY-VOTER` | `app/views.py::identify_voter` | 利用者識別子の取得 |
| `DS-IF-POLLS-PAGE` | `app/views.py::index` | 投票の一覧 |
| `DS-IF-POLL-PAGE` | `app/views.py::poll_page` | 投票の詳細と結果 |
| `DS-IF-NOT-FOUND` | `app/views.py::poll_page` | 存在しない投票の 404 表示 |
| `DS-IF-VOTE-ACTION` | `app/views.py::vote` | 投票の受け付け |
| `DS-IF-RESULTS-PAGE` | `app/views.py::results` | 全投票の結果 |
| `DS-TS-UNIT-REPOSITORY` | `tests/test_repository.py` | 単体テスト |
| `DS-TS-UNIT-VOTING` | `tests/test_voting.py` | 単体テスト |
| `DS-TS-BROWSE-POLLS-E2E` | `e2e/test_polls_e2e.py::test_browse_polls` | E2E |
| `DS-TS-CAST-VOTE-E2E` | `e2e/test_polls_e2e.py::test_cast_vote` | E2E |
| `DS-TS-REJECT-INVALID-VOTE-E2E` | `e2e/test_polls_e2e.py::test_reject_invalid_vote` | E2E |
| `DS-TS-ONE-VOTE-E2E` | `e2e/test_polls_e2e.py::test_one_vote_per_poll` | E2E |
| `DS-TS-RESULT-AFTER-VOTE-E2E` | `e2e/test_polls_e2e.py::test_result_after_vote` | E2E |
| `DS-TS-ALL-RESULTS-E2E` | `e2e/test_polls_e2e.py::test_all_results` | E2E |
| `DS-TS-NAVIGATION-E2E` | `e2e/test_polls_e2e.py::test_navigation` | E2E |
| `DS-TS-SAMPLE-DATA-E2E` | `e2e/test_polls_e2e.py::test_sample_data_on_empty_data_dir` | E2E |
| `DS-TS-THEME-E2E` | `e2e/test_polls_e2e.py::test_theme` | E2E |
| `DS-TS-PUBLIC-ACCESS-E2E` | `e2e/test_polls_e2e.py::test_public_access` | E2E |
| `DS-TS-VOTED-POLL-STATE-E2E` | `e2e/test_polls_e2e.py::test_voted_poll_state` | E2E |
