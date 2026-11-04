# タスク: 投票の作成ページ（Create poll）

対象: `.history/20261104-create-poll/change_requirements.md` と `change_detail_design.md`（変更フロー）。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装後に `isdd-build` の実装後レビューが反映する。

## 0. isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無を確かめる。既にあるので導入はしない。`scripts/isdd/VERSION` が `.claude/skills/isdd-setup` の版と合うことだけ確かめる。
- 対象の設計 ID: なし
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。

## 0-2. 進行中の変更の登録確認

- 対象: `docs/active_change` の 1 行目が `.history/20261104-create-poll/` を指していることを確かめる（`isdd-spec` で書いた）。正本には変更を反映しない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-create-poll/change_requirements.md .history/20261104-create-poll/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 投票の作成（業務ロジック）

- 対象: `app/voting.py`。例外 `InvalidPoll`（メッセージを持つ）を足し、`VotingService.create_poll(question, options, created_at)` を足す。前後の空白を除き、空の選択肢を除いてから判定する。判定の順は、質問が空、質問が 200 文字超、選択肢が 2 件未満、選択肢が 100 文字超、選択肢の重複。不備があれば `InvalidPoll` を送出し、何も書かない。不備が無ければ、`BEGIN IMMEDIATE` の 1 トランザクションで投票（説明は空文字）と選択肢（並び順は 1 から）を書き、投票の番号を返す。エラーメッセージは設計書 4-1 のとおり英語の文言を使う。
- 対象の設計 ID: `DS-FN-CREATE-POLL`（[追加]）、`DS-CL-VOTING-SERVICE`（既存のクラスにメソッドを足す）
- 完了条件: `tests/test_voting.py` に作成の正常系（投票と選択肢が保存され、番号が返る）と不備の各判定（投票が増えない）を書いて、`.venv/bin/python -m pytest tests` が FAIL 0。

## 2. 作成画面と経路

- 対象: `app/views.py` に `show_create_poll`（GET `/polls/new`、空のフォーム）と `submit_create_poll`（POST `/polls/new`）を足す。成功時は投票の詳細へ 303 で `created=1` を付けてリダイレクトする。不備があれば作成画面を 400 で再表示し、入力値を残し、理由を 1 つ出す。`app/templates/new_poll.html` を新しく作る（見出し「Create a poll」、Question、Option 1〜4、Create poll ボタン、英語の文言）。`app/templates/poll.html` に `created=1` のとき「Your poll has been created.」を出す行を足す。`app/static/style.css` の入力欄の見た目は指定の配色（light yellow の背景、dark slate gray の部品、部品の上の文字は白）に合わせる。
- 対象の設計 ID: `DS-IF-CREATE-POLL-PAGE`（[追加]）、`DS-IF-CREATE-POLL-ACTION`（[追加]）、`DS-IF-POLL-PAGE`（[追加]: 作成直後の表示）
- 完了条件: GET `/polls/new` が 200、正しい入力の POST が 303 で `/polls/<番号>?created=1` へ、不備の入力の POST が 400 で「Please enter at least two options.」等のエラーと入力値を返す（テストクライアントで確かめる）。

## 3. ナビゲーション

- 対象: `app/templates/base.html` のナビゲーションを `Polls`、`Create poll`、`Results` の 3 項目（この順）にする。現在の画面の項目を強調する（作成画面では `Create poll`）。
- 対象の設計 ID: `DS-IF-POLLS-PAGE`（[追加]: 共通部品のナビゲーション）、`DS-MD-VIEWS`（[追加]）
- 完了条件: 全画面（一覧、詳細、作成、結果）に 3 項目があり、作成画面で `Create poll` が強調される。

## 4. E2E テストの更新

- 対象: `e2e/test_polls_e2e.py` に `test_create_poll`（作成、完了の文、投票、結果の表示まで）と `test_reject_invalid_poll`（選択肢 1 件の入力で作られず、一覧の件数が変わらない）を足す。`test_navigation` を 3 項目（Polls、Create poll、Results）を確かめるように直す。既存のテストの期待は変えない。
- 対象の設計 ID: `DS-TS-CREATE-POLL-E2E`（[追加]）、`DS-TS-REJECT-INVALID-POLL-E2E`（[追加]）、`DS-TS-NAVIGATION-E2E`（[削除] と [追加]）
- 完了条件: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件通過。

## 5. README.md 記載

- 対象: `README.md` の「Pages」に、投票の作成（`/polls/new`、ナビゲーションの「Create poll」）の説明を足し、Polls の説明に作成された投票が一覧に出ることを書く。
- 完了条件: README.md の記述が実装と一致する。

## 6. 既存機能の回帰確認

- 対象: 既存の単体テストと E2E（一覧、詳細、投票、1 投票 1 票、結果、配色、投票済みの表示、サンプルデータ）が変わらず通ること。作成は初期データに影響しない（`DATA_DIR` が空のときのサンプルは従来どおり）。
- 完了条件: `.venv/bin/python -m pytest tests` と E2E の両方が FAIL 0。

## 7. 起動確認

- 対象: `bash setup.sh`、`PORT=任意 bash run.sh` で起動し、一覧、作成画面、作成した投票の詳細、結果を開く。確認後に自分が起動したプロセスだけを止める。
- 完了条件: 起動がエラーなく完了し、主要な画面が開ける。

## 末尾の固定タスク

### 8. 対応表（docs/trace_map.md）更新

- 対象: 実装したファイル・関数・クラスを `docs/trace_map.md` に登録する。追加する行は次のとおり。`DS-FN-CREATE-POLL` → `app/voting.py::VotingService.create_poll`、`DS-FN-CREATE-POLL` → `app/voting.py::InvalidPoll`（例外）、`DS-IF-CREATE-POLL-PAGE` → `app/views.py::show_create_poll`、`DS-IF-CREATE-POLL-ACTION` → `app/views.py::submit_create_poll`、`DS-TS-CREATE-POLL-E2E` → `e2e/test_polls_e2e.py::test_create_poll`、`DS-TS-REJECT-INVALID-POLL-E2E` → `e2e/test_polls_e2e.py::test_reject_invalid_poll`。既存の行は変更しない。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件。

### 9. 起動確認タスク

- 7 と同じ。実行形態は CLI・サーバー（`bash run.sh`）。
- 完了条件: 起動がエラーなく完了すること。

### 10. 単体テスト・E2E テスト全件通過

- `.venv/bin/python -m pytest tests` と `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` を実行する。
- 完了条件: テスト結果に FAIL が 0 件。

### 11. README.md 記載

- 5 と同じ。

### 12. 実装完了チェック

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 完了条件: 全項目が OK。

### 13. 変更点の確認（最後）

- `change_requirements.md` の [追加] の `RQ-FT`・`RQ-UI`・`RQ-NF`・`RQ-TS` と、`change_detail_design.md` の [追加] の `DS-*` が実装されたかを確かめる（`RQ-TS` → `DS-TS` → E2E の結果。`DS-*` → 対応表）。[削除] の要素（`RQ-UI-NAV-MENU`、`RQ-TS-NAVIGATION`（旧））が残っていないかを確かめる（ナビゲーションが 2 項目のままになっていないこと）。
- 完了条件: 未実装の [追加] の設計 ID が 0 件。

## 要件の変更の記録

- 要件の直しは無し。設計の段階で、画面の選択肢の入力欄の数（4 つ）を要件 `RQ-FT-CREATE-POLL` に書いた（依頼に件数の指定が無く、ANSWERS.md の「最も単純に決める」に従う）。
