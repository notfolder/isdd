# 対応表: 設計 ID とコードの対応

設計 ID（DS-ID）とソースコードの対応。書式は isdd の対応表ルールに従う（列: DS-ID、修飾名、備考）。
ソースファイル（DS-MD）、クラス（DS-CL）、関数とメソッド（DS-FN）、画面（DS-IF）、E2E テスト（DS-TS）を 1 つの表にまとめる。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-SERVER-ENTRY` | `src/server.py` | 起動と HTTP の振り分け |
| `DS-MD-REPOSITORY` | `src/repository.py` | SQLite の読み書き |
| `DS-MD-VALIDATION` | `src/validation.py` | 入力の検査、検索条件、固定リスト |
| `DS-MD-SEED-DATA` | `src/seed_data.py` | 見本データ |
| `DS-MD-VIEWS` | `src/views.py` | HTML の画面 |
| `DS-CL-SPECIES-REQUEST-HANDLER` | `src/server.py::SpeciesRequestHandler` | HTTP のリクエストを処理する |
| `DS-CL-SPECIES-REPOSITORY` | `src/repository.py::SpeciesRepository` | 種のテーブルを扱う |
| `DS-FN-MAIN` | `src/server.py::main` | PORT と DATA_DIR を読み、サーバーを起動する |
| `DS-FN-HANDLE-GET` | `src/server.py::SpeciesRequestHandler.do_GET` | GET の振り分け |
| `DS-FN-HANDLE-POST` | `src/server.py::SpeciesRequestHandler.do_POST` | 登録・修正・削除の処理 |
| `DS-FN-INITIALIZE-DATABASE` | `src/repository.py::SpeciesRepository.initialize` | テーブル作成と初回の見本投入 |
| `DS-FN-SEARCH-SPECIES` | `src/repository.py::SpeciesRepository.search` | 部分一致検索と絞り込み |
| `DS-FN-COUNT-SPECIES` | `src/repository.py::SpeciesRepository.count_species` | 全件数 |
| `DS-FN-COUNT-THREATENED-SPECIES` | `src/repository.py::SpeciesRepository.count_threatened_species` | VU・EN・CR の件数 |
| `DS-FN-GET-SPECIES` | `src/repository.py::SpeciesRepository.get` | 1 件の取得 |
| `DS-FN-CREATE-SPECIES` | `src/repository.py::SpeciesRepository.create` | 登録 |
| `DS-FN-UPDATE-SPECIES` | `src/repository.py::SpeciesRepository.update` | 修正 |
| `DS-FN-DELETE-SPECIES` | `src/repository.py::SpeciesRepository.delete` | 削除 |
| `DS-FN-IS-SCIENTIFIC-NAME-TAKEN` | `src/repository.py::SpeciesRepository.is_scientific_name_taken` | 学名の重複確認 |
| `DS-FN-VALIDATE-SPECIES-FIELDS` | `src/validation.py::validate_species_fields` | 項目ごとの検査 |
| `DS-FN-PARSE-SEARCH-QUERY` | `src/validation.py::parse_search_query` | 検索条件の読み取り |
| `DS-FN-SAMPLE-SPECIES-DATA` | `src/seed_data.py::sample_species_data` | 見本の種 12 件 |
| `DS-FN-RENDER-LAYOUT` | `src/views.py::render_layout` | 共通の枠と案内メニュー |
| `DS-FN-RENDER-HOME` | `src/views.py::render_home` | ホーム画面 |
| `DS-FN-RENDER-SPECIES-LIST` | `src/views.py::render_species_list` | 一覧・検索画面 |
| `DS-FN-RENDER-SPECIES-DETAIL` | `src/views.py::render_species_detail` | 詳細画面 |
| `DS-FN-RENDER-SPECIES-FORM` | `src/views.py::render_species_form` | 登録・修正画面 |
| `DS-FN-RENDER-NOT-FOUND` | `src/views.py::render_not_found` | 見つからない画面 |
| `DS-IF-NAVIGATION-MENU` | `src/views.py::render_layout` | 案内メニュー |
| `DS-IF-HOME-SCREEN` | `src/views.py::render_home` | ホーム画面 |
| `DS-IF-SPECIES-LIST-SCREEN` | `src/views.py::render_species_list` | 一覧・検索画面 |
| `DS-IF-SPECIES-DETAIL-SCREEN` | `src/views.py::render_species_detail` | 詳細画面 |
| `DS-IF-SPECIES-CREATE-SCREEN` | `src/views.py::render_species_form` | 登録画面 |
| `DS-IF-SPECIES-EDIT-SCREEN` | `src/views.py::render_species_form` | 修正画面 |
| `DS-IF-NOT-FOUND-SCREEN` | `src/views.py::render_not_found` | 見つからない画面 |
| `DS-TS-OPEN-HOME-AND-MENU` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_open_home_and_menu` | |
| `DS-TS-SAMPLE-DATA-ON-FIRST-RUN` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_sample_data_on_first_run` | |
| `DS-TS-BROWSE-SPECIES-LIST` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_browse_species_list` | |
| `DS-TS-SEARCH-SPECIES-BY-NAME` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_search_species_by_name` | |
| `DS-TS-FILTER-SPECIES` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_filter_species` | |
| `DS-TS-NO-MATCH-MESSAGE` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_no_match_message` | |
| `DS-TS-VIEW-SPECIES-DETAIL` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_view_species_detail` | |
| `DS-TS-CREATE-SPECIES` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_create_species` | |
| `DS-TS-VALIDATE-SPECIES-INPUT` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_validate_species_input` | |
| `DS-TS-UNIQUE-SCIENTIFIC-NAME` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_unique_scientific_name` | |
| `DS-TS-UPDATE-SPECIES` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_update_species` | |
| `DS-TS-DELETE-SPECIES` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_delete_species` | |
| `DS-TS-UNKNOWN-SPECIES` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_unknown_species` | |
| `DS-TS-ESCAPE-USER-INPUT` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_escape_user_input` | |
| `DS-TS-COLOR-THEME` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_color_theme` | 非機能（配色） |
| `DS-TS-ENGLISH-UI` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_english_ui` | 非機能（英語表示） |
| `DS-TS-RESPONSE-TIME` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_response_time` | 非機能（応答時間） |
| `DS-TS-CONCURRENT-ACCESS` | `e2e/test_species_e2e.py::SpeciesE2ETest.test_concurrent_access` | 非機能（同時接続） |
