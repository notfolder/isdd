# 実装タスク: 画面の用語 poll を survey にする（変更）

入力: `.history/20261105-poll-to-survey/change_requirements.md`、`.history/20261105-poll-to-survey/change_detail_design.md`（正本 `docs/requirements.md`・`docs/detail_design.md` に重ねて読む。有効な設計 ID は「正本 ＋ [追加] − [削除]」）。上から順に実行する。
実行形態: サーバー（`bash run.sh`）。認証: 無し。外部連携: 無し。対応表の粒度: function。
正本（`docs/requirements.md`・`docs/detail_design.md`・`docs/trace_map.md`）は、この tasks では書き換えない（反映は実装後レビューの段階）。ただし対応表（`docs/trace_map.md`）は前回の変更と同様に、この段階で変更の行を直接書く（実装と同じ作業で更新するという CLAUDE.md の規則のため）。

---

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` が存在する（導入済み）。`scripts/isdd/VERSION`（v2.2.0）と isdd-build の `metadata.version`（v2.2.0）を比べ、一致することを確かめる。違えば `isdd-setup` を再実行する。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` と `scripts/isdd/dependencies.json` が正本の設計書と一致していること（この変更で依存の規則は変えない）。

## 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-poll-to-survey/` を指していることを確認する（isdd-spec が書く）。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-poll-to-survey/change_requirements.md .history/20261105-poll-to-survey/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 文言と URL の変更（DS-IF-NAVIGATION-MENU、DS-IF-POLL-LIST-SCREEN、DS-IF-POLL-DETAIL-SCREEN、DS-IF-VOTE-SUBMIT-ONCE、DS-IF-ALREADY-VOTED-STATE、DS-IF-POLL-RESULTS-SCREEN、DS-IF-RESULTS-OVERVIEW-SCREEN、DS-FN-HANDLE-NOT-FOUND）

- `src/web/app.py`:
  - URL の規則: `/polls/<int:poll_id>` → `/surveys/<int:poll_id>`、`/polls/<int:poll_id>/vote` → `/surveys/<int:poll_id>/vote`、`/polls/<int:poll_id>/results` → `/surveys/<int:poll_id>/results`。関数名（endpoint 名）は変えない（`show_poll_list` など）。
  - ナビゲーションの表示名: `"Polls"` → `"Surveys"`（endpoint とメニューの定義の両方）。
  - 変えるのは表示と URL だけ。ロジック、Cookie、ステータスコードは変えない。
- `src/web/templates/base.html`: `<title>` の `| Polls` → `| Surveys`、サイト名 `Polls` → `Surveys`、ホームへのリンクの `href` は `url_for` のまま。
- `src/web/templates/poll_list.html`: `{% block title %}` と見出し「Polls」→「Surveys」、説明「Choose a poll to vote, or look at the results.」→「Choose a survey to vote, or look at the results.」、「No polls yet.」→「No surveys yet.」、「option」「vote」の語はそのまま。
- `src/web/templates/poll_results.html`: 「Vote on this poll」→「Vote on this survey」、「Back to polls」→「Back to surveys」。
- `src/web/templates/results_overview.html`: 表の見出し「Poll」→「Survey」、説明「for every poll」→「for every survey」、「No polls yet.」→「No surveys yet.」。
- `src/web/templates/not_found.html`: 「Go to Polls」→「Go to Surveys」。
- `src/web/templates/poll_detail.html`: 画面の語（`poll.question` など）に poll の語は無い。URL は `url_for` のため変更不要。確認のみ。
- 完了条件: `grep -rn -i "poll" src/web/templates src/web/static` の結果が、テンプレートの変数名（`poll.`、`poll_id`、`poll_list.html` などのファイル名）と `url_for` の endpoint 名だけであること。出力された HTML に `poll` の語が無いことは E2E（3）で確かめる。

## 2. 対応表（docs/trace_map.md）の更新（DS-TS-NO-POLL-WORD-IN-UI）

- `docs/trace_map.md` に次の行を加える（[追加]）: `DS-TS-NO-POLL-WORD-IN-UI` → `e2e/test_site.py::PollsSiteTest.test_no_poll_word_in_ui`（E2E）。
- 関数の対応は変わらない（DS-IF の関数は同じ。文言と URL だけが変わる）。
- 完了条件: `bash scripts/isdd/check.sh` で対応表のエラーが 0 件（テスト関数は次の 3 で作る。作る前は警告が出てよい）。

## 3. E2E テストの変更（DS-TS-NAVIGATE-MENU、DS-TS-NO-POLL-WORD-IN-UI。既存の DS-TS の期待値を新しい語に合わせる）

- `e2e/test_site.py`:
  - 既存のテストの URL（`/polls/...`）と期待する文言（「Polls」「No polls yet.」「Vote on this poll」「Back to polls」「Poll」の表の見出し、「Go to Polls」）を、新しい URL と語に合わせる。テスト関数名（`test_browse_poll_list` など）は変えない。
  - `test_navigate_menu`（DS-TS-NAVIGATE-MENU）: メニューの「Polls」を「Surveys」に変える。
  - `test_no_poll_word_in_ui`（DS-TS-NO-POLL-WORD-IN-UI）を追加する: 一覧、詳細、結果、結果一覧、存在しない URL（`/surveys/9999`）の HTML を取得する。投票した後の結果画面（Cookie 付きの同じブラウザ）と、投票済みの詳細画面も取得する。取得した各 HTML に `re.search(r"poll", html, re.I)` が無いことを確かめる。HTML の全体（URL、タイトル、リンク、ボタン、コメントを含む）を対象にする。
  - 「Surveys」「survey」が一覧の見出しに出ることも確かめる。
- 完了条件: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で全件通過（FAIL 0 件）。失敗したら修正と再実行を全件通過まで続ける。

## 4. 単体テスト（変更なし）

- `tests/test_store.py` は保存処理の関数だけを見ており、画面の語には依存しない。変えない。
- 完了条件: `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t . -v` が全件通過する。

## 5. README 記載の更新（画面の語）

- `README.md` の「Polls」「Pages」の説明と見出し（`# Polls`）を `Surveys` の語に直す。起動方法、`DATA_DIR` の説明（`polls.db` の名前は変わらない）、投票のルール（1 ブラウザ 1 回、Cookie `voter_id`）は変えない。
- 完了条件: README.md の画面の説明が新しい語で書かれ、`polls.db` の説明が実際の保存先と一致すること。

## 6. 対応表・チェックの実行

- `bash scripts/isdd/check.sh --strict` を実行する（対応表チェック、依存チェック、受け入れ判定）。
- 完了条件: エラー 0 件・警告 0 件。依存チェックが合格。受け入れ判定で、変更分の RQ-UI-SURVEY-WORDING と RQ-TS-NO-POLL-WORD-IN-UI が実装済みになること。

## 7. 実装完了確認タスク

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK であること。
- 確認: 変更設計書の [追加] の設計要素（DS-TS-NO-POLL-WORD-IN-UI）が実装されていること。[削除] の要素（旧い URL `/polls/` と旧い文言「Polls」「Poll」）が画面の HTML と `src/` に残っていないこと。
- 単体テスト（4）、E2E（3）、起動（8）の完了を、この段階で改めて全件確かめる。

## 8. 起動確認タスク

- 詳細設計書 9 章のとおり起動する: `bash setup.sh`（既存の `.venv` があれば変更なし）→ `PORT=8123 DATA_DIR=<空の一時ディレクトリ> bash run.sh` を前景で起動し、`http://127.0.0.1:8123/` が応答すること。一覧・詳細・結果・結果一覧が HTTP 200 で返ること。確かめ終えたら、そのプロセスの PID だけを止める（他のプロセスは止めない）。
- 完了条件: 起動がエラーなく完了し、各画面が HTTP 200 で返り、HTML に `poll` の語が無いこと。
