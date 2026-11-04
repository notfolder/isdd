# 実装タスク: 配色の変更と登録画面の項目の変更

- 変更要件定義書: `.history/20261104-theme-and-add-species-form/change_requirements.md`
- 変更設計書: `.history/20261104-theme-and-add-species-form/change_detail_design.md`
- 正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中は書き換えない。反映は実装後の `isdd-build` の実装後レビューが行う。

## 固定の先頭タスク

### 0. isdd-setup 導入確認タスク

- 対象の設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` があることを確かめる。`scripts/isdd/completeness.json`（runtime: server、auth: false、external: false、e2e_dir: e2e）が詳細設計書 1 章・9 章と一致することを確かめる。`scripts/isdd/dependencies.json` が設計書 7 章の依存の規則と一致することを確かめる（変更なし）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、上の内容が一致すること。

### 0-2. 進行中の変更の登録確認タスク

- 対象の設計 ID: なし
- 内容: `docs/active_change` の 1 行目が `.history/20261104-theme-and-add-species-form/` を指していることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-theme-and-add-species-form/change_requirements.md .history/20261104-theme-and-add-species-form/change_detail_design.md --base docs/requirements.md` が合格すること。

## 実装タスク

### 1. 配色の変更（画面の見た目）

- 対象の設計 ID: `DS-TS-THEME-HONEYDEW-OLIVE`（配色を確かめるテストの設計。実装はスタイルシート）
- 対象の要件: `RQ-NF-VISUAL-THEME-HONEYDEW-OLIVE`
- 内容: `app/static/style.css` の色を `:root` の変数で定義し直す。背景 `#F0FFF0`（honeydew）。部品（案内メニュー、ボタン、リンク、表の見出し、入力欄の枠、バッジ、削除確認の枠など）は `#556B2F`（dark olive green）。部品の上の文字は `#FFFFFF`。linen と maroon の値は残さない。
- 完了条件: `app/static/style.css` に `#FAF0E6` と `#800000` が無く、`#F0FFF0` と `#556B2F` が使われていること（`grep` で確かめる）。画面を開いて一覧、詳細、登録の各画面が新しい配色で表示されること。

### 2. 登録・修正の項目の変更（学名・界・保全状況を任意に）

- 対象の設計 ID: `DS-SC-SPECIES-TABLE`（スキーマの NULL 可）、`DS-FN-ENSURE-DATABASE-SCHEMA`（移行の呼び出し）、`DS-FN-MIGRATE-SPECIES-TABLE`（新設、`app/db.py`）、`DS-MD-REPOSITORY`・`DS-CL-SPECIES-REPOSITORY`・`DS-FN-INSERT-SPECIES-RECORD`・`DS-FN-UPDATE-SPECIES-RECORD`（NULL の保存）、`DS-FN-FIND-SPECIES-ID-BY-SCIENTIFIC-NAME`（学名が空の種を除く判定）、`DS-CL-SPECIES-FORM`・`DS-FN-PARSE-SPECIES-FORM`・`DS-FN-VALIDATE-SPECIES-FORM`・`DS-MD-VALIDATION`（規則の変更、空の任意項目は NULL）、`DS-FN-SHOW-CREATE-FORM-PAGE`・`DS-FN-SUBMIT-CREATE-FORM`・`DS-FN-SUBMIT-EDIT-FORM`・`DS-MD-ROUTES`（経路の処理）、`DS-IF-SPECIES-FORM-SCREEN`（画面の項目と「*」）、`DS-IF-SPECIES-LIST-SCREEN`・`DS-IF-SPECIES-DETAIL-SCREEN`（空の欄に「—」）
- 対象の要件: `RQ-FT-ADD-SPECIES-FORM`、`RQ-FT-VALIDATE-SPECIES-FORM`、`RQ-UI-SPECIES-FORM-SCREEN`、`RQ-OP-MIGRATE-EXISTING-DATABASE`
- 内容:
  - `app/db.py`: `species` 表の `scientific_name`、`kingdom`、`conservation_status` を NULL 可にする（CHECK は NULL を許す。UNIQUE は COLLATE NOCASE のまま）。既存の表が旧い定義（上の 3 カラムが NOT NULL）なら、`species_new` を作って全行を写し、`species` を削除して改名する（1 トランザクション）。`PRAGMA table_info` で判定し、新しい定義なら何もしない。
  - `app/validation.py` と `app/constants.py`: 名前（`common_name`）、生息環境、食性だけを必須にする。学名、界、保全状況は値がある場合だけ規則を当てる。学名の重複判定は学名がある場合だけ。エラーの文言は変更設計書 4-1 のとおり。
  - `app/repository.py`: 空の任意項目を NULL で保存する。
  - `app/routes.py`: 登録と修正の処理は既存の流れのまま。
  - `app/templates/species_form.html`: 項目の順は Name、Habitat、Diet、Description を先頭にし、残りの任意項目を後ろに置く。必須に「*」を付ける。見出しの「Add species」「Edit species」は変えない。ラベル「Common name」は「Name」に変える。
  - `app/templates/species_list.html` と `app/templates/species_detail.html`: 学名、界、保全状況が空のときは「—」を出す。
- 完了条件: 単体テストが通ること（タスク 3）。空の学名、界、保全状況で登録と修正ができ、同じ学名（大小違い）の 2 回目は保存されず重複のエラーが出ること。既存の DB（旧い定義）が起動時に移行され、行が残ること。

### 3. 単体テストの更新と追加

- 対象の設計 ID: `DS-MD-VALIDATION`、`DS-CL-SPECIES-FORM`、`DS-MD-REPOSITORY`、`DS-FN-ENSURE-DATABASE-SCHEMA`、`DS-FN-MIGRATE-SPECIES-TABLE`（テストは `tests/` に書く。テストファイルには DS-* を書かない）
- 内容: `tests/test_validation.py` を新しい規則に合わせる（学名が空でも通る、名前・生息環境・食性の必須、学名の重複は学名がある場合だけ）。`tests/test_repository.py` に NULL の保存を足す。`tests/test_seed.py` は変更の影響を確かめる。移行のテストを足す（旧い定義の表を作り、起動で新しい定義になり、行が残ること。新しい定義では何もしないこと）。
- 完了条件: `.venv/bin/python -m unittest discover -s tests -t . -v` が全件通過すること。

### 4. E2E テストの更新と追加

- 対象の設計 ID: `DS-TS-ADD-SPECIES-FORM`（新設。旧い `DS-TS-CREATE-SPECIES-RECORD` の関数を置き換える）、`DS-TS-THEME-HONEYDEW-OLIVE`（旧い `DS-TS-THEME-LINEN-MAROON` の関数を置き換える）、`DS-TS-MIGRATE-EXISTING-DATABASE`（新設）、`DS-TS-UPDATE-SPECIES-RECORD`（既存。修正の期待は変えない）、`DS-TS-STARTUP-WITH-SAMPLE-DATA`・`DS-TS-BROWSE-AND-VIEW-SPECIES`・`DS-TS-SEARCH-SPECIES-KEYWORD`・`DS-TS-FILTER-AND-COMBINE`・`DS-TS-DELETE-SPECIES-RECORD`（既存。通ること）
- 内容: `e2e/test_species_site.py` の関数を 8-2 の変更どおりに直す。`test_create_species_record` を `test_add_species_form`、`test_theme_linen_maroon` を `test_theme_honeydew_olive`、新しく `test_migrate_existing_database` を足す。登録の E2E は、実サーバーに `/species/new` へ POST し、追加された種が `/`、`/?q=gecko`、`/?habitat=Terrestrial&diet=Carnivore` に出ること、2 回目の同じ学名が 200 で重複のエラーを返すことを確かめる。
- 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` が全件通過すること（FAIL 0 件）。

### 5. README の更新

- 対象の設計 ID: なし（文書）
- 内容: README の Features の Manage（登録の項目の必須、学名は任意で一意）と、配色の説明（あれば）を現状に合わせる。Start の説明は変えない。
- 完了条件: README を読んで、登録の必須項目と起動方法が分かること。

## 実装完了確認の固定タスク

### 6. 対応表（docs/trace_map.md）更新タスク

- 内容: 変更設計書 11 章の追加（`DS-FN-MIGRATE-SPECIES-TABLE`、`DS-TS-ADD-SPECIES-FORM`、`DS-TS-THEME-HONEYDEW-OLIVE`、`DS-TS-MIGRATE-EXISTING-DATABASE`）の行を足し、削除（`DS-TS-CREATE-SPECIES-RECORD`、`DS-TS-THEME-LINEN-MAROON`）の行を外す。`DS-FN-MIGRATE-SPECIES-TABLE` は `app/db.py::migrate_species_table`（関数名は実装で決めるが、対応表の行に書く）。新設・改名したクラスや関数の行も足す。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

### 7. 起動確認タスク

- 内容: 詳細設計書 9 章の起動方法のとおり `bash setup.sh` と `PORT=任意 bash run.sh` で起動し、`/`、`/species/1`、`/species/new` が開くことを確かめる。
- 完了条件: 起動がエラーなく完了し、3 画面が 200 で返ること。

### 8. 単体テスト・結合テスト全件通過タスク

- 内容: 8-1 の実行コマンドで単体テストを全件実行する。
- 完了条件: FAIL が 0 件であること。

### 9. E2E テスト全件通過タスク

- 内容: 8-4 の実行コマンドで E2E を全件実行する。
- 完了条件: FAIL が 0 件であること。

### 10. 変更点の実装確認タスク

- 内容: 変更要件定義書の [追加] の要件（`RQ-FT-ADD-SPECIES-FORM`、`RQ-FT-VALIDATE-SPECIES-FORM`、`RQ-NF-VISUAL-THEME-HONEYDEW-OLIVE`、`RQ-OP-MIGRATE-EXISTING-DATABASE`、`RQ-UI-SPECIES-FORM-SCREEN` の表示の変更）と、[削除] の要件（`RQ-FT-CREATE-SPECIES-RECORD`、`RQ-FT-VALIDATE-SPECIES-RECORD`、`RQ-NF-VISUAL-THEME-LINEN-MAROON`）が、コードとテストから消えているか、実装されているかを確かめる。
- 完了条件: 上のすべてが実装され、旧い配色の値と旧い必須の規則がコードに残っていないこと。

## 修正の記録（tasks.md の末尾）

- 変更要件・変更設計で、番号を付けた ID の変更はない（新しい要件 ID は [追加] で採番済み）。
