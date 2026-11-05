# tasks.md: 「景品」を「報酬」に統一（変更依頼 2）

変更要件: `change_requirements.md`。変更設計: `change_detail_design.md`。正本（`docs/requirements.md`・`docs/detail_design.md`）は実装の間は書き換えない。上から順に進める。コードに要件 ID・設計 ID は書かない。対応は `docs/trace_map.md` に登録する。

変更の要点:
- 画面に見える「prize」を「reward」に置き換える（メニュー、タイトル、見出し、表の見出し、エラーの文言、初期データの名前と説明、起動時の表示）。
- URL を `/prizes` → `/rewards`、API を `/api/prizes` → `/api/rewards` にする（旧い URL は 404。転送は作らない）。
- ID、ファイル名、クラス名、テーブル名、JSON のキー、テスト関数名は変えない。
- 抽選、利用者名の必須、当選記録、配色（ivory と dark green）は変えない。

## 0. 固定: isdd-setup 導入確認

- 対象: `scripts/isdd/check.sh` の有無、`scripts/isdd/VERSION` と isdd-build の `metadata.version` の一致。
- 完了条件: `bash scripts/isdd/check.sh` が実行できる。版が一致している。

## 0-2. 固定: 進行中の変更の登録確認

- 対象: `docs/active_change` の 1 行目が `.history/20261105-prize-to-reward-rename/` を指していること。
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があること。

## 1. サーバーの URL と API（`src/web/router.py`、`src/web/api.py`、`src/server.py`）

- 実装: `PAGE_FILES` の `/prizes` を `/rewards`（画面ファイル `prizes.html` は変えない）。API の振り分けを `/api/prizes` から `/api/rewards` にする（関数 `handle_list_prizes` の名前は変えない。説明文の URL を直す）。`server_version` を `RewardWheel/1.0` にする。起動時の表示を「Reward wheel is running at ...」にする。
- 対応（設計 ID）: `DS-IF-PAGE-ROUTES`、`DS-IF-PRIZES-SCREEN`、`DS-IF-PRIZES-API`、`DS-MD-HTTP-ROUTER`、`DS-CL-REQUEST-HANDLER`、`DS-MD-SERVER-ENTRY`、`DS-MD-API-HANDLERS`。
- 完了条件: `GET /rewards` と `GET /api/rewards` が応答し、`GET /prizes` と `GET /api/prizes` が 404 になる。

## 2. 画面の文言（`src/web/static/*.html`、`js/*.js`）

- 実装: `index.html` の `<title>` と `h1`（Reward Wheel）、メニューの項目（Spin Wheel、Reward List（`/rewards`）、My Winning Records）、`canvas` の `aria-label`（Reward wheel）。`prizes.html` を `rewards.html` に、`js/prizes.js` を `js/rewards.js` に改名する（内容は下の通り）。`rewards.html` の `<title>`、`h1`、メニュー、`h2`（Reward List）、表の見出し（Reward）、要素 ID を `reward-message`・`reward-rows` にする。`records.html` の `<title>`、`h1`、メニュー（Reward List の項目は `/rewards`）、表の見出し（Player、Reward、Won at）。`js/rewards.js` は関数を `initRewardsPage`、`renderRewardTable` にし、文言（Could not load rewards.）と API の URL（`/api/rewards`）、コメントを直す。`js/wheel.js` の文言（Could not load rewards.）、API の URL（`/api/rewards`）、コメント、ローカル変数（`prizes` → `rewards`）を直す。API の応答の JSON キー（`prize_name`、`prize_id`）は読むだけで変えない。
- 対応（設計 ID）: `DS-IF-PRIZES-SCREEN`、`DS-IF-SPIN-SCREEN-NAME-FIELD`、`DS-IF-RECORDS-SCREEN-PLAYER-COLUMN`、`DS-MD-COMMON-JS`、`DS-MD-PRIZES-JS`、`DS-MD-WHEEL-JS`、`DS-FN-RENDER-PRIZE-TABLE`。
- 完了条件: `grep -ril prize src/web/static/` の結果が、JSON のキーを読む行（`prize_name`、`prize_id`）だけになる。`grep -i prize src/web/static/*.html` が 0 件。

## 3. 初期データ（`src/store/seed.py`）

- 実装: 「Grand Prize: $50 Gift Card」を「Grand Reward: $50 Gift Card」に、「No prize this time」を「No reward this time」に変える。変数名（`SAMPLE_PRIZES`）と他の名前は変えない。
- 対応（設計 ID）: `DS-SC-SAMPLE-DATA-SET`、`DS-FN-SEED-SAMPLE-DATA`、`DS-MD-SEED-DATA`。
- 完了条件: 空の `DATA_DIR` で起動すると、報酬 7 件のうち 6 番目が「Grand Reward: $50 Gift Card」、7 番目の説明が「No reward this time」になる。

## 4. テストの更新（`tests/unit/`、`e2e/`）

- 実装: E2E（`e2e/test_wheel_e2e.py`）の URL と文言を新しいものにする（`/rewards`、`/api/rewards`、見出し「Reward List」、表の見出し「Reward」、メニューの項目）。旧い URL が 404 になることを確かめる（`DS-TS-VIEW-PRIZES-E2E`、`DS-TS-NAVIGATION-THEME-E2E`）。「prize」の語が画面の HTML に無いことを確かめる（`DS-TS-NAVIGATION-THEME-E2E`）。当選履歴の見出しを「Reward」にする（`DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E`）。単体テスト（`tests/unit/`）は内部の名前を使うので、初期データの名前が変わった分だけ直す（`test_store.py`、`test_integration.py`）。
- 完了条件: `python3 -m unittest discover -s tests/unit -p "test_*.py"` が全件通過。E2E は `python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml` で全件通過。

## 5. README と対応表

- 実装: `README.md` の見出し、メニューの説明、URL（`/rewards`）、「景品」を「報酬」に直す。`docs/trace_map.md` の説明文（景品 → 報酬）と、`DS-IF-PRIZES-API` の URL（`GET /api/rewards`）を直す。行の対応先（ファイルとクラス）は変えない。
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件（受け入れ判定を含む）。

## 6. 確認

- 実装: `bash setup.sh` の後、`PORT=18081 bash run.sh` を起動し、`/`、`/rewards`、`/records`、`/api/rewards`、`/api/records?player_name=Sample%20Player` を取得する。画面に「prize」の語が無いことを確かめる。確認後、起動した PID だけを止める。
- 完了条件: 3 画面が 200、旧い URL が 404、画面の HTML に「prize」が無い。
