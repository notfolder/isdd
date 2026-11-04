# タスク: 配色の変更と投票済みの投票の操作無効化

対象: `.history/20261104-theme-and-vote-lock/change_requirements.md` と `change_detail_design.md`（変更フロー）。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装後に `isdd-build` の実装後レビューが反映する。

## 0. isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無を確かめる。既にあるので、導入はしない。`scripts/isdd/VERSION` が `.claude/skills/isdd-setup` の版と合うことだけ確かめる。
- 対象の設計 ID: なし
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。

## 0-2. 進行中の変更の登録確認

- 対象: `docs/active_change` の 1 行目が `.history/20261104-theme-and-vote-lock/` を指していることを確かめる（`isdd-spec` で書いた）。正本には変更を反映しない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-theme-and-vote-lock/change_requirements.md .history/20261104-theme-and-vote-lock/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 配色の変更（`RQ-NF-SLATE-THEME`、`RQ-TS-THEME`）

- 対象: `app/static/style.css`。背景を `#FFFFE0`（light yellow）、部品（ナビゲーション、ボタン、カード、見出し、結果の棒の塗り）を `#2F4F4F`（dark slate gray）にする。部品の上の文字は `#FFFFFF`、それ以外は `#111111`。`#ffffff` と `#000080` を残さない（カードの背景も `#FFFFE0`）。結果の棒の下地は `#2F4F4F` の半透明の薄い色にする。
- 対象の設計 ID: `DS-IF-POLLS-PAGE`（[追加] の内容）、`DS-TS-THEME-E2E`（[追加] の内容）
- 完了条件: `style.css` に `#FFFFE0` と `#2F4F4F` があり、`#ffffff` と `#000080` が無い。E2E の `DS-TS-THEME-E2E` が通る（task 4）。

## 2. 投票済みの投票の詳細（`RQ-FT-DISABLE-VOTE-AFTER-VOTE`、`RQ-UI-VOTED-POLL-STATE`）

- 対象: `app/views.py::poll_page`（投票済みの判定は既存の Cookie と票の確認のまま）、`app/templates/poll.html`。投票済みの場合は、選択肢のラジオボタンに `disabled`、Vote ボタンに `disabled` を付け、「You have already voted」の文を出し、結果を出す。未投票の場合は今までどおりフォームを有効にする。フォームを隠さず無効にする。
- 対象の設計 ID: `DS-IF-POLL-PAGE`（[追加] の内容）
- 完了条件: 投票済みの詳細を GET すると、`disabled` の選択肢と Vote、「You have already voted」、結果が含まれる。未投票の詳細は `disabled` を含まない。

## 3. 投票済みの利用者の再送信（`RQ-FT-REFUSE-REPEAT-VOTE`）

- 対象: `app/views.py::vote`。票を作らない結果（`cast_vote` の戻り値 `already_voted`、または一意制約で失敗した場合）は、「Thank you」の付かない投票の詳細へ 303 でリダイレクトする。初めての投票の成功は今までどおり `thanks=1` 付きで戻す。`app/voting.py` の振る舞いは変えない（`DS-FN-CAST-VOTE` の既存の対応に従う）。
- 対象の設計 ID: `DS-IF-VOTE-ACTION`（[追加] の内容）、`DS-FN-CAST-VOTE`（既存。振る舞いは変えない）
- 完了条件: 投票済みの利用者が同じ投票へ送信しても票が増えず、リダイレクト先に「Thank you」が無く「You have already voted」が出る。初めての投票の成功は「Thank you for your vote.」が出る。

## 4. テストの更新（`RQ-TS-THEME`、`RQ-TS-VOTED-POLL-STATE`、`RQ-TS-ONE-VOTE-PER-POLL`）

- 対象: `e2e/test_polls_e2e.py`。`test_theme` を新しい色の指定に直す（`#FFFFE0`、`#2F4F4F`、`#ffffff`・`#000080` が無いこと）。`test_one_vote_per_poll` の期待に「You have already voted」を加える。`test_voted_poll_state` を新設する（`DS-TS-VOTED-POLL-STATE-E2E`。投票後の詳細の `disabled`、「You have already voted」、結果、再送信で票が増えないこと、「Thank you」が出ないこと）。単体テストは変更なし（`tests/`）。
- 対象の設計 ID: `DS-TS-THEME-E2E`、`DS-TS-ONE-VOTE-E2E`、`DS-TS-VOTED-POLL-STATE-E2E`
- 完了条件: `.venv/bin/python -m pytest tests` が FAIL 0。`.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件通過。

## 5. 対応表（docs/trace_map.md）更新

- 対象: 新しいテスト関数 `e2e/test_polls_e2e.py::test_voted_poll_state` を `DS-TS-VOTED-POLL-STATE-E2E` の行で登録する（書式は対応表のルール）。既存の行は変更しない（ファイルやクラス・関数を増やしていないため）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

## 6. 起動確認

- 対象: `bash setup.sh`、`PORT=任意 bash run.sh`。投票済みの詳細・一覧・結果の画面を開き、新しい配色と「You have already voted」を確かめる。
- 完了条件: 起動がエラーなく完了し、主要な画面が開ける。確認後に自分が起動したプロセスだけを止める。

## 7. README.md 記載

- 対象: `README.md` の「Pages」の説明（投票の詳細の記述）を、投票済みの投票は操作が無効で「You have already voted」が出る内容に直す。
- 完了条件: README.md の記述が実装と一致する。

## 8. 実装完了チェック

- 対象: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

## 9. 変更点の確認（最後）

- 対象: `change_requirements.md` の [追加] の `RQ-FT`・`RQ-UI`・`RQ-NF`・`RQ-TS` と、`change_detail_design.md` の [追加] の `DS-*` が実装されたかを確かめる（`RQ-TS` → `DS-TS` → E2E の結果。`DS-*` → 対応表）。[削除] の要素（`RQ-NF-VISUAL-THEME` の `#ffffff`・`#000080`）が残っていないかを確かめる。
- 完了条件: 未実装の [追加] の設計 ID が 0 件。
