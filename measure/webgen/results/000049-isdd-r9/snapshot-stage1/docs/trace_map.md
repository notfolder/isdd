# 対応表（設計 ID とコードの対応）

粒度: class（設計書 第 7 章）。要件 ID との対応は設計書 第 11 章。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| DS-MD-SERVER-ENTRY | `src/web/server.py` | 起動部 |
| DS-MD-APP-HANDLER | `src/web/app.py` | HTTP 層 |
| DS-MD-VIEWS | `src/web/views.py` | HTML 生成 |
| DS-MD-STORE | `src/core/db.py` | 保存 |
| DS-MD-VALIDATION | `src/core/validation.py` | 入力検査 |
| DS-MD-WHATSAPP-LINK | `src/core/whatsapp.py` | 送信リンク |
| DS-CL-STORE | `src/core/db.py::Store` | SQLite の保存と取得 |
| DS-CL-APP-HANDLER | `src/web/app.py::AppHandler` | 経路の振り分けと POST の処理 |
| DS-CL-VALIDATION-ERROR | `src/core/validation.py::ValidationError` | エラー文の一覧を運ぶ例外 |
| DS-FN-SEED-SAMPLE-DATA | `src/core/db.py::Store.seed_sample_data_if_empty` | 空のときサンプルを投入 |
| DS-FN-VALIDATE-BARBER-FORM | `src/core/validation.py::validate_barber_form` | D7 |
| DS-FN-VALIDATE-SERVICE-FORM | `src/core/validation.py::validate_service_form` | D8 |
| DS-FN-VALIDATE-NOTIFY-FORM | `src/core/validation.py::validate_notify_form` | D9 |
| DS-FN-BUILD-WHATSAPP-LINK | `src/core/whatsapp.py::build_whatsapp_link` | wa.me リンク |
| DS-FN-SPLIT-PHONE-LIST | `src/core/whatsapp.py::split_phone_list` | 番号の分解 |
| DS-IF-HTTP-ROUTES | `src/web/app.py::AppHandler.do_GET` | GET の経路 |
| DS-IF-HTTP-ROUTES | `src/web/app.py::AppHandler.do_POST` | POST の経路 |
| DS-IF-HOME-SCREEN | `src/web/views.py::render_home` | Home |
| DS-IF-BARBER-LIST-SCREEN | `src/web/views.py::render_barber_list` | Barbers 一覧 |
| DS-IF-BARBER-ADD-SCREEN | `src/web/views.py::render_barber_form` | Add barber |
| DS-IF-SERVICE-LIST-SCREEN | `src/web/views.py::render_service_list` | Services 一覧 |
| DS-IF-SERVICE-ADD-SCREEN | `src/web/views.py::render_service_form` | Add service |
| DS-IF-NOTIFY-SCREEN | `src/web/views.py::render_notify_form` | Notify |
| DS-IF-PAGE-LAYOUT | `src/web/views.py::render_layout` | 共通レイアウト（雪、配色、メニュー） |
| DS-TS-START-WITH-SAMPLE-DATA-E2E | `e2e/test_site.py::EmptyDataDirTests.test_start_with_sample_data` | |
| DS-TS-NAVIGATE-FROM-HOME-E2E | `e2e/test_site.py::SampleSiteTests.test_navigate_from_home` | |
| DS-TS-BROWSE-AND-ADD-BARBER-E2E | `e2e/test_site.py::SampleSiteTests.test_browse_and_add_barber` | |
| DS-TS-BROWSE-AND-ADD-SERVICE-E2E | `e2e/test_site.py::SampleSiteTests.test_browse_and_add_service` | |
| DS-TS-SEND-WHATSAPP-LINKS-E2E | `e2e/test_site.py::SampleSiteTests.test_send_whatsapp_links` | |
| DS-TS-REJECT-INVALID-ENTRIES-E2E | `e2e/test_site.py::SampleSiteTests.test_reject_invalid_entries` | |
| DS-TS-SNOW-AND-GRAY-THEME-E2E | `e2e/test_site.py::SampleSiteTests.test_snow_and_gray_theme` | |
