# 実装タスク: 生物種情報データベース

作業ディレクトリ: プロジェクトルート（`/private/tmp/webgen/work/000088-isdd-r1`）。実装は下のタスクを上から順に進める。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時の値: 実行形態 `server`、認証なし（`--no-auth`）、外部連携なし（`--no-external`）、対応表の粒度 `function`、ソースディレクトリ `src`。
- 依存の規則（詳細設計書 7-3）を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態が `server`、認証が無し、外部連携が無しで、詳細設計書と一致していること。

## 1. 基盤ファイル

- 対象設計 ID: `DS-MD-VOCABULARY`、`DS-MD-SERVER`（ファイルのみ）
- `src/core/vocabulary.py`（分類群・生息環境・食性・保全状況の選択肢。詳細設計書 1-1・3-1・7-2 の値どおり）、`src/web/` の空のパッケージ構成（`__init__.py` は作らない）。
- 完了条件: `python3 -c "import src.core.vocabulary"` が成功する。

## 2. 保存層

- 対象設計 ID: `DS-MD-STORE`、`DS-CL-SPECIES-STORE`、`DS-FN-INITIALIZE-STORE`、`DS-FN-LIST-SPECIES`、`DS-FN-GET-SPECIES`、`DS-FN-IS-SCIENTIFIC-NAME-TAKEN`、`DS-FN-CREATE-SPECIES`、`DS-FN-UPDATE-SPECIES`、`DS-FN-DELETE-SPECIES`、`DS-SC-SPECIES-TABLE`
- `src/core/store.py` に `SpeciesStore` を実装する。テーブル `species` と式インデックス（学名の一意）は 3-1 のとおり。`initialize` はテーブルが新しく作られたときだけサンプルを投入する（`DS-FN-SAMPLE-SPECIES` を呼ぶ）。
- 完了条件: 単体テスト `tests/test_store.py` が合格（検索の AND 条件、LIKE のエスケープ、並び順、学名の重複判定、削除）。

## 3. サンプルデータ

- 対象設計 ID: `DS-MD-SEED-DATA`、`DS-FN-SAMPLE-SPECIES`
- `src/core/seed_data.py` に `sample_species` を実装する。12 件程度。分類群・生息環境・食性・保全状況を散らし、寿命の空欄（Unknown の確認用）を 1 件含める。
- 完了条件: 返す値が入力チェックを通ること（`tests/test_validation.py` で確認）。

## 4. 入力チェックと条件の読み取り

- 対象設計 ID: `DS-MD-VALIDATION`、`DS-FN-VALIDATE-SPECIES-INPUT`、`DS-FN-READ-FILTER-CONDITIONS`
- `src/core/validation.py` に `validate_species_input(values, is_name_taken)` と `read_filter_conditions(params)` を実装する。エラー文言は詳細設計書 4-1 と要件 3-2 の英語の文言に従う。
- 完了条件: `tests/test_validation.py` が合格（必須、長さ、選択肢、寿命の範囲、体重の範囲、学名の重複、不正な条件値は All 扱い）。

## 5. 画面生成

- 対象設計 ID: `DS-MD-VIEWS`、`DS-FN-RENDER-LAYOUT`、`DS-FN-RENDER-LIST-PAGE`、`DS-FN-RENDER-DETAIL-PAGE`、`DS-FN-RENDER-FORM-PAGE`、`DS-FN-RENDER-NOT-FOUND-PAGE`、`DS-IF-SITE-LAYOUT`、`DS-IF-SPECIES-LIST-PAGE`、`DS-IF-SPECIES-DETAIL-PAGE`、`DS-IF-SPECIES-FORM-PAGE`
- `src/web/views.py` を実装する。全値を HTML エスケープする。詳細画面の削除は確認ダイアログ付き。`src/web/static/style.css` を作る（背景 #FAF0E6、部品 #800000、白文字）。
- 完了条件: 各関数が文字列を返し、エスケープされること（単体テストは作らず、E2E で確認）。

## 6. HTTP サーバーと起動

- 対象設計 ID: `DS-MD-SERVER`、`DS-FN-MAIN`、`DS-CL-SPECIES-REQUEST-HANDLER`、`DS-IF-SPECIES-CREATE`、`DS-IF-SPECIES-UPDATE`、`DS-IF-SPECIES-DELETE`
- `src/web/server.py` を実装する。`main` は環境変数 PORT（既定 8000）と DATA_DIR（既定はプロジェクトの `data`）を読み、`127.0.0.1` で待ち受ける。経路は詳細設計書 4-1 の表のとおり。POST 後は 303 でリダイレクトする。
- 完了条件: 手動で `PORT=8123 bash run.sh` を起動し、`curl -s http://127.0.0.1:8123/` が 200 を返すこと（確認後に自分の起動したプロセスの PID だけを止める）。

## 7. 起動スクリプトと README

- 対象設計 ID: `DS-OP-SETUP-SCRIPT`、`DS-OP-RUN-SCRIPT`
- `setup.sh`（Python 3.9 以上の確認、DATA_DIR の作成）と `run.sh`（PORT と DATA_DIR の既定値、`src` を import できる場所から `python3 -m src.web.server` を前面で実行）。
- `README.md` に起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、画面の URL）を書く。
- 完了条件: `bash setup.sh` が成功し、`PORT=任意 bash run.sh` で起動すること。

## 8. 単体テスト

- `tests/test_validation.py`、`tests/test_store.py`
- 実行コマンド: `python3 -m unittest discover -s tests -p "test_*.py"`
- 完了条件: テストに FAIL が 0 件。

## 9. E2E テスト

- 対象設計 ID: 詳細設計書 8-2 の `DS-TS-*` 10 件
- `e2e/test_browse_species.py`、`e2e/test_search_filter.py`、`e2e/test_manage_species.py`、`e2e/test_layout.py`。各テストは一時フォルダを DATA_DIR にして子プロセスで実サーバーを起動し、終わったら子プロセスを止める。
- 実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`
- 完了条件: 全件通過。FAIL が 0 件。
- 対応表の `DS-TS` 行（テスト関数）は、XML の testcase 名を確かめてから登録する（タスク 10）。

## 10. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は trace-map-rules.md。粒度 function）。`DS-TS-*` はテスト関数に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること（受け入れ判定は E2E の XML を読む）。

## 11. 起動確認タスク

- 詳細設計書 9 章の起動方法（`bash setup.sh`、`PORT=任意 bash run.sh`）で起動し、`/` と詳細・登録画面が開けること。起動確認後、起動したプロセスの PID だけを止める。
- 完了条件: 起動がエラーなく完了し、主要な画面が 200 を返すこと。

## 12. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- `python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` を実行する。
- 完了条件: 全項目が OK、rq_ds_link_checker が問題 0 件。

## 13. 実装後レビュー（isdd-build の段階 2）

- 新規フローのため変更の反映は無い。未マッピング一覧の作成、`docs/proposals.md` の削除（あれば）、`docs/requirements.md` の整合チェック、`check.sh --strict` を実行し、結果を報告する。
- 完了条件: 未マッピングの確認、要件ごとの実装済み判定の表。

## 14. 全変更点の確認タスク（最後）

- 要件 `RQ-FT-*`・`RQ-UI-*`・`RQ-OP-*`・`RQ-NF-*` のすべてが、画面または起動で確かめられること。詳細設計書 11 章の対応が実装されていること。
- 完了条件: 全 `DS-TS-*` が合格、画面の目視確認（Chromium は使わず、HTML と CSS の値を確認）。
