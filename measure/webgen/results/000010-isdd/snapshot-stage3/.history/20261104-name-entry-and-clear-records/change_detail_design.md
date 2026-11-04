# 変更設計書: 利用者名の表示と抽選記録の一括削除

作成日: 2026-11-04。フロー: 変更。対応する変更要件定義書: `change_requirements.md`（同じディレクトリ）。対応する正本: `docs/detail_design.md`（正本は書き換えない）。
画面の文言は英語（要件 `RQ-NF-ENGLISH-UI`）。設計書の本文は日本語で書く。

区分の書き方: 要素の中身が変わるものは旧 ID を [削除]、新 ID を [追加] にする。ファイル単位の ID（`DS-MD-*`）は 7-2 のファイル一覧と 1 対 1 で、ファイルの中身が変わっても ID は変えない。変えない要素は「変更なし（既存）」と書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、標準ライブラリの `http.server`、SQLite、HTML・CSS・素の JavaScript）。

## 2. システム構成

### 2-1. コンポーネント一覧

変更なし。

### 2-2. システム全体構成図

変更なし。

### 2-3. 各コンポーネントの役割

変更なし。

### 2-4. インターフェースとデータフロー

変更あり。My Records 画面から `DELETE /api/records` を呼び、抽選記録を全件削除する経路を加える。

### ネットワーク構成図

変更なし。

## 3. データ設計

### 3-1. データモデル

変更なし。`spin_record` は既に `player_name`・`prize_name`・`spun_at` を持つ。テーブルの項目と索引は変えない。

### 3-2. トランザクションと排他制御

変更なし。一括削除は 1 つの `DELETE` 文（1 トランザクション）で行う。

### 3-3. 状態遷移

変更なし。

### 3-4. 景品の追加の扱い（データ項目）

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース

変更あり。

| DS-ID | 種類 | 内容 |
|---|---|---|
| [削除] DS-IF-RECORDS-API | Web API | `GET /api/records?player_name=` 利用者名の抽選記録を返す（旧内容。記録に利用者名が無い） |
| [追加] DS-IF-RECORDS-WITH-NAME-API | Web API | `GET /api/records?player_name=` 利用者名の抽選記録を返す。各記録に利用者名を含める |
| [追加] DS-IF-CLEAR-RECORDS-API | Web API | `DELETE /api/records` すべての抽選記録を削除する |

（上記以外の利用者向けインターフェースは変更なし）

#### インターフェース仕様

**DS-IF-RECORDS-WITH-NAME-API（GET /api/records?player_name=）**

| 項目 | 内容 |
|---|---|
| 入力 | クエリの `player_name`（文字列） |
| 入力のバリデーション | 変更なし。`DS-FN-VALIDATE-PLAYER-NAME` で確かめる。空白だけ、未指定、31 文字以上は不正 |
| 出力（200） | `records` の配列。各要素は `id`・`player_name`・`prize_name`・`spun_at`。`spun_at` の新しい順。該当が無いときは空の配列 |
| エラー 400 | 利用者名が不正。`error` に `Please enter your name` を返す（変更なし） |

**DS-IF-CLEAR-RECORDS-API（DELETE /api/records）**

| 項目 | 内容 |
|---|---|
| 入力 | なし。利用者名で絞らず、すべての抽選記録を対象にする |
| 入力のバリデーション | なし |
| 出力（200） | `deleted`（削除した抽選記録の件数。0 件でもよい） |
| 景品 | 景品（`prize` 表）は消さない |
| エラー 500 | 削除に失敗。`error` に `Something went wrong. Please try again.` を返す |

API の共通: 応答は JSON（UTF-8）。`/api/records` は `GET`（一覧）と `DELETE`（一括削除）を受け、それ以外の組み合わせは 404。`/api/spin`・`/api/prizes`・`/api/prizes/{id}` の扱いは変えない。

### 4-2. 内部設計

#### 抽選記録の一括削除の処理フロー

1. My Records 画面で Clear records を押す。
2. ブラウザの確認ダイアログ（`window.confirm`、文言 `Delete all winning records? This cannot be undone.`）を出す。Cancel なら何もせず終わる（記録も表も変えない）。
3. OK なら `DELETE /api/records` を送る。
4. 200 なら、記録の表を空にし、成功の文言「All winning records were deleted.」を表示する。入力欄の利用者名は残す。
5. 失敗（通信失敗、500）なら、My Records のエラー欄に `Something went wrong. Please try again.` を表示し、表は変えない。

サーバー側は `handle_clear_records` が `delete_all_records` を呼び、件数を返す。

#### 抽選記録の表の描き方

My Records の検索が成功したとき、`DS-FN-RENDER-RECORDS` が記録の配列から表を描く。列は利用者名・景品名・抽選日時（`toLocaleString("en-US")`）の順。

#### 各処理の役割

| 処理 | 役割 | 変更 |
|---|---|---|
| `find_records_by_name` | 利用者名が完全一致する記録を新しい順に返す。返す項目に `player_name` を加える | 変更あり |
| `delete_all_records` | `spin_record` の全件を削除し、件数を返す | 追加 |
| `handle_records` | 利用者名を検証して記録を返す | 変更なし（返す中身が増えるだけ） |
| `handle_clear_records` | `DELETE /api/records` を受け、全件削除の結果を返す | 追加 |
| `renderRecords` | 記録の表を描く（利用者名・景品名・日時） | 追加（既存の検索の処理から切り出す） |
| `clearRecords` | 確認、`DELETE /api/records`、表と文言の更新 | 追加 |

#### 景品の追加と削除の処理フロー

変更なし。

#### 景品の追加の業務ルール

変更なし。

#### バッチ設計

変更なし。

## 5. クラス設計

変更なし。クラスは無い（関数の分割のみ）。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

変更あり。`DELETE /api/records` の例外は 500 と `Something went wrong. Please try again.` を返す。想定外の例外は既存の `do_DELETE` の共通処理で 500 `Internal error` を返す。

### 6-2. 認証と認可

変更なし。認証は無い（`RQ-NF-PUBLIC-NO-AUTH`）。誰でも全件を削除できる点は、依頼の範囲で受け入れる。

### 6-3. 監査ログ

変更なし。

### 6-4. その他のセキュリティ対策

変更なし。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。

### 7-2. ファイル一覧

変更あり（含まれる要素の行を変える。ファイルの ID は変えない）。

| ファイル | 役割 | 含まれる要素の変更 | DS-ID |
|---|---|---|---|
| `app/server.py` | 経路の判定、JSON API、静的ファイルの配信 | [追加] `handle_clear_records`（`DELETE /api/records`）。`do_DELETE` の振り分けに `/api/records` を加える | `DS-MD-SERVER`（変更なし） |
| `app/repository.py` | 景品の一覧・追加・削除、抽選記録の追加・検索・全件削除 | `find_records_by_name` の項目に `player_name` を加える（DS-FN-FIND-RECORDS-WITH-NAME）。`delete_all_records` を新しく加える（DS-FN-DELETE-ALL-RECORDS） | `DS-MD-REPOSITORY`（変更なし） |
| `app/validation.py` | 利用者名と景品名の検証 | 変更なし | `DS-MD-VALIDATION`（変更なし） |
| `app/db.py` | 変更なし | 変更なし | `DS-MD-DB`（変更なし） |
| `static/index.html` | 共通メニュー、4 つの画面の枠 | 変更あり（My Records 画面の表に利用者名の列、Clear records ボタン、成功の文言の欄） | `DS-MD-INDEX-HTML`（変更なし） |
| `static/app.js` | 画面の切り替え、抽選、景品の管理、記録の検索と表示 | 変更あり（記録の表の描き方を `renderRecords` に切り出す。`clearRecords` を加える） | `DS-MD-APP-JS`（変更なし） |
| `tests/test_units.py` | 単体テスト | 変更あり（記録の項目、全件削除、`DELETE /api/records` の応答を確かめる） | 対応表の対象外（テスト用） |
| `e2e/test_e2e.py` | E2E テスト | 変更あり（記録の表の列、利用者名の必須、一括削除を確かめる） | 対応表の `DS-TS-*` 行 |

### 7-3. コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。単体テストと E2E テスト（実サーバー、HTTP と実ブラウザ相当の操作）。

### 8-2. E2E テストのシナリオ

変更あり。

| DS-ID | テスト関数（`e2e/test_e2e.py::E2EScenarios`） | 対応要件 |
|---|---|---|
| [削除] DS-TS-SPIN-AND-RECORD-E2E | `test_spin_and_record` | 旧 `RQ-TS-SPIN-AND-RECORD` |
| [追加] DS-TS-SPIN-AND-RECORD-V2-E2E | `test_spin_and_record`（記録の表の列を確かめる） | `RQ-TS-SPIN-AND-RECORD-V2` |
| [削除] DS-TS-VALIDATE-PLAYER-NAME-E2E | `test_validate_player_name` | 旧 `RQ-TS-VALIDATE-PLAYER-NAME` |
| [追加] DS-TS-VALIDATE-PLAYER-NAME-V2-E2E | `test_validate_player_name`（回す前の必須と検索の空欄を確かめる） | `RQ-TS-VALIDATE-PLAYER-NAME-V2` |
| [削除] DS-TS-VIEW-OWN-RECORDS-E2E | `test_view_own_records` | 旧 `RQ-TS-VIEW-OWN-RECORDS` |
| [追加] DS-TS-VIEW-OWN-RECORDS-V2-E2E | `test_view_own_records`（各行に利用者名が出ることを確かめる） | `RQ-TS-VIEW-OWN-RECORDS-V2` |
| [追加] DS-TS-CLEAR-RECORDS-E2E | `test_clear_records` | `RQ-TS-CLEAR-RECORDS` |

（上記以外のテストは変更なし）

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし。

### 9-1 〜 9-6

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

変更の行は、旧い対応を [削除]、新しい対応を [追加] で書く。1 行に [追加] と [削除] を同時に書かない。変更なしの行は書かない（既存の `docs/detail_design.md` 第 11 章のまま）。

| DS-ID | 対応要件ID |
|---|---|
| [削除] `DS-MD-SERVER` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-MD-SERVER` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-FT-CLEAR-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [削除] `DS-MD-REPOSITORY` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-DT-STORAGE-SQLITE-RETENTION` |
| [追加] `DS-MD-REPOSITORY` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-FT-CLEAR-RECORDS`, `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-MD-DB` | `RQ-DT-STORAGE-SQLITE-RETENTION` |
| [追加] `DS-MD-DB` | `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-MD-VALIDATION` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-MD-VALIDATION` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-FT-SPIN-REQUIRES-NAME` |
| [削除] `DS-MD-INDEX-HTML` | `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-MD-INDEX-HTML` | `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [削除] `DS-MD-APP-JS` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-MD-APP-JS` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-FT-CLEAR-RECORDS`, `RQ-FT-SPIN-REQUIRES-NAME`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [削除] `DS-FN-FIND-RECORDS-BY-NAME` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-FN-FIND-RECORDS-WITH-NAME` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME` |
| [削除] `DS-FN-VALIDATE-PLAYER-NAME` | `RQ-FT-VIEW-OWN-RECORDS` |
| [追加] `DS-FN-VALIDATE-PLAYER-NAME` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-FT-SPIN-REQUIRES-NAME` |
| [追加] `DS-FN-HANDLE-SPIN` | `RQ-FT-SPIN-REQUIRES-NAME` |
| [追加] `DS-FN-DRAW-PRIZE` | `RQ-FT-DRAW-UNIFORM-PRIZE` |
| [追加] `DS-FN-INSERT-SPIN-RECORD` | `RQ-FT-RECORD-WIN` |
| [追加] `DS-MD-DRAW` | `RQ-FT-DRAW-UNIFORM-PRIZE` |
| [追加] `DS-MD-APP-JS` | `RQ-FT-SPIN-WHEEL` |
| [追加] `DS-FN-HANDLE-SPIN` | `RQ-FT-SPIN-WHEEL`, `RQ-FT-RECORD-WIN` |
| [追加] `DS-MD-INDEX-HTML` | `RQ-UI-SPIN-SCREEN`, `RQ-UI-NAVIGATION-MENU-WITH-MANAGE`, `RQ-UI-MANAGE-PRIZES-SCREEN` |
| [追加] `DS-FN-LIST-PRIZES` | `RQ-FT-LIST-PRIZES` |
| [追加] `DS-IF-PRIZES-API` | `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-FT-WHEEL-FOLLOWS-PRIZES` |
| [追加] `DS-FN-INSERT-PRIZE` | `RQ-FT-ADD-PRIZE` |
| [追加] `DS-FN-DELETE-PRIZE` | `RQ-FT-REMOVE-PRIZE` |
| [追加] `DS-FN-SHOW-VIEW-AND-RELOAD` | `RQ-FT-WHEEL-FOLLOWS-PRIZES`, `RQ-UI-NAVIGATION-MENU-WITH-MANAGE` |
| [追加] `DS-FN-RENDER-MANAGE-PRIZES` | `RQ-UI-MANAGE-PRIZES-SCREEN`, `RQ-FT-REMOVE-PRIZE` |
| [削除] `DS-FN-REMEMBER-PLAYER-NAME` | `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-FN-REMEMBER-PLAYER-NAME` | `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [追加] `DS-FN-DELETE-ALL-RECORDS` | `RQ-FT-CLEAR-RECORDS`, `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [追加] `DS-FN-HANDLE-CLEAR-RECORDS` | `RQ-FT-CLEAR-RECORDS` |
| [追加] `DS-FN-RENDER-RECORDS` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [追加] `DS-FN-CLEAR-RECORDS` | `RQ-FT-CLEAR-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [削除] `DS-FN-OPEN-DATABASE` | `RQ-DT-STORAGE-SQLITE-RETENTION` |
| [追加] `DS-FN-OPEN-DATABASE` | `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-FN-DELETE-PRIZE` | `RQ-DT-STORAGE-SQLITE-RETENTION` |
| [追加] `DS-FN-DELETE-PRIZE` | `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-SC-SPIN-RECORD-TABLE` | `RQ-DT-STORAGE-SQLITE-RETENTION` |
| [追加] `DS-SC-SPIN-RECORD-TABLE` | `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-IF-RECORDS-API` | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN` |
| [追加] `DS-IF-RECORDS-WITH-NAME-API` | `RQ-FT-VIEW-OWN-RECORDS-WITH-NAME`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR` |
| [追加] `DS-IF-CLEAR-RECORDS-API` | `RQ-FT-CLEAR-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN-CLEAR`, `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` |
| [削除] `DS-TS-SPIN-AND-RECORD-E2E` | `RQ-TS-SPIN-AND-RECORD` |
| [追加] `DS-TS-SPIN-AND-RECORD-V2-E2E` | `RQ-TS-SPIN-AND-RECORD-V2` |
| [削除] `DS-TS-VALIDATE-PLAYER-NAME-E2E` | `RQ-TS-VALIDATE-PLAYER-NAME` |
| [追加] `DS-TS-VALIDATE-PLAYER-NAME-V2-E2E` | `RQ-TS-VALIDATE-PLAYER-NAME-V2` |
| [削除] `DS-TS-VIEW-OWN-RECORDS-E2E` | `RQ-TS-VIEW-OWN-RECORDS` |
| [追加] `DS-TS-VIEW-OWN-RECORDS-V2-E2E` | `RQ-TS-VIEW-OWN-RECORDS-V2` |
| [追加] `DS-TS-CLEAR-RECORDS-E2E` | `RQ-TS-CLEAR-RECORDS` |

### 11-1. 除外要件

除外要件は無い。

### 要件の対応の補足

- `RQ-FT-SPIN-REQUIRES-NAME` は、既存の入力検証（`DS-FN-VALIDATE-PLAYER-NAME`、サーバーの `DS-FN-HANDLE-SPIN` で確かめる）と、画面の入力欄の必須（`DS-MD-APP-JS` の抽選の処理）で実現する。既存の動作の明文化であり、新しい検証の処理は増やさない。
- `RQ-FT-CLEAR-RECORDS` の確認は、ブラウザの `window.confirm` を使う（DS-FN-CLEAR-RECORDS）。確認の画面は作らない。
- `RQ-DT-STORAGE-SQLITE-RETENTION-CLEAR` の「景品を消しても抽選記録は残す」は、景品の削除（`DS-FN-DELETE-PRIZE`）が記録の表に触れないことで保つ（変更なし）。
