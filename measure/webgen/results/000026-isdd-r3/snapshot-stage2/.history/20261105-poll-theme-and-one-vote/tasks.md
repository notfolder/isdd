# tasks.md: 配色の変更と 1 投票テーマ 1 ブラウザ 1 票

実装は上から順に行う。各タスクの完了条件を満たしてから次へ進む。
対象の変更: `change_requirements.md`・`change_detail_design.md`（同じディレクトリ）。正本（`docs/`）は実装後レビューまで書き換えない。

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は既に存在する（導入済み）。`scripts/isdd/dependencies.json` の依存の規則は第 7 章（変更なし）のとおり。
   - 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（サーバー）・認証（無し）・外部連携（無し）が詳細設計書と一致していること

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261105-poll-theme-and-one-vote/` であることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261105-poll-theme-and-one-vote/change_requirements.md .history/20261105-poll-theme-and-one-vote/change_detail_design.md --base docs/requirements.md` が合格すること

1. **投票済み記録の保存の実装**（`src/storage.py`）
   - 設計 ID: `DS-SC-BALLOT-TABLE`（SCHEMA に ballots を足す）、`DS-FN-FIND-BALLOT`（`find_ballot`）、`DS-FN-RECORD-VOTE-ONCE`（`record_vote_once`。投票と投票済み記録を 1 トランザクションで追加し、一意制約違反を専用の例外で知らせる）
   - 削除: `DS-FN-INSERT-VOTE`（`insert_vote`）を取り除く。`DS-SC-VOTE-TABLE` の対応先は `record_vote_once` になる
   - 完了条件: 単体テスト（`tests/unit/test_storage.py`）で、同じ投票テーマ・同じブラウザの 2 回目の記録が拒否され、票が増えないこと。別のブラウザ・別の投票テーマは記録できること。既存の DB（ballots が無い polls.db）を開いても ballots が作られ、既存の票が残ること

2. **業務処理の実装**（`src/poll_service.py`）
   - 設計 ID: `DS-CL-ALREADY-VOTED-ERROR`（`AlreadyVotedError`）、`DS-FN-SERVICE-HAS-VOTED`（`has_voted`）、`DS-FN-SERVICE-CAST-VOTE-ONCE`（`cast_vote` を投票者付きで置き換える。順序: 投票テーマの存在 → 投票済みの拒否 → 選択肢の検査 → 記録）
   - 削除: `DS-FN-SERVICE-CAST-VOTE`（旧 `cast_vote`）
   - 完了条件: 単体テスト（`tests/unit/test_poll_service.py`）で、2 回目の投票が `AlreadyVotedError` になり票が増えないこと。未選択は従来どおり `NoOptionSelectedError` で、投票済みでなければ記録されること

3. **画面の生成の実装**（`src/views.py`）
   - 設計 ID: `DS-IF-COLOR-THEME`（`STYLE` の配色を `#FFFFE0`（背景）と `#2F4F4F`（部品）にし、白と navy の背景を無くす。部品の文字は白）、`DS-FN-RENDER-VOTE-PAGE-ONE-VOTE`（`render_vote_page(poll, options, error=None, already_voted=False)`。投票済みならラジオと送信ボタンを disabled にし、「You have already voted.」と結果画面へのリンクを出す）
   - 削除: `DS-FN-RENDER-VOTE-PAGE`（旧 `render_vote_page`）
   - 完了条件: 単体テスト（`tests/unit/test_views.py`）で、配色の値が `#FFFFE0` と `#2F4F4F` であり `#000080` と白い背景（`background: #ffffff`）が無いこと。投票済みの画面に `disabled` と「You have already voted.」があり、未投票の画面には無いこと。HTML エスケープと案内メニューは従来どおり

4. **Web サーバーと経路の実装**（`src/web.py`）
   - 設計 ID: `DS-FN-READ-VOTER-COOKIE`（cookie `voter_id` を読む。32 桁の 16 進数でなければ発行する。発行したときは HTML 応答と 302 応答に `Set-Cookie`（HttpOnly、SameSite=Lax、Path=/、Max-Age 1 年）を付ける）、`DS-IF-POLL-VOTE-PAGE-ONE-VOTE`（`handle_vote_page` が投票済みの状態を渡す）、`DS-IF-VOTE-SUBMIT-ONE-VOTE`（`handle_vote_submit` が投票者付きで記録し、投票済みなら 200 で投票画面を再表示）
   - 削除: `DS-IF-POLL-VOTE-PAGE`、`DS-IF-VOTE-SUBMIT`（旧ハンドラの役割を置き換える。経路の振り分け `do_GET`・`do_POST` の分岐は変えない）
   - 完了条件: 設計の HTTP 応答の表（変更分）のとおりに応答すること。特に、投票済みの POST は 200 で票が増えず、cookie が無い GET は Set-Cookie を返すこと。手動確認は後の E2E（タスク 6）で行う

5. **単体テストの更新**（`tests/unit/`）
   - タスク 1〜3 の完了条件に書いた単体テストを、既存のテストファイルに追加・更新する。既存の `insert_vote`・`cast_vote` の呼び出しは新しい関数に合わせる
   - 完了条件: `python3 -m unittest discover -s tests/unit -p "test_*.py"` で FAIL・ERROR が 0 件

6. **E2E テストの追加と更新**（`e2e/test_polls_e2e.py`）
   - 設計 ID: `DS-TS-ONE-VOTE-PER-POLL-E2E`（テスト関数 `test_one_vote_per_poll`）、`DS-TS-THEME-COLORS-E2E`（テスト関数 `test_theme_colors`）
   - 既存の `_post` などの HTTP の補助に cookie を保持する仕組みを足す（新しいブラウザごとに cookie の入れ物を分ける）。既存の 7 本は cookie を持たない新しいブラウザとして動く
   - 完了条件: `test_one_vote_per_poll` で、同じブラウザの 2 回目の画面が無効化と「You have already voted.」を表示し、直接 POST の応答も同じで、票が増えないこと。`test_theme_colors` で 4 画面の背景 `#FFFFE0`・部品 `#2F4F4F` があり、`#000080` が無いこと

7. **対応表（docs/trace_map.md）の更新タスク**
   - 追加: `DS-SC-BALLOT-TABLE`・`DS-FN-FIND-BALLOT`・`DS-FN-RECORD-VOTE-ONCE`・`DS-CL-ALREADY-VOTED-ERROR`・`DS-FN-SERVICE-HAS-VOTED`・`DS-FN-SERVICE-CAST-VOTE-ONCE`・`DS-FN-READ-VOTER-COOKIE`・`DS-IF-POLL-VOTE-PAGE-ONE-VOTE`・`DS-IF-VOTE-SUBMIT-ONE-VOTE`・`DS-IF-COLOR-THEME`・`DS-FN-RENDER-VOTE-PAGE-ONE-VOTE`・`DS-TS-ONE-VOTE-PER-POLL-E2E`・`DS-TS-THEME-COLORS-E2E` の行を書く
   - 削除: `DS-FN-INSERT-VOTE`・`DS-FN-SERVICE-CAST-VOTE`・`DS-IF-POLL-VOTE-PAGE`・`DS-IF-VOTE-SUBMIT`・`DS-FN-RENDER-VOTE-PAGE` の行を取り除く
   - 変更: `DS-SC-VOTE-TABLE` の行の対応先を `record_vote_once` にする
   - 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること（警告は報告に含めるため、出た場合は直す）

8. **README.md の更新**
   - 「Screens」と起動方法の節に、一投票テーマ一ブラウザ一票（cookie の `voter_id`）と、配色の変更を書く。cookie を消すと別のブラウザとして扱われることを明記する
   - 完了条件: README.md の記述が実装と一致していること

9. **起動確認タスク**
   - `bash setup.sh` の後、`PORT=<空きポート> bash run.sh` で起動し、`/`、`/polls/1`、`/polls/1/results`、`/results` が 200 で開けることを確認する。確認後、起動したプロセスの PID だけを止める
   - 完了条件: 起動がエラーなく完了し、4 画面が 200 で応答すること

10. **単体テスト・E2E テスト全件通過タスク**
   - 単体テスト: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
   - E2E テスト: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
   - 完了条件: どちらも FAIL・ERROR が 0 件。失敗した場合は修正と再実行を全件通過まで繰り返す

11. **実装完了チェックタスク**
   - `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する
   - 完了条件: 全項目が OK であること

12. **変更点の実装確認タスク**
   - 変更要件定義書の [追加] の要件（`RQ-FT-ONE-VOTE-PER-POLL`・`RQ-UI-VOTED-STATE`・`RQ-DT-BROWSER-BALLOT`・`RQ-DT-BALLOT`・`RQ-NF-COLOR-THEME`・`RQ-TS-ONE-VOTE-PER-POLL`・`RQ-TS-THEME-COLORS`）と、変更設計書の [追加] の設計要素がすべて実装され、[削除] の要素が残っていないことを確かめる
   - 完了条件: `bash scripts/isdd/check.sh --strict` と `python3 scripts/isdd/acceptance_checker.py` の結果で、上記の要件が実装済みと判定されること

## 変更で直した要件 ID

無し。
