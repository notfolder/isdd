# 対応表（設計 ID とコードの対応）

書式は対応表のルール（trace-map-rules.md）に従う。粒度は function。要件 ID との対応は詳細設計書の「要件と設計の対応表」にある。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-APP-FACTORY` | `app/__init__.py` | アプリの組み立て |
| `DS-FN-CREATE-APP` | `app/__init__.py::create_app` | DATA_DIR の準備、表の作成、サンプル投入 |
| `DS-MD-APP-MAIN` | `app/__main__.py` | 127.0.0.1 の PORT で起動 |
| `DS-OP-START-SERVER` | `app/__main__.py::main` | 前景で起動（run.sh と setup.sh は対応表の対象外。下の記録） |
| `DS-MD-DB` | `app/db.py` | SQLite 接続と表 |
| `DS-FN-CONNECT-DATABASE` | `app/db.py::connect_database` | DATA_DIR/species.db へ接続 |
| `DS-FN-ENSURE-DATABASE-SCHEMA` | `app/db.py::ensure_database_schema` | 表の作成 |
| `DS-FN-MIGRATE-SPECIES-TABLE` | `app/db.py::migrate_species_table` | 旧い定義の species 表を新しい定義へ移す |
| `DS-SC-SPECIES-TABLE` | `app/db.py::ensure_database_schema` | species 表の定義 |
| `DS-MD-CONSTANTS` | `app/constants.py` | 選択肢と入力の上限 |
| `DS-MD-REPOSITORY` | `app/repository.py` | 生物種の表の読み書き |
| `DS-CL-SPECIES-REPOSITORY` | `app/repository.py::SpeciesRepository` | 読み書きのクラス |
| `DS-CL-SPECIES-REPOSITORY` | `app/repository.py::SpeciesRepository.close` | 接続を閉じる |
| `DS-FN-SEARCH-SPECIES-RECORDS` | `app/repository.py::SpeciesRepository.search` | キーワードと条件の AND 検索 |
| `DS-FN-GET-SPECIES-RECORD` | `app/repository.py::SpeciesRepository.get` | id で 1 件取得 |
| `DS-FN-FIND-SPECIES-ID-BY-SCIENTIFIC-NAME` | `app/repository.py::SpeciesRepository.find_id_by_scientific_name` | 学名の重複判定 |
| `DS-FN-INSERT-SPECIES-RECORD` | `app/repository.py::SpeciesRepository.insert` | 追加 |
| `DS-FN-UPDATE-SPECIES-RECORD` | `app/repository.py::SpeciesRepository.update` | 更新 |
| `DS-FN-DELETE-SPECIES-RECORD` | `app/repository.py::SpeciesRepository.delete` | 削除 |
| `DS-MD-VALIDATION` | `app/validation.py` | 入力の読み取りと検証 |
| `DS-CL-SPECIES-FORM` | `app/validation.py::SpeciesForm` | 入力値とエラー |
| `DS-CL-SPECIES-FORM` | `app/validation.py::SpeciesForm.field_values` | 入力値の辞書 |
| `DS-FN-PARSE-SPECIES-FORM` | `app/validation.py::parse_species_form` | フォームの読み取り |
| `DS-FN-VALIDATE-SPECIES-FORM` | `app/validation.py::validate_species_form` | 項目と学名の検証 |
| `DS-MD-ROUTES` | `app/routes.py` | 経路と画面の処理 |
| `DS-FN-LIST-SPECIES-PAGE` | `app/routes.py::list_species` | 一覧・検索・絞り込み |
| `DS-IF-SPECIES-LIST-SCREEN` | `app/routes.py::list_species` | 一覧画面（GET /） |
| `DS-IF-GLOBAL-NAVIGATION` | `app/routes.py::list_species` | 案内メニュー（base.html を全画面で使う） |
| `DS-FN-SHOW-SPECIES-DETAIL-PAGE` | `app/routes.py::show_species_detail` | 詳細画面 |
| `DS-IF-SPECIES-DETAIL-SCREEN` | `app/routes.py::show_species_detail` | 詳細画面（存在しない種の 404 を含む） |
| `DS-FN-SHOW-CREATE-FORM-PAGE` | `app/routes.py::show_create_form` | 登録画面の表示 |
| `DS-IF-SPECIES-FORM-SCREEN` | `app/routes.py::show_create_form` | 登録・修正画面 |
| `DS-FN-SUBMIT-CREATE-FORM` | `app/routes.py::submit_create_form` | 登録の保存 |
| `DS-FN-SHOW-EDIT-FORM-PAGE` | `app/routes.py::show_edit_form` | 修正画面の表示 |
| `DS-IF-SPECIES-FORM-SCREEN` | `app/routes.py::show_edit_form` | 登録・修正画面（修正） |
| `DS-FN-SUBMIT-EDIT-FORM` | `app/routes.py::submit_edit_form` | 修正の保存 |
| `DS-FN-SHOW-DELETE-CONFIRM-PAGE` | `app/routes.py::show_delete_confirm` | 削除確認画面 |
| `DS-IF-SPECIES-DELETE-CONFIRM-SCREEN` | `app/routes.py::show_delete_confirm` | 削除確認画面 |
| `DS-FN-SUBMIT-DELETE-SPECIES` | `app/routes.py::submit_delete` | 削除の実行 |
| `DS-MD-SEED` | `app/seed.py` | サンプルの定義 |
| `DS-FN-SEED-SAMPLE-SPECIES-IF-EMPTY` | `app/seed.py::seed_sample_species_if_empty` | 表が空のときの投入 |
| `DS-TS-STARTUP-WITH-SAMPLE-DATA` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_startup_with_sample_data` | 空の DATA_DIR の起動 |
| `DS-TS-BROWSE-AND-VIEW-SPECIES` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_browse_and_view_species` | 一覧から詳細 |
| `DS-TS-SEARCH-SPECIES-KEYWORD` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_search_species_keyword` | キーワード検索 |
| `DS-TS-FILTER-AND-COMBINE` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_filter_and_combine` | 絞り込みと組み合わせ |
| `DS-TS-UPDATE-SPECIES-RECORD` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_update_species_record` | 修正 |
| `DS-TS-DELETE-SPECIES-RECORD` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_delete_species_record` | 削除の確認と取り消し |
| `DS-TS-ADD-SPECIES-FORM` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_add_species_form` | 登録画面と、一覧・検索・絞り込みへの反映、学名の重複 |
| `DS-TS-MIGRATE-EXISTING-DATABASE` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_migrate_existing_database` | 旧い定義の既存データの移行 |
| `DS-TS-THEME-HONEYDEW-OLIVE` | `e2e/test_species_site.py::SpeciesSiteE2ETest.test_theme_honeydew_olive` | 配色 |
