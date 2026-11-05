# 実装タスク: Wheel of Fortune

- 入力: docs/requirements.md、docs/detail_design.md（新規フロー。docs/active_change は無い）
- 実行環境: Node.js 24（外部パッケージ無し）

## 0. isdd-setup 導入確認タスク（先頭）

- 内容: `scripts/isdd/check.sh` が無ければ `isdd-setup` を実行する。`--src src --runtime server --no-auth --no-external --granularity function` で導入し、依存の規則（無し）を `scripts/isdd/dependencies.json` に書く
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態（server）・認証（無し）・外部連携（無し）が詳細設計書と一致している
- 注: `isdd-setup` は `src/` を走査するので、src/ にコードを置いてから実行してよい（実装タスク 6 の後）

## 1. 土台: package.json、setup.sh、run.sh

- 設計 ID: DS-OP-SETUP-SCRIPT、DS-OP-START-SCRIPT
- 内容:
  - `package.json`: `"type": "module"`、`"engines": {"node": ">=24"}`、外部依存は無し。scripts は無し
  - `setup.sh`: Node.js が 24 以上であることと、`node:sqlite` を読めることを確かめる。失敗時は終了コード 1
  - `run.sh`: `PORT`（既定 8000）と `DATA_DIR`（既定 `./data`）を環境変数から読み、`DATA_DIR` を作り、`exec node src/server.js`
- 完了条件: `bash setup.sh` が成功する。`PORT=8123 bash run.sh` で `http://127.0.0.1:8123/` が応答する（確認後に起動したプロセスを PID で止める）

## 2. データ層: src/db.js

- 設計 ID: DS-MD-DB、DS-FN-OPEN-DATABASE、DS-FN-SEED-INITIAL-DATA、DS-FN-LIST-PRIZES、DS-FN-INSERT-WINNING-RECORD、DS-FN-LIST-WINNINGS-BY-NAME、DS-SC-DATABASE-FILE、DS-SC-PRIZE、DS-SC-WINNING-RECORD
- 内容:
  - `openDatabase(dataDir)`: DATA_DIR を作り、`wheel.sqlite` を開き、prize と winning_record を作る（無ければ）。設計書 3-1 の制約と索引（player_name, won_at）を付ける
  - `seedInitialData(db)`: prize が 0 件なら設計書 4-2 の景品 8 件を入れる。winning_record が 0 件なら `Sample Player` の記録 3 件を入れる（景品は既存の景品から選び、prize_name を入れる）
  - `listPrizes(db)`: 表示順（sort_order）で景品を返す
  - `insertWinningRecord(db, {playerName, prize, wonAt})`: 1 件追加し、採番された記録を返す
  - `listWinningsByName(db, name, limit)`: 名前が完全一致する記録を won_at の新しい順に最大 limit 件返す。SQL はプレースホルダで渡す
- 完了条件: 単体テスト（タスク 6）で確かめる。空の DATA_DIR で `openDatabase` と `seedInitialData` が景品 8 件と記録 3 件を作る

## 3. 抽選: src/spin.js

- 設計 ID: DS-MD-SPIN、DS-FN-VALIDATE-PLAYER-NAME、DS-FN-PICK-WEIGHTED-PRIZE、DS-FN-PERFORM-SPIN
- 内容:
  - `validatePlayerName(raw)`: 文字列でなければ、前後の空白を除いて 1〜30 文字か判定する。結果（名前、またはエラー文言）を返す
  - `pickWeightedPrize(prizes, randomInt)`: 重みの合計 T を求め、randomInt(T)（0 以上 T 未満）から累積の重みで景品を 1 件選ぶ。randomInt は注入できる（既定は `crypto.randomInt`）
  - `performSpin(db, rawName, randomInt)`: 名前を検証 → 景品を取得 → 0 件なら「No prizes are available.」（409 扱い） → 抽選 → 記録。結果の種類（成功・名前の違反・景品無し）を返す
- 完了条件: 単体テスト（タスク 6）で確かめる（乱数を注入して境界値を確かめる）

## 4. HTTP: src/routes.js、src/server.js

- 設計 ID: DS-MD-ROUTES、DS-FN-ROUTE-REQUEST、DS-FN-SERVE-STATIC-FILE、DS-IF-API-SPIN、DS-IF-API-PRIZES、DS-IF-API-WINNINGS、DS-MD-SERVER、DS-FN-START-SERVER
- 内容:
  - `startServer({port, dataDir})`: DB を開き、初期データを入れ、127.0.0.1 で待ち受ける HTTP サーバーを返す。ポートが使用中なら標準エラーに出して終了コード 1
  - `handleRequest(req, res, context)`: `/api/spin`（POST）、`/api/prizes`（GET）、`/api/winnings`（GET）を振り分け、それ以外は静的ファイルへ
  - `serveStaticFile(res, pathname)`: `public/` の index.html、style.css、app.js を返す（Content-Type 付き）。`public/` の外は返さない。無ければ 404
  - `handleSpin`、`handlePrizes`、`handleWinnings`: 設計書 4-1 の JSON 仕様（成功、400、409、500）どおりに応答する。JSON が壊れていれば 400
  - 予期しない例外は 500 `{"error": "Something went wrong."}` を返し、詳細を標準エラーに出す
- 完了条件: `node src/server.js` で起動し、`curl` で /api/prizes と /api/spin（名前あり・なし）が設計どおりに応答する

## 5. 画面: public/index.html、public/style.css、public/app.js

- 設計 ID: DS-IF-NAVIGATION-MENU、DS-IF-SPIN-SCREEN、DS-IF-PRIZE-LIST-SCREEN、DS-IF-MY-WINNINGS-SCREEN、DS-IF-STYLESHEET
- 内容:
  - 上部メニュー（Spin the Wheel、Prize List、My Winnings）。現在の画面を強調する。英語
  - Spin: 名前の入力欄（localStorage の `wheel.playerName` に保存し、次回に入れる）、Spin ボタン、ホイール（SVG か Canvas ではなく、CSS の回転で描く扇形）、結果欄、エラー欄。結果の景品に止まるように回す
  - Prize List: 景品名と確率（小数点 1 桁の %）の表
  - My Winnings: 名前の入力欄、Show my winnings ボタン、表（景品名、日時）、件数
  - 配色: 背景 #e6e6e6、部品 #8b0000、文字は白。文字列は textContent で入れる
  - ルーティング: `#/`、`#/prizes`、`#/winnings`（ハッシュの変更で画面を切り替える）
- 完了条件: `PORT=8123 bash run.sh` でブラウザ（または curl で HTML と CSS の取得）から 3 画面が開ける。メニューの 3 リンクが全画面にある

## 6. 単体テスト: tests/unit/

- 設計 ID: なし（対応表には載せない。テストファイル）
- 内容: `validatePlayerName`（空、空白のみ、30 字、31 字、前後の空白）、`pickWeightedPrize`（乱数の境界で景品が変わる、重み 1 の景品）、`openDatabase`＋`seedInitialData`（空の DATA_DIR で件数、2 回目の起動で増えない）
- 完了条件: `node --test tests/unit/` が全件通過

## 7. E2E テスト: e2e/

- 設計 ID: DS-TS-SPIN-AND-RECORD-E2E、DS-TS-NAME-VALIDATION-E2E、DS-TS-VIEW-PRIZES-E2E、DS-TS-VIEW-OWN-WINNINGS-E2E、DS-TS-NAVIGATE-SCREENS-E2E、DS-TS-INITIAL-DATA-E2E
- 内容: 設計書 8-2 の 6 シナリオを 1 ファイルずつ（`e2e/spin-and-record.test.js` など）。各テストは一時的な DATA_DIR と空きポートで `src/server.js` を子プロセスとして起動し、HTTP で確かめ、終わったら止める
- 完了条件: 8-4 のコマンドで全件通過し、`e2e/results/e2e.xml` ができる

## 8. 対応表: docs/trace_map.md

- 設計 ID: 第 7 章の全 DS-MD と公開関数、DS-IF-API-*、DS-TS-*-E2E
- 内容: `scripts/isdd/` の導入（タスク 0）の後、`docs/trace_map.md` に登録する（DS-MD と修飾名。関数は公開関数のみ。`DS-TS` は `e2e/<file>.test.js` の行）
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件、受け入れ判定が全 DS-TS 合格、全要件が実装済み

## 9. README.md

- 内容: 起動方法（`bash setup.sh`、`PORT=8000 bash run.sh`、`DATA_DIR`）、画面の説明、テストの実行方法
- 完了条件: README.md だけで起動できる

## 10. 実装完了の確認（末尾）

1. 対応表の更新（タスク 8）: `bash scripts/isdd/check.sh --strict` がエラー 0・警告 0
2. 起動確認（タスク 1）: `PORT=任意 bash run.sh` で主要な 3 画面が開ける。確認後、起動したプロセスを PID で止める
3. 単体テスト（タスク 6）と結合・E2E テスト（タスク 7）の全件通過
4. `python3 scripts/isdd/implementation_completeness_checker.py .` の全項目 OK
5. `python3 .claude/skills/isdd-build/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md` が問題 0 件
6. 要件の全 RQ-FT・RQ-UI・RQ-NF・RQ-DT がテストまたは実装で確かめられている（要件ごとの実装済み判定を出す）

## 補足: 途中で設計に無い要素が要った場合

コーディングを止め、`docs/proposals.md` に提案を書く。設計 ID は採番しない。
