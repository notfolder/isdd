# tasks.md: 生物種情報データベースの実装タスク

詳細設計書 `docs/detail_design.md` と要件定義書 `docs/requirements.md` にもとづく。上から順に進める。
実装のコードには要件 ID・設計 ID を書かない。対応は `docs/trace_map.md` に記録する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時の値は次のとおり: `--src src --runtime server --no-auth --no-external --granularity function`
- 第 7 章の依存の規則（無し）を `scripts/isdd/dependencies.json` の雛形のまま使う
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態が server、認証が無し、外部連携が無しである

## 1. 入力検査と検索条件（DS-MD-VALIDATION）

- 実装: `src/validation.py`。固定リスト（綱、生息環境、食性、保全状況の値と表示名）、学名・一般名・科・平均寿命・平均体重・説明の検査、検索条件の読み取り
- 実装する設計 ID: DS-MD-VALIDATION、DS-FN-VALIDATE-SPECIES-FIELDS、DS-FN-PARSE-SEARCH-QUERY、DS-SC-CODE-LISTS
- 完了条件: `tests/test_validation.py` が全件通過する（空欄、範囲外、固定リスト外、学名の長さ、体重の小数桁、検索文字列の空白、All の無視）

## 2. 見本データ（DS-MD-SEED-DATA）

- 実装: `src/seed_data.py`。見本の種 12 件を返す関数。要件 1-2 の見本一覧に従う
- 実装する設計 ID: DS-MD-SEED-DATA、DS-FN-SAMPLE-SPECIES-DATA
- 完了条件: 12 件、学名が一意、綱・生息環境・食性・保全状況が固定リストの値である（`tests/test_seed_data.py`）

## 3. データ access（DS-MD-REPOSITORY）

- 実装: `src/repository.py`。SpeciesRepository（初期化、検索、件数、取得、作成、更新、削除、学名の重複確認）。SQLite ファイルは DATA_DIR の `species.sqlite3`
- 実装する設計 ID: DS-MD-REPOSITORY、DS-CL-SPECIES-REPOSITORY、DS-FN-INITIALIZE-DATABASE、DS-FN-SEARCH-SPECIES、DS-FN-COUNT-SPECIES、DS-FN-COUNT-THREATENED-SPECIES、DS-FN-GET-SPECIES、DS-FN-CREATE-SPECIES、DS-FN-UPDATE-SPECIES、DS-FN-DELETE-SPECIES、DS-FN-IS-SCIENTIFIC-NAME-TAKEN、DS-SC-SPECIES-TABLE、DS-SC-META-TABLE、DS-OP-FIRST-RUN-SEED
- 完了条件: `tests/test_repository.py` が全件通過する（初回の見本投入と再起動で重複投入しないこと、学名の大文字小文字を区別しない一意性、部分一致検索と AND の絞り込み、並び順、作成・更新・削除）

## 4. 画面生成とスタイル（DS-MD-VIEWS）

- 実装: `src/views.py`（共通の枠、ホーム、一覧、詳細、登録・修正、見つからない画面）と `src/static/style.css`（リネン #FAF0E6 の背景、マルーン #800000 のコンポーネント）
- 実装する設計 ID: DS-MD-VIEWS、DS-FN-RENDER-LAYOUT、DS-FN-RENDER-HOME、DS-FN-RENDER-SPECIES-LIST、DS-FN-RENDER-SPECIES-DETAIL、DS-FN-RENDER-SPECIES-FORM、DS-FN-RENDER-NOT-FOUND、DS-IF-NAVIGATION-MENU、DS-IF-HOME-SCREEN、DS-IF-SPECIES-LIST-SCREEN、DS-IF-SPECIES-DETAIL-SCREEN、DS-IF-SPECIES-CREATE-SCREEN、DS-IF-SPECIES-EDIT-SCREEN、DS-IF-NOT-FOUND-SCREEN
- 完了条件: `tests/test_views.py` が全件通過する（利用者の入力が HTML としてエスケープされる、案内メニューが全画面にある、「Species not found.」などの英語の文言）

## 5. Web サーバーと起動（DS-MD-SERVER-ENTRY）

- 実装: `src/server.py`（SpeciesRequestHandler。GET と POST の振り分け、POST 後は 303 で移動、削除の確認はブラウザ側）。main は PORT（既定 8000）と DATA_DIR（既定 `data`）を環境変数から読み、0.0.0.0 で待ち受け、ThreadingHTTPServer で前面実行する
- 実装する設計 ID: DS-MD-SERVER-ENTRY、DS-CL-SPECIES-REQUEST-HANDLER、DS-FN-MAIN、DS-FN-HANDLE-GET、DS-FN-HANDLE-POST、DS-OP-START-SCRIPT
- 完了条件: `tests/test_http.py`（結合テスト）が全件通過する。一覧・詳細・登録・修正・削除・見つからない画面の HTTP 応答を確かめる。`PORT=18123 DATA_DIR=<一時ディレクトリ> bash run.sh` で起動し、ホームが HTTP 200 で返る（確認後、自分が起動したプロセスだけを止める）

## 6. 準備と文書

- 実装: `setup.sh`（`.venv` の作成、`requirements-dev.txt` の Playwright 1.64.1 のインストール、`playwright install chromium`。何度実行しても同じ状態）、`run.sh`（環境変数の既定値を決め、`python3 src/server.py` を実行）、`requirements-dev.txt`、`README.md`（起動方法、PORT と DATA_DIR、見本データの注意）、`.gitignore`（`data/`、`.venv/`）
- 実装する設計 ID: DS-OP-SETUP-SCRIPT、DS-OP-START-SCRIPT
- 完了条件: `bash setup.sh` が成功する。`README.md` に「起動方法」がある

## 7. E2E テスト

- 実装: `e2e/test_species_e2e.py`（unittest と Playwright）。テストごとに一時の DATA_DIR とテスト用ポートでサーバーを起動し、テスト後に自分が起動したプロセスだけを止める
- 実装する設計 ID: 詳細設計書 8-2 の DS-TS-*（18 本）。対応表の `DS-TS` の行でテスト関数に結ぶ
- 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` の全件が通過する

## 8. 対応表の更新（docs/trace_map.md）

- 実装したファイル、クラス、公開関数、DS-IF の画面関数、DS-TS のテスト関数を、詳細設計書 第 7 章と第 8 章に従って対応表に登録する
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（受け入れ判定を含む）

## 9. 起動確認タスク

- 詳細設計書 第 9 章のとおり `bash setup.sh` の後、`PORT=任意 bash run.sh` で起動し、ホームと主要画面が開けることを確かめる。確認後、自分が起動したプロセスだけを PID で止める
- 完了条件: 起動がエラーなく完了し、ホームと一覧が HTTP 200 で返ること

## 10. 単体テスト・結合テスト全件通過タスク

- 実行コマンド: `python3 -m unittest discover -s tests -p "test_*.py" -v`
- 完了条件: FAIL と ERROR が 0 件

## 11. E2E テスト全件通過タスク

- 実行コマンド: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
- 完了条件: FAIL と ERROR が 0 件。失敗した場合は修正と再実行を繰り返す

## 12. README.md 記載タスク

- README.md に「起動方法」を書く（認証が無いため「初期ユーザー」は書かない）
- 完了条件: README.md だけで初回起動が完結する

## 13. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
- 完了条件: 全項目 OK

## 14. 実装後レビュー（isdd-build 段階 2）

- 正本の反映は新規フローのため、変更の反映は無い。`docs/proposals.md` を作った場合は削除する。
- `python3 .claude/skills/isdd-build/scripts/rq_integrity_checker.py docs/requirements.md`、`rq_ds_link_checker.py`、`bash scripts/isdd/check.sh --strict` の結果を確かめる
- 完了条件: 未マッピング一覧（該当なしを含む）、要件ごとの実装済み判定の表を報告に載せる
