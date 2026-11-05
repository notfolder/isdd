# 変更設計書: 配色の変更、名前欄の必須化、当選記録の表示項目

判定日: 2026-11-05 / 入力要件: `.history/20261105-theme-and-player-name/change_requirements.md`（正本: `docs/requirements.md`、正本の設計: `docs/detail_design.md`）

この変更設計書は既存の設計を変えるものだけを書く。書き方は次のとおり。
- 設計要素の中身が変わるものは、旧い設計 ID を [削除]、新しい設計 ID を [追加] にする（削除する要素には削除理由を書く）。
- 中身が変わらず、要件の対応だけが変わるものは、対応表の行を旧い対応は [削除]、新しい対応は [追加] で書く。
- 変えない章は「変更なし」とだけ書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照。Python 3.9 以上、標準ライブラリだけ、SQLite。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。当選記録の列（名前、景品ID、景品名、当選日時）と索引は変えない。当選記録を表示するときに、既に保存している名前を一緒に返す（3-1 の表の列は変えない）。

## 4. アーキテクチャ設計

### 4-1. 外部設計

画面（変更）

| 設計 ID | 画面 | 配信元 | 要素と機能 |
|---|---|---|---|
| `DS-IF-SPIN-SCREEN` [削除] | Spin the Wheel（`/`） | `web/index.html`、`web/static/spin.js` | 削除理由: 名前の入力欄を Spin ボタンの隣へ移し、必須にし、結果欄に名前・景品名・当選日時を出すため、画面の中身が変わる |
| `DS-IF-SPIN-SCREEN-NAME-FIELD` [追加] | Spin the Wheel（`/`） | `web/index.html`、`web/static/spin.js` | 見出し、ホイール（canvas）、指針、名前の入力欄（Spin ボタンと同じ行、ラベルは「Your name (required)」、required の属性）、Spin ボタン、結果欄（景品名、名前、景品名、当選日時）。名前は localStorage に保存し、読み込み時に入れる。空、または 31 文字以上で Spin を押したら、名前欄の下に検証の文言を出し、回さない |
| `DS-IF-MY-WINNINGS-SCREEN` [削除] | My Winnings（`/my-winnings`） | `web/my-winnings.html`、`web/static/my-winnings.js` | 削除理由: 当選記録の表に名前の列を足すため、画面の中身が変わる |
| `DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` [追加] | My Winnings（`/my-winnings`） | `web/my-winnings.html`、`web/static/my-winnings.js` | 見出し、名前の入力欄、Show ボタン、当選記録の表（列は Player（名前）、Prize（景品名）、Date won（当選日時））。記録が無いときの案内文は変えない |
| `DS-IF-STYLESHEET` [削除] | 配色 | `web/static/style.css` | 削除理由: 配色を light gray と dark red から ivory と dark green に変えるため、中身が変わる |
| `DS-IF-THEME-STYLESHEET` [追加] | 配色 | `web/static/style.css` | 背景 ivory（#FFFFF0）。部品（ナビゲーション、ボタン、カード、見出し、表の見出し、指針、エラーの文字）は dark green（#006400）。カードの文字は白。light gray（#D3D3D3）と dark red（#8B0000）は使わない |

API（変更）

| 設計 ID | メソッドとパス | 入力 | 出力（成功） | エラー |
|---|---|---|---|---|
| `DS-IF-WINNINGS-API` [削除] | GET `/api/winnings?name=文字列` | クエリの `name` | 削除理由: 当選記録の 1 件に名前（`player_name`）を足すため、応答の中身が変わる | ― |
| `DS-IF-WINNINGS-API-WITH-NAME` [追加] | GET `/api/winnings?name=文字列` | クエリの `name`（前後の空白は除く、1〜30 文字。大文字小文字は区別しない） | 200。`{"player_name": 文字列, "winnings": [{"id", "player_name", "prize_id", "prize_name", "won_at"}]}`（新しい順） | 400: 名前が空・30 文字超（従来と同じ文言）。エラーの形式は変えない |

- `DS-IF-SPINS-API`（POST `/api/spins`）は変更なし。応答の `record` に既に `player_name` と `won_at` があるため、結果欄はそれを使う。
- 画面の表示は引き続き英語。動的な文字は `textContent` で入れる。

### 4-2. 内部設計

処理フロー: 変更なし（抽選の処理フローは同じ）。

処理（関数）の変更

| 設計 ID | 処理 | 役割 |
|---|---|---|
| `DS-FN-LIST-WINNINGS-BY-NAME` [削除] | 当選記録の取得 | 削除理由: 返す項目に名前を足すため、問い合わせ（SELECT の項目）の中身が変わる |
| `DS-FN-LIST-WINNINGS-WITH-NAME` [追加] | 当選記録の取得 | 名前（大文字小文字を区別しない完全一致）で絞り込み、新しい順（当選日時、記録IDの降順）に、記録ID・名前・景品ID・景品名・当選日時を返す |

バッチは無い（変更なし）。

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照。`SpinService` の責務（抽選と取得）と、`Database` の責務は変わらない。

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照。名前の検査の文言（「Please enter your name.」「Name must be 30 characters or fewer.」）と、画面の入力欄の下に出す文言（「Please enter your name before spinning.」「Name must be 30 characters or fewer.」）は既存のまま。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。既存設計 `docs/detail_design.md` セクション 7-1 を参照。

### 7-2. ソースファイルの一覧

変更なし（ファイル、DS-MD-* は変えない）。実現する設計 ID の列だけを次のとおり変える。

| ファイル | DS-MD | 役割 | 実現する設計 ID |
|---|---|---|---|
| `app/server.py` | `DS-MD-SERVER` | HTTP 要求の振り分け、画面・静的ファイル・API の応答 | `DS-IF-SPIN-SCREEN` [削除]、`DS-IF-MY-WINNINGS-SCREEN` [削除]、`DS-IF-WINNINGS-API` [削除]、`DS-IF-STYLESHEET` [削除] |
| `app/server.py` | `DS-MD-SERVER` | HTTP 要求の振り分け、画面・静的ファイル・API の応答 | `DS-IF-SPIN-SCREEN-NAME-FIELD` [追加]、`DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` [追加]、`DS-IF-WINNINGS-API-WITH-NAME` [追加]、`DS-IF-THEME-STYLESHEET` [追加] |
| `app/database.py` | `DS-MD-DATABASE` | SQLite の表の作成、初期データ、問い合わせ | `DS-FN-LIST-WINNINGS-BY-NAME` [削除] |
| `app/database.py` | `DS-MD-DATABASE` | SQLite の表の作成、初期データ、問い合わせ | `DS-FN-LIST-WINNINGS-WITH-NAME` [追加] |

- 削除した ID を実現していたファイルでも、ファイル自体（`DS-MD-*`）は残る。
- `web/` の HTML・CSS・JavaScript は `DS-MD-*` の対象外（変更なし）。

### 7-3. 対応表の粒度

変更なし（`function`）。

### 7-4. 依存の規則

変更なし。既存設計 `docs/detail_design.md` セクション 7-4 を参照。

### 7-5. コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし（単体・結合・E2E の方針、実行コマンドは同じ）。変更点として、単体テストに「当選記録の取得で名前が返ること」を足す（`DS-FN-LIST-WINNINGS-WITH-NAME` を確かめる）。

### 8-2. E2E テストのシナリオ

次の表で、テストを変える。既存のシナリオ（`DS-TS-SPIN-AND-RECORD`、`DS-TS-REQUIRE-PLAYER-NAME` など）は変えない。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| `DS-TS-THEME-COLORS` [削除] | 削除理由: 配色の設計（`DS-IF-STYLESHEET`）を外すため、このテストも外す。下の新しいテストが引き継ぐ | ― | ― | ― |
| `DS-TS-THEME-IVORY-GREEN` [追加] | 背景 ivory、部品 dark green で、light gray と dark red が無いこと | 初期データ入りの一時 DB で実サーバーが起動している | 1. `/`、`/prizes`、`/my-winnings` を取得 2. `/static/style.css` を取得 3. 各 HTML が stylesheet を読み込むか調べる | 2 のスタイルシートに `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` が無い。1 の 3 画面はすべて `/static/style.css` を読み込む |
| `DS-TS-SPIN-NAME-FIELD` [追加] | 名前の入力欄が Spin ボタンと同じ行にあり、required の属性があること。空の名前は抽選されないこと | 同上 | 1. `/` を取得 2. 名前の入力欄（`player-name`）と Spin ボタン（`spin-button`）が同じ form の中にあり、入力欄に required の属性があるか調べる 3. 名前を空にして `POST /api/spins` を呼ぶ | 2 は両方が `spin-form` の中にあり、入力欄に required がある。3 は 400 で、件数は増えない |
| `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE` [追加] | 当選記録に名前、景品名、当選日時が必ず含まれること | 同上 | 1. `POST /api/spins` を名前「Alice」で呼ぶ 2. `GET /api/winnings?name=Alice` を呼ぶ 3. `/my-winnings` を取得し、表の列の見出しを調べる | 1 の応答の記録に `player_name`、`prize_name`、`won_at` がある。2 の各行に `player_name`、`prize_name`、`won_at` がある。3 の表の見出しは Player、Prize、Date won の順 |

既存の `DS-TS-OWN-WINNINGS-FILTER` は、応答の内容を確かめる項目を増やさない（名前の一致と並び順だけを確かめる）。

### 8-3. E2E の実行手段

変更なし。既存設計 `docs/detail_design.md` セクション 8-3 を参照（HTTP で実サーバーを確かめる。ブラウザは使わない）。

### 8-4. E2E の実行コマンドと運用

変更なし。既存設計 `docs/detail_design.md` セクション 8-4 を参照。テスト関数は `e2e/test_wheel_site.py::WheelSiteTest` のメソッドで、対応表の `DS-TS` の行で結ぶ。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

変更の対応（既存の対応のうち、この変更で変わるものだけ）。要件ごとに見る。変わらない対応は既存設計の表のとおり。

| DS-ID | 対応要件ID |
|---|---|
| `DS-IF-SPIN-SCREEN` [削除] | `RQ-UI-SPIN-SCREEN` [削除] |
| `DS-IF-SPIN-SCREEN-NAME-FIELD` [追加] | `RQ-UI-SPIN-SCREEN`, `RQ-UI-SPIN-NAME-FIELD`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| `DS-IF-MY-WINNINGS-SCREEN` [削除] | `RQ-UI-MY-WINNINGS-SCREEN` [削除] |
| `DS-IF-MY-WINNINGS-SCREEN-WITH-NAME` [追加] | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| `DS-IF-WINNINGS-API` [削除] | `RQ-UI-MY-WINNINGS-SCREEN` [削除]、`RQ-FT-VIEW-OWN-WINNINGS` [削除] |
| `DS-IF-WINNINGS-API-WITH-NAME` [追加] | `RQ-UI-MY-WINNINGS-SCREEN`, `RQ-FT-VIEW-OWN-WINNINGS`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| `DS-IF-STYLESHEET` [削除] | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` [削除] |
| `DS-IF-THEME-STYLESHEET` [追加] | `RQ-UI-IVORY-DARK-GREEN-THEME` |
| `DS-IF-STATIC-ASSETS` [削除] | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` [削除] |
| `DS-IF-STATIC-ASSETS` [追加] | `RQ-UI-IVORY-DARK-GREEN-THEME` |
| `DS-MD-SERVER` [削除] | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` [削除] |
| `DS-MD-SERVER` [追加] | `RQ-UI-IVORY-DARK-GREEN-THEME` |
| `DS-FN-LIST-WINNINGS-BY-NAME` [削除] | `RQ-FT-VIEW-OWN-WINNINGS` [削除] |
| `DS-FN-LIST-WINNINGS-WITH-NAME` [追加] | `RQ-FT-VIEW-OWN-WINNINGS`, `RQ-FT-WINNING-RECORD-DISPLAY` |
| `DS-FN-ADD-WINNING-RECORD` | `RQ-FT-WINNING-RECORD-DISPLAY`（変更なし（既存）。記録の応答に名前と当選日時が既にある） |
| `DS-TS-THEME-COLORS` [削除] | `RQ-TS-THEME-COLORS` [削除] |
| `DS-TS-THEME-IVORY-GREEN` [追加] | `RQ-TS-IVORY-DARK-GREEN-THEME` |
| `DS-TS-SPIN-NAME-FIELD` [追加] | `RQ-TS-SPIN-NAME-FIELD` |
| `DS-TS-RECORD-SHOWS-NAME-PRIZE-DATE` [追加] | `RQ-TS-RECORD-SHOWS-NAME-PRIZE-DATE` |
| `DS-IF-SPINS-API` | `RQ-UI-SPIN-SCREEN`, `RQ-FT-RECORD-WINNING`（変更なし（既存）） |
| `DS-MD-DATABASE` | `RQ-DT-DATABASE-FILE`, `RQ-FT-RECORD-WINNING`（変更なし（既存）） |
| `DS-TS-SPIN-AND-RECORD` | `RQ-TS-SPIN-AND-RECORD`（変更なし（既存）） |
| `DS-TS-REQUIRE-PLAYER-NAME` | `RQ-TS-REQUIRE-PLAYER-NAME`（変更なし（既存）） |
| `DS-TS-OWN-WINNINGS-FILTER` | `RQ-TS-OWN-WINNINGS-FILTER`（変更なし（既存）） |

### 11-1. 除外要件

除外要件は無い。
