# tasks.md: 利用者に見える「poll」を「survey」に変える

実装は上から順に行う。各タスクの完了条件を満たしてから次へ進む。
対象の変更: `change_requirements.md`・`change_detail_design.md`（同じディレクトリ）。正本（`docs/`）は実装後レビューまで書き換えない。

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/VERSION`（v2.2.0）と skill の `metadata.version`（v2.2.0）が一致することを確かめる（確認済み）。
   - 完了条件: `bash scripts/isdd/check.sh --strict` が通ること（変更の前の基準線として確認済み）

0-2. **進行中の変更の登録タスク**
   - `docs/active_change` の 1 行目に `.history/20261105-poll-to-survey/` を書く
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があること

1. **画面の文字と経路の変更**（`src/views.py`、`src/web.py`、`src/app.py`）
   - 設計 ID: `DS-FN-RENDER-LAYOUT`、`DS-IF-NAVIGATION-MENU`、`DS-FN-RENDER-POLL-LIST`、`DS-FN-RENDER-POLL-RESULTS`、`DS-FN-RENDER-ALL-RESULTS`、`DS-FN-RENDER-VOTE-PAGE-ONE-VOTE`、`DS-FN-RENDER-NOT-FOUND`（文言と経路）、`DS-FN-DISPATCH-GET-REQUEST`・`DS-FN-DISPATCH-POST-REQUEST`（経路の正規表現を `/surveys/...` に）、`DS-IF-POLL-RESULT-PAGE`・`DS-IF-POLL-VOTE-PAGE-ONE-VOTE`・`DS-IF-VOTE-SUBMIT-ONE-VOTE`（404 の文言と転送先）、`DS-FN-MAIN`（起動時の表示）
   - 完了条件: 変更設計書 4-1 の表の文言と経路のとおりに出力すること。`grep -i poll` で利用者に見える文字列（HTML とコンソール）に該当が無いこと（コードの識別子とファイル名は対象外）

2. **単体テストの更新**（`tests/unit/test_views.py`）
   - 「Polls」「No polls available.」「/polls/1/results」の期待値を新しい文言と経路に合わせる
   - 完了条件: `python3 -m unittest discover -s tests/unit -p "test_*.py"` で FAIL・ERROR が 0 件

3. **E2E テストの更新と追加**（`e2e/test_polls_e2e.py`）
   - 既存の 9 本の URL と期待文言を新しい名称に合わせる（関数名は変えない）
   - 設計 ID: `DS-TS-SURVEY-TERMINOLOGY-E2E`（テスト関数 `test_survey_terminology`）を追加する。4 画面の本文に poll・polls（大文字小文字を問わず）が無いこと、`/polls/1` が 404 になることを確かめる
   - 完了条件: 追加したテストと既存の 9 本が合格すること

4. **対応表（docs/trace_map.md）の更新**
   - 追加: `DS-TS-SURVEY-TERMINOLOGY-E2E` → `e2e/test_polls_e2e.py::PollsE2ETest.test_survey_terminology`
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること

5. **README.md の更新**
   - 題名、画面の説明（Surveys、`/surveys/<id>`）、起動時の表示を新しい名称に合わせる。DATA_DIR の `polls.db` は変えないことを書く
   - 完了条件: README の記述が実装と一致していること

6. **テストの全件通過**
   - 単体テスト: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
   - E2E テスト: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
   - 完了条件: どちらも FAIL・ERROR が 0 件

7. **起動確認タスク**
   - `bash setup.sh` の後、`PORT=<空きポート> bash run.sh` で起動し、`/`、`/surveys/1`、`/surveys/1/results`、`/results` が 200、`/polls/1` が 404 であること、本文に poll が無いことを確認する。確認後、起動したプロセスの PID だけを止める（`pkill`・`killall` は使わない）

8. **実装完了チェック**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK、`bash scripts/isdd/check.sh --strict` が通ること

## 変更で直した要件 ID

無し（要件 ID は変えない）。
