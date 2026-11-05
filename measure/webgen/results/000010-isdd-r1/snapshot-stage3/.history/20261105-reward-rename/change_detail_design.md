# 変更設計書: 「prize（景品）」を「reward（報酬）」へ用語変更

- 作成日: 2026-11-05
- 入力: `change_requirements.md`（この変更の要件）、正本 `docs/requirements.md`・`docs/detail_design.md`（既存設計）
- 正本: `docs/detail_design.md`（書き換えない。反映は実装後に isdd-build の実装後レビューが行う）
- 記法: 設計要素の ID は据え置く（変更要件定義書 1-2 のとおり。ID の中の PRIZE は内部の識別子）。中身の変更は「文言変更」と書く。新しい ID は E2E の 1 本だけ [追加] する

## 1. 最小設計と要件の除外

要件と設計の対応は、第 11 章の対応表に書く。新しい要件は RQ-TS-REWARD-WORDING の 1 件（既存の RQ-FT・RQ-UI・RQ-NF は増やさない）。

### 11-1. 除外要件

変更なし。この変更で除外する要件は無い。

## 2. 技術選定

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。表・列の名前（`prize`、`prize_name`）は内部の識別子として据え置く。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース（画面）

| DS-IF | 画面・要素 | 機能 |
|---|---|---|
| DS-IF-NAVIGATION-MENU [文言変更] | 上部メニュー。リンク名は「Spin the Wheel」「Reward List」「My Winnings」。「Reward List」のリンク先は `#/rewards`（旧 `#/prizes`）。現在の画面のリンクを強調する | 3 画面への移動 |
| DS-IF-SPIN-SCREEN-NAME-REQUIRED [文言変更] | 結果カードの文言は「You won」、報酬名、「Recorded for 名前 at 日時」。ホイールの表示語（aria-label）は「Reward wheel」。その他は変更なし | 名前を必須で入力して回し、結果を表示する |
| DS-IF-PRIZE-LIST-SCREEN [文言変更] | 見出し「Reward List」、説明文「Each reward has a chance based on its weight. The wheel shows every reward in the same-sized slice.」、表（列: Reward（報酬名）、Chance（確率））。画面の機能は変えない | 報酬と確率を一覧で見る |
| DS-IF-MY-WINNINGS-SCREEN-DETAILS [文言変更] | 表の見出しは「Player」「Reward」「Won at」（旧「Prize」を「Reward」に）。その他は変更なし | 名前で絞った当選記録を、名前・報酬・日時の 3 項目で見る |

#### Web API（画面を支える内部 API。外部公開しない）

| DS-IF | メソッドとパス | 用途 | 入力 | 出力 | エラー |
|---|---|---|---|---|---|
| DS-IF-API-SPIN [文言変更] | POST /api/spin | 抽選と記録 | 変更なし | 変更なし（応答の JSON のキー `prize`、`prizeName`、`prizeIndex` は内部の識別子として据え置く） | 409: `{"error": "No rewards are available."}`（旧「No prizes are available.」）。他は変更なし |
| DS-IF-API-PRIZES | GET /api/prizes | 報酬一覧 | なし | 変更なし（パスとキーは据え置く） | なし |
| DS-IF-API-WINNINGS-DETAILS | GET /api/winnings?name=... | 名前で絞った当選記録 | 変更なし | 変更なし | 変更なし |

#### 外部システム連携・外部 DB 連携

変更なし。

#### 静的ファイル

変更なし（`public/index.html` の文言、`public/app.js` の経路の対応だけを変える。配色は変えない）。

### 4-2. 内部設計

#### 画面の経路（ハッシュ）

`public/app.js` の経路の対応（`SCREEN_BY_ROUTE`）で、`/prizes` を `/rewards` に変える。`/rewards` を報酬一覧の画面（`prizes` の画面）に対応させる。画面を開いたとき報酬一覧を読み込む動きは変えない。

#### 処理フロー（抽選）

変更なし。

#### 初期データ

`src/db.js` の初期景品の名前「Grand Prize Headphones」を「Grand Reward Headphones」にする（重み 3 は変えない）。DATA_DIR が空のときだけ入る。既に保存された旧名は書き換えない（変更要件定義書 1-2）。

### 4-3. 処理（クラス・関数の中身）

- `src/spin.js`: 景品が 0 件のときのエラー文言を「No rewards are available.」にする（関数名・戻り値の状態名 `no-prizes` は据え置く）。

### 5. クラス設計

変更なし（クラス・公開関数の追加・改名・削除は無い）。

## 6. エラーハンドリングとセキュリティ設計

- 景品 0 件のエラー: 文言のみ変更（「No rewards are available.」）。動作（抽選せず、記録しない）は変えない。

## 7. コード設計

変更なし。ソースファイル・公開関数は増やさない。対応表（`docs/trace_map.md`）の行も変えない。E2E のファイルを 1 つ足す（第 8 章）。

## 8. テスト設計

### 8-2. E2E テストの内容

| DS-TS | 確かめること（RQ-TS） | 前提条件 | テスト手順 | 期待される結果 |
|---|---|---|---|---|
| DS-TS-NAVIGATE-SCREENS-E2E [文言変更] | 3 画面を上部メニューだけで行き来できること（RQ-TS-NAVIGATE-SCREENS） | 初期データのある起動 | GET / の上部メニュー（リンク名とリンク先 `#/rewards`）と英語の見出し | メニューに「Reward List」があり、リンク先は `#/rewards` |
| DS-TS-VIEW-PRIZES-E2E [文言変更] | 報酬一覧に全報酬と確率が出る（RQ-TS-VIEW-PRIZES） | 初期データのある起動 | GET /api/prizes と GET / の見出し「Reward List」、表の見出し「Reward」 | 8 件、確率の合計が 100。見出しは「Reward List」 |
| DS-TS-WINNING-DETAILS-E2E [文言変更] | 当選記録に名前・報酬名・日時がすべて出る（RQ-TS-WINNING-DETAILS） | 初期データのある起動 | POST /api/spin `{"name":"Alice"}` → 201。GET /api/winnings?name=Alice。GET / の My Winnings の表の見出し | 各記録に playerName が Alice、prizeName、wonAt がある。見出しに Player、Reward、Won at がある |
| DS-TS-REWARD-WORDING-E2E [追加] | 画面の語が reward に統一され、prize が画面に出ないこと（RQ-TS-REWARD-WORDING） | 初期データのある起動 | GET / の HTML を取り、見える文字（タグの外の文字）と、aria-label・placeholder の値に prize の語（大文字小文字を問わず）が無いことを確かめる。上部メニューの「Reward List」と `#/rewards` を確かめる。GET /api/prizes の名前（ホイールと一覧に出る）に prize の語が無く、「Grand Reward Headphones」が含まれる | 見える文字と各ラベルに prize の語が無い。メニューと一覧の名前は reward に統一されている。ID・data 属性・API の名前（内部の識別子）は対象外 |

E2E のファイル（追加）: `e2e/reward-wording.test.js`。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

この変更で文言が変わる設計要素の対応を書く。対応は既存の正本（`docs/detail_design.md` 第 11 章）のまま変えない（ID を据え置くため）。[追加] の行は新しい E2E の 1 本だけ。

| DS-ID | 対応要件ID |
|---|---|
| DS-IF-API-SPIN | RQ-FT-SPIN-WHEEL, RQ-FT-NAME-REQUIRED, RQ-FT-RECORD-WINNING |
| DS-IF-API-PRIZES | RQ-FT-VIEW-PRIZE-LIST |
| DS-IF-API-WINNINGS-DETAILS | RQ-FT-VIEW-OWN-WINNINGS, RQ-FT-SHOW-WINNING-DETAILS |
| DS-SC-PRIZE | RQ-DT-PRIZE |
| DS-MD-DB | RQ-DT-STORAGE-FILE, RQ-DT-PRIZE, RQ-DT-WINNING-RECORD |
| DS-FN-PICK-WEIGHTED-PRIZE | RQ-FT-WEIGHTED-DRAW, RQ-FT-SPIN-WHEEL |
| DS-IF-SPIN-SCREEN-NAME-REQUIRED | RQ-UI-SPIN-SCREEN, RQ-UI-SPIN-NAME-FIELD, RQ-FT-NAME-REQUIRED, RQ-FT-SHOW-WINNING-DETAILS, RQ-NF-BROWSER-SUPPORT, RQ-NF-UI-LANGUAGE-EN |
| DS-IF-PRIZE-LIST-SCREEN | RQ-UI-PRIZE-LIST-SCREEN, RQ-NF-UI-LANGUAGE-EN |
| DS-IF-MY-WINNINGS-SCREEN-DETAILS | RQ-UI-MY-WINNINGS-SCREEN, RQ-FT-SHOW-WINNING-DETAILS, RQ-NF-UI-LANGUAGE-EN |
| DS-IF-NAVIGATION-MENU | RQ-UI-NAVIGATION-MENU, RQ-NF-UI-LANGUAGE-EN |
| DS-TS-NAVIGATE-SCREENS-E2E | RQ-TS-NAVIGATE-SCREENS |
| DS-TS-VIEW-PRIZES-E2E | RQ-TS-VIEW-PRIZES |
| DS-TS-WINNING-DETAILS-E2E | RQ-TS-WINNING-DETAILS |
| DS-IF-THEME-STYLESHEET | RQ-NF-THEME-IVORY-GREEN, RQ-NF-BROWSER-SUPPORT |
| DS-TS-REWARD-WORDING-E2E [追加] | RQ-TS-REWARD-WORDING |

### 11-1. 除外要件

変更なし。この変更で除外する要件は無い。
