# 実装タスク: 配色の変更と投票操作の無効化（Polls Website）

前提: 変更フロー。入力は本ディレクトリの `change_requirements.md`（変更要件定義書）と `change_detail_design.md`（変更設計書）。正本の `docs/requirements.md`・`docs/detail_design.md` は実装中に書き換えない（反映は後段の実装後レビュー）。上から順に実行する。

## 0. 進行中の変更の登録確認

### 0-1. isdd-setup 導入確認

- `scripts/isdd/check.sh` と `scripts/isdd/dependencies.json` が既にある。`scripts/isdd/VERSION` が `v2.2.0` であることを確かめる。導入し直しは不要。
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。

### 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-theme-and-vote-lock/` であることを確かめる。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。反映は実装後に `isdd-build` の実装後レビューが行う。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261105-theme-and-vote-lock/change_requirements.md .history/20261105-theme-and-vote-lock/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 実装: 投票詳細の表示（DS-IF-POLL-VOTE-SCREEN、DS-IF-CAST-VOTE-ACTION）

- `src/web.py` の `poll_detail_page`: `DS-FN-HAS-VOTED` で投票済みを判定し、テンプレートへ `voted` を渡す（既存の処理の流れを変えない）。
- `src/web.py` の `cast_vote_action`: 失敗して再表示するとき、`voted` を `DS-FN-HAS-VOTED` で判定し直す。409 の場合はエラー文を出さず、投票済みの案内文を出す（`error` は `None`）。400 の場合は従来のエラー文を出し、`voted` が真なら投票済みの案内文も出す。
- `src/templates/poll_detail.html`: 投票済みのとき、`<fieldset>` に disabled を付け、選択肢のラジオボタンと Vote ボタンに disabled を付ける。案内文「You have already voted in this poll.」と結果へのリンクを出す。未投票の表示は従来どおり。各 input は `name="option_id" value="N"` の並びを保つ（E2E の抽出に使う）。
- 完了条件: 投票済みの詳細で、ラジオと Vote が disabled で、「You have already voted in this poll.」が 1 回出る。未投票の詳細は従来どおり操作できる。`DS-FN-CAST-VOTE`、`polls.py` は変えない。

## 2. 実装: 配色（DS-IF-COLOR-THEME）

- `src/static/style.css`: 背景は `#FFFFE0`、部品（ナビゲーション、見出し、カード、ボタン、表の見出し、棒グラフ、枠）は `#2F4F4F`、部品の文字は `#FFFFE0`。`#ffffff` と `#000080` を使わない（エラー文の赤 `#8b0000` は残す）。無効なボタンと選択肢は不透明度 0.5 とカーソル not-allowed。
- `src/templates/base.html`: 色は CSS で指定するため、テンプレートに色の値を書かない（ヘッダーの class 名だけ使う）。
- 完了条件: 全画面（`/polls`、`/polls/1`、`/polls/1/results`、`/results`）で背景が `#FFFFE0`、部品が `#2F4F4F`。CSS に `#ffffff` と `#000080` が無い（`grep -i` で確かめる）。

## 3. テスト更新と追加

- `tests/test_web.py`: 投票済みの詳細画面で disabled が付くこと、投票済みで未選択の POST（400）でも disabled のまま案内文が出ることを追加する。既存の 409 のテストは残す。
- `e2e/test_polls_e2e.py`:
  - `test_navigation`: CSS の配色の確認（`#000080`、`#ffffff` の検査）を外し、ナビゲーションの確認だけにする。
  - 追加 `test_verify_vote_lock`（`DS-TS-VERIFY-VOTE-LOCK-E2E`）: 投票 → 同じ投票テーマの詳細で disabled と案内文 → 別の選択肢を POST → 409、票数は変わらない。
  - 追加 `test_verify_color_theme`（`DS-TS-VERIFY-COLOR-THEME-E2E`）: 4 画面の HTML が `style.css` を読み、CSS に `#FFFFE0` と `#2F4F4F` があり、`#ffffff` と `#000080` が無い。
- 完了条件: テストファイルの docstring に DS-TS-ID を書く（既存の形式）。

## 4. 単体・結合テスト全件通過

- 実行コマンド: `.venv/bin/python -m unittest discover -s tests -v`
- 完了条件: FAIL と ERROR が 0 件。

## 5. E2E テスト全件通過（DS-TS-* の 9 件）

- 実行コマンド: `.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml`
- 完了条件: FAIL と ERROR が 0 件。`e2e/results/e2e.xml` が出ている。

## 6. 対応表（docs/trace_map.md）更新

- `DS-IF-POLL-DETAIL-SCREEN` の行を削除し、`DS-IF-POLL-VOTE-SCREEN`（`src/web.py::poll_detail_page`、投票済みの無効化を含む）の行を入れる。
- `DS-TS-VERIFY-VOTE-LOCK-E2E`（`e2e/test_polls_e2e.py::PollsEndToEndTest.test_verify_vote_lock`）と `DS-TS-VERIFY-COLOR-THEME-E2E`（`...::test_verify_color_theme`）の行を入れる。
- `DS-TS-NAVIGATION-E2E` の備考を「ナビゲーション」だけにする（配色は別の行で確かめる）。
- `DS-IF-COLOR-THEME` は CSS・テンプレートが実現する（対応表の対象外。行は入れない）。
- 完了条件: `bash scripts/isdd/check.sh --strict` でエラー 0 件、警告 0 件（警告が出るなら報告に書く）。

## 7. README.md 更新

- 「Pages」の説明に、投票済みの投票テーマでは選択肢と Vote が無効になり、「You have already voted」と出ることを一文で足す。
- 完了条件: README を読むだけで、投票済みの表示が分かる。

## 8. 起動確認

- `bash setup.sh` を実行する。`PORT=8765 bash run.sh` で起動し（前面で動くので、バックグラウンドで起動して PID を控える）、`/`（302 で `/polls`）、`/polls`、`/polls/1`、`/polls/1/results`、`/results` が 200 系で応答すること、`/static/style.css` に `#FFFFE0` と `#2F4F4F` があることを確かめる。
- 投票済みの詳細画面（同じ Cookie で投票後の `/polls/1`）で disabled と案内文が出ることを確かめる。
- 確認後、起動したプロセスを PID（`kill <PID>`）だけで止める。`pkill`、`killall` は使わない。
- 完了条件: 主要な画面が開け、起動したプロセスを止めた。

## 9. 実装完了チェックと実装後レビュー

- `python3 scripts/isdd/implementation_completeness_checker.py .` を実行する。
- 実装後レビュー（isdd-build の実装後レビュー）: 変更を `docs/requirements.md`・`docs/detail_design.md` へ反映し、`[削除]` の ID を正本から消し、`docs/active_change` を消す。反映後、正本だけで `rq_ds_link_checker.py` と `bash scripts/isdd/check.sh --strict` が合格すること。
- 完了条件: 全項目 OK。`docs/active_change` が無い。

## 10. 最終確認

- `change_detail_design.md` の [追加] の DS-ID（`DS-IF-POLL-VOTE-SCREEN`、`DS-IF-COLOR-THEME`、`DS-TS-VERIFY-VOTE-LOCK-E2E`、`DS-TS-VERIFY-COLOR-THEME-E2E`）が、実装・対応表・テストのいずれにもあることを 1 つずつ照らす。
- 完了条件: 未実装の変更の DS-ID が 0 件。
