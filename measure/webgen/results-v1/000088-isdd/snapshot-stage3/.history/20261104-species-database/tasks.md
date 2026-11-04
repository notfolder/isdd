# 実装タスク: 生物種情報データベース

対象: `docs/requirements.md`（要件）と `docs/detail_design.md`（設計）。タスクは上から順に行う。
すべてのコマンドはプロジェクトルートで実行する。E2E 以外のテストは `.venv/bin/python` を使う。

## 0. isdd-setup 導入確認

- 対象の設計 ID: なし（導入の確認）
- 作業: `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。実行時に渡す値は、実行形態 = サーバー、認証 = 無し、外部連携 = 無し、対応表の粒度 = function（詳細設計書 第 7 章）。第 7 章の依存の規則を `scripts/isdd/dependencies.json` に書き写す。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致している。

## 1. 起動スクリプトと依存

- 対象の設計 ID: `DS-MD-SETUP-SCRIPT`、`DS-MD-RUN-SCRIPT`、`DS-OP-START-SERVER`
- 作業:
  - `requirements.txt` に `Flask==3.1.3` を書く。
  - `setup.sh`: `.venv`（Python 3.12）を作り、`requirements.txt` を入れる。何度実行しても同じ状態になる。
  - `run.sh`: `PORT`（既定 8000）と `DATA_DIR`（既定 `./data`）を環境変数から読み、`DATA_DIR` を作成し、`.venv/bin/python -m app` を前景で実行する。
- 完了条件: `bash setup.sh` が成功する。`PORT=8123 bash run.sh` が起動し、`127.0.0.1` の 8123 で応答する（`app/` が無い段階では、起動の失敗ではなく `No module named app` の表示まで確かめる）。
- 検証: `bash setup.sh && bash setup.sh`（2 回目も成功）。

## 2. データベース接続と表の作成

- 対象の設計 ID: `DS-MD-DB`、`DS-FN-CONNECT-DATABASE`、`DS-FN-ENSURE-DATABASE-SCHEMA`、`DS-SC-SPECIES-TABLE`、`DS-MD-CONSTANTS`
- 作業:
  - `app/constants.py`: 界（Animalia、Plantae、Fungi、Protista、Bacteria、Archaea）、生息環境（Terrestrial、Freshwater、Marine、Mixed）、食性（Herbivore、Carnivore、Omnivore、Other）、保全状況（コード LC、NT、VU、EN、CR、EW、EX、DD と英語の表示名）の選択肢を定義する。
  - `app/db.py`: `DATA_DIR/species.db` へ接続する。`species` 表（設計書 3-1 のカラムと CHECK 制約、UNIQUE の COLLATE NOCASE）を無ければ作る。
- 完了条件: 単体テスト（`tests/test_repository.py` の表作成のテスト）が通る。空の DATA_DIR で表が作られる。
- 検証: `.venv/bin/python -m unittest discover -s tests -t . -v`。

## 3. リポジトリ（生物種の読み書き）

- 対象の設計 ID: `DS-MD-REPOSITORY`、`DS-CL-SPECIES-REPOSITORY`、`DS-FN-SEARCH-SPECIES-RECORDS`、`DS-FN-GET-SPECIES-RECORD`、`DS-FN-FIND-SPECIES-ID-BY-SCIENTIFIC-NAME`、`DS-FN-INSERT-SPECIES-RECORD`、`DS-FN-UPDATE-SPECIES-RECORD`、`DS-FN-DELETE-SPECIES-RECORD`
- 作業: `app/repository.py` の `SpeciesRepository` を実装する。検索はキーワード（学名・和名・説明の部分一致、大文字小文字を区別しない、パラメータ渡し）と 4 つの条件を AND で組み合わせる。学名の判定は、大文字小文字を区別せず、除外する id を受け取る。
- 完了条件: 単体テストで、検索（キーワード、条件、AND の組み合わせ、0 件）、取得（存在しない id は無し）、学名の重複判定（除外 id を含む）、追加・更新・削除が確かめられる。
- 検証: `.venv/bin/python -m unittest discover -s tests -t . -v`。

## 4. 入力の読み取りと検証

- 対象の設計 ID: `DS-MD-VALIDATION`、`DS-CL-SPECIES-FORM`、`DS-FN-PARSE-SPECIES-FORM`、`DS-FN-VALIDATE-SPECIES-FORM`
- 作業: `app/validation.py` の `SpeciesForm`、`parse_species_form`、`validate_species_form` を実装する。設計書 4-1 のエラーメッセージの表（英語）のとおりに、項目ごとのエラーを作る。学名の重複は `SpeciesRepository.find_id_by_scientific_name` で判定する（修正時は自分の id を除く）。
- 完了条件: 単体テストで、各項目の違反（空、桁数、選択肢外、平均体長の範囲と小数桁、学名の重複、修正時の自分の学名は重複としない）と、正しい入力の通過が確かめられる。
- 検証: `.venv/bin/python -m unittest discover -s tests -t . -v`。

## 5. サンプルの投入と Flask アプリケーションの組み立て

- 対象の設計 ID: `DS-MD-SEED`、`DS-FN-SEED-SAMPLE-SPECIES-IF-EMPTY`、`DS-MD-APP-FACTORY`、`DS-FN-CREATE-APP`、`DS-MD-APP-MAIN`
- 作業:
  - `app/seed.py`: 表が空のとき 12 件の英語のサンプル（学名、和名、界、綱、生息環境、食性、保全状況、平均体長、説明。全保全区分と全生息環境を少なくとも 1 件ずつ含める）を入れる。
  - `app/__init__.py` の `create_app`: `DATA_DIR` を読み、表を作り、サンプルを投入し、Flask アプリを返す。
  - `app/__main__.py`: `127.0.0.1` と環境変数 `PORT` で、デバッグを切って起動する。
- 完了条件: 単体テストで、空の DB に 12 件が入り、2 回目の起動では増えないことを確かめる。
- 検証: `.venv/bin/python -m unittest discover -s tests -t . -v`。

## 6. 画面の描画と経路

- 対象の設計 ID: `DS-MD-ROUTES`、`DS-FN-LIST-SPECIES-PAGE`、`DS-FN-SHOW-SPECIES-DETAIL-PAGE`、`DS-FN-SHOW-CREATE-FORM-PAGE`、`DS-FN-SUBMIT-CREATE-FORM`、`DS-FN-SHOW-EDIT-FORM-PAGE`、`DS-FN-SUBMIT-EDIT-FORM`、`DS-FN-SHOW-DELETE-CONFIRM-PAGE`、`DS-FN-SUBMIT-DELETE-SPECIES`、`DS-MD-TEMPLATE-BASE`、`DS-MD-TEMPLATE-SPECIES-LIST`、`DS-MD-TEMPLATE-SPECIES-DETAIL`、`DS-MD-TEMPLATE-SPECIES-FORM`、`DS-MD-TEMPLATE-SPECIES-DELETE-CONFIRM`、`DS-MD-STYLESHEET`、`DS-IF-SPECIES-LIST-SCREEN`、`DS-IF-SPECIES-DETAIL-SCREEN`、`DS-IF-SPECIES-FORM-SCREEN`、`DS-IF-SPECIES-DELETE-CONFIRM-SCREEN`、`DS-IF-GLOBAL-NAVIGATION`
- 作業:
  - `app/routes.py`: 設計書 4-1 の経路（`/`、`/species/<id>`、`/species/new`、`/species/<id>/edit`、`/species/<id>/delete`）を実装する。登録と修正の成功は詳細へ 302 で転送し、削除の成功は `/?notice=deleted` へ転送する。存在しない id は 404 で「Species not found.」を返す。
  - テンプレート 5 つ（英語。`base.html` に上部の案内メニュー「Species Database」「Browse species」「Add species」を置く）と `style.css`（背景 `#FAF0E6`、部品は `#800000`。ボタン、リンク、案内メニュー、表の見出し、入力欄の枠、選択の強調をすべて maroon 系にする）を作る。
  - 一覧の選択欄は、`app/constants.py` の値と表示名から作る。空の選択は「All」。
- 完了条件: 設計書 4-1 の全画面が 200 で描画され、一覧の 0 件表示（「No species match」）と `notice=deleted` の表示が出る。HTML の値は自動エスケープされる。
- 検証: `PORT=8123 bash run.sh` で起動し、`curl -s http://127.0.0.1:8123/` と `/species/1`、`/species/new` が 200 を返すこと。

## 7. 単体テストと結合テスト

- 対象の設計 ID: `DS-TS-*` は E2E（タスク 8）で扱う。ここでは設計書 8-1 の単体・結合テストを書く。
- 作業: `tests/test_repository.py`、`tests/test_validation.py`、`tests/test_seed.py` を書く（標準ライブラリ `unittest`）。タスク 2〜5 の完了条件のテストを含める。
- 完了条件: `.venv/bin/python -m unittest discover -s tests -t . -v` で FAIL が 0 件。
- 検証: 同上。

## 8. E2E テスト

- 対象の設計 ID: `DS-TS-STARTUP-WITH-SAMPLE-DATA`、`DS-TS-BROWSE-AND-VIEW-SPECIES`、`DS-TS-SEARCH-SPECIES-KEYWORD`、`DS-TS-FILTER-AND-COMBINE`、`DS-TS-CREATE-SPECIES-RECORD`、`DS-TS-UPDATE-SPECIES-RECORD`、`DS-TS-DELETE-SPECIES-RECORD`、`DS-TS-THEME-LINEN-MAROON`
- 作業: `e2e/test_species_site.py` に、設計書 8-2 の 8 場面を 8 つのテスト関数（関数名は `test_` で始まる英語の名前）として書く。各テストは、一時ディレクトリを `DATA_DIR` にして、`127.0.0.1` の空きポートで実サーバーを起動し、HTTP（`urllib`）で確かめる。テストの後はサーバーを停止する（起動したプロセスの PID だけを止める）。
- 完了条件: 下の実行コマンドで全件通過する（FAIL 0 件）。
- 検証: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`。

## 9. README

- 対象の設計 ID: `DS-OP-START-SERVER`
- 作業: `README.md` に、起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、`PORT` と `DATA_DIR` の意味、サンプルデータ）を書く。初期ユーザーは無い。
- 完了条件: README だけを読んで初回起動が完結する。

## 10. 対応表（docs/trace_map.md）更新

- 対象の設計 ID: 設計書の全 `DS-MD`、`DS-CL`、`DS-FN`、`DS-TS` と、第 7 章の「実現する設計 ID」
- 作業: 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は対応表のルール。粒度は function）。`DS-TS-*` は `e2e/test_species_site.py::関数名` で結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通る。

## 11. 起動確認

- 作業: `bash setup.sh` の後、`PORT=8000 bash run.sh` を起動し、`/`、`/species/1`、`/species/new` を開けることを確かめる。
- 完了条件: エラーなく起動し、3 画面が 200 を返す。

## 12. 単体・結合テストと E2E テストの全件通過

- 作業: タスク 7 と 8 の実行コマンドを全件実行する。失敗したら修正と再実行を繰り返す。
- 完了条件: 両方の FAIL が 0 件。

## 13. 実装完了チェック

- 作業: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 14. 変更点の確認（最後）

- 作業: 要件定義書 2 章から 7 章と設計書 1 章から 11 章のすべての項目が実装されているかを確かめる（RQ-FT・RQ-UI・RQ-NF・RQ-OP・RQ-TS の全件が E2E と対応表で追跡できること）。
- 完了条件: 未実装の項目が 0 件。
