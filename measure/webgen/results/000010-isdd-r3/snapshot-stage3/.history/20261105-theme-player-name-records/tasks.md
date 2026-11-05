# tasks.md: 配色の変更、利用者名の必須化、当選履歴への利用者名の表示（変更依頼 1）

変更要件: `change_requirements.md`。変更設計: `change_detail_design.md`。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装の間は書き換えない。上から順に進める。コードに要件 ID・設計 ID は書かない。対応は `docs/trace_map.md` に登録する。

変更の要点:
- 配色: 背景 ivory（#FFFFF0）、部品 dark green（#006400）。light gray（#D3D3D3）と dark red（#8B0000）を全画面から外す。
- 景品ルーレット画面: 利用者名の入力欄を Spin ボタンの左隣に置く。空欄・空白・21 文字以上では回さず、入力欄の下に「Please enter a name of 1 to 20 characters.」を出す（API を呼ばない）。
- 当選履歴: 各行に利用者名（Player）、景品名（Prize）、当選日時（Won at）を出す。`/api/records` の各要素に `player_name` を加える。

## 0. 固定: isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無、`scripts/isdd/VERSION` と isdd-build の `metadata.version` の一致、`scripts/isdd/completeness.json`（実行形態 server、認証なし、外部連携なし）、`scripts/isdd/dependencies.json`（第 7 章の依存の規則）。
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`completeness.json` の実行形態・認証・外部連携が詳細設計書と一致している。

## 0-2. 固定: 進行中の変更の登録確認

- 対象: `docs/active_change` の 1 行目が `.history/20261105-theme-player-name-records/` を指していること。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-player-name-records/change_requirements.md .history/20261105-theme-player-name-records/change_detail_design.md --base docs/requirements.md` が合格すること。

## 1. 配色（3 画面の見た目）

- 実装: `src/web/static/styles.css`。背景 `#FFFFF0`、部品の色 `#006400`。`.site-header`、`.site-nav a`、`.site-nav a.current`、`button`、`.panel`、`.panel h2`、`.data-table th`、`.data-table td` の枠、`.error`、`.result`、`input[type="text"]` の枠、`button:disabled` の色を変える。ルーレットの区分の文字は既存の白と dark green の対。表の地は `#FFFFFF`。`#D3D3D3` と `#8B0000` は CSS に残さない（コメントも含む）。
- 対応（設計 ID）: `DS-IF-SPIN-SCREEN-NAME-FIELD`、`DS-IF-PRIZES-SCREEN`、`DS-IF-RECORDS-SCREEN-PLAYER-COLUMN`（配色の要件 `RQ-NF-COLOR-THEME-IVORY-GREEN`）。
- 完了条件: `grep -ri "d3d3d3\|8b0000" src/` が 0 件。`styles.css` に `#FFFFF0` と `#006400` がある。

## 2. 景品ルーレット画面（利用者名欄の配置と検査、区分の色）

- 実装: `src/web/static/index.html`（利用者名の入力欄と抽選ボタン（Spin）を同じ `inline-form` の行に置き、入力欄に `required` を付け、検証の文言の欄 `error-message` を入力欄の下に置く。canvas と結果欄は残す）。`src/web/static/js/wheel.js`:
  - `startSpin` を `DS-FN-START-SPIN-WITH-NAME-CHECK` として書き換える。押されたら、入力欄の値を前後の空白を除いて検査（1〜20 文字）。違反なら `error-message` に「Please enter a name of 1 to 20 characters.」を出し、回さず、`/api/spin` を呼ばずに戻る。規則どおりなら既存の流れ（`localStorage` に保存、抽選、回転、結果）。
  - `drawWheel` を `DS-FN-DRAW-WHEEL-THEMED` として書き換える。`WHEEL_COLORS` を dark green（`#006400`）と白（`#FFFFFF`）、`WHEEL_TEXT_COLORS` を白と dark green に変え、区分の縁と中央の円（`#8B0000` を使っている箇所）を dark green にする。
  - `initSpinPage` は `DS-IF-SPIN-SCREEN-NAME-FIELD` として、この変更の中身を持つ（入力欄の初期値、景品一覧の取得）。
- 対応（設計 ID）: `DS-IF-SPIN-SCREEN-NAME-FIELD`（`src/web/static/js/wheel.js::initSpinPage`）、`DS-FN-START-SPIN-WITH-NAME-CHECK`（`wheel.js::startSpin`）、`DS-FN-DRAW-WHEEL-THEMED`（`wheel.js::drawWheel`）。
- 完了条件: 空欄、空白だけ、21 文字の名前で Spin を押すと、ルーレットは回らず、入力欄の下に規則の文言が出る（ブラウザで確かめる。ヘッドレス Chrome があれば使う）。20 文字は回る。
- 注意: 利用者名の検査は画面の補助であり、サーバーの検証（400）は残す。

## 3. 当選履歴画面（利用者名の列、API の項目）

- 実装:
  - `src/service/wheel.py`（`WheelService.list_records`）: 検証済みの利用者名（`name`）を各記録の `player_name` として付ける（DS-CL-WHEEL-SERVICE の責務は変えない）。
  - `src/web/api.py`（`handle_list_records`）: 変更なし（サービスの出力をそのまま返す）。対応表の `DS-IF-RECORDS-API-WITH-PLAYER` は `handle_list_records` に結ぶ。
  - `src/web/static/records.html`: 表の列を「Player」「Prize」「Won at」の 3 列にする（`<th scope="col">`）。
  - `src/web/static/js/records.js`: `loadRecords` を `DS-FN-LOAD-RECORDS-WITH-PLAYER` として書き換える。行に `escapeHtml` で利用者名（`record.player_name`）、景品名、当選日時を並べる。0 件は既存の「No winning records yet.」。`initRecordsPage` は `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` として、この変更の中身を持つ。
- 対応（設計 ID）: `DS-IF-RECORDS-API-WITH-PLAYER`（`src/web/api.py::handle_list_records`）、`DS-IF-RECORDS-SCREEN-PLAYER-COLUMN`（`src/web/static/js/records.js::initRecordsPage`）、`DS-FN-LOAD-RECORDS-WITH-PLAYER`（`records.js::loadRecords`）。
- 完了条件: `/api/records?player_name=Sample Player` の各要素に `player_name` が「Sample Player」で入る。`/records` の表に 3 列の見出しがあり、行に利用者名・景品名・日時が出る。
- 注意: 既存の `RecordRepository.find_by_player` と `DS-CL-RECORD-REPOSITORY` は変更しない（SQL の列は変えない）。

## 4. 単体テスト・結合テストの更新

- 実装: `tests/unit/test_integration.py` に、`list_records` の各要素の `player_name` が検証済みの利用者名と一致する確認を足す（抽選で記録した後の確認）。既存のテストが通ること。
- 実行コマンド: `python3 -m unittest discover -s tests/unit -p "test_*.py"`
- 完了条件: 全件通過（FAIL が 0 件）。

## 5. E2E テストの更新

- 実装: `e2e/test_wheel_e2e.py`:
  - `test_name_validation` を `test_spin_name_required` に改名し、サーバーの 400（空、空白、21 文字）に加えて、`/` の HTML に `id="player-name"` と `id="spin-button"` が同じ `class="inline-form"` の中にあること、`/static/js/wheel.js` に規則の検査（`length`、`20`）があることを確かめる。
  - `test_view_own_records` を `test_view_records_with_player` に改名し、`/api/records` の各要素の `player_name` が「Sample Player」であること、`/records` の HTML に「Player」「Prize」「Won at」の見出しがあることを確かめる。
  - `test_navigation` を `test_navigation_and_theme` に改名し、`styles.css` に `#fffff0` と `#006400` があり、`#d3d3d3` と `#8b0000` が無いことを確かめる。
  - 他のテスト（`test_spin_and_record`、`test_view_prizes`、`test_seed_data`）は変えない。
- 対応: 対応表の `DS-TS` の行（`DS-TS-SPIN-NAME-REQUIRED-E2E` → `test_spin_name_required`、`DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` → `test_view_records_with_player`、`DS-TS-NAVIGATION-THEME-E2E` → `test_navigation_and_theme`）。旧い `DS-TS-NAME-VALIDATION-E2E`、`DS-TS-VIEW-OWN-RECORDS-E2E`、`DS-TS-NAVIGATION-E2E` の行は対応表から消す。
- 実行コマンド: `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`
- 完了条件: 全件通過（FAIL が 0 件）。

## 6. README.md の更新

- 実装: 「画面」の説明に、利用者名欄が抽選ボタンの横にあり、空欄では回らないこと、当選履歴に利用者名・景品名・当選日時を表示することを書く。配色（背景 ivory、部品 dark green）は書かなくてよい。
- 完了条件: README.md に「起動方法」があり、変更後の画面の説明と一致する。

## 7. 対応表（docs/trace_map.md）の更新

- 実装: 変更設計書の [削除] の設計 ID の行（`DS-IF-SPIN-SCREEN`、`DS-FN-START-SPIN`、`DS-FN-DRAW-WHEEL`、`DS-IF-RECORDS-SCREEN`、`DS-FN-LOAD-RECORDS`、`DS-IF-RECORDS-API`、`DS-TS-NAME-VALIDATION-E2E`、`DS-TS-VIEW-OWN-RECORDS-E2E`、`DS-TS-NAVIGATION-E2E`）を消し、[追加] の ID の行を登録する（修飾名は上の 1〜5 の対応のとおり）。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（対応表チェック、依存チェック、受け入れ判定）。

## 8. 起動確認

- 完了条件: `bash setup.sh` が終了コード 0 で終わり、`PORT=任意の空いている番号 bash run.sh` で起動し、`/`、`/prizes`、`/records` が 200 で返り、`/api/prizes` が 7 件、`/api/records?player_name=Sample%20Player` の要素に `player_name` があることを `curl` で確かめる。ブラウザで 3 画面を開き、配色と利用者名欄の位置を確かめる（ヘッドレス Chrome が使えれば、スクリーンショットを撮って見る）。確認後、起動したプロセスだけを PID で止める。

## 9. 実装完了チェック

- 完了条件: `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目が OK。
- 完了条件（全件）: 単体・結合テスト、E2E テストが全件通過。`rq_ds_link_checker.py`（変更の組み合わせ、`--base docs/requirements.md`）が問題 0 件。

## 10. 要件の網羅確認（変更点の実装確認）

- 完了条件: `RQ-NF-COLOR-THEME-IVORY-GREEN`、`RQ-UI-SPIN-NAME-FIELD`、`RQ-UI-RECORDS-SCREEN` が、E2E テスト（`RQ-TS-NAVIGATION`、`RQ-TS-NAME-VALIDATION`、`RQ-TS-VIEW-OWN-RECORDS`）か、実装の確認（4 の単体テスト、画面の確認）で確かめられている。既存の `RQ-FT-*`、`RQ-UI-SPIN-SCREEN`、`RQ-UI-PRIZE-LIST-SCREEN`、`RQ-TS-SPIN-AND-RECORD`、`RQ-TS-VIEW-PRIZES`、`RQ-TS-SEED-DATA` は、今までどおり通ること。
