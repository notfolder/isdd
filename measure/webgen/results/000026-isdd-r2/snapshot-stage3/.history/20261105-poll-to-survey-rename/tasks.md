# 実装タスク: 「poll」から「survey」への用語変更（Survey Website）

前提: 変更フロー。入力は本ディレクトリの `change_requirements.md`（変更要件定義書）と `change_detail_design.md`（変更設計書）。正本の `docs/requirements.md`・`docs/detail_design.md` は実装中に書き換えない（反映は後段の実装後レビュー）。上から順に実行する。

## 0. 進行中の変更の登録

- `docs/active_change` の 1 行目が `.history/20261105-poll-to-survey-rename/` であることを確かめる。
- 完了条件: `rq_ds_link_checker.py` を `--base docs/requirements.md` 付きで change_requirements.md と change_detail_design.md に対して実行し、合格する。

## 1. 実装: 旧パスの転送と URL の変更（DS-IF-LEGACY-POLL-REDIRECT、DS-IF-POLL-LIST-SCREEN、DS-IF-POLL-VOTE-SCREEN、DS-IF-CAST-VOTE-ACTION、DS-IF-POLL-RESULTS-SCREEN、DS-IF-ROOT-REDIRECT）

- `src/web.py`: ルートの転送先を `/surveys` にする。`/polls` → `/surveys`、`/polls/<id>` → `/surveys/<id>`、`/polls/<id>/vote`（POST）→ `/surveys/<id>/vote`、`/polls/<id>/results` → `/surveys/<id>/results` に変える。関数名（`poll_list_page` など）は変えない。
- `src/web.py::legacy_poll_redirect`（新規）: `/polls` と `/polls/<path>` を GET で受け、`/surveys` と `/surveys/<path>` へ 302 で転送する。
- 完了条件: `GET /polls/1` が `/surveys/1` へ 302。`GET /surveys/1` が 200。

## 2. 実装: 画面の文言（DS-IF-*、RQ-UI-SURVEY-WORDING）

- `src/templates/base.html`: サイト名「Survey Website」、ナビゲーションは「Surveys」（`/surveys`）と「Results」。ブラウザのタイトルの接尾辞も「Survey Website」。
- `src/templates/poll_list.html`: 見出し「Surveys」、案内「Choose a survey to see its options and vote.」、「No surveys yet.」。
- `src/templates/poll_detail.html`: パンくず「Surveys」、「You have already voted in this survey.」、リンクは `/surveys` 系。
- `src/templates/poll_results.html`: 「Vote in this survey」。
- `src/templates/results_list.html`: 「Select a survey to see its vote counts.」、「No surveys yet.」。
- `src/polls.py::MESSAGES`: 「The selected option is not valid for this survey.」、「You have already voted in this survey.」。
- 完了条件: 4 画面（`/surveys`、`/surveys/1`、`/surveys/1/results`、`/results`）と投票後の案内で `poll`（大文字小文字を問わず）が出ない。`src/static/style.css` と配色は変えない。

## 3. テスト更新と追加

- `tests/test_web.py`: 新しいパスに読み替える。旧パスの転送（`/polls` → `/surveys`、`/polls/1/results` → `/surveys/1/results`）のテストを追加。ルートの転送先は `/surveys`。
- `tests/test_polls_unit.py`: 文言の確認が無いので変更なし（内部の名前は変えない）。
- `e2e/test_polls_e2e.py`: URL を `/surveys` 系に読み替え、「Polls」の確認は「Surveys」にする。起動待ちの URL も `/surveys`。
  - 追加 `test_verify_survey_wording`（`DS-TS-VERIFY-SURVEY-WORDING-E2E`）: 4 画面と投票後の詳細に `poll` が無く、ナビゲーションに「Surveys」と「Results」がある。
  - 追加 `test_verify_legacy_url`（`DS-TS-VERIFY-LEGACY-URL-E2E`）: `/polls` と `/polls/1/results` が、転送後に `/surveys` と `/surveys/1/results` で 200。
- 完了条件: テストの docstring に DS-TS-ID を書く（既存の形式）。

## 4. 単体・結合テスト全件通過

- 実行コマンド: `.venv/bin/python -m unittest discover -s tests -v`
- 完了条件: FAIL と ERROR が 0 件。

## 5. E2E テスト全件通過（DS-TS-* の 11 件）

- 実行コマンド: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`
- 完了条件: FAIL と ERROR が 0 件。`e2e/results/e2e.xml` が出ている。

## 6. 対応表（docs/trace_map.md）更新

- `DS-IF-LEGACY-POLL-REDIRECT`（`src/web.py::legacy_poll_redirect`）の行を入れる。
- `DS-TS-VERIFY-SURVEY-WORDING-E2E`（`...::test_verify_survey_wording`）、`DS-TS-VERIFY-LEGACY-URL-E2E`（`...::test_verify_legacy_url`）の行を入れる。
- 完了条件: `bash scripts/isdd/check.sh --strict` でエラー 0 件、警告 0 件（警告が出るなら報告に書く）。

## 7. README.md 更新

- 起動方法と画面の名前（「Surveys」「Results」）、URL（`/surveys`）を合わせる。旧パスは転送される旨を一文で書く。

## 8. 起動確認

- `bash setup.sh`、`PORT=8766 bash run.sh` をバックグラウンドで起動し PID を控える。`/`（302 で `/surveys`）、`/surveys`、`/surveys/1`、`/surveys/1/results`、`/results` が 200、`/polls` が 302 で `/surveys` へ、画面の HTML に `poll` が無いことを確かめる。
- 確認後、起動したプロセスを PID（`kill <PID>`）だけで止める。`pkill`、`killall` は使わない。
- 完了条件: 主要な画面が開け、起動したプロセスを止めた。

## 9. 実装完了チェックと実装後レビュー

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 実装後レビュー（isdd-build の実装後レビュー）: 変更を `docs/requirements.md`・`docs/detail_design.md`・`docs/trace_map.md` へ反映し、`docs/active_change` を消す。反映後、正本だけで `rq_ds_link_checker.py` と `bash scripts/isdd/check.sh --strict` が合格すること。
- 完了条件: 全項目 OK。`docs/active_change` が無い。

## 10. 最終確認

- `change_detail_design.md` の [追加] の DS-ID（`DS-IF-LEGACY-POLL-REDIRECT`、`DS-TS-VERIFY-SURVEY-WORDING-E2E`、`DS-TS-VERIFY-LEGACY-URL-E2E`）が、実装・対応表・テストのいずれにもあることを 1 つずつ照らす。
- 完了条件: 未実装の変更の DS-ID が 0 件。
