# 変更設計書: 配色の変更、回すときの名前の必須化、当選記録への名前の表示

判定日: 2026-11-05 / 入力要件: `.history/20261105-theme-name-records/change_requirements.md`（正本 `docs/requirements.md` に重ねて読む）

本書は変更分だけを書く。すべての設計要素に [追加] か [削除] を付ける。中身が変わる要素は、旧い要素を [削除]、新しい要素を [追加] に分けて書き、削除する要素には削除理由を書く。正本 `docs/detail_design.md` は書き換えない。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12 の標準ライブラリ、SQLite、素の HTML・CSS・JavaScript）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし。既存設計 `docs/detail_design.md` セクション 3-1 を参照。`winning_records` は既に `player_name` を保存しているため、表の定義は変えない。

### 3-2. トランザクションと排他制御

変更なし。既存設計 `docs/detail_design.md` セクション 3-2 を参照。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者向けインターフェース（画面と API）の変更。

画面

| 設計 ID | 画面 | 配信元 | 要素と機能 |
|---|---|---|---|
| [削除] `DS-IF-SPIN-SCREEN` | Spin the Wheel（`/`） | `web/index.html`、`web/static/spin.js` | 削除理由: 名前の入力欄の配置と必須表示、結果欄の表示項目（当選日時）が変わるため（`DS-IF-SPIN-SCREEN-NAME-REQUIRED` に置き換える） |
| [追加] `DS-IF-SPIN-SCREEN-NAME-REQUIRED` | Spin the Wheel（`/`） | `web/index.html`、`web/static/spin.js` | 見出し、ホイール（canvas、区画は dark green の濃淡）、指針、フォーム（名前の入力欄とSpin ボタンを 1 行に並べる）。名前の入力欄のラベルは「Your name (required)」、`required` 属性と `aria-required="true"`。Spin を押すと、名前が空・30 文字超なら抽選せず、入力欄の下のエラー欄に既存の文言を出す。結果欄は景品名と説明、名前、当選日時（当選記録の `won_at` を既存の書式で表示）。名前は localStorage に保存し、読み込み時に入れる |
| [削除] `DS-IF-MY-WINNINGS-SCREEN` | My Winnings（`/my-winnings`） | `web/my-winnings.html`、`web/static/my-winnings.js` | 削除理由: 当選記録の表の列（名前の列の追加）が変わるため（`DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER` に置き換える） |
| [追加] `DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER` | My Winnings（`/my-winnings`） | `web/my-winnings.html`、`web/static/my-winnings.js` | 見出し、名前の入力欄、Show ボタン、当選記録の表（列は「Player」「Won at」「Prize」の順。各行に名前、当選日時、景品名）。記録が無いときの文言は既存のまま |
| [削除] `DS-IF-STYLESHEET` | 配色 | `web/static/style.css` | 削除理由: 背景と部品の配色が変わるため（`DS-IF-IVORY-GREEN-STYLESHEET` に置き換える） |
| [追加] `DS-IF-IVORY-GREEN-STYLESHEET` | 配色 | `web/static/style.css` | 背景 `#FFFFF0`（ivory）。部品（ナビゲーション、ボタン、カード、見出しの線、表の見出し、ホイールの区画、指針）は `#006400`（dark green）。ホイールの区画は `#006400` と `#004D00`、奇数件の最後の区画は `#1F5F1F`。部品の上の文字は白、背景の上の文字は `#1A1A1A`。エラー文字は太字の `#1A1A1A` と `#006400` の枠線。light gray（`#D3D3D3`）と dark red（`#8B0000`）は使わない |
| `DS-IF-NAVIGATION-MENU` | 全画面の上部の共通メニュー | 各 HTML の `<header>` | 変更なし（配色は `DS-IF-IVORY-GREEN-STYLESHEET` が受け持つ）。既存設計 `docs/detail_design.md` 4-1 を参照 |
| `DS-IF-STATIC-ASSETS` | 静的ファイルの配信 | `web/static/` 配下 | 変更なし（配信の仕組みは同じ。対応要件の行だけ変わる。第 11 章を参照） |

API

| 設計 ID | メソッドとパス | 入力 | 出力（成功） | エラー |
|---|---|---|---|---|
| [削除] `DS-IF-WINNINGS-API` | GET `/api/winnings?name=文字列` | クエリの `name` | 200。`{"player_name", "winnings": [{"id", "prize_id", "prize_name", "won_at"}]}` | 削除理由: 各行に `player_name` を足すため（`DS-IF-WINNINGS-API-WITH-PLAYER` に置き換える） |
| [追加] `DS-IF-WINNINGS-API-WITH-PLAYER` | GET `/api/winnings?name=文字列` | クエリの `name` | 200。`{"player_name": 文字列, "winnings": [{"id", "player_name", "prize_id", "prize_name", "won_at"}]}`（新しい順）。各行の `player_name` は保存された名前 | 400: 名前が空・30 文字超（既存と同じ文言） |
| `DS-IF-PRIZES-API` | GET `/api/prizes` | 無し | 変更なし | 変更なし |
| `DS-IF-SPINS-API` | POST `/api/spins` | JSON `{"player_name"}` | 変更なし（結果の `record` は既に `player_name` と `won_at` を含む） | 変更なし |

- 名前の検査（前後の空白の除去、1〜30 文字）と、エラーの応答の形（`{"error": 文字列}`）は変えない。

### 4-2. 内部設計

- [追加] 当選記録の取得の処理（`DS-FN-LIST-WINNINGS-WITH-PLAYER-NAME`）: `SELECT id, player_name, prize_id, prize_name, won_at` を返す。絞り込み（`COLLATE NOCASE`）と並び（当選日時、記録IDの降順）は変えない。
- [削除] 旧い当選記録の取得の処理（第 11 章の [削除] の行を参照）。削除理由: 各行に `player_name` を足すため（中身が変わる要素は新しい ID にする）。
- 業務ロジック（`DS-FN-GET-OWN-WINNINGS`）は、データ層の返した行をそのまま返すため変更なし。
- 抽選（`DS-FN-SPIN-WHEEL`）の処理フローは変えない。

ホイールの描画（ブラウザ側、`DS-IF-SPIN-SCREEN-NAME-REQUIRED` の一部）: 区画の色を `#006400` と `#004D00` で交互に塗る。他の描画の仕組み（角度、回転、約 4 秒）は変えない。

| 名前 | 役割の変更 |
|---|---|
| 共通の処理（`web/static/common.js`） | 当選日時の書式を `WheelApp.formatWonAt` として共通化し、スピン結果と My Winnings の両方で使う（画面の JavaScript であり、対応表の対象外） |

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照（`SpinService`、`RequestError`、`Database`、`WheelRequestHandler` の責務は変わらない）。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

変更なし。既存の名前のエラー（空、30 文字超）は、入力欄の下に太字の `#1A1A1A` で出す（配色の変更に伴う表示の変更だけ）。

### 6-2〜6-5

変更なし。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。

### 7-2. ソースファイルの一覧

| ファイル | DS-MD | 役割 | 実現する設計 ID |
|---|---|---|---|
| `app/server.py` | `DS-MD-SERVER` | 変更の一部。[追加] の実現 ID: `DS-IF-SPIN-SCREEN-NAME-REQUIRED`、`DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER`、`DS-IF-IVORY-GREEN-STYLESHEET`、`DS-IF-WINNINGS-API-WITH-PLAYER` |
| `app/server.py` | `DS-MD-SERVER` | 変更の一部。[削除] の実現 ID は第 11 章の [削除] の行を参照（旧い画面・配色・API の ID）。他の実現 ID（`DS-CL-WHEEL-REQUEST-HANDLER`、`DS-FN-CREATE-SERVER`、`DS-FN-ROUTE-REQUEST`、`DS-IF-PRIZE-LIST-SCREEN`、`DS-IF-NAVIGATION-MENU`、`DS-IF-STATIC-ASSETS`、`DS-IF-PRIZES-API`、`DS-IF-SPINS-API`）は変更なし |
| `app/database.py` | `DS-MD-DATABASE` | 変更の一部。[追加] の実現 ID: `DS-FN-LIST-WINNINGS-WITH-PLAYER-NAME`。[削除] の実現 ID は第 11 章の [削除] の行を参照。それ以外は変更なし |
| `app/service.py` | `DS-MD-SERVICE` | 変更なし |
| `app/__main__.py` | `DS-MD-MAIN` | 変更なし |

テストファイル（`tests/`、`e2e/`）と `web/` は `DS-MD-*` の対象外。

### 7-3. 対応表の粒度

変更なし（`function`）。

### 7-4. 依存の規則

変更なし。既存設計 `docs/detail_design.md` セクション 7-4 を参照。

### 7-5. コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。追加する単体テスト: 当選記録の取得（`list_winnings_by_name`）の各行が `player_name` を含み、保存された名前（大文字小文字の違いを含む）を返すこと。

### 8-2. E2E テストのシナリオ

要件 `RQ-TS-*` の変更に従う。

| DS-ID | 区分 | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [削除] `DS-TS-THEME-COLORS` | 削除理由: 旧配色の検査を新配色の検査に置き換えるため | 背景 light gray、部品 dark red の指定がある | - | - | - |
| [追加] `DS-TS-THEME-IVORY-DARK-GREEN` | 追加 | 背景 ivory、部品 dark green の指定があり、旧配色が無い | 同上（サーバーが起動している） | 1. `/static/style.css` を取得 2. `/`、`/prizes`、`/my-winnings` がそれを読み込むか調べる 3. 旧配色の値が無いか調べる | スタイルシートに `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` が無い。3 画面とも `/static/style.css` を読み込む |
| [追加] `DS-TS-SPIN-NAME-FIELD-REQUIRED` | 追加 | 名前の入力欄が Spin と同じ行にあり、必須と表示され、空のときは回らない | 同上（サーバーが起動している） | 1. `/` の HTML を取得 2. 名前の入力欄の属性とラベルを調べる 3. 名前を空にして `POST /api/spins` | 2: 入力欄が Spin ボタンと同じフォームにあり、`required` と `aria-required="true"` があり、ラベルが「Your name (required)」。3: 400 が返り、記録は増えない |
| [追加] `DS-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` | 追加 | 当選記録に名前・景品名・当選日時が出る | 初期データ入りの一時 DB で実サーバーが起動している | 1. 名前「Alice」で `POST /api/spins` 2. `GET /api/winnings?name=Alice` 3. `/my-winnings` の表の見出しを調べる | 1 の記録に名前・景品名・当選日時がある。2 の各行に `player_name`、`prize_name`、`won_at` がある。3 の見出しが「Player」「Won at」「Prize」の順 |

変更なし（既存のまま）: `DS-TS-SPIN-AND-RECORD`、`DS-TS-REQUIRE-PLAYER-NAME`、`DS-TS-PRIZE-LIST-SHOWS-ALL`、`DS-TS-OWN-WINNINGS-FILTER`、`DS-TS-PRIZE-SELECTION-RULE`、`DS-TS-NAVIGATION-ALL-PAGES`、`DS-TS-START-WITH-SAMPLE-DATA`。

### 8-3. E2E の実行手段

変更なし。既存設計 `docs/detail_design.md` セクション 8-3 を参照（HTTP で実サーバーを確かめる。ブラウザは使わない）。

### 8-4. E2E の実行コマンドと運用

変更なし。テストの関数は `e2e/test_wheel_site.py` の `WheelSiteTest` のメソッド。新しい `DS-TS-*` の行は、対応する新しいメソッドに結ぶ。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

| 区分 | DS-ID | 対応要件ID |
|---|---|---|
| [削除] | `DS-MD-SERVER` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-UI-NAVIGATION-MENU`, `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` |
| [追加] | `DS-MD-SERVER` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-UI-NAVIGATION-MENU`, `RQ-UI-IVORY-DARK-GREEN-THEME`, `RQ-UI-SPIN-NAME-FIELD`, `RQ-UI-WINNING-RECORD-DISPLAY` |
| [削除] | `DS-MD-DATABASE` | `RQ-FT-RECORD-WINNING`, `RQ-DT-PRIZE`, `RQ-DT-WINNING-RECORD`, `RQ-DT-DATABASE-FILE`, `RQ-OP-START-WITH-SAMPLE-DATA` |
| [追加] | `DS-MD-DATABASE` | `RQ-FT-RECORD-WINNING`, `RQ-DT-PRIZE`, `RQ-DT-WINNING-RECORD`, `RQ-DT-DATABASE-FILE`, `RQ-OP-START-WITH-SAMPLE-DATA` |
| [削除] | `DS-IF-SPIN-SCREEN` | `RQ-UI-SPIN-SCREEN` |
| [追加] | `DS-IF-SPIN-SCREEN-NAME-REQUIRED` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-SPIN-NAME-FIELD`, `RQ-UI-WINNING-RECORD-DISPLAY` |
| [削除] | `DS-IF-MY-WINNINGS-SCREEN` | `RQ-UI-MY-WINNINGS-SCREEN` |
| [追加] | `DS-IF-MY-WINNINGS-SCREEN-WITH-PLAYER` | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-UI-WINNING-RECORD-DISPLAY` |
| [削除] | `DS-IF-STYLESHEET` | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` |
| [追加] | `DS-IF-IVORY-GREEN-STYLESHEET` | `RQ-UI-IVORY-DARK-GREEN-THEME` |
| [削除] | `DS-IF-STATIC-ASSETS` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` |
| [追加] | `DS-IF-STATIC-ASSETS` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-IVORY-DARK-GREEN-THEME` |
| [削除] | `DS-IF-WINNINGS-API` | `RQ-UI-MY-WINNINGS-SCREEN` |
| [追加] | `DS-IF-WINNINGS-API-WITH-PLAYER` | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-UI-WINNING-RECORD-DISPLAY` |
| [削除] | `DS-FN-LIST-WINNINGS-BY-NAME` | `RQ-FT-VIEW-OWN-WINNINGS`, `RQ-DT-WINNING-RECORD` |
| [追加] | `DS-FN-LIST-WINNINGS-WITH-PLAYER-NAME` | `RQ-FT-VIEW-OWN-WINNINGS`, `RQ-DT-WINNING-RECORD`, `RQ-UI-WINNING-RECORD-DISPLAY` |
| 変更なし | `DS-CL-WHEEL-REQUEST-HANDLER` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-WINNINGS-SCREEN` |
| 変更なし | `DS-CL-SPIN-SERVICE` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-PRIZE-SELECTION-RULE` |
| 変更なし | `DS-CL-REQUEST-ERROR` | `RQ-FT-REQUIRE-PLAYER-NAME` |
| 変更なし | `DS-CL-DATABASE` | `RQ-FT-RECORD-WINNING`, `RQ-DT-DATABASE-FILE` |
| 変更なし | `DS-MD-MAIN` | `RQ-OP-LAUNCH-COMMAND`, `RQ-OP-DATA-DIR-STORAGE` |
| 変更なし | `DS-MD-SERVICE` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-PRIZE-SELECTION-RULE`, `RQ-FT-REQUIRE-PLAYER-NAME`, `RQ-FT-VIEW-PRIZE-LIST`, `RQ-FT-VIEW-OWN-WINNINGS` |
| 変更なし | `DS-FN-MAIN` | `RQ-OP-LAUNCH-COMMAND`, `RQ-OP-DATA-DIR-STORAGE`, `RQ-OP-START-WITH-SAMPLE-DATA` |
| 変更なし | `DS-FN-CREATE-SERVER` | `RQ-OP-LAUNCH-COMMAND` |
| 変更なし | `DS-FN-ROUTE-REQUEST` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-WINNINGS-SCREEN` |
| 変更なし | `DS-FN-SPIN-WHEEL` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-PRIZE-SELECTION-RULE` |
| 変更なし | `DS-FN-GET-PRIZE-LIST` | `RQ-FT-VIEW-PRIZE-LIST` |
| 変更なし | `DS-FN-GET-OWN-WINNINGS` | `RQ-FT-VIEW-OWN-WINNINGS` |
| 変更なし | `DS-FN-VALIDATE-PLAYER-NAME` | `RQ-FT-REQUIRE-PLAYER-NAME` |
| 変更なし | `DS-FN-INITIALIZE-DATABASE` | `RQ-OP-START-WITH-SAMPLE-DATA`, `RQ-DT-DATABASE-FILE` |
| 変更なし | `DS-FN-LIST-PRIZES` | `RQ-FT-VIEW-PRIZE-LIST`, `RQ-DT-PRIZE` |
| 変更なし | `DS-FN-ADD-WINNING-RECORD` | `RQ-FT-RECORD-WINNING`, `RQ-DT-WINNING-RECORD` |
| 変更なし | `DS-IF-PRIZE-LIST-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN` |
| 変更なし | `DS-IF-NAVIGATION-MENU` | `RQ-UI-NAVIGATION-MENU` |
| 変更なし | `DS-IF-PRIZES-API` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN` |
| 変更なし | `DS-IF-SPINS-API` | `RQ-UI-SPIN-SCREEN` |
| 変更なし | `DS-OP-RUN-SCRIPT` | `RQ-OP-LAUNCH-COMMAND`, `RQ-OP-DATA-DIR-STORAGE` |
| 変更なし | `DS-SC-PRIZE-TABLE` | `RQ-DT-PRIZE` |
| 変更なし | `DS-SC-WINNING-RECORD-TABLE` | `RQ-DT-WINNING-RECORD` |
| 変更なし | `DS-SC-DATABASE-FILE` | `RQ-DT-DATABASE-FILE`, `RQ-OP-DATA-DIR-STORAGE` |
| [削除] | `DS-TS-THEME-COLORS` | `RQ-TS-THEME-COLORS` |
| [追加] | `DS-TS-THEME-IVORY-DARK-GREEN` | `RQ-TS-THEME-IVORY-DARK-GREEN` |
| [追加] | `DS-TS-SPIN-NAME-FIELD-REQUIRED` | `RQ-TS-SPIN-NAME-FIELD-REQUIRED` |
| [追加] | `DS-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` | `RQ-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` |
| 変更なし | `DS-TS-SPIN-AND-RECORD` | `RQ-TS-SPIN-AND-RECORD` |
| 変更なし | `DS-TS-REQUIRE-PLAYER-NAME` | `RQ-TS-REQUIRE-PLAYER-NAME` |
| 変更なし | `DS-TS-PRIZE-LIST-SHOWS-ALL` | `RQ-TS-PRIZE-LIST-SHOWS-ALL` |
| 変更なし | `DS-TS-OWN-WINNINGS-FILTER` | `RQ-TS-OWN-WINNINGS-FILTER` |
| 変更なし | `DS-TS-PRIZE-SELECTION-RULE` | `RQ-TS-PRIZE-SELECTION-RULE` |
| 変更なし | `DS-TS-NAVIGATION-ALL-PAGES` | `RQ-TS-NAVIGATION-ALL-PAGES` |
| 変更なし | `DS-TS-START-WITH-SAMPLE-DATA` | `RQ-TS-START-WITH-SAMPLE-DATA` |

### 11-1. 除外要件

除外要件は無い。
