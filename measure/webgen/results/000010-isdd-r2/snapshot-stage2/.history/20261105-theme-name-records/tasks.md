# 実装タスク: 配色の変更、回すときの名前の必須化、当選記録への名前の表示（変更フロー）

入力: `.history/20261105-theme-name-records/change_requirements.md`、`.history/20261105-theme-name-records/change_detail_design.md`。正本 `docs/requirements.md`・`docs/detail_design.md` に重ねて読む（正本は実装後のレビューで反映する）。上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` は導入済み（stage 1 で導入）。`scripts/isdd/dependencies.json` が詳細設計書 7-4 の依存の規則と一致することを確かめる。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が正本の詳細設計書と一致する。

## 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261105-theme-name-records/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には実装中に変更を反映しない。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-name-records/change_requirements.md .history/20261105-theme-name-records/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 配色（`DS-IF-IVORY-GREEN-STYLESHEET`）

1.1 `web/static/style.css` の配色を置き換える。背景 `#FFFFF0`（ivory）、部品は `#006400`（dark green）。文字は背景の上で `#1A1A1A`、部品の上で白。エラー文字は太字の `#1A1A1A` と `#006400` の枠線（dark red を使わない）。
1.2 `web/static/spin.js` の描画色を置き換える。区画は `#006400` と `#004D00` の交互、奇数件の最後の区画は `#1F5F1F`、中心の円の縁と空の円は `#006400`。
- 完了条件: `grep -rn "D3D3D3\|8B0000\|8b0000\|d3d3d3\|A52A2A" web/` が 0 件。`grep -n "FFFFF0\|006400" web/static/style.css` がヒットする。

## 2. 回す画面の名前の必須入力欄（`DS-IF-SPIN-SCREEN-NAME-REQUIRED`）

2.1 `web/index.html` の名前の入力欄を Spin ボタンと同じ行（同じフォーム）に置く。ラベルを「Your name (required)」にし、入力欄に `required` と `aria-required="true"` を付ける。エラー欄は入力欄の下に置く。
2.2 `web/static/spin.js` の検査（空、30 文字超）と文言は既存のまま。結果欄に名前、景品名と説明、当選日時（`WheelApp.formatWonAt`）を表示する。
- 完了条件: `node --check web/static/spin.js` が通る。`GET /` の HTML に `required` と `aria-required="true"` があり、ラベルが「Your name (required)」。

## 3. 共通の処理（`web/static/common.js`）

3.1 当選日時の書式 `formatWonAt` を `WheelApp` に追加する（既存の書式: en-US、dateStyle medium、timeStyle short、解釈できなければ元の文字列）。`web/static/my-winnings.js` の同じ関数を、この共通の関数の呼び出しに替える。
- 完了条件: `node --check web/static/common.js` と `node --check web/static/my-winnings.js` が通る。

## 4. データ層（`DS-FN-LIST-WINNINGS-WITH-PLAYER-NAME`）

4.1 `app/database.py` の `list_winnings_by_name` の SELECT に `player_name` を足す（絞り込み、並び順は変えない）。
4.2 `tests/test_database.py` に、行に `player_name` が入り、大文字小文字の違う名前で絞り込んでも保存された名前が返ることを確かめるテストを足す。
- 完了条件: `python3 -m unittest discover -s tests -t . -v` が全件通過。

## 5. My Winnings 画面（`DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER`）

5.1 `web/my-winnings.html` の表の見出しを「Player」「Won at」「Prize」の順にする。
5.2 `web/static/my-winnings.js` の表の行に、名前、当選日時（`WheelApp.formatWonAt`）、景品名を出す。
- 完了条件: `GET /my-winnings` の HTML に `Player`、`Won at`、`Prize` の見出しが、この順に現れる。

## 6. HTTP 層（`DS-IF-WINNINGS-API-WITH-PLAYER`）

6.1 `app/server.py` の `handle_winnings` は業務ロジックの結果をそのまま返す。変更が要らないことを確かめる。変更が要る場合は、`app/` の設計 ID の行（`docs/trace_map.md`）を更新する。
- 完了条件: `GET /api/winnings?name=Sample%20Player` の各行に `player_name`、`prize_name`、`won_at` がある。

## 7. E2E テスト（`DS-TS-*`）

7.1 `e2e/test_wheel_site.py` の配色の検査（`DS-TS-THEME-COLORS` のメソッド）を、新しい配色の検査（`DS-TS-THEME-IVORY-DARK-GREEN`）に置き換える。旧配色の検査は削除する。
7.2 `DS-TS-SPIN-NAME-FIELD-REQUIRED` のメソッドを追加する（`/` の HTML の入力欄の属性とラベル、空の名前での `POST /api/spins` の 400 と記録の件数）。
7.3 `DS-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` のメソッドを追加する（1 件抽選し、`/api/winnings` の各行に `player_name`、`prize_name`、`won_at`、`/my-winnings` の見出しの順）。
7.4 `DS-TS-OWN-WINNINGS-FILTER` は既存のまま通ることを確かめる。
- 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で FAIL が 0 件。

## 8. 対応表（`docs/trace_map.md`）の更新

8.1 `[削除]` の設計 ID（`DS-IF-SPIN-SCREEN`、`DS-IF-MY-WINNINGS-SCREEN`、`DS-IF-STYLESHEET`、`DS-IF-WINNINGS-API`、`DS-FN-LIST-WINNINGS-BY-NAME`、`DS-TS-THEME-COLORS`）の行を消し、`[追加]` の設計 ID の行を足す（`DS-IF-SPIN-SCREEN-NAME-REQUIRED`、`DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER`、`DS-IF-IVORY-GREEN-STYLESHEET`、`DS-IF-WINNINGS-API-WITH-PLAYER`、`DS-FN-LIST-WINNINGS-WITH-PLAYER-NAME`、`DS-TS-THEME-IVORY-DARK-GREEN`、`DS-TS-SPIN-NAME-FIELD-REQUIRED`、`DS-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE`）。`app/database.py` の関数の行（`list_winnings_by_name`）は新しい設計 ID に結ぶ。
- 完了条件: `bash scripts/isdd/check.sh --strict` のエラーが 0 件（警告は報告に書く）。

## 9. 起動確認タスク（詳細設計書 9-1）

- `bash setup.sh` が成功し、`PORT=8123 bash run.sh` で起動する。`/`、`/prizes`、`/my-winnings`、`/api/prizes`、`/api/winnings?name=Sample%20Player` が返る。確認後、自分が起動したプロセスだけを PID で止める。
- 完了条件: 起動と主要な画面の応答がエラー無く確かめられること。

## 10. README の確認

- README.md の画面の説明と起動方法が変更後も正しいことを確かめる。配色の説明は無いため、変更は要らない見込み。変更が必要なら直す。
- 完了条件: README.md を読むだけで、変更後の画面（名前の必須入力、My Winnings の名前の列）と起動が分かること。

## 11. 実装完了確認（末尾の固定タスク）

11.1 **対応表（docs/trace_map.md）更新タスク**: 上の 8 を完了している。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（警告があれば報告に書く）。
11.2 **起動確認タスク**: 9 を完了している。
11.3 **単体テスト・結合テスト全件通過タスク**: `python3 -m unittest discover -s tests -t . -v` が全件通過。
11.4 **E2E テスト全件通過タスク**: 7 の E2E が全件通過（FAIL 0 件）。
11.5 **README 記載タスク**: 10 を完了している。
11.6 **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` を実行し、全項目が OK。

## 12. 実装後レビュー（isdd-build の実装後レビュー。正本への反映）

12.1 変更要件定義書・変更設計書を正本へ反映する。`docs/requirements.md` の `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` と `RQ-TS-THEME-COLORS` を削除し、[追加] の要件を入れる。`docs/detail_design.md` の [削除] の設計 ID を削除し、[追加] の設計 ID を入れる（章立てと「要件と設計の対応表」を揃える）。
12.2 変更の反映後、`docs/active_change` を消す。
12.3 要件・設計・対応表・コードの整合を逆引きで確かめる（`rq_integrity_checker.py docs/requirements.md`、`rq_ds_link_checker.py docs/requirements.md docs/detail_design.md`、`bash scripts/isdd/check.sh --strict`）。
- 完了条件: 3 つのチェックがすべて合格（エラー 0 件）。`docs/active_change` が無い。

## 変更の途中で直した事項

無し。
