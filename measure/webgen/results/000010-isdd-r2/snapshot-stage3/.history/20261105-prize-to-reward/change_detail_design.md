# 変更設計書: 利用者に見える「景品（prize）」の表示語を「報酬（reward）」に置き換える

判定日: 2026-11-05 / 入力要件: `.history/20261105-prize-to-reward/change_requirements.md`（正本 `docs/requirements.md` に重ねて読む）

本書は変更分だけを書く。設計要素の中身が変わるものは、旧い要素を [削除]、新しい要素を [追加] に分けて書く。画面の英語の文言（表示語）だけが変わる要素は、ID を変えず、変更要件定義書 3-8 の表を正とする。正本 `docs/detail_design.md` は書き換えない。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし。既存設計 `docs/detail_design.md` セクション 3-1 を参照（テーブル名と列名は内部のまま）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

画面の URL と表示語の変更。

画面

| 設計 ID | 画面 | 配信元 | 要素と機能 |
|---|---|---|---|
| [削除] `DS-IF-PRIZE-LIST-SCREEN` | Prize List（`/prizes`） | `web/prizes.html`、`web/static/prizes.js` | 削除理由: 画面の URL と表示名が `/rewards` と「Reward List」に変わるため（`DS-IF-REWARD-LIST-SCREEN` に置き換える） |
| [追加] `DS-IF-REWARD-LIST-SCREEN` | Reward List（`/rewards`） | `web/rewards.html`、`web/static/rewards.js` | 見出し「Reward List」、報酬のカード（名前、説明）、件数（「N reward(s) to win on the wheel」）、読み込み失敗（「The reward list could not be loaded.」）。旧い URL `/prizes` は `/rewards` へ 301 で転送する |

- 表示語だけが変わる既存の画面（`DS-IF-SPIN-SCREEN-NAME-FIELD`、`DS-IF-MY-WINNINGS-SCREEN-WITH-NAME`、`DS-IF-NAVIGATION-MENU`）は ID を変えない。文言は変更要件定義書 3-8 の表による（ナビゲーションのリンク名は「Reward List」、My Winnings の列名は「Reward」、結果欄の項目名は「Reward」）。
- 公開 API（`DS-IF-PRIZES-API`、`DS-IF-SPINS-API`、`DS-IF-WINNINGS-API-WITH-NAME`）は変えない。パスと JSON のキー（`prizes`、`prize`、`prize_name`）は内部の約束として残す。

### 4-2. 内部設計

- `app/server.py` の画面の対応表（`DS-IF-REWARD-LIST-SCREEN`）: `/rewards` → `rewards.html`。`/prizes` は `/rewards` へ 301 で転送する（`serve_page` の前で振り分ける）。
- `web/` の配信は変えない（`DS-IF-STATIC-ASSETS`）。

## 5. クラス設計

変更なし。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

- 0 件のときのメッセージ（`DS-FN-SPIN-WHEEL`）と、景品一覧の読み込み失敗のメッセージ（`DS-IF-REWARD-LIST-SCREEN`）の文言だけを変える（変更要件定義書 3-8）。応答のコードは変えない。

### 6-2〜6-5

変更なし。

## 7. コード設計

### 7-1. ディレクトリ構成

- `web/prizes.html` → `web/rewards.html`、`web/static/prizes.js` → `web/static/rewards.js` に名前を変える（内容は文言の置き換えと URL の変更）。

### 7-2. ソースファイルの一覧

| ファイル | 設計 ID | 役割 | 対応する関数・クラス |
|---|---|---|---|
| `web/rewards.html`（旧 `web/prizes.html`） | `DS-IF-REWARD-LIST-SCREEN` | Reward List 画面 | 無し（HTML） |
| `web/static/rewards.js`（旧 `web/static/prizes.js`） | `DS-IF-REWARD-LIST-SCREEN` | 報酬の一覧の描画 | 無し（JavaScript） |

- 他のソースファイルは変えない（`app/` のファイル構成と対応表の関数名は変えない）。

### 7-3. 対応表の粒度

変更なし（function）。

### 7-4. 依存の規則

無い。変更なし。

### 7-5. コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。

### 8-2. E2E テストのシナリオ

DS-TS の ID は変えない。検証内容は同じで、次の手順の URL と文言だけを新しくする（テスト関数名は変えない）。

- `DS-TS-PRIZE-LIST-SHOWS-ALL`: 2 の URL を `GET /rewards` にする。1 は `GET /api/prizes` のまま。
- `DS-TS-NAVIGATION-ALL-PAGES`: 1 の URL を `/rewards` にする。リンク名は「Reward List」。
- `DS-TS-THEME-IVORY-GREEN`: 1 の URL を `/rewards` にする。
- `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE`: 3 の表の列を「Player、Reward、Date won」にする。
- `DS-TS-START-WITH-SAMPLE-DATA`: 変えない（`/api/prizes` のまま）。

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし（`bash setup.sh`、`PORT=任意 bash run.sh` のまま）。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

変更要件定義書 3-8 の表示語の置き換えは、RQ-ID と DS-ID の対応を変えない。次の表の [削除] と [追加] の行だけが対応の変更で、「変更なし（既存）」の行は既存の対応をそのまま書いたもの（変更要件定義書の RQ-ID に対応する DS-ID を示す）。

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [削除] | `DS-IF-PRIZE-LIST-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN` |
| [追加] | `DS-IF-REWARD-LIST-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN` |
| 変更なし（既存） | `DS-IF-NAVIGATION-MENU` | `RQ-UI-NAVIGATION-MENU` |
| 変更なし（既存） | `DS-IF-SPIN-SCREEN-NAME-FIELD` | `RQ-UI-SPIN-SCREEN`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| 変更なし（既存） | `DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| 変更なし（既存） | `DS-IF-PRIZES-API` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN` |
| 変更なし（既存） | `DS-IF-SPINS-API` | `RQ-UI-SPIN-SCREEN` |
| 変更なし（既存） | `DS-IF-WINNINGS-API-WITH-NAME` | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-FT-VIEW-OWN-WINNINGS` |
| 変更なし（既存） | `DS-IF-STATIC-ASSETS` | `RQ-UI-SPIN-SCREEN`, `RQ-TS-IVORY-DARK-GREEN-THEME` |
| 変更なし（既存） | `DS-FN-SPIN-WHEEL` | `RQ-FT-PRIZE-SELECTION-RULE` |
| 変更なし（既存） | `DS-FN-GET-PRIZE-LIST` | `RQ-FT-VIEW-PRIZE-LIST` |
| 変更なし（既存） | `DS-FN-GET-OWN-WINNINGS` | `RQ-FT-VIEW-OWN-WINNINGS` |
| 変更なし（既存） | `DS-TS-NAVIGATION-ALL-PAGES` | `RQ-TS-NAVIGATION-ALL-PAGES` |
| 変更なし（既存） | `DS-TS-PRIZE-LIST-SHOWS-ALL` | `RQ-TS-PRIZE-LIST-SHOWS-ALL` |
| 変更なし（既存） | `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE` | `RQ-TS-RECORD-SHOWS-NAME-PRIZE-DATE` |
| 変更なし（既存） | `DS-TS-THEME-IVORY-GREEN` | `RQ-TS-IVORY-DARK-GREEN-THEME` |
| 変更なし（既存） | `DS-TS-START-WITH-SAMPLE-DATA` | `RQ-TS-START-WITH-SAMPLE-DATA` |

### 11-1. 除外要件

無し。
