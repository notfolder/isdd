# 対応表: 設計 ID とコードの対応

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-VOCABULARY` | `src/core/vocabulary.py` | モジュール |
| `DS-MD-SEED-DATA` | `src/core/seed_data.py` | モジュール |
| `DS-FN-SAMPLE-SPECIES` | `src/core/seed_data.py::sample_species` | 初期サンプル |
| `DS-MD-VALIDATION` | `src/core/validation.py` | モジュール |
| `DS-FN-VALIDATE-SPECIES-INPUT` | `src/core/validation.py::validate_species_input` | 入力チェック |
| `DS-FN-READ-FILTER-CONDITIONS` | `src/core/validation.py::read_filter_conditions` | 検索条件の読み取り |
| `DS-MD-STORE` | `src/core/store.py` | モジュール |
| `DS-CL-SPECIES-STORE` | `src/core/store.py::SpeciesStore` | 保存クラス |
| `DS-FN-INITIALIZE-STORE` | `src/core/store.py::SpeciesStore.initialize` | DB とテーブルの作成、初回だけサンプル投入 |
| `DS-FN-LIST-SPECIES` | `src/core/store.py::SpeciesStore.list_species` | 検索と絞り込み |
| `DS-FN-GET-SPECIES` | `src/core/store.py::SpeciesStore.get_species` | 1 件の取得 |
| `DS-FN-IS-SCIENTIFIC-NAME-TAKEN` | `src/core/store.py::SpeciesStore.is_scientific_name_taken` | 学名の重複判定 |
| `DS-FN-CREATE-SPECIES` | `src/core/store.py::SpeciesStore.create_species` | 登録 |
| `DS-FN-UPDATE-SPECIES` | `src/core/store.py::SpeciesStore.update_species` | 修正 |
| `DS-FN-DELETE-SPECIES` | `src/core/store.py::SpeciesStore.delete_species` | 削除 |
| `DS-MD-SERVER` | `src/web/server.py` | モジュール |
| `DS-FN-MAIN` | `src/web/server.py::main` | 起動（PORT、DATA_DIR、127.0.0.1） |
| `DS-CL-SPECIES-REQUEST-HANDLER` | `src/web/server.py::SpeciesRequestHandler` | 経路の振り分け |
| `DS-IF-SPECIES-CREATE` | `src/web/server.py::SpeciesRequestHandler.do_POST` | POST /species/new |
| `DS-IF-SPECIES-UPDATE` | `src/web/server.py::SpeciesRequestHandler.do_POST` | POST /species/<id>/edit |
| `DS-IF-SPECIES-DELETE` | `src/web/server.py::SpeciesRequestHandler.do_POST` | POST /species/<id>/delete |
| `DS-MD-VIEWS` | `src/web/views.py` | モジュール |
| `DS-FN-RENDER-LAYOUT` | `src/web/views.py::render_layout` | 共通レイアウト |
| `DS-IF-SITE-LAYOUT` | `src/web/views.py::render_layout` | ナビゲーションと配色の枠 |
| `DS-CL-SPECIES-REQUEST-HANDLER` | `src/web/server.py::SpeciesRequestHandler.do_GET` | GET の経路（一覧・詳細・登録修正・スタイルシート） |
| `DS-FN-RENDER-LIST-PAGE` | `src/web/views.py::render_list_page` | 一覧画面 |
| `DS-IF-SPECIES-LIST-PAGE` | `src/web/views.py::render_list_page` | GET / |
| `DS-FN-RENDER-DETAIL-PAGE` | `src/web/views.py::render_detail_page` | 詳細画面 |
| `DS-IF-SPECIES-DETAIL-PAGE` | `src/web/views.py::render_detail_page` | GET /species/<id> |
| `DS-FN-RENDER-FORM-PAGE` | `src/web/views.py::render_form_page` | 登録・修正画面 |
| `DS-IF-SPECIES-FORM-PAGE` | `src/web/views.py::render_form_page` | GET /species/new、GET /species/<id>/edit |
| `DS-FN-RENDER-NOT-FOUND-PAGE` | `src/web/views.py::render_not_found_page` | 404 画面 |
| `DS-TS-BROWSE-SPECIES-LIST` | `e2e/test_browse_species.py::BrowseSpeciesTest.test_browse_species_list` | E2E |
| `DS-TS-VIEW-SPECIES-DETAIL` | `e2e/test_browse_species.py::BrowseSpeciesTest.test_view_species_detail` | E2E |
| `DS-TS-SEARCH-SPECIES` | `e2e/test_search_filter.py::SearchFilterTest.test_search_species` | E2E |
| `DS-TS-FILTER-SPECIES` | `e2e/test_search_filter.py::SearchFilterTest.test_filter_species` | E2E |
| `DS-TS-CREATE-SPECIES` | `e2e/test_manage_species.py::ManageSpeciesTest.test_create_species` | E2E |
| `DS-TS-VALIDATE-SPECIES-INPUT` | `e2e/test_manage_species.py::ManageSpeciesTest.test_validate_species_input` | E2E |
| `DS-TS-UPDATE-SPECIES` | `e2e/test_manage_species.py::ManageSpeciesTest.test_update_species` | E2E |
| `DS-TS-DELETE-SPECIES` | `e2e/test_manage_species.py::ManageSpeciesTest.test_delete_species` | E2E |
| `DS-TS-NAVIGATION-AND-STYLE` | `e2e/test_layout.py::LayoutTest.test_navigation_and_style` | E2E |
| `DS-TS-FRESH-START` | `e2e/test_browse_species.py::FreshStartTest.test_fresh_start_shows_samples_and_keeps_them_after_restart` | E2E |
