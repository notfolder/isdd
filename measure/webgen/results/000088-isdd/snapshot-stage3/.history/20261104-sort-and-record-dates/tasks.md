# タスク: 一覧の名前順の並べ替えと詳細画面の登録日時

- 変更要件: `change_requirements.md`、変更設計書: `change_detail_design.md`
- 正本（`docs/requirements.md`・`docs/detail_design.md`）は実装中に書き換えない。実装後レビューで反映する。
- 各タスクの「実装する設計 ID」は変更設計書の 11 章に載っているものだけを使う。

## 0. isdd-setup 導入確認タスク

- 実装する設計 ID: なし（導入の確認）
- 内容: `scripts/isdd/check.sh` が存在し、実行できることを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（ローカルのサーバー）、認証（無し）、外部連携（無し）が正本の第 1 章と第 9 章に一致している。

## 0-2. 進行中の変更の登録確認タスク

- 実装する設計 ID: なし
- 内容: `docs/active_change` の 1 行目が `.history/20261104-sort-and-record-dates` であることを確かめる。正本には変更を反映しない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261104-sort-and-record-dates/change_requirements.md .history/20261104-sort-and-record-dates/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 並べ替えの規則（app/sorting.py）

- 実装する設計 ID: `DS-MD-SORTING`、`DS-FN-SORT-SPECIES-ROWS`
- 内容: 並べ替えの値 `name_asc`（既定）と `name_desc` を定数 `SORT_ORDERS` に持つ。`sort_species_rows(rows, order)` は、行を和名・一般名で大文字小文字を区別せずに並べる。同じ名前は学名（空は後ろ）で比べる。`name_desc` は全体を逆順にする。Flask と SQLite に依存しない。
- 単体テスト: `tests/test_sorting.py` に、昇順・降順、大文字小文字、同じ名前のときの学名の順、空の学名、既定値、空の入力を書く。
- 完了条件: `.venv/bin/python -m unittest tests.test_sorting -v` が全件通ること。

## 2. 並べ替えの値の読み取りと一覧の処理（app/routes.py）

- 実装する設計 ID: `DS-FN-READ-SORT-ORDER`、`DS-FN-LIST-SPECIES-PAGE-SORTED`
- 内容: `read_sort_order` はクエリの `sort` を読み、`SORT_ORDERS` に無い値や未指定は `name_asc` にする。`list_species` は既存の検索・絞り込みの後に `sort_species_rows` で並べ、選んだ並べ替えの値をテンプレートに渡す。既存の `q`・絞り込み・`notice` の動作を変えない。旧い一覧の処理の ID（11 章で [削除]）に対応していた処理は、新しい ID の処理に置き換える。
- 完了条件: 既存の単体テストが全件通ること（`.venv/bin/python -m unittest discover -s tests -t . -v`）。手で `/?sort=name_desc` と `/?sort=xxx` を開き、降順と既定の順になること。

## 3. 並べ替えの選択欄（一覧画面）

- 実装する設計 ID: `DS-IF-SPECIES-LIST-SORT-CONTROL`
- 内容: `species_list.html` の検索の枠に「Sort」の選択欄を置く（ラベル「Sort」、選択肢「Name (A to Z)」値 `name_asc`、「Name (Z to A)」値 `name_desc`）。選択欄は現在の値を選んだ状態で表示する。選択が変わったら検索フォームを送信する（`onchange`）。「Search」ボタンも従来どおり働く。「Clear」は既定に戻る（`/` へのリンクのまま）。
- 完了条件: 一覧画面で Sort を変えると、検索欄と絞り込みの値を保ったまま順序が逆になること。配色は既存の入力欄と同じ（honeydew の背景、dark olive green の枠）。

## 4. 詳細画面の登録日時と最終更新日時（詳細画面）

- 実装する設計 ID: `DS-IF-SPECIES-DETAIL-RECORD-DATES`
- 内容: `species_detail.html` の項目の一覧の末尾に「Added」（`created_at`）と「Last updated」（`updated_at`）を置く。保存値の先頭 16 文字（年月日と時分）の `T` を空白にし、末尾に ` UTC` を付けて「YYYY-MM-DD HH:MM UTC」の形で表示する。
- 完了条件: 詳細画面に Added と Last updated が年月日時分の UTC 表示で出ること。既存の項目（学名、和名、界、綱、生息環境、食性、保全状況、平均体長、説明）の表示は変わらないこと。

## 5. E2E テスト（e2e/test_species_site.py）

- 実装する設計 ID: `DS-TS-SORT-SPECIES-LIST`、`DS-TS-SHOW-SPECIES-RECORD-DATES`
- 内容: `test_sort_species_list` と `test_show_species_record_dates` を既存の E2E の仕組みで追加する。`DS-TS-SORT-SPECIES-LIST` は既定の昇順、降順、検索と絞り込みとの組み合わせ、Clear での既定への復帰を確かめる。`DS-TS-SHOW-SPECIES-RECORD-DATES` は一覧の各行の和名から詳細へ行けること、詳細に全項目と Added・Last updated が出ることを確かめる。
- 完了条件: 2 件のテスト関数が通ること。

## 6. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する。`app/sorting.py`（`DS-MD-SORTING`）、`app/sorting.py::sort_species_rows`（`DS-FN-SORT-SPECIES-ROWS`）、`app/sorting.py::SORT_ORDERS`（定数は `DS-MD-SORTING` の行に含める）、`app/routes.py::read_sort_order`（`DS-FN-READ-SORT-ORDER`）、`app/routes.py::list_species`（`DS-FN-LIST-SPECIES-PAGE-SORTED`）、テスト `DS-TS-SORT-SPECIES-LIST` と `DS-TS-SHOW-SPECIES-RECORD-DATES` の行を e2e のテスト関数へ結ぶ。`DS-FN-LIST-SPECIES-PAGE` の行は削除する（11 章で [削除]）。テンプレートの要素（`DS-IF-SPECIES-LIST-SORT-CONTROL`、`DS-IF-SPECIES-DETAIL-RECORD-DATES`）は対応表の対象（関数）外のため行を作らない。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

## 7. 起動確認タスク

- 内容: `PORT=8011 bash run.sh` を起動し、一覧・詳細・登録の画面が開くことを確かめる。確かめた後は、自分で起動したプロセスだけを止める。
- 完了条件: 起動がエラーなく完了し、一覧画面が HTTP 200 で返ること。

## 8. 単体テスト・結合テスト全件通過タスク

- 内容: `.venv/bin/python -m unittest discover -s tests -t . -v` を全件実行する。
- 完了条件: FAIL が 0 件。

## 9. E2E テスト全件通過タスク

- 内容: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml` を実行する（JUnit XML を `e2e/results/` に出す）。
- 完了条件: FAIL が 0 件。既存の `DS-TS-*` の全件（配色、移行、登録、修正、削除を含む）が通ること。

## 10. README.md 記載タスク

- 内容: README.md の「Features」の一覧に、並べ替え（Name A to Z と Z to A）と、詳細画面の登録日時・最終更新日時を加える。起動方法は変えない。
- 完了条件: README を読むだけで、並べ替えと日時の表示を知れること。

## 11. 実装完了チェックタスク

- 内容: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行し、結果を報告する。
- 完了条件: 全項目が OK であること。

## 12. 変更の全点検タスク

- 内容: 変更要件（`RQ-FT-SORT-SPECIES-LIST`、`RQ-FT-SHOW-SPECIES-RECORD-DATES`、`RQ-UI-SPECIES-LIST-SORT-CONTROL`、`RQ-UI-SPECIES-DETAIL-RECORD-DATES`）と変更設計書の [追加] 設計要素が、すべて実装され対応表に載っていることを確かめる。[削除] の要素が残っていないことを確かめる。
- 完了条件: 未実装・未登録が 0 件であること。結果を実装後レビューに渡す。

## 13. 実装後レビュー（isdd-build に渡す）

- 内容: 変更要件と変更設計書を正本（`docs/requirements.md`・`docs/detail_design.md`）に反映し、`docs/active_change` を消す。
- 完了条件: 正本に、この変更の [追加] が入り、[削除] が消えていること。`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が合格すること。

## 要件の修正の記録

- 変更フローの途中で要件を直した点は無い。

## 設計の修正の記録（段階 1 の途中）

- 実装中に、変更設計書 7 章の依存の規則と `app/routes.py` からの `app/sorting.py` の import が衝突することがわかった（規則は `app/routes.py` の依存先を 3 つに限る）。ユーザーに聞けない条件のため、変更設計書 7 章の依存の規則に `app/sorting.py` を 1 項目だけ足し、`scripts/isdd/dependencies.json` も同じく 1 項目足した。他の規則は変えていない。
