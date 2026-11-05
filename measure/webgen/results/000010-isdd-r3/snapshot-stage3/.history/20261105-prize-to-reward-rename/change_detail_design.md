# 変更設計書: 報酬ルーレット Web サイト（「景品」を「報酬」に統一）

本書は変更要件定義書 `change_requirements.md` を満たす変更の設計。正本 `docs/detail_design.md` は書き換えない。変更は `isdd-build` の実装後レビューで正本へ反映する。
区分: 中身が変わる設計要素は、旧い行を `[削除]`、新しい行を `[追加]` で書く（同じ ID を使う）。文言だけの置き換え（用語の表記）は、変更要件定義書 1-3 の一覧に従って正本の本文で行い、ここには書かない。内部の名前（ID、ファイル名、クラス名、テーブル名、JSON のキー、テスト関数名）は変えない。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（技術は引き継ぐ）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし（テーブルと項目は変えない）。サンプルデータの名前だけ変える（下の 3-1 の内容の変更。`DS-SC-SAMPLE-DATA-SET`）。

### 3-1. 変更するサンプルデータ（`DS-SC-SAMPLE-DATA-SET`）

| 区分 | 行 | 内容 |
|---|---|---|
| [削除] `DS-SC-SAMPLE-DATA-SET` | 景品 7 件の 6 番目と 7 番目 | 6 番目「Grand Prize: $50 Gift Card」、7 番目の説明「No prize this time」 |
| [追加] `DS-SC-SAMPLE-DATA-SET` | 報酬 7 件の 6 番目と 7 番目 | 6 番目「Grand Reward: $50 Gift Card」、7 番目の説明「No reward this time」。他の 5 件と、当選記録の 2 件（Free Coffee、10% Off Coupon）と利用者名「Sample Player」は変えない |

## 4. アーキテクチャ設計

### 4-1. 外部設計

画面と API の URL、表の見出し、API の URL を変える。

| 区分 | 種類 | 設計 ID | 画面・URL・API | 内容 |
|---|---|---|---|---|
| [削除] | 画面 | `DS-IF-PRIZES-SCREEN` | `/prizes` | 景品一覧画面（`src/web/static/prizes.html` と `js/prizes.js`、`styles.css`） |
| [追加] | 画面 | `DS-IF-PRIZES-SCREEN` | `/rewards` | 報酬一覧画面（`src/web/static/rewards.html` と `js/rewards.js`、`styles.css`。`prizes.html` と `prizes.js` から改名。要素 ID は `reward-message`、`reward-rows`。関数は `initRewardsPage`、`renderRewardTable`）。メニューの項目は Reward List。表の見出しは Reward。取得に失敗したら「Could not load rewards.」 |
| [削除] | 画面 | `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `/records` | 当選履歴画面（利用者名・景品名・当選日時の列） |
| [追加] | 画面 | `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `/records` | 当選履歴画面（利用者名（Player）・報酬名（Reward）・当選日時（Won at）の列） |
| [削除] | 画面の配信 | `DS-IF-PAGE-ROUTES` | `/`、`/prizes`、`/records`、`/static/...` | 画面ファイルと静的ファイルを返す |
| [追加] | 画面の配信 | `DS-IF-PAGE-ROUTES` | `/`、`/rewards`、`/records`、`/static/...` | 画面ファイルと静的ファイルを返す。`/prizes` は返さない（404） |
| [削除] | API | `DS-IF-PRIZES-API` | GET `/api/prizes` | 報酬（景品）の一覧 |
| [追加] | API | `DS-IF-PRIZES-API` | GET `/api/rewards` | 報酬の一覧。応答の項目（id、name、description、weight、probability_percent、is_miss、position）は変えない |

- 画面の配信（`DS-IF-PAGE-ROUTES`）の本文も、`/prizes` を `/rewards` に読み替える（正本の本文へ反映する）。
- 変更なし（既存）: `DS-IF-SPIN-SCREEN-NAME-FIELD`（`/` の画面。名前だけ 1-3 の置き換え）、`DS-IF-SPIN-API`（応答の項目 `prize_name` などは内部の名前として変えない）、`DS-IF-RECORDS-API-WITH-PLAYER`。

### 4-2. 内部設計

変更なし。内部の処理の流れは変えない。ただし `DS-MD-HTTP-ROUTER`、`DS-CL-REQUEST-HANDLER` の説明文の中の `/prizes` と `/api/prizes` は、上の 4-1 の URL に読み替える（正本の本文へ反映する）。

## 5. クラス設計

変更なし（クラス名 `PrizeRepository` などは内部の名前として変えない）。

## 6. エラーハンドリングとセキュリティ設計

変更なし。ただし `DS-FN-FETCH-JSON` の説明の中の「景品一覧の取得失敗」の文言は、「Could not load rewards.」に読み替える（`DS-FN-RENDER-PRIZE-TABLE` の周りの説明も同じ）。

## 7. コード設計

画面を作るファイルを改名する: `src/web/static/prizes.html` → `rewards.html`、`src/web/static/js/prizes.js` → `js/rewards.js`。`js/rewards.js` の関数は `initRewardsPage`、`renderRewardTable` に改名する（`DS-IF-PRIZES-SCREEN`、`DS-MD-PRIZES-JS`、`DS-FN-RENDER-PRIZE-TABLE` の対応先を直す）。`DS-MD-PRIZES-JS` の ID は変えない（ID は内容の名前ではない）。他のファイルとクラス、関数の名前は変えない。サーバーの起動時の表示は「Reward wheel is running at ...」にする（`DS-MD-SERVER-ENTRY`。文言だけの変更）。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。

### 8-2. E2E テストのシナリオ

| 区分 | 設計 ID | テストの内容 | 前提 | 操作 | 期待する結果 |
|---|---|---|---|---|---|
| [削除] | `DS-TS-VIEW-PRIZES-E2E` | 景品一覧の内容 | 同上 | `/api/prizes` と `/prizes` を取得する | 7 件、確率の合計は 100.0。`/prizes` は英語の表の見出しを含む |
| [追加] | `DS-TS-VIEW-PRIZES-E2E` | 報酬一覧の内容 | 同上 | `/api/rewards` と `/rewards` を取得する。`/prizes` は 404 になる | 7 件、確率の合計は 100.0。`/rewards` は見出し「Reward List」と表の見出し「Reward」を含む。`/prizes` は 404 |
| [削除] | `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | 利用者名による絞り込みと、各記録の利用者名 | 「Sample Player」の初期記録 | `/api/records` を「Sample Player」と「Nobody Here」で呼ぶ。`/records` の HTML を取得する | 前者は 2 件で新しい順。各要素の `player_name` は「Sample Player」。後者は空の配列。`/records` の表に「Player」「Prize」「Won at」の見出しがある |
| [追加] | `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | 利用者名による絞り込みと、各記録の利用者名 | 同上 | 同上 | 前者は 2 件で新しい順。各要素の `player_name` は「Sample Player」。後者は空の配列。`/records` の表に「Player」「Reward」「Won at」の見出しがある |
| [削除] | `DS-TS-NAVIGATION-THEME-E2E` | 画面の配信、メニュー、配色（ivory と dark green）と英語 | 同上 | `/`、`/prizes`、`/records` を取得し、メニューの 3 つの項目を確かめる。`styles.css` の色を確かめる | 3 画面にメニューのリンク（`/`、`/prizes`、`/records`）がある。`styles.css` に `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` は無い |
| [追加] | `DS-TS-NAVIGATION-THEME-E2E` | 画面の配信、メニュー、配色（ivory と dark green）と英語、「prize」の語が無いこと | 同上 | `/`、`/rewards`、`/records` を取得し、メニューの 3 つの項目を確かめる。`styles.css` の色を確かめる。3 画面の HTML と `/api/rewards` の応答に「prize」（大文字小文字を問わず）が無いことを確かめる | 3 画面にメニューのリンク（`/`、`/rewards`、`/records`）があり、メニューの項目は Spin Wheel、Reward List、My Winning Records。`styles.css` に `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` は無い。画面の HTML に「prize」が無い |

- `DS-TS-SPIN-AND-RECORD-E2E`、`DS-TS-SPIN-NAME-REQUIRED-E2E`、`DS-TS-SEED-DATA-E2E` は変更なし（テストの中身は変えない。画面の文言を照合していれば新しい文言に合わせる）。

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

変更した設計要素の行だけを書く（[削除] は旧い対応、[追加] は新しい対応）。変更の無い要素の対応は既存設計のまま有効。

| 区分 | 設計 ID | 対応する要件 ID |
|---|---|---|
| [削除] | `DS-IF-PRIZES-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |
| [追加] | `DS-IF-PRIZES-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |
| [削除] | `DS-IF-PRIZES-API` | `RQ-FT-LIST-PRIZES` |
| [追加] | `DS-IF-PRIZES-API` | `RQ-FT-LIST-PRIZES` |
| [削除] | `DS-IF-PAGE-ROUTES` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN` |
| [追加] | `DS-IF-PAGE-ROUTES` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN` |
| [削除] | `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `RQ-UI-RECORDS-SCREEN`, `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] | `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `RQ-UI-RECORDS-SCREEN`, `RQ-FT-VIEW-OWN-RECORDS` |
| [削除] | `DS-SC-SAMPLE-DATA-SET` | `RQ-DT-SAMPLE-SEED` |
| [追加] | `DS-SC-SAMPLE-DATA-SET` | `RQ-DT-SAMPLE-SEED` |
| [削除] | `DS-TS-VIEW-PRIZES-E2E` | `RQ-TS-VIEW-PRIZES` |
| [追加] | `DS-TS-VIEW-PRIZES-E2E` | `RQ-TS-VIEW-PRIZES` |
| [削除] | `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | `RQ-TS-VIEW-OWN-RECORDS` |
| [追加] | `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | `RQ-TS-VIEW-OWN-RECORDS` |
| [削除] | `DS-TS-NAVIGATION-THEME-E2E` | `RQ-TS-NAVIGATION` |
| [追加] | `DS-TS-NAVIGATION-THEME-E2E` | `RQ-TS-NAVIGATION` |
| 変更なし（既存） | `DS-IF-SPIN-SCREEN-NAME-FIELD` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-SPIN-NAME-FIELD` |
| 変更なし（既存） | `DS-TS-SPIN-NAME-REQUIRED-E2E` | `RQ-TS-NAME-VALIDATION` |
| 変更なし（既存） | `DS-TS-SPIN-AND-RECORD-E2E` | `RQ-TS-SPIN-AND-RECORD` |
| 変更なし（既存） | `DS-TS-SEED-DATA-E2E` | `RQ-TS-SEED-DATA` |
| 変更なし（既存） | `DS-MD-HTTP-ROUTER` | `RQ-FT-SPIN-WHEEL`, `RQ-UI-SPIN-SCREEN` |
| 変更なし（既存） | `DS-CL-REQUEST-HANDLER` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-LIST-PRIZES`, `RQ-FT-VIEW-OWN-RECORDS` |
| 変更なし（既存） | `DS-MD-SERVER-ENTRY` | `RQ-OP-CONFIG-ENV`, `RQ-DT-LOCAL-DATABASE` |
| 変更なし（既存） | `DS-FN-FETCH-JSON` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-LIST-PRIZES`, `RQ-FT-VIEW-OWN-RECORDS` |
| 変更なし（既存） | `DS-FN-RENDER-PRIZE-TABLE` | `RQ-FT-LIST-PRIZES` |
| 変更なし（既存） | `DS-IF-SPIN-API` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-RECORD-WINNING` |
| 変更なし（既存） | `DS-IF-RECORDS-API-WITH-PLAYER` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` |
| 変更なし（既存） | `DS-MD-WHEEL-SERVICE` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-DRAW-BY-WEIGHT`, `RQ-FT-RECORD-WINNING`, `RQ-FT-MISS-NOT-RECORDED` |
| 変更なし（既存） | `DS-MD-NAME-VALIDATION` | `RQ-FT-PLAYER-NAME-REQUIRED` |
| 変更なし（既存） | `DS-FN-CHOOSE-SEGMENT-BY-WEIGHT` | `RQ-FT-DRAW-BY-WEIGHT` |

### 11-1. 除外要件

無し。

