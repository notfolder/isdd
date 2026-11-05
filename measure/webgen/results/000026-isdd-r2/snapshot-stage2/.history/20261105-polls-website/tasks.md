# 実装タスク: 投票サイト（Polls Website）

前提: `docs/requirements.md` と `docs/detail_design.md` が正本（新規フロー）。変更フローではない（`docs/active_change` は作らない）。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。導入時は実行形態 `server`、認証なし（`--no-auth`）、外部連携なし（`--no-external`）、対応表の粒度 `function`、ソース `src` を渡す。
- 依存の規則は「無い」なので `scripts/isdd/dependencies.json` は規則なしの雛形のままにする。
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。`scripts/isdd/completeness.json` の実行形態が server、認証なし、外部連携なしになっている。

## 1. 実装: 業務処理と DB（DS-MD-DB、DS-MD-POLLS、DS-MD-VOTER、DS-MD-SAMPLE-DATA）

- `src/db.py`: `DS-FN-GET-DB`（DATA_DIR の `polls.db` へ接続。外部キーを有効化）、`DS-FN-INIT-DB`（`DS-SC-POLL-TABLE`・`DS-SC-OPTION-TABLE`・`DS-SC-VOTE-TABLE` のテーブルを作る。既にあれば何もしない。UNIQUE(poll_id, voter_token)、UNIQUE(poll_id, position) を含む）。
- `src/polls.py`: `DS-CL-VOTE-ERROR`（code を持つ例外）、`DS-FN-LIST-POLLS`、`DS-FN-GET-POLL`（選択肢を position 順）、`DS-FN-HAS-VOTED`、`DS-FN-CAST-VOTE`（検査と INSERT を 1 トランザクション。一意制約違反は already_voted）、`DS-FN-GET-RESULTS`（票数、合計、割合を小数第 1 位で。合計 0 は 0.0）、`DS-FN-LIST-POLL-SUMMARIES`（投票テーマごとの合計票数）。
- `src/voter.py`: `DS-FN-GET-VOTER-TOKEN`（Cookie `voter_token` を読む。無ければ None）、`DS-FN-ISSUE-VOTER-TOKEN`（英数字 32 文字を発行）。
- `src/sample_data.py`: `DS-OP-SAMPLE-DATA`（投票テーマが 0 件のときだけ、サンプル 3 件と各 3〜4 選択肢、数票を投入）。
- 完了条件: 各関数が `docs/detail_design.md` の 4-1・4-2・3-1・3-2 に合う。パラメータ化 SQL のみを使う。

## 2. 実装: 画面と起動（DS-MD-SERVER、DS-MD-WEB、DS-OP-START-SERVER）

- `src/web.py`: `DS-IF-ROOT-REDIRECT`（`/` → `/polls` 302）、`DS-IF-POLL-LIST-SCREEN`（`/polls`）、`DS-IF-POLL-DETAIL-SCREEN`（`/polls/<id>`。存在しなければ 404）、`DS-IF-CAST-VOTE-ACTION`（`POST /polls/<id>/vote`。未選択 400、不正 400、投票済み 409（詳細を再表示）、成功は 303 → 結果。Cookie 未発行なら発行して 1 年の HttpOnly・SameSite=Lax で設定）、`DS-IF-POLL-RESULTS-SCREEN`（`/polls/<id>/results`。棒グラフは navy）、`DS-IF-RESULTS-LIST-SCREEN`（`/results`）。
- テンプレート（`src/templates/`）: 共通レイアウト（白背景、navy のナビゲーション「Polls」「Results」）、各画面。英語表示。
- `src/static/style.css`: 白背景、navy（#000080）のコンポーネント。
- `src/server.py`: `DS-FN-CREATE-APP`（DATA_DIR を作り、テーブルを作り、サンプルを入れ、Flask アプリを返す）、`DS-OP-START-SERVER`（`main`。PORT（既定 8000）と DATA_DIR を環境変数から読み、127.0.0.1 で前面起動）。
- 完了条件: 各画面の要素が `docs/detail_design.md` の 4-1 の表どおり。

## 3. 起動スクリプト（DS-OP-SETUP-ENV）

- `setup.sh`: `.venv` を作る（`python3.12` があればそれ、無ければ `python3`）。`requirements.txt`（`Flask==3.1.3`）を入れる。何度実行しても同じ状態になる。
- `run.sh`: `.venv` の Python で `src/server.py` を起動する。PORT と DATA_DIR を読む。
- 完了条件: `bash setup.sh` が完了し、`PORT=任意 bash run.sh` で起動する。

## 4. 単体テスト・結合テスト全件通過タスク

- `tests/`: polls、voter、db、sample_data の関数を一時 DB で確かめる。`web.py` のルートを Flask のテストクライアントで確かめる。
- 実行コマンド（詳細設計書 8-1）: `.venv/bin/python -m unittest discover -s tests -v`
- 完了条件: FAIL が 0 件。

## 5. E2E テスト全件通過タスク（DS-TS-* の 7 件）

- `e2e/test_polls_e2e.py`: 次の関数を作る。`test_browse_polls_flow`（DS-TS-BROWSE-POLLS-E2E）、`test_cast_vote_flow`（DS-TS-CAST-VOTE-E2E）、`test_one_vote_rule`（DS-TS-ONE-VOTE-RULE-E2E）、`test_validate_vote`（DS-TS-VALIDATE-VOTE-E2E）、`test_view_results`（DS-TS-VIEW-RESULTS-E2E）、`test_results_list`（DS-TS-RESULTS-LIST-E2E）、`test_navigation`（DS-TS-NAVIGATION-E2E）。実サーバーを空きポートと一時 DATA_DIR で起動する。
- 実行コマンド（詳細設計書 8-4）: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`
- 完了条件: FAIL と ERROR が 0 件。`e2e/results/e2e.xml` が出ている。

## 6. 対応表（docs/trace_map.md）更新タスク

- 実装したファイル・クラス・公開関数を `docs/trace_map.md` に登録する（書式は trace-map-rules.md。粒度 function）。`DS-MD-*` は各ソースファイル、`DS-TS-*` は E2E の関数（`e2e/test_polls_e2e.py::test_...`）に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 7. README.md 記載タスク

- README.md に起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、`PORT`・`DATA_DIR` の説明）を書く。
- 完了条件: README を読むだけで起動できる。

## 8. 起動確認タスク

- `bash setup.sh` → `PORT=8765 bash run.sh` で起動し、`/`、`/polls`、`/polls/1`、`/results` が 200 系で応答すること、`/` が `/polls` へ転送されることを確認する。
- 完了条件: 起動し、主要な画面が開ける。確認後、起動したプロセスを PID で止める。

## 9. 実装完了チェックタスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目 OK。

## 10. 最終確認（すべての変更点を実装したか）

- `docs/detail_design.md` の 7-2 のファイル一覧と 11 章の DS-ID を 1 つずつ照らし、実装・対応表・テストのいずれにも無い設計要素が無いことを確かめる。
- 完了条件: 未実装の DS-ID が 0 件。
