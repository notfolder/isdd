# 実装タスク: Polls Website（投票サイト）

入力: `docs/requirements.md`、`docs/detail_design.md`。上から順に実行する。
実行形態: サーバー（`bash run.sh`）。認証: 無し。外部連携: 無し。対応表の粒度: function。

---

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が存在しなければ `isdd-setup` を実行する。導入時は `--src src --runtime server --no-auth --no-external --granularity function` を渡す。依存の規則を `scripts/isdd/dependencies.json` に書き写す（設計書 7-4 の 2 行）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致していること。`scripts/isdd/dependencies.json` が設計書 7-4 と一致していること。

## 1. 保存処理（DS-MD-STORE、DS-FN-INIT-DB、DS-FN-SEED-SAMPLE-POLLS、DS-FN-LIST-POLLS、DS-FN-GET-POLL、DS-FN-CAST-VOTE、DS-SC-POLL、DS-SC-POLL-OPTION、DS-SC-VOTE）

- `src/store/__init__.py`（空）と `src/store/db.py` を作る。
- `init_db(db_path)`: テーブル `polls`・`poll_options`・`votes` を作る（設計書 3-1 の制約どおり）。`PRAGMA foreign_keys = ON`。
- `seed_sample_polls(db_path)`: `polls` が 0 件のときだけ、投票テーマ 3 件（各 3〜4 選択肢）とサンプル票数件を入れる。
- `list_polls(db_path)`: 全投票テーマを返す（総票数と一番多い選択肢の名前を含む）。
- `get_poll(db_path, poll_id)`: 投票テーマ 1 件と、選択肢ごとの票数・割合（小数点 1 桁、四捨五入）・総票数を返す。無ければ `None`。
- `cast_vote(db_path, poll_id, option_id)`: 1 トランザクションで、選択肢が投票テーマに属するかを確かめ、`votes` に 1 行追加する。属さない・存在しない場合は `ValueError`。
- 完了条件: 単体テスト `tests/test_store.py` を書き、`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -v` で全件通過する（テストは 2 の後に走らせてよい。Flask 無しでも動くこと）。

## 2. 起動処理（DS-MD-MAIN、DS-FN-READ-SETTINGS、DS-FN-MAIN）と仮想環境（DS-OP-SETUP-ENVIRONMENT、DS-OP-START-SERVER）

- `requirements.txt`（`Flask==3.1.3`）、`setup.sh`（`.venv` を作り、依存を入れる。何度実行しても同じ状態）、`run.sh`（`PORT` 既定 8000、`DATA_DIR` 既定 `./data`、`exec .venv/bin/python src/main.py`）を作る。`.gitignore` に `.venv/`、`data/`、`e2e/results/` を入れる。
- `src/main.py`: `read_settings()` で環境変数を読み、`main()` で `init_db` と `seed_sample_polls` を呼び、Flask アプリを `127.0.0.1:PORT` で起動する（`src/web/app.py` の `create_app` を使う）。
- 完了条件: `bash setup.sh` が成功し、`PORT=8123 DATA_DIR=<空の一時ディレクトリ> bash run.sh` が前景で起動し、`http://127.0.0.1:8123/` が応答すること。

## 3. 画面（DS-MD-APP、DS-FN-CREATE-APP、DS-IF-POLL-LIST-SCREEN、DS-IF-POLL-DETAIL-SCREEN、DS-IF-VOTE-SUBMIT、DS-IF-POLL-RESULTS-SCREEN、DS-IF-RESULTS-OVERVIEW-SCREEN、DS-IF-NAVIGATION-MENU、DS-FN-HANDLE-NOT-FOUND）

- `src/web/app.py`: `create_app(db_path)`（`app.config["DB_PATH"]` に保存し、ルートとエラー処理と文脈プロセッサを登録する）。ルート関数はモジュールの直下に置く（`show_poll_list`、`show_poll_detail`、`submit_vote`、`show_poll_results`、`show_results_overview`）。`handle_not_found`（404）と `provide_navigation`（メニュー）も同じ。
- テンプレート（英語。`src/web/templates/`）: `base.html`（白背景、上部の navy のナビゲーション「Polls」「Results」、現在の画面の強調）、`poll_list.html`、`poll_detail.html`（ラジオボタン、「Vote」、エラー文言 "Please select one option before you vote."）、`poll_results.html`（票数の表、navy の横棒グラフ、「Thank you for voting.」は `voted=1` のときだけ、0 件は "No votes yet"、「Back to polls」）、`results_overview.html`（投票テーマごとの行、「Details」）、`not_found.html`（"Not found"、「Polls」へのリンク）。
- `src/web/static/style.css`: 背景 #FFFFFF。ナビゲーション、見出し、ボタン、結果バーなどの部品は navy（#000080）。
- 投票: 未選択・整数でない・属さない選択肢は詳細画面を 400 で再表示。成功は 303 で `/polls/<id>/results?voted=1`。
- 完了条件: Flask のテストクライアントか実サーバーで、全 URL（`/`、`/polls/<id>`、`/polls/<id>/vote`、`/polls/<id>/results`、`/results`、存在しない URL）が期待の HTTP 状態で応答すること。

## 4. E2E テスト（DS-TS-BROWSE-POLL-LIST、DS-TS-VIEW-POLL-OPTIONS、DS-TS-CAST-VOTE-AND-VIEW-RESULT、DS-TS-REJECT-INVALID-VOTE、DS-TS-VIEW-ALL-RESULTS、DS-TS-NAVIGATE-MENU、DS-TS-SAMPLE-DATA-ON-EMPTY-START）

- `e2e/test_site.py`: クラス `PollsSiteTest`（unittest）。`setUpClass` で空の一時 DATA_DIR と空きポートを用意し、`src/main.py` を子プロセス（`sys.executable`）として起動する。`tearDownClass` で停止する。各シナリオを次のメソッド名で書く: `test_browse_poll_list`、`test_view_poll_options`、`test_cast_vote_and_view_result`、`test_reject_invalid_vote`、`test_view_all_results`、`test_navigate_menu`、`test_sample_data_on_empty_start`（最後のテストは別の一時 DATA_DIR で別プロセスを起動する）。
- 完了条件: 設計書 8-4 の実行コマンドで全件通過する。

## 5. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・関数を `docs/trace_map.md` に登録する（書式は trace-map-rules.md。粒度 function）。DS-MD（`src/main.py`、`src/store/db.py`、`src/web/app.py`）、DS-FN、DS-IF、DS-TS（`e2e/test_site.py::PollsSiteTest.test_...`）の行を書く。DS-SC は載せない（第 7 章の「実現する設計 ID」に書いていないため）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること（E2E の XML を先に出しておく）。

## 6. 起動確認タスク

- 設計書 9 章の起動方法（`bash setup.sh` → `PORT=<任意> bash run.sh`）で起動し、`http://127.0.0.1:<PORT>/` が開けること。
- 完了条件: 起動がエラーなく完了し、主要な画面が開けること。

## 7. 単体テスト・結合テスト全件通過タスク

- 設計書 8-1 の実行コマンド（`PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -v`）を実行する。
- 完了条件: テスト結果に FAIL・ERROR が 0 件。

## 8. E2E テスト全件通過タスク

- 設計書 8-4 の実行コマンド（`.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`）を実行する。
- 完了条件: テスト結果に FAIL・ERROR が 0 件。失敗したら修正と再実行を繰り返し、全件通過まで続ける。

## 9. README.md 記載タスク

- README.md に「起動方法」（`bash setup.sh`、`PORT=8000 bash run.sh`、`http://127.0.0.1:8000`、`DATA_DIR` と `PORT` の説明）を書く。認証は無いので初期ユーザーは書かない。
- 完了条件: README.md だけで初回起動が完結すること。

## 10. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK であること。

## 11. 要件・設計の全変更点の実装確認タスク

- 要件定義書 3 章の機能（RQ-FT 5 件、RQ-FT 2 件の業務ルール）、4-5 の画面（RQ-UI 5 件）、4-1 のデータ（RQ-DT）、7 章のシナリオ（RQ-TS 7 件）がすべて実装されていることを確かめる。
- 完了条件: 上記のすべてが E2E で通り、`check.sh --strict` の受け入れ判定が全要件を「実装済み」と判定すること。
