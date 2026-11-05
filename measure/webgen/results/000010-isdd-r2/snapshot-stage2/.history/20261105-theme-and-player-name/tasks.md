# 実装タスク: 配色の変更、名前欄の必須化、当選記録の表示項目（変更フロー）

入力: `.history/20261105-theme-and-player-name/change_requirements.md`、`.history/20261105-theme-and-player-name/change_detail_design.md`（正本: `docs/requirements.md`、`docs/detail_design.md`、`docs/trace_map.md` は変更の実装後に実装後レビューで反映する）。上から順に実行する。

## 0. 導入確認とフロー確認

0. **isdd-setup 導入確認タスク**
   - `scripts/isdd/check.sh` は存在する。`scripts/isdd/VERSION`（`v2.2.0`）と isdd-setup の `metadata.version`（`v2.2.0`）は一致する。`scripts/isdd/completeness.json` は runtime server・auth false・external false で、詳細設計書と一致する。再実行は不要。
   - 完了条件: `bash scripts/isdd/check.sh` が実行できる。

0-2. **進行中の変更の登録確認タスク**
   - `docs/active_change` の 1 行目が `.history/20261105-theme-and-player-name/` であること。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない。
   - 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-and-player-name/change_requirements.md .history/20261105-theme-and-player-name/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. データ層（`app/database.py`）

1.1 `Database.list_winnings_by_name` の問い合わせに名前を足す（設計 `DS-FN-LIST-WINNINGS-WITH-NAME`。対応表の行は実装後レビューで `DS-FN-LIST-WINNINGS-BY-NAME` から書き換える）。返す各行は `id`、`player_name`、`prize_id`、`prize_name`、`won_at`。絞り込みと並び順（当選日時、記録IDの降順）は変えない。
- 完了条件: 単体テスト `tests/test_database.py` で、名前が返ることと、大文字小文字違いの絞り込みが従来どおりであることを確かめる。

## 2. 業務ロジック（`app/service.py`）

2.1 変更なし（`SpinService.get_winnings` は `Database` の結果をそのまま返すため、名前が応答に入る）。`DS-FN-GET-OWN-WINNINGS` は既存のまま。
- 完了条件: `tests/test_service.py` が従来どおり全件通過する。

## 3. HTTP 層（`app/server.py`）

3.1 変更なし。画面・静的ファイル・API の振り分けは同じ。`/api/winnings` の応答に入る項目が増えるだけ。
- 完了条件: 3-2 の E2E（`/api/winnings` と `/static/style.css`）が通る。

## 4. 画面（`web/`）

4.1 `web/static/style.css`（`DS-IF-THEME-STYLESHEET`）: 背景 ivory（#FFFFF0）。部品（ナビゲーション、ボタン、カード、見出し、表の見出し、指針、ホイールの区画のうち CSS で塗るもの、エラーの文字）を dark green（#006400）にする。カードの文字は白。light gray（#D3D3D3）と dark red（#8B0000）を CSS から消す。
- 完了条件: `style.css` に `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` が無い（E2E で確かめる）。

4.2 `web/static/spin.js` の区画の色（`DS-IF-SPIN-SCREEN-NAME-FIELD`）: 区画は #006400 と #003300 を交互に、区画数が奇数のときの最後の区画は #004A1F。区画の文字は白。中央の円は白、縁は #006400。
- 完了条件: `node --check` が通る。

4.3 `web/index.html`（`DS-IF-SPIN-SCREEN-NAME-FIELD`）: 名前の入力欄と Spin ボタンを同じ行（同じ form の中）に置く。ラベルは「Your name (required)」。入力欄に `required` の属性を付ける（form は `novalidate` のまま、検査は画面の JavaScript で行う）。結果欄は当選記録の表示（景品名、名前、当選日時）に使う。
- 完了条件: `GET /` の HTML で、`player-name` の入力欄に `required` があり、`spin-button` と同じ `spin-form` の中にある（E2E で確かめる）。

4.4 `web/static/spin.js`（`DS-IF-SPIN-SCREEN-NAME-FIELD`）: 空、または 31 文字以上で Spin を押したら、名前欄の下に検証の文言を出し、回さず、要求もしない（従来どおり）。当選したら、結果欄に「You won 景品名!」（見出し）と、名前、景品名、当選日時（`WheelApp.formatWonAt` で地域形式）を表示する。
- 完了条件: `node --check` が通る。

4.5 `web/static/common.js`: 当選日時を表示する関数 `formatWonAt` を `WheelApp` に足し、`spin.js` と `my-winnings.js` の両方から使う（同じ書式を 2 か所に書かない）。
- 完了条件: `node --check` が通る。

4.6 `web/my-winnings.html` と `web/static/my-winnings.js`（`DS-IF-MY-WINNINGS-SCREEN-WITH-NAME`）: 表の列を Player（名前）、Prize（景品名）、Date won（当選日時）の順にする。各行に名前、景品名、当選日時を入れる。見出しの `th` は `scope="col"` を付ける。文言（件数の要約、記録が無いときの案内）は従来どおり。
- 完了条件: `GET /my-winnings` の HTML の表の見出しが Player、Prize、Date won の順である（E2E で確かめる）。

4.7 `web/prizes.html`、`web/static/prizes.js`: 変更なし（配色は `style.css` で変わる）。
- 完了条件: `/prizes` が 200 で返り、景品一覧の API が 6 件を返す（既存の E2E で確かめる）。

## 5. 起動（`app/__main__.py`）

5.1 変更なし。
- 完了条件: 9-1 の起動方法どおり `PORT=8123 bash run.sh` で起動する（実装完了時に確認）。

## 6. テスト

6.1 `tests/test_database.py`: 当選記録の取得に名前が含まれること、絞り込みと並び順が従来どおりであることを確かめる。
- 完了条件: `python3 -m unittest discover -s tests -t . -v` が全件通過する。

6.2 `e2e/test_wheel_site.py`（`WheelSiteTest`）:
- `test_theme_colors_in_stylesheet` を `test_theme_ivory_and_dark_green` に改める（`DS-TS-THEME-IVORY-GREEN`）。背景 `#FFFFF0`、部品 `#006400` があり、`#D3D3D3` と `#8B0000` が無いこと、3 画面がスタイルシートを読み込むこと。
- 追加: `test_spin_name_field_is_required_next_to_spin`（`DS-TS-SPIN-NAME-FIELD`）。`/` の HTML で名前欄に `required` があり、Spin ボタンと同じ form にあること。空の名前の `POST /api/spins` が 400 で、件数が増えないこと。
- 追加: `test_record_shows_name_prize_and_date`（`DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE`）。`POST /api/spins` の記録に名前、景品名、当選日時があること。`GET /api/winnings` の各行に `player_name`、`prize_name`、`won_at` があること。`/my-winnings` の表の見出しが Player、Prize、Date won の順であること。
- 既存のテスト（`test_spin_and_record`、`test_spin_requires_valid_name`、`test_own_winnings_filtered_and_newest_first` など）は内容を変えない。
- 完了条件: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` が全件通過する。

## 7. 対応表と文書

7.1 `docs/trace_map.md`: 次のとおり直す（変更設計書の [削除] と [追加] の ID に合わせる）。
- 削除: `DS-IF-SPIN-SCREEN`、`DS-IF-MY-WINNINGS-SCREEN`、`DS-IF-WINNINGS-API`、`DS-IF-STYLESHEET`、`DS-FN-LIST-WINNINGS-BY-NAME`、`DS-TS-THEME-COLORS`。
- 追加: `DS-IF-SPIN-SCREEN-NAME-FIELD`（`serve_page`）、`DS-IF-MY-WINNINGS-SCREEN-WITH-NAME`（`serve_page`）、`DS-IF-WINNINGS-API-WITH-NAME`（`handle_winnings`）、`DS-IF-THEME-STYLESHEET`（`serve_static`）、`DS-FN-LIST-WINNINGS-WITH-NAME`（`app/database.py::Database.list_winnings_by_name`）、`DS-TS-THEME-IVORY-GREEN`、`DS-TS-SPIN-NAME-FIELD`、`DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE`（E2E のテスト関数に結ぶ）。
- 完了条件: `bash scripts/isdd/check.sh --strict` でエラー 0 件、警告 0 件（実装後レビューで正本の対応表に合流させる）。

7.2 `README.md`: 画面の説明を直す（Spin the Wheel は名前の入力欄と Spin ボタンが同じ行にあり、名前が必須。My Winnings の表は Player、Prize、Date won）。
- 完了条件: README の「起動方法」と「画面」が現在の画面と一致する。

## 8. 最後に確認するタスク

8.1 **対応表（docs/trace_map.md）更新タスク**: 上の 7.1 を満たし、`bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること。

8.2 **起動確認タスク**: `bash setup.sh` が成功し、`PORT=8123 bash run.sh` が起動し、`/`、`/prizes`、`/my-winnings` が 200 で返ること。確認後、自分が起動したプロセスだけを PID で止める。

8.3 **単体・結合テスト全件通過タスク**: `python3 -m unittest discover -s tests -t . -v` が全件通過すること。

8.4 **E2E テスト全件通過タスク**: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` が全件通過すること。失敗したら修正と再実行を全件通過まで繰り返す。

8.5 **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK であること。
