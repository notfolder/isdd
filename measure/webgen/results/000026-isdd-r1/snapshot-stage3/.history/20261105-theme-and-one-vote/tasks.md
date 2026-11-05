# 実装タスク: 配色の変更と、1 ブラウザ 1 回の投票（変更）

入力: `.history/20261105-theme-and-one-vote/change_requirements.md`、`.history/20261105-theme-and-one-vote/change_detail_design.md`（正本 `docs/requirements.md`・`docs/detail_design.md` に重ねて読む。有効な設計 ID は「正本 ＋ [追加] − [削除]」）。上から順に実行する。
実行形態: サーバー（`bash run.sh`）。認証: 無し。外部連携: 無し。対応表の粒度: function。
正本（`docs/requirements.md`・`docs/detail_design.md`・`docs/trace_map.md`）は、この tasks では書き換えない（反映は実装後レビューの段階）。

---

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が存在する（導入済み）。`scripts/isdd/VERSION`（v2.2.0）と isdd-build の `metadata.version`（v2.2.0）を比べ、一致することを確かめる。違えば `isdd-setup` を再実行する。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致していること。`scripts/isdd/dependencies.json` が正本の設計書 7-4 と一致していること（この変更で依存の規則は変えない）。

## 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-theme-and-one-vote/` を指していることを確認する（isdd-spec が書く）。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-and-one-vote/change_requirements.md .history/20261105-theme-and-one-vote/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 保存処理の変更（DS-SC-VOTER-RECORD、DS-FN-HAS-VOTED、DS-FN-CAST-VOTE-ONCE）

- `src/store/db.py`:
  - `init_db`: `CREATE TABLE IF NOT EXISTS poll_voters`（`poll_id` INTEGER NOT NULL REFERENCES polls(id)、`voter_id` TEXT NOT NULL、`voted_at` TEXT NOT NULL、PRIMARY KEY (poll_id, voter_id)）を追加する。既存の票は消さない（DS-SC-VOTER-RECORD）。
  - `has_voted(db_path, poll_id, voter_id) -> bool`（DS-FN-HAS-VOTED）: `poll_voters` に組があれば `True`。
  - `cast_vote(db_path, poll_id, option_id, voter_id) -> bool`（DS-FN-CAST-VOTE-ONCE。旧 `cast_vote` の置き換え）: 3-2 の順。選択肢が属さなければ `ValueError`。`INSERT OR IGNORE INTO poll_voters` の影響行数が 0 なら、ロールバックして `False`。記録したら `votes` に 1 行追加してコミットし、`True`。
- 単体テスト `tests/test_store.py` を更新する（旧 `cast_vote` の呼び出しを新しい引数に合わせる。追加: 同じ投票者の 2 回目は `False` で票が増えないこと、別の投票テーマは投票できること、別の投票者は投票できること、`has_voted` の結果、属さない選択肢は `ValueError` で投票者記録も残らないこと）。
- 完了条件: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -v` が全件通過する（Flask 無しでも動くこと）。

## 2. 投票者 ID の Cookie と投票画面の変更（DS-FN-READ-VOTER-COOKIE、DS-FN-SET-VOTER-COOKIE、DS-IF-VOTE-SUBMIT-ONCE、DS-IF-ALREADY-VOTED-STATE）

- `src/web/app.py`:
  - `read_voter_cookie() -> Optional[str]`（DS-FN-READ-VOTER-COOKIE）: Cookie `voter_id` を読み、32 桁の英小文字と数字なら返す。それ以外は `None`。
  - `set_voter_cookie(response, voter_id)`（DS-FN-SET-VOTER-COOKIE）: HttpOnly、SameSite=Lax、Path=/、Max-Age=31536000 で Cookie を付けて返す。
  - `submit_vote`（DS-IF-VOTE-SUBMIT-ONCE。旧 `submit_vote` の置き換え）: 4-1 と 4-2 の処理フロー。投票者 ID が無ければ `uuid.uuid4().hex` を発行する。すべての応答に `set_voter_cookie` を付ける。投票済み（`has_voted`）は 409、未選択・不正・属さないは 400、`cast_vote` が `False` は 409、記録は 303。
  - `show_poll_detail`（DS-IF-ALREADY-VOTED-STATE）: `read_voter_cookie()` があれば `has_voted` で判定し、テンプレートに `already_voted` を渡す。
- `src/web/templates/poll_detail.html`: `already_voted` のとき、ラジオボタンと「Vote」ボタンを `disabled` にし、「You have already voted」を表示する（`role="status"`）。「View results」は有効のまま。エラー文言（「Please select one option before you vote.」）は従来どおり。
- 完了条件: `PORT=8123 DATA_DIR=<空の一時ディレクトリ> bash run.sh` で起動し、詳細画面で 1 回投票した後の詳細画面に「You have already voted」が出て、ラジオボタンが無効であること（手で確かめるか、E2E の 5 で確かめる）。

## 3. 配色の変更（DS-IF-COLOR-THEME）

- `src/web/static/style.css`: CSS の変数を次の値にする。背景 `#FFFFE0`（light yellow）。部品（`.site-header`、`.site-nav`、`h1, h2`、`.button`、`.card`、`fieldset`、`legend`、`table.results th`、`.bar`、`.success` の枠と文字、`.option input` の色）`#2F4F4F`（dark slate gray）。本文の文字 `#2F4F4F`。部品の上の文字 `#FFFFE0`。白（`#FFFFFF`）と navy（`#000080`）を残さない。エラー文言の赤（`#8B0000`）は従来どおり。`.card` の背景は `#2F4F4F`、文字は `#FFFFE0`。`.button-outline` は背景 `#FFFFE0`、文字と枠 `#2F4F4F`。`.bar` の下地（`.bar-cell` の背景）は `#FFFFE0`、枠 `#2F4F4F`。
- ファイル先頭のコメントを新しい配色に合わせる（白・navy の記述を消す）。
- 完了条件: `grep -n -i -e "ffffff" -e "000080" -e "navy" -e "white" src/web/static/style.css` が何も返さない（コメントも含む）。背景と部品の色が `#FFFFE0` と `#2F4F4F` だけであること。

## 4. E2E テストの変更（DS-TS-CAST-VOTE-ONCE-PER-POLL、DS-TS-COLOR-THEME。DS-TS-CAST-VOTE-AND-VIEW-RESULT は削除）

- `e2e/test_site.py`:
  - 旧 `test_cast_vote_and_view_result` を削除する（DS-TS-CAST-VOTE-AND-VIEW-RESULT の [削除]）。
  - `test_cast_vote_once_per_poll` を追加する（DS-TS-CAST-VOTE-ONCE-PER-POLL）。`http.cookiejar` で Cookie を保持する同じブラウザ（opener）と、Cookie の無い別のブラウザ（別の opener）を使う。手順は変更設計書 8-2 のとおり。期待: 1 回目の後に「Thank you for voting.」と票数 +1、詳細画面に「You have already voted」と無効なラジオボタン、同じ Cookie での直接送信は 409 で票数が変わらない、別のブラウザの投票は票数 +1。
  - `test_color_theme` を追加する（DS-TS-COLOR-THEME）。一覧・詳細・結果・結果一覧の各画面が `style.css` を読み込み、そのスタイルシートに `#FFFFE0` と `#2F4F4F` があり、`#FFFFFF` と `#000080` が無いことを確かめる。
- テスト関数名は対応表（DS-TS の行）と一致させる。
- 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で全件通過する（FAIL 0 件）。失敗したら修正と再実行を全件通過まで続ける。

## 5. 起動確認タスク

- 詳細設計書 9 章のとおり起動する: `bash setup.sh`（既存の `.venv` があれば変更なし）→ `PORT=8123 DATA_DIR=<空の一時ディレクトリ> bash run.sh` を前景で起動し、`http://127.0.0.1:8123/` が応答すること。確かめ終えたら、そのプロセスの PID だけを止める（他のプロセスは止めない）。
- 完了条件: 起動がエラーなく完了し、一覧・詳細・結果・結果一覧が HTTP 200 で返ること。

## 6. README 記載タスク

- `README.md` の「Pages」と説明を更新する: 1 ブラウザにつき投票テーマごとに 1 回だけ投票できること（投票済みの詳細画面の表示）、Cookie（`voter_id`）を消すと再投票できること、配色（light yellow の背景、dark slate gray の部品）。
- 完了条件: README.md を読むだけで、新しい投票のルールと配色が分かること。

## 7. 対応表（docs/trace_map.md）更新タスク

- `docs/trace_map.md` を変更設計書 11 章と 7-2 に合わせる（変更中なので、正本の対応表を直接書き換える。正本の反映は実装後レビューの段階で行うため、ここでは実装のための対応表の行を、変更設計書の [追加] の DS-ID で書く）。
  - [削除] の行を消す: `DS-FN-CAST-VOTE`、`DS-IF-VOTE-SUBMIT`、`DS-TS-CAST-VOTE-AND-VIEW-RESULT`（E2E の行）。
  - [追加] の行を書く: `DS-FN-HAS-VOTED` → `src/store/db.py::has_voted`、`DS-FN-CAST-VOTE-ONCE` → `src/store/db.py::cast_vote`、`DS-FN-READ-VOTER-COOKIE` → `src/web/app.py::read_voter_cookie`、`DS-FN-SET-VOTER-COOKIE` → `src/web/app.py::set_voter_cookie`、`DS-IF-VOTE-SUBMIT-ONCE` → `src/web/app.py::submit_vote`、`DS-IF-ALREADY-VOTED-STATE` → `src/web/app.py::show_poll_detail`、`DS-TS-CAST-VOTE-ONCE-PER-POLL` → `e2e/test_site.py::PollsSiteTest.test_cast_vote_once_per_poll`、`DS-TS-COLOR-THEME` → `e2e/test_site.py::PollsSiteTest.test_color_theme`。
  - `DS-IF-COLOR-THEME`（CSS）と `DS-SC-VOTER-RECORD`（テーブル）は対応表に載せない（7 章の規則。CSS は対象外、DS-SC は修飾名で表せない）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。依存チェックが合格。受け入れ判定で、変更分の RQ-FT・RQ-UI が実装済みになること。

## 8. 実装完了確認タスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK であること。
- 確認: 変更設計書の [追加] の設計要素がすべて実装されていること、[削除] の要素（`cast_vote` の旧契約、`submit_vote` の旧契約、旧 E2E）が残っていないこと。
- 単体テスト（1）、E2E（4）、起動（5）の完了を、この段階で改めて全件確かめる。
