# 実装タスク: 配色の変更、名前必須のスピン欄、当選記録への名前の表示（変更 1）

- 入力: `change_requirements.md`、`change_detail_design.md`（変更フロー）。正本 `docs/requirements.md`・`docs/detail_design.md` は実装中は書き換えない
- 登録: `docs/active_change` に `.history/20261105-theme-and-player-name/` を書いてある
- 実行環境: Node.js 24（外部パッケージ無し）。画面は英語

## 0. isdd-setup 導入確認タスク（先頭）

- 内容: `scripts/isdd/check.sh` と `scripts/isdd/VERSION` を確かめる。VERSION（v2.2.0）がスキルの版（v2.2.0）と一致していれば再導入は不要
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致している

## 0-2. 進行中の変更の登録確認タスク

- 内容: `docs/active_change` の 1 行目が `.history/20261105-theme-and-player-name/` であることを確かめる。正本には変更を反映しない
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-and-player-name/change_requirements.md .history/20261105-theme-and-player-name/change_detail_design.md --base docs/requirements.md` が合格すること

## 1. 配色（DS-IF-THEME-STYLESHEET）

- 設計 ID: DS-IF-THEME-STYLESHEET（旧 DS-IF-STYLESHEET は使わない）
- 内容:
  - `public/style.css`: 変数を背景 `--bg: #fffff0`（ivory）、部品 `--green: #006400`（dark green）、濃い色 `--green-dark: #004d1a`、ホバー `--green-hover: #00800f` に変える。`#e6e6e6`・`#8b0000`・`#5e0000`・`#a31515`・`#fbe3e3`・`#faf4f4` などの赤系と灰色の背景を全部無くす
  - 上部メニュー、ボタン、見出し、パネルの枠、結果カードの背景（dark green、文字は白）、表の見出し、フッター、ホイールの枠、ポインタを dark green にする
  - エラー欄（`.message.error`）は白地に dark green の枠と濃い文字（赤は使わない）
  - 表の偶数行は薄い緑 `#eef5ea`
  - 入力欄の枠は dark green
- 完了条件: `PORT=8123 bash run.sh` で `GET /style.css` が `#fffff0` と `#006400` を含み、`#e6e6e6`・`#8b0000` を含まない。Chrome（ヘッドレス）で 3 画面のスクリーンショットを撮り、背景が ivory、部品が dark green に見えること

## 2. スピン画面（DS-IF-SPIN-SCREEN-NAME-REQUIRED）

- 設計 ID: DS-IF-SPIN-SCREEN-NAME-REQUIRED（旧 DS-IF-SPIN-SCREEN は使わない）
- 内容:
  - `public/index.html`: 名前欄のラベルを「Your name (required)」にし、input に `required` と `aria-required="true"` を付ける。Spin ボタンと同じ form の中に置く。結果欄（`#spin-result`）に「You won」、景品名、「Recorded for 名前 at 日時」を出す
  - `public/app.js`: Spin の送信時に、前後の空白を除いた名前が 1〜30 文字でなければ、サーバーへ送らず `#spin-error` に「Please enter your name (1-30 characters).」を出し、名前欄にフォーカスする。ホイールは回さない。1〜30 文字なら従来どおり POST /api/spin を送る
  - 同じ `app.js`: ホイールの扇形の色を dark green の 2 色（`#006400`、`#1e7b34`）にし、景品数が奇数のときは最後の扇形だけ `#004d1a`
  - form には `novalidate` を付け、ブラウザ標準の吹き出しでなく画面のメッセージを出す
- 完了条件: `GET /` の HTML で `#spin-name` に `required` があり、Spin ボタンと同じ form にある。Chrome（ヘッドレス）で名前を空のまま Spin を押した後の画面（メッセージ、ホイールが回らない）を確かめる。手順が難しい場合は、確かめた手順と結果を報告に書く

## 3a. 当選記録の API（DS-IF-API-WINNINGS-DETAILS）

- 設計 ID: DS-IF-API-WINNINGS-DETAILS（旧 DS-IF-API-WINNINGS は使わない）。対応表の `src/routes.js::handleWinnings`
- 内容: `src/routes.js::handleWinnings` の応答の各記録に `playerName` を入れる（値は検証済みの名前。完全一致で絞るため記録の名前と同じ）。`db.js::listWinningsByName` は変えない
- 完了条件: `PORT=8123 bash run.sh` で POST /api/spin `{"name":"Alice"}` の後、GET /api/winnings?name=Alice の各記録に `playerName: "Alice"`、`prizeName`、`wonAt` がある。確認後、起動したプロセスを PID で止める

## 3b. 当選記録の画面（DS-IF-MY-WINNINGS-SCREEN-DETAILS）

- 設計 ID: DS-IF-MY-WINNINGS-SCREEN-DETAILS（旧 DS-IF-MY-WINNINGS-SCREEN は使わない）
- 内容: `public/index.html` の My Winnings の表の見出しを「Player」「Prize」「Won at」の 3 列にする。`public/app.js` で各行に名前・景品名・日時を入れる（textContent）。件数の文は変えない
- 完了条件: `GET /` の HTML の My Winnings 表の見出しに Player、Prize、Won at がある。Chrome で `Sample Player` を検索し、3 列すべてに値が出ること

## 4. テスト: e2e/

- 設計 ID: DS-TS-NAVIGATE-SCREENS-E2E（内容を変える）、DS-TS-SPIN-NAME-REQUIRED-E2E、DS-TS-WINNING-DETAILS-E2E、DS-TS-THEME-COLORS-E2E（新規）
- 内容:
  - `e2e/navigate-screens.test.js`: 配色の確認（#e6e6e6・#8b0000）を外す。メニューのリンク 3 件、`lang="en"`、英語の見出しは残す
  - `e2e/theme-colors.test.js`（新規）: `/style.css` が `#fffff0` と `#006400` を含み、`#e6e6e6`・`#8b0000` を含まない
  - `e2e/spin-name-required.test.js`（新規）: `GET /` の HTML で `#spin-name` に `required` があり、Spin ボタンと同じ form にある。POST /api/spin に空の名前と 31 文字の名前を送ると 400、同じ文言、記録の件数が変わらない
  - `e2e/winning-details.test.js`（新規）: Alice で回した後、GET /api/winnings?name=Alice の各記録に playerName・prizeName・wonAt があり、playerName が Alice。`GET /` の My Winnings の表の見出しに Player、Prize、Won at がある
  - 既存の E2E は内容を変えない（`view-own-winnings` は応答に名前が増えるだけで件数と順序の確認は同じ）
- 完了条件: `node --test 'tests/unit/*.test.js'` と `node --test 'e2e/*.test.js'` が全件通過する（3a・3b・1・2 の後に実施）

## 5. 対応表: docs/trace_map.md

- 設計 ID: DS-IF-API-WINNINGS-DETAILS（旧 DS-IF-API-WINNINGS の行を置き換える）、DS-TS-SPIN-NAME-REQUIRED-E2E、DS-TS-WINNING-DETAILS-E2E、DS-TS-THEME-COLORS-E2E
- 内容:
  - `DS-IF-API-WINNINGS` の行を `DS-IF-API-WINNINGS-DETAILS` に書き換える（修飾名 `src/routes.js::handleWinnings`）
  - E2E の行を 3 つ足す（`e2e/spin-name-required.test.js`、`e2e/winning-details.test.js`、`e2e/theme-colors.test.js`）
- 完了条件: `bash scripts/isdd/check.sh` のエラーが 0 件

## 6. README.md

- 内容: 「画面」の説明を更新する（名前は必須で、欄の隣の Spin を押す。空の名前では回らずメッセージが出る。My Winnings の表は Player・Prize・Won at の 3 列）。配色の説明が必要なら 1 行。テストの節は変えない
- 完了条件: README.md だけで、変更後の画面と操作が分かる

## 7. 実装完了の確認（末尾）

1. 対応表の更新（タスク 5）。`bash scripts/isdd/check.sh --strict` がエラー 0・警告 0（E2E を `e2e/results/e2e.xml` に出してから実行）
2. 起動確認: `PORT=任意 bash run.sh` で 3 画面が開ける（HTML と CSS と JSON の取得、Chrome の確認）。確認後、起動したプロセスを PID で止める
3. 単体テストと E2E テストの全件通過（タスク 4 の完了条件）
4. `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目 OK
5. `python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py .history/20261105-theme-and-player-name/change_requirements.md .history/20261105-theme-and-player-name/change_detail_design.md --base docs/requirements.md` が問題 0 件
6. 変更の要件（RQ-FT-SHOW-WINNING-DETAILS、RQ-UI-SPIN-NAME-FIELD、RQ-NF-THEME-IVORY-GREEN）が E2E または手動確認で確かめられている

## 補足: 途中で設計に無い要素が要った場合

コーディングを止め、`docs/proposals.md` に提案を書く。設計 ID は採番しない。
