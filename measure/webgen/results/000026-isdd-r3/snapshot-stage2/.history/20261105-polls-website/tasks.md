# tasks.md: 投票サイト（Polls Website）

実装は上から順に行う。各タスクの完了条件を満たしてから次へ進む。

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。実行形態は `server`、認証は無し、外部連携は無し、対応表の粒度は `function`。
   - 第 7 章の依存の規則を `scripts/isdd/dependencies.json` に書き写す。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること。

1. **データ保存の実装**（`src/storage.py`）
   - 設計 ID: `DS-MD-STORAGE`、`DS-FN-OPEN-DATABASE`、`DS-FN-SEED-SAMPLE-DATA`、`DS-FN-LIST-POLLS-WITH-TOTALS`、`DS-FN-FIND-POLL`、`DS-FN-LIST-OPTIONS-WITH-COUNTS`、`DS-FN-FIND-OPTION`、`DS-FN-INSERT-VOTE`、`DS-SC-DATABASE-FILE`、`DS-SC-POLL-TABLE`、`DS-SC-OPTION-TABLE`、`DS-SC-VOTE-TABLE`
   - 完了条件: 単体テスト（`tests/unit/test_storage.py`）で、空の DATA_DIR に初期データが入り、2 回目の起動では増えないこと。

2. **業務処理の実装**（`src/poll_service.py`）
   - 設計 ID: `DS-MD-POLL-SERVICE`、`DS-CL-POLL-SERVICE`、`DS-CL-POLL-NOT-FOUND-ERROR`、`DS-CL-NO-OPTION-SELECTED-ERROR`、`DS-FN-SERVICE-LIST-POLLS`、`DS-FN-SERVICE-GET-POLL`、`DS-FN-SERVICE-CAST-VOTE`、`DS-FN-SERVICE-GET-POLL-RESULTS`、`DS-FN-SERVICE-GET-ALL-RESULTS`
   - 完了条件: 単体テスト（`tests/unit/test_poll_service.py`）で、投票の記録、未選択の拒否、存在しない投票テーマ、割合の計算（0 件は 0.0%、小数第 1 位）が確かめられること。

3. **画面の生成の実装**（`src/views.py`）
   - 設計 ID: `DS-MD-VIEWS`、`DS-FN-RENDER-LAYOUT`、`DS-IF-NAVIGATION-MENU`、`DS-FN-RENDER-POLL-LIST`、`DS-FN-RENDER-VOTE-PAGE`、`DS-FN-RENDER-POLL-RESULTS`、`DS-FN-RENDER-ALL-RESULTS`、`DS-FN-RENDER-NOT-FOUND`
   - 完了条件: 単体テスト（`tests/unit/test_views.py`）で、案内メニュー（Polls・Results）、英語の文言、HTML エスケープが確かめられること。

4. **Web サーバーと経路の実装**（`src/web.py`）
   - 設計 ID: `DS-MD-WEB`、`DS-CL-POLL-REQUEST-HANDLER`、`DS-FN-CREATE-SERVER`、`DS-FN-DISPATCH-GET-REQUEST`、`DS-FN-DISPATCH-POST-REQUEST`、`DS-IF-POLL-LIST-PAGE`、`DS-IF-POLL-VOTE-PAGE`、`DS-IF-VOTE-SUBMIT`、`DS-IF-POLL-RESULT-PAGE`、`DS-IF-ALL-RESULTS-PAGE`
   - 完了条件: 設計 4-1 の経路と応答（200・302・404・405）どおりに応答すること。

5. **起動の実装**（`src/app.py`、`setup.sh`、`run.sh`）
   - 設計 ID: `DS-MD-APP`、`DS-FN-MAIN`、`DS-OP-START-SCRIPTS`
   - 完了条件: `bash setup.sh` が成功し、`PORT=<任意> bash run.sh` が前面で起動し、`DATA_DIR` 未指定時は `./data` を使うこと。

6. **README.md の作成**
   - 「起動方法」（`bash setup.sh`、`PORT=<番号> bash run.sh`、`DATA_DIR` の既定値）と、画面の説明を書く。認証は無いため「初期ユーザー」は書かない。
   - 完了条件: README.md を読むだけで起動できること。

7. **単体テスト・結合テスト全件通過タスク**
   - 実行コマンド: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
   - 完了条件: FAIL が 0 件。

8. **E2E テストの実装と全件通過タスク**（`e2e/`）
   - 設計 ID: `DS-TS-BROWSE-POLLS-E2E`、`DS-TS-VOTE-FOR-OPTION-E2E`、`DS-TS-REJECT-EMPTY-VOTE-E2E`、`DS-TS-VIEW-ALL-RESULTS-E2E`、`DS-TS-OPEN-UNKNOWN-POLL-E2E`、`DS-TS-ANONYMOUS-ACCESS-E2E`、`DS-TS-SEED-SAMPLE-DATA-E2E`
   - 各 `DS-TS-*` を対応表の `DS-TS` 行で `e2e/test_polls_e2e.py::PollsE2ETest.<メソッド>` に結ぶ。
   - 実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
   - 完了条件: FAIL が 0 件。XML が `e2e/results/e2e.xml` にある。

9. **対応表（docs/trace_map.md）更新タスク**
   - 実装したファイル・クラス・公開関数を登録する（書式は trace-map-rules.md）。
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

10. **起動確認タスク**
    - 第 9 章の起動方法（`bash setup.sh` → `PORT=<番号> bash run.sh`）で起動し、`/`、`/polls/1`、`/polls/1/results`、`/results` が 200 で開けること。
    - 完了条件: 起動がエラーなく完了し、主要な画面が開けること。

11. **実装完了チェックタスク**
    - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
    - 完了条件: 全項目が OK。

12. **要件・設計の逆引き確認**
    - `python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が問題 0 件であること。
    - 完了条件: 問題 0 件。
