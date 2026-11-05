# 実装タスク: 利用者に見える「prize」の表示語を「reward」に置き換える（変更フロー）

入力: `.history/20261105-prize-to-reward/change_requirements.md`、`.history/20261105-prize-to-reward/change_detail_design.md`。正本 `docs/requirements.md`・`docs/detail_design.md` に重ねて読む（正本は実装後のレビューで反映する）。上から順に実行する。

## 0. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-prize-to-reward/` を指していることを確認する。正本には実装中に変更を反映しない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md --base docs/requirements.md` 相当の確認（変更設計書の DS-ID が対応表に載る）が合格する。

## 1. 画面（web/）の表示語と URL（`DS-IF-REWARD-LIST-SCREEN`、`DS-IF-NAVIGATION-MENU`、`DS-IF-SPIN-SCREEN-NAME-REQUIRED`、`DS-IF-MY-WINNINGS-SCREEN-WITH-NAME`）

1.1 `web/prizes.html` を `web/rewards.html` に、`web/static/prizes.js` を `web/static/rewards.js` に名前を変え、`<script>` の参照を直す。
1.2 文言を変更要件定義書 3-8 の表どおりに替える（`Prize List` → `Reward List`、ページのタイトルと見出し、リンク先 `/rewards`、件数の文、読み込み失敗の文、`Prize wheel` → `Reward wheel`、`see which prize you win` → `see which reward you win`、My Winnings の列名 `Prize` → `Reward`、結果欄の項目名 `Prize` → `Reward`、記録が無いときの文 `a prize` → `a reward`）。3 つの HTML のナビゲーションも同じ文言にする。
1.3 `web/static/rewards.js` の表示文言と `web/static/spin.js` の結果欄の項目名を替える。`app.getJSON("/api/prizes")` の URL は変えない（公開 API は内部の約束のまま）。
1.4 `web/static/style.css` と HTML の class / id の `prize-` を `reward-` に替える（`prize-grid`、`prize-count`、`prize-error`、`prize-list`）。
- 完了条件: `grep -rni "prize" web/` の結果が `/api/prizes` と JavaScript の内部の変数名（`prizes`、`prize`、`data.prize`）だけ。`grep -rn "Prize\|prize" web/*.html` が 0 件。`node --check web/static/spin.js web/static/rewards.js web/static/my-winnings.js` が通る。

## 2. 画面の経路（`DS-IF-REWARD-LIST-SCREEN`）

2.1 `app/server.py` の画面の対応表で `/prizes` を `/rewards`（`rewards.html`）にする。旧い `/prizes` は `/rewards` への 301 転送にする（`DS-IF-REWARD-LIST-SCREEN` の内部設計）。
2.2 `app/server.py` の `serve_page` 以外（`DS-IF-PRIZES-API`、`DS-IF-SPINS-API`、`DS-IF-WINNINGS-API-WITH-NAME`）は変えない。
- 完了条件: `GET /rewards` が 200 で Reward List の HTML を返す。`GET /prizes` が 301 で `/rewards` を指す。`GET /api/prizes` が 6 件を返す（契約どおり）。

## 3. 業務の文言（`app/service.py`）

3.1 `app/service.py` の 0 件のメッセージを「No rewards are available right now.」に替える（応答 409 は変えない）。`app/database.py` のテーブル名・列名、Python の関数名は変えない。
- 完了条件: `grep -rn "No prizes\|prize list" app/` が 0 件。`python3 -m unittest discover -s tests -t . -v` が全件通過（テストの期待文言を直す。ただし動作の期待は変えない）。

## 4. 単体・結合テスト（`tests/`）

4.1 `tests/test_service.py` の 0 件のメッセージの期待文言を新しい文言にする。動作の期待（抽選、記録）は変えない。
- 完了条件: `python3 -m unittest discover -s tests -t . -v` が全件通過。

## 5. E2E テスト（`e2e/test_wheel_site.py`、`DS-TS-*`）

5.1 `DS-TS-PRIZE-LIST-SHOWS-ALL` の画面の URL を `/rewards` に替える（`/api/prizes` の確認は同じ）。
5.2 `DS-TS-NAVIGATION-ALL-PAGES`、`DS-TS-THEME-IVORY-GREEN` の URL を `/rewards` にする。リンク名は「Reward List」。
5.3 `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE` の My Winnings の列の期待を「Player、Reward、Date won」にする。
5.4 `DS-TS-START-WITH-SAMPLE-DATA` は変えない（`/api/prizes`、`/api/winnings` のまま）。
5.5 新しい文言の確認を足す: `GET /rewards` が「Reward List」を含み、`/prizes`（旧い URL）を `/rewards` へ転送する（`DS-TS-PRIZE-LIST-SHOWS-ALL` の中に足す。ID は増やさない）。
- 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で FAIL が 0 件。`e2e/results/e2e.xml` の testcase が 10 件（既存と同数）。

## 6. 対応表（`docs/trace_map.md`）の更新

6.1 `[削除]` の `DS-IF-PRIZE-LIST-SCREEN` の行を消し、`[追加]` の `DS-IF-REWARD-LIST-SCREEN` の行を足す（修飾名は `app/server.py::WheelRequestHandler.serve_page`、備考は `/rewards` の画面と旧い URL の転送）。
6.2 `DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` と `DS-IF-NAVIGATION-MENU` の備考の英語（Prize → Reward、Prize List → Reward List）を替える（ID は変えない）。
- 完了条件: `bash scripts/isdd/check.sh --strict` のエラーが 0 件（警告は報告に書く）。

## 7. README の確認

7.1 `README.md` の画面の説明（Prize List → Reward List、`/prizes` → `/rewards`、My Winnings の列の名前、「win a prize」→「win a reward」）を替える。
- 完了条件: README.md の英語の説明に「prize」が無いこと（日本語の説明の「景品」は残してよい）。

## 8. 起動確認タスク（詳細設計書 9-1）

8.1 `bash setup.sh` が成功し、`PORT=8123 bash run.sh` で起動する。`/`、`/rewards`、`/my-winnings`、`/api/prizes`、`/api/winnings?name=Sample%20Player` が返る。`/prizes` は `/rewards` へ転送される。確認後、自分が起動したプロセスだけを PID で止める。
- 完了条件: 起動と主要な画面の応答がエラー無く確かめられること。

## 9. 実装完了確認（末尾の固定タスク）

9.1 **対応表（docs/trace_map.md）更新タスク**: 上の 6 を完了している。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（警告があれば報告に書く）。
9.2 **起動確認タスク**: 8 を完了している。
9.3 **単体テスト・結合テスト全件通過タスク**: 4 を完了している。
9.4 **E2E テスト全件通過タスク**: 5 を完了している。
9.5 **README 記載タスク**: 7 を完了している。
9.6 **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行し、全項目が OK。

## 10. 実装後レビュー（isdd-build の実装後レビュー。正本への反映）

10.1 変更要件定義書 3-8 の表示語の置き換えを正本 `docs/requirements.md` に反映する（該当の英語の文言だけを替え、RQ-ID と意味は変えない）。対象は `RQ-UI-NAVIGATION-MENU`、`RQ-UI-PRIZE-LIST-SCREEN`、`RQ-UI-SPIN-SCREEN`、`RQ-UI-MY-WINNINGS-SCREEN`、`RQ-FT-WINNING-RECORD-DISPLAY`、`RQ-FT-PRIZE-SELECTION-RULE`、`RQ-FT-VIEW-OWN-WINNINGS`、`RQ-FT-VIEW-PRIZE-LIST`、第 7 章の `RQ-TS-NAVIGATION-ALL-PAGES`、`RQ-TS-PRIZE-LIST-SHOWS-ALL`、`RQ-TS-RECORD-SHOWS-NAME-PRIZE-DATE`、`RQ-TS-IVORY-DARK-GREEN-THEME`。
10.2 `docs/detail_design.md` の `DS-IF-PRIZE-LIST-SCREEN` を `DS-IF-REWARD-LIST-SCREEN` に替え（7-2 のファイル名も）、第 11 章の対応の行を変更設計書 11 のとおりに替える。8-2 の `DS-TS-*` の手順の URL と文言を替える。
10.3 反映の後、`docs/active_change` を消す。
10.4 要件・設計・対応表・コードの整合を逆引きで確かめる（`rq_integrity_checker.py docs/requirements.md`、`rq_ds_link_checker.py docs/requirements.md docs/detail_design.md`、`bash scripts/isdd/check.sh --strict`）。
- 完了条件: 3 つのチェックがすべて合格（エラー 0 件）。`docs/active_change` が無い。

## 変更の途中で直した事項

無し。
