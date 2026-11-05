# 変更設計書: 景品ルーレット Web サイト（配色の変更、利用者名の必須化、当選履歴への利用者名の表示）

本書は変更要件定義書 `change_requirements.md` を満たす変更の設計。正本 `docs/detail_design.md` は書き換えない。変更は `isdd-build` の実装後レビューで正本へ反映する。
区分: 中身が変わる設計要素は、旧い ID を `[削除]`、新しい ID を `[追加]` で書く。要素は変えず対応だけ変わる行も `[削除]`（旧い対応）と `[追加]`（新しい対応）で書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（技術は引き継ぐ）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。当選記録は既に利用者名（`player_name`）を持ち、テーブルと索引は変えない。

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者向けインターフェース（画面と API）

| 種類 | 設計 ID | 経路 | 役割 |
|---|---|---|---|
| [削除] 画面 | `DS-IF-SPIN-SCREEN` | `/` | 景品ルーレット画面（旧い中身。下の新しい ID に置き換える） |
| [追加] 画面 | `DS-IF-SPIN-SCREEN-NAME-FIELD` | `/` | 景品ルーレット画面（`src/web/static/index.html` と `js/wheel.js`、`styles.css`）。抽選ボタンの横に必須の利用者名欄を置く |
| 画面 | `DS-IF-PRIZES-SCREEN` | `/prizes` | 景品一覧画面（`src/web/static/prizes.html` と `js/prizes.js`、`styles.css`）。中身は変えず、配色だけ `RQ-NF-COLOR-THEME-IVORY-GREEN` に従う |
| [削除] 画面 | `DS-IF-RECORDS-SCREEN` | `/records` | 当選履歴画面（旧い中身。下の新しい ID に置き換える） |
| [追加] 画面 | `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `/records` | 当選履歴画面（`src/web/static/records.html` と `js/records.js`、`styles.css`）。一覧に利用者名の列を加え、利用者名・景品名・当選日時を並べる |
| 画面の配信 | `DS-IF-PAGE-ROUTES` | `/`、`/prizes`、`/records`、`/static/...` | 画面ファイルと静的ファイルを返す（変更なし。対応する要件 ID だけ変わる） |
| API | `DS-IF-PRIZES-API` | GET `/api/prizes` | 景品の一覧（変更なし） |
| API | `DS-IF-SPIN-API` | POST `/api/spin` | 抽選して結果を返す（変更なし。サーバー側の検証は残す） |
| [削除] API | `DS-IF-RECORDS-API` | GET `/api/records` | 利用者名に一致する当選記録の一覧（旧い中身。下の新しい ID に置き換える） |
| [追加] API | `DS-IF-RECORDS-API-WITH-PLAYER` | GET `/api/records` | 利用者名に一致する当選記録の一覧。各要素に利用者名を含む |

画面の共通事項

- [削除] 配色は背景 #D3D3D3（light gray）、ボタン・メニュー・ルーレットの区分の塗りは #8B0000（dark red）、区分の文字は白。
- [追加] 配色は背景 #FFFFF0（ivory）。ボタン、メニュー、見出し帯、表の見出し、パネルの上の枠、検証とエラーの文字は #006400（dark green）。表の地とルーレットの区分の一方は #FFFFFF（白）。ルーレットの区分は dark green と白を交互に使い、区分の文字は塗りと反対の色にする。light gray（#D3D3D3）と dark red（#8B0000）は使わない。
- 文言はすべて英語（変更なし）。
- [追加] 利用者名の規則違反の表示: 景品ルーレット画面では、入力欄の下に規則の文言を出す（規則違反で `DS-IF-SPIN-API` を呼ばない）。当選履歴画面では、一覧の上に規則の文言を出す（変更なし）。

画面ごとの要素（DS-IF の説明）

- [削除] 景品ルーレット画面（旧い中身）: 利用者名の入力欄がルーレットの上にあり、抽選ボタン（Spin）は別の行にある。
- [追加] 景品ルーレット画面（`DS-IF-SPIN-SCREEN-NAME-FIELD`）: 利用者名の入力欄（`name`、必須の入力欄）と抽選ボタン（Spin）を同じ行に並べ、入力欄を抽選ボタンの左隣に置く。入力欄の下に検証の文言の欄を置く。ルーレットの canvas、結果の表示欄は変えない。起動時に景品一覧を `/api/prizes` で取得し、区分を描く。利用者名は `localStorage` のキー `wheel.playerName` に保存し、次回の表示で入れておく。抽選中は抽選ボタンを無効にする。
- 景品一覧画面: 変更なし（中身は同じ。配色だけ変わる）。
- [削除] 当選履歴画面（旧い中身）: 表の列は「当選日時」「景品名」の 2 列。
- [追加] 当選履歴画面（`DS-IF-RECORDS-SCREEN-PLAYER-COLUMN`）: 表の列は「利用者名（Player）」「景品名（Prize）」「当選日時（Won at）」の 3 列。利用者名の入力欄、表示ボタン（Show）、0 件のときの「No winning records yet.」は変えない。

インターフェース仕様

| 設計 ID | 入力と検証 | 出力 | エラー仕様 |
|---|---|---|---|
| `DS-IF-PRIZES-API` | 変更なし | 変更なし | 変更なし |
| `DS-IF-SPIN-API` | 変更なし（利用者名の規則は `RQ-FT-PLAYER-NAME-REQUIRED`） | 変更なし | 変更なし。サーバーは規則違反を 400 で返し、記録を残さない |
| [削除] `DS-IF-RECORDS-API` | クエリの `player_name`。規則に合わないと 400 | 200 で当選記録の配列。各要素は id、prize_name、won_at。新しい順 | 規則違反は 400 と利用者名の文言。想定外の失敗は 500 |
| [追加] `DS-IF-RECORDS-API-WITH-PLAYER` | クエリの `player_name`。規則に合わないと 400（検証は変更なし） | 200 で当選記録の配列。各要素は id、player_name、prize_name、won_at。`player_name` は検証済みの利用者名（記録の利用者名と同じ値）。新しい順（変更なし） | 規則違反は 400 と利用者名の文言。想定外の失敗は 500（変更なし） |

- 画面の配信（`DS-IF-PAGE-ROUTES`）: 変更なし。

帳票・出力ファイル: 無し（変更なし）。外部システム連携: 無し（変更なし）。

### 4-2. 内部設計

処理フロー（抽選）: 変更なし。既存設計 `docs/detail_design.md` 4-2 の図のとおり。

- [追加] 画面の抽選の開始（`DS-FN-START-SPIN-WITH-NAME-CHECK`）: 抽選ボタンが押されたら、利用者名の入力欄の値を前後の空白を除いて検査する。1〜20 文字でなければ、入力欄の下に「Please enter a name of 1 to 20 characters.」を出し、ルーレットを回さず、`/api/spin` を呼ばない。規則どおりなら `/api/spin` を呼ぶ（既存の流れ）。
- [追加] 当選履歴の取り出し（`WheelService.list_records` の出力）: 利用者名で一致する記録を取り出す。取り出した各記録に、検証済みの利用者名を `player_name` として付ける。記録の利用者名は絞り込みの値と完全に同じなので、保存の表と読み取りの処理は変えない。
- バッチ: 無し。

## 5. クラス設計

変更なし。`WheelService`（`DS-CL-WHEEL-SERVICE`）は `list_records` の出力に利用者名を加えるが、クラスの責務は変わらない（出力の項目は 4-1 の `DS-IF-RECORDS-API-WITH-PLAYER` で定める）。`RecordRepository`（`DS-CL-RECORD-REPOSITORY`）は変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照。ただし、画面に出す利用者名は引き続き `escapeHtml` で必ずエスケープする（`DS-FN-ESCAPE-HTML`）。新しく出す `player_name` も同じ扱いにする。

## 7. コード設計

ファイルの一覧（変更する行だけ書く。変更の無いファイルは既存設計 7 を参照）

| ファイル | 役割 | 含まれるクラス・関数（設計 ID） | 実現する設計 ID |
|---|---|---|---|
| `src/web/api.py` | 3 つの API の処理（要求から応答まで） | `handle_list_prizes`、`handle_spin` | `DS-MD-API-HANDLERS`、`DS-IF-PRIZES-API`、`DS-IF-SPIN-API`（変更なし） |
| `src/web/api.py` | 当選履歴の API の処理 | `handle_list_records` | [削除] `DS-IF-RECORDS-API` |
| `src/web/api.py` | 当選履歴の API の処理（利用者名を含む項目） | `handle_list_records` | [追加] `DS-IF-RECORDS-API-WITH-PLAYER` |
| `src/web/static/js/wheel.js` | 景品ルーレット画面の処理（ルーレットの描画、区分の文字、回転） | `drawSegmentLabel`、`animateWheelTo` | `DS-MD-WHEEL-JS`、`DS-FN-DRAW-SEGMENT-LABEL`、`DS-FN-ANIMATE-WHEEL-TO`（変更なし） |
| `src/web/static/js/wheel.js` | 景品ルーレット画面の画面と処理（旧い中身） | `initSpinPage`、`startSpin`、`drawWheel` | [削除] `DS-IF-SPIN-SCREEN`、[削除] `DS-FN-START-SPIN`、[削除] `DS-FN-DRAW-WHEEL` |
| `src/web/static/js/wheel.js` | 景品ルーレット画面の画面と処理（名前の検査、配色） | `initSpinPage`、`startSpin`、`drawWheel` | [追加] `DS-IF-SPIN-SCREEN-NAME-FIELD`、[追加] `DS-FN-START-SPIN-WITH-NAME-CHECK`、[追加] `DS-FN-DRAW-WHEEL-THEMED` |
| `src/web/static/js/records.js` | 当選履歴画面の処理 | `initRecordsPage`、`loadRecords` | `DS-MD-RECORDS-JS`（変更なし） |
| `src/web/static/js/records.js` | 当選履歴画面の処理（旧い中身） | `initRecordsPage`、`loadRecords` | [削除] `DS-IF-RECORDS-SCREEN`、[削除] `DS-FN-LOAD-RECORDS` |
| `src/web/static/js/records.js` | 当選履歴画面の処理（利用者名の列） | `initRecordsPage`、`loadRecords` | [追加] `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN`、[追加] `DS-FN-LOAD-RECORDS-WITH-PLAYER` |
| `src/web/static/styles.css` と HTML | 3 画面の配色と表（対応表の対象外。設計 ID は画面の DS-IF に含める） | 配色のクラス | 対象外（画面の DS-IF で受ける） |

- 依存の規則（第 7 章の表）: 変更なし。`scripts/isdd/dependencies.json` も変えない。
- コーディング規約: 変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` 8-1 のとおり。ただし、当選履歴の取り出し（利用者名を付けた記録）を単体テストで確かめる（`tests/unit/test_integration.py`）。

### 8-2. E2E テストのシナリオ

変更されるシナリオだけ書く。変更の無いシナリオ（`DS-TS-SPIN-AND-RECORD-E2E`、`DS-TS-VIEW-PRIZES-E2E`、`DS-TS-SEED-DATA-E2E`）は既存設計 8-2 のまま。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| [削除] `DS-TS-NAME-VALIDATION-E2E` | 利用者名の規則違反（旧い中身） | 同上 | 空、空白だけ、21 文字の名前で抽選する | 3 回とも 400 と規則の文言。履歴は増えない |
| [追加] `DS-TS-SPIN-NAME-REQUIRED-E2E` | 利用者名の必須（サーバーの検証と、画面の入力欄の配置） | 同上 | 1. 空、空白だけ、21 文字の名前を `/api/spin` に送る。2. `/` の HTML を取得し、利用者名の入力欄（`id="player-name"`）と抽選ボタン（`id="spin-button"`）が同じ行（同じ `inline-form` の中）にあることを見る。3. `wheel.js` に規則の検査（1 と 20 の文字数）があることを見る | 1. は 3 回とも 400 と規則の文言、履歴は増えない。2. と 3. は、入力欄と抽選ボタンが同じ行にあり、画面の検査の処理がある |
| [削除] `DS-TS-VIEW-OWN-RECORDS-E2E` | 利用者名による絞り込み（旧い中身） | 「Sample Player」の初期記録 | `/api/records` を「Sample Player」と「Nobody Here」で呼ぶ | 前者は 2 件で新しい順。後者は空の配列 |
| [追加] `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | 利用者名による絞り込みと、各記録の利用者名 | 「Sample Player」の初期記録 | `/api/records` を「Sample Player」と「Nobody Here」で呼ぶ。`/records` の HTML を取得する | 前者は 2 件で新しい順。各要素の `player_name` は「Sample Player」。後者は空の配列。`/records` の表に「Player」「Prize」「Won at」の見出しがある |
| [削除] `DS-TS-NAVIGATION-E2E` | 画面の配信、メニュー、配色と英語（旧い中身） | 同上 | `/`、`/prizes`、`/records` を取得し、メニューの 3 つの項目と CSS の色を確かめる | 3 画面にメニューのリンク（`/`、`/prizes`、`/records`）があり、`styles.css` に `#D3D3D3` と `#8B0000` がある |
| [追加] `DS-TS-NAVIGATION-THEME-E2E` | 画面の配信、メニュー、配色（ivory と dark green）と英語 | 同上 | `/`、`/prizes`、`/records` を取得し、メニューの 3 つの項目を確かめる。`styles.css` の色を確かめる | 3 画面にメニューのリンク（`/`、`/prizes`、`/records`）がある。`styles.css` に `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` は無い |

- 外部連携が無いため、モードは設けない（変更なし）。

### 8-3. E2E の実行手段

変更なし（標準ライブラリの `unittest` と `urllib`。ブラウザ自動化は使わない）。

### 8-4. E2E の実行コマンドと運用

変更なし。`python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

この表には、[削除] と [追加] の行に加えて、変更しない既存の設計 ID が変更要件の要件 ID を受ける行を「変更なし（既存）」の区分で書く（正本の対応をそのまま写す）。ここに無い既存の対応は正本のまま有効。

| DS-ID | 対応要件ID |
|---|---|
| 変更なし（既存） `DS-MD-WHEEL-JS` | `RQ-FT-SPIN-WHEEL`, `RQ-UI-SPIN-SCREEN` |
| 変更なし（既存） `DS-MD-WHEEL-SERVICE` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-DRAW-BY-WEIGHT`, `RQ-FT-RECORD-WINNING`, `RQ-FT-MISS-NOT-RECORDED` |
| 変更なし（既存） `DS-MD-API-HANDLERS` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-VIEW-OWN-RECORDS`, `RQ-FT-LIST-PRIZES` |
| 変更なし（既存） `DS-CL-WHEEL-SERVICE` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-RECORD-WINNING`, `RQ-FT-MISS-NOT-RECORDED` |
| 変更なし（既存） `DS-CL-RECORD-REPOSITORY` | `RQ-FT-RECORD-WINNING`, `RQ-FT-VIEW-OWN-RECORDS`, `RQ-DT-WINNING-RECORD-ENTITY` |
| 変更なし（既存） `DS-FN-DRAW-SEGMENT-LABEL` | `RQ-FT-SPIN-WHEEL` |
| 変更なし（既存） `DS-FN-ANIMATE-WHEEL-TO` | `RQ-FT-SPIN-WHEEL` |
| 変更なし（既存） `DS-FN-ESCAPE-HTML` | `RQ-FT-LIST-PRIZES`, `RQ-FT-VIEW-OWN-RECORDS` |
| 変更なし（既存） `DS-IF-PRIZES-API` | `RQ-FT-LIST-PRIZES` |
| 変更なし（既存） `DS-IF-SPIN-API` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-RECORD-WINNING` |
| 変更なし（既存） `DS-TS-SPIN-AND-RECORD-E2E` | `RQ-TS-SPIN-AND-RECORD` |
| 変更なし（既存） `DS-TS-VIEW-PRIZES-E2E` | `RQ-TS-VIEW-PRIZES` |
| 変更なし（既存） `DS-TS-SEED-DATA-E2E` | `RQ-TS-SEED-DATA` |
| [削除] `DS-IF-SPIN-SCREEN` | `RQ-UI-SPIN-SCREEN`, `RQ-NF-COLOR-THEME`, `RQ-NF-ENGLISH-UI` |
| [追加] `DS-IF-SPIN-SCREEN-NAME-FIELD` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-SPIN-NAME-FIELD`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |
| [削除] `DS-FN-START-SPIN` | `RQ-FT-SPIN-WHEEL` |
| [追加] `DS-FN-START-SPIN-WITH-NAME-CHECK` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-PLAYER-NAME-REQUIRED`, `RQ-UI-SPIN-NAME-FIELD` |
| [削除] `DS-FN-DRAW-WHEEL` | `RQ-FT-SPIN-WHEEL` |
| [追加] `DS-FN-DRAW-WHEEL-THEMED` | `RQ-FT-SPIN-WHEEL`, `RQ-NF-COLOR-THEME-IVORY-GREEN` |
| [削除] `DS-IF-RECORDS-SCREEN` | `RQ-UI-MY-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME`, `RQ-NF-ENGLISH-UI` |
| [追加] `DS-IF-RECORDS-SCREEN-PLAYER-COLUMN` | `RQ-UI-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |
| [削除] `DS-FN-LOAD-RECORDS` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-FN-LOAD-RECORDS-WITH-PLAYER` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-IF-RECORDS-API` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-IF-RECORDS-API-WITH-PLAYER` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-MD-COMMON-JS` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-MD-COMMON-JS` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-MD-RECORDS-JS` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-MD-RECORDS-JS` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-IF-PRIZES-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-NF-COLOR-THEME`, `RQ-NF-ENGLISH-UI` |
| [追加] `DS-IF-PRIZES-SCREEN` | `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |
| [削除] `DS-IF-PAGE-ROUTES` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-IF-PAGE-ROUTES` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-TS-NAME-VALIDATION-E2E` | `RQ-TS-NAME-VALIDATION` |
| [追加] `DS-TS-SPIN-NAME-REQUIRED-E2E` | `RQ-TS-NAME-VALIDATION`, `RQ-FT-PLAYER-NAME-REQUIRED`, `RQ-UI-SPIN-NAME-FIELD` |
| [削除] `DS-TS-VIEW-OWN-RECORDS-E2E` | `RQ-TS-VIEW-OWN-RECORDS` |
| [追加] `DS-TS-VIEW-RECORDS-WITH-PLAYER-E2E` | `RQ-TS-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` |
| [削除] `DS-TS-NAVIGATION-E2E` | `RQ-TS-NAVIGATION`, `RQ-NF-COLOR-THEME`, `RQ-NF-ENGLISH-UI` |
| [追加] `DS-TS-NAVIGATION-THEME-E2E` | `RQ-TS-NAVIGATION`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` |

### 11-1. 除外要件

除外要件は無い。
