# 変更設計書: 配色の変更と 1 投票テーマ 1 ブラウザ 1 票

- 入力: `change_requirements.md`（同じディレクトリ）と正本 `docs/requirements.md`・`docs/detail_design.md`
- 記号: 設計要素は [追加] か [削除] の区分を付ける。中身が変わる要素は旧要素を [削除]、新要素を [追加] に分ける。
- 正本は書き換えない。反映は実装後に isdd-build が行う。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12 の標準ライブラリ、SQLite）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

- [追加] 投票済み記録テーブル `ballots`（DS-SC-BALLOT-TABLE）。投票テーマ × ブラウザ識別子 を 1 件ずつ持つ。
  - ballots: poll_id INTEGER NOT NULL（polls.id への外部キー）、voter_id TEXT NOT NULL（32 桁の 16 進数）、created_at TEXT NOT NULL（UTC の ISO 8601）、主キー (poll_id, voter_id)
- 既存テーブル（polls・options・votes）は変えない（polls・options・votes の各テーブルは変更なし）。
- 既存の DATA_DIR の `polls.db` には `CREATE TABLE IF NOT EXISTS` で `ballots` が足される。既存の票には投票者が無いため、移行は行わない。
- ER 図の追加: `POLLS ||--o{ BALLOTS : "投票済み"`

### 3-2. トランザクションと排他制御

- [追加] 投票の送信は、votes への追加と ballots への追加を 1 トランザクションで行う（DS-FN-RECORD-VOTE-ONCE）。どちらかが失敗したら両方取り消す。
- [追加] 同時送信の排他: ballots の主キー (poll_id, voter_id) の一意制約で、同じブラウザからの同時送信は 1 件だけ成功する。失敗した方は投票済みとして扱う（DS-CL-ALREADY-VOTED-ERROR）。
- 初期データ投入の 1 トランザクションは変更なし。

### 3-3. 状態遷移

変更なし。状態を持つエンティティは無い（投票済みは記録の有無で表す）。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 配色（[追加] DS-IF-COLOR-THEME）

全画面に次の配色を使う。白と navy は使わない。

| 対象 | 色 | 値 |
|---|---|---|
| 背景 | light yellow | `#FFFFE0` |
| 案内メニュー・見出し・ボタン・カードの枠・表の罫線・棒グラフ・通知の背景 | dark slate gray | `#2F4F4F` |
| 部品の上の文字（ボタン、案内メニューのリンク、通知） | 白 | `#FFFFFF` |
| 本文の文字 | 黒寄り | `#1A1A1A` |
| 棒グラフの地（トラック） | 淡い黄 | `#F3F0C8` |
| 無効なボタン | 灰 | `#8A9696` |

- 配色の定義は `src/views.py` の共通の CSS（`render_layout` が埋め込む）に 1 か所だけ置く。

#### 投票済みの判定（[追加] ブラウザ識別子）

- 利用者の区別ではなく、ブラウザの区別。ブラウザが初めて画面を開いたとき、サーバーは 32 桁の乱数 `voter_id` を発行して cookie に入れる（HttpOnly、SameSite=Lax、Path=/、有効期限 1 年）。
- 受け取った cookie の値が 32 桁の 16 進数でなければ、新しい値を発行する（DS-FN-READ-VOTER-COOKIE）。
- 発行したときは、その応答に `Set-Cookie` を付ける（HTML 応答と 302 応答の両方）。

#### 画面と経路の変更

- [追加] 投票画面（DS-IF-POLL-VOTE-PAGE-ONE-VOTE、GET `/polls/<id>`）: そのブラウザが投票済みの投票テーマでは、選択肢のラジオボタンと送信ボタンを無効にし、「You have already voted.」を上部に表示する。結果画面へのリンクを置く。未投票なら従来どおり。
- [追加] 投票の送信（DS-IF-VOTE-SUBMIT-ONE-VOTE、POST `/polls/<id>/vote`）: 投票済みなら票を記録せず、投票画面を 200 で再表示し「You have already voted.」を表示する（直接の POST も同じ）。
- 経路の一覧、結果画面、一覧画面、全体の結果画面は変えない（案内メニューも同じ）。

#### HTTP の応答（変更分）

| 経路 | 入力 | 出力 | エラー仕様 |
|---|---|---|---|
| GET `/polls/<id>` | id、cookie `voter_id` | 200、投票画面（投票済みなら無効化と通知） | 存在しない → 404（変更なし） |
| POST `/polls/<id>/vote` | option_id、cookie `voter_id` | 有効な未投票の送信 → 302 で `/polls/<id>/results?voted=1`（変更なし） | 投票済み → 200、投票画面を再表示し「You have already voted.」。票は増えない。option_id が無効 → 200、「Please select an option.」（変更なし）。存在しない → 404（変更なし） |

- 画面遷移図の追加: 投票画面 → 送信（投票済み）→ 投票画面（無効化）

### 4-2. 内部設計

- 処理フロー（投票の送信、変更分）

  ```mermaid
  graph TD
      A[POST を受ける] --> B{投票テーマが存在するか}
      B -->|無い| N[404 を返す]
      B -->|ある| J{このブラウザは投票済みか}
      J -->|投票済み| E[投票画面を再表示する（投票済み）]
      J -->|未投票| C{選択肢 id が有効か}
      C -->|無効| F[投票画面を再表示する（未選択）]
      C -->|有効| D[投票と投票済み記録を 1 トランザクションで追加する]
      D -->|一意制約違反| E
      D -->|成功| G[結果画面へ 302 で移動する]
  ```

- バッチ設計: 無し。

## 5. クラス設計

- [追加] 例外 `AlreadyVotedError`（DS-CL-ALREADY-VOTED-ERROR）: そのブラウザが投票テーマに投票済みであることを表す。`src/poll_service.py`。
- クラス `PollService` の責務は変えない（DS-CL-POLL-SERVICE）。
- クラス `PollRequestHandler` の責務は変えない（DS-CL-POLL-REQUEST-HANDLER）。

## 6. エラーハンドリングとセキュリティ設計

- [追加] エラーの追加
  | 想定エラー | 利用者への見え方 | ログ | 処理 |
  |---|---|---|---|
  | 投票済みのブラウザが送信した | 200、投票画面、「You have already voted.」 | なし | 票を記録しない |
  | cookie の値が不正 | 新しい識別子を発行し、通常の画面 | なし | 新しい値を cookie に入れる |
- [追加] cookie の扱い: HttpOnly、SameSite=Lax。値は乱数の 32 桁 16 進数だけを受け入れる（それ以外は捨てる）。cookie は認証ではない（投票者の本人確認はしない）。
- 認証・認可・監査ログ: 変更なし（認証は無い。権限の区別は無い）。

## 7. コード設計

- ディレクトリ構成: 変更なし（ファイルは増やさない）。
- 依存の規則: 変更なし。`src/web.py` は `http.cookies`（標準ライブラリ）を使う。
- コーディング規約: 変更なし。

### 7-1. ファイルごとの変更

| ファイル | 区分 | 設計 ID | 内容 |
|---|---|---|---|
| `src/storage.py` | [追加] | `DS-SC-BALLOT-TABLE` | 投票済み記録の表（ballots）の定義を SCHEMA に足す |
| `src/storage.py` | [追加] | `DS-FN-FIND-BALLOT` | 投票テーマ × ブラウザ識別子の投票済みを探す |
| `src/storage.py` | [追加] | `DS-FN-RECORD-VOTE-ONCE` | 投票と投票済み記録を 1 トランザクションで追加する。一意制約違反は投票済みとして扱う |
| `src/storage.py` | [削除] | `DS-FN-INSERT-VOTE` | `record_vote_once` に置き換える（投票済み記録と同じトランザクションで扱うため） |
| `src/poll_service.py` | [追加] | `DS-CL-ALREADY-VOTED-ERROR` | 投票済みを表す例外 |
| `src/poll_service.py` | [追加] | `DS-FN-SERVICE-HAS-VOTED` | 投票済みの判定 |
| `src/poll_service.py` | [追加] | `DS-FN-SERVICE-CAST-VOTE-ONCE` | 投票者を受け取り、投票済みなら拒否して記録する |
| `src/poll_service.py` | [削除] | `DS-FN-SERVICE-CAST-VOTE` | `cast_vote_once` に置き換える（投票者の引数と投票済みの拒否を加えるため） |
| `src/web.py` | [追加] | `DS-FN-READ-VOTER-COOKIE` | cookie からブラウザ識別子を読み、無ければ発行する |
| `src/web.py` | [追加] | `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | 投票済みの投票テーマの投票画面（無効化と通知） |
| `src/web.py` | [追加] | `DS-IF-VOTE-SUBMIT-ONE-VOTE` | 投票済みの送信の応答（票を増やさず、通知を付けて再表示） |
| `src/web.py` | [削除] | `DS-IF-POLL-VOTE-PAGE` | `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` に置き換える（投票済みの状態を扱うため） |
| `src/web.py` | [削除] | `DS-IF-VOTE-SUBMIT` | `DS-IF-VOTE-SUBMIT-ONE-VOTE` に置き換える（投票済みの応答を加えるため） |
| `src/views.py` | [追加] | `DS-IF-COLOR-THEME` | 配色の定義（共通の CSS） |
| `src/views.py` | [追加] | `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | 投票済みの状態を受けて投票画面を作る |
| `src/views.py` | [削除] | `DS-FN-RENDER-VOTE-PAGE` | `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` に置き換える（投票済みの状態を受けるため） |
| `src/app.py` | 変更なし | — | — |

- 変更なしの要素: 経路の振り分け（GET・POST）、サーバーの作成、一覧・結果・全体の結果・案内メニュー・404 の画面の生成、votes テーブル。配色は [追加] の配色の定義の値を使い、共通の枠の関数の役割は変えない。
- 対応表の対応先の変更: votes テーブルの対応先は `insert_vote` から `record_vote_once` に変わる（設計要素は同じ）。

## 8. テスト設計

### 8-1. テストの種類と方針

- 変更なし（単体テストと E2E の方針は既存どおり）。単体テストは `tests/unit/` の既存ファイルを更新する（投票者の引数、投票済みの拒否、配色と投票済みの画面、ballots テーブル）。
- 既存の E2E テストは、cookie を持たない新しいブラウザとして投票する（従来どおり 1 票ずつ数えられる）。

### 8-2. E2E テストのシナリオ（変更分）

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| [追加] `DS-TS-ONE-VOTE-PER-POLL-E2E` | 同じブラウザの 2 回目が数えられない | 起動済み、cookie を保持するブラウザ | 投票テーマ 2 に Go を選んで送信。同じブラウザで投票画面を開く。同じブラウザから直接 POST する。結果画面で合計を見る | 投票画面の選択肢と送信ボタンが無効で「You have already voted.」。直接 POST の応答に「You have already voted.」。合計は 1 回目の後と同じ |
| [追加] `DS-TS-THEME-COLORS-E2E` | 全画面の配色 | 起動済み | `/`、`/polls/1`、`/polls/1/results`、`/results` の応答の CSS を見る | 背景 `#FFFFE0`、部品 `#2F4F4F` があり、`#000080`（navy）と `#FFFFFF` の背景指定が無い |

- 既存の 7 本の E2E は変えない。投票と未選択の送信の 2 本は cookie を持たない新しいブラウザで動くため、そのまま通る。

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし。`PORT`・`DATA_DIR` は既存のまま。`ballots` テーブルは起動時に自動作成される。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

区分の書式: [追加] の行は新しい対応、[削除] の行は旧い対応。既存の設計要素で対応する要件が増える行も [追加] で書く。

| DS-ID | 対応要件ID |
|---|---|
| [追加] `DS-MD-STORAGE` | `RQ-DT-BROWSER-BALLOT`, `RQ-DT-BALLOT`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-MD-POLL-SERVICE` | `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-MD-WEB` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE` |
| [追加] `DS-MD-VIEWS` | `RQ-UI-VOTED-STATE`, `RQ-NF-COLOR-THEME` |
| [追加] `DS-CL-POLL-SERVICE` | `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-CL-POLL-REQUEST-HANDLER` | `RQ-UI-VOTED-STATE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-SC-DATABASE-FILE` | `RQ-DT-BROWSER-BALLOT` |
| [追加] `DS-SC-BALLOT-TABLE` | `RQ-DT-BROWSER-BALLOT`, `RQ-DT-BALLOT`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-FN-FIND-BALLOT` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE` |
| [追加] `DS-FN-RECORD-VOTE-ONCE` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-FT-CAST-VOTE`, `RQ-DT-BROWSER-BALLOT` |
| [追加] `DS-CL-ALREADY-VOTED-ERROR` | `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-FN-SERVICE-HAS-VOTED` | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE` |
| [追加] `DS-FN-SERVICE-CAST-VOTE-ONCE` | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-FN-READ-VOTER-COOKIE` | `RQ-DT-BROWSER-BALLOT` |
| [追加] `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-VOTED-STATE` |
| [追加] `DS-IF-VOTE-SUBMIT-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [追加] `DS-IF-COLOR-THEME` | `RQ-NF-COLOR-THEME` |
| [追加] `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-UI-VOTED-STATE` |
| [追加] `DS-TS-ONE-VOTE-PER-POLL-E2E` | `RQ-TS-ONE-VOTE-PER-POLL` |
| [追加] `DS-TS-THEME-COLORS-E2E` | `RQ-TS-THEME-COLORS` |
| [削除] `DS-FN-INSERT-VOTE` | `RQ-FT-CAST-VOTE` |
| [削除] `DS-FN-SERVICE-CAST-VOTE` | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-EMPTY-VOTE` |
| [削除] `DS-IF-POLL-VOTE-PAGE` | `RQ-UI-POLL-VOTE-SCREEN` |
| [削除] `DS-IF-VOTE-SUBMIT` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN` |
| [削除] `DS-FN-RENDER-VOTE-PAGE` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-REJECT-EMPTY-VOTE` |

#### 11 の既存の行（変更なし）

既存の対応表（`docs/detail_design.md` 第 11 章）の行は、上の [追加] と [削除] で示した行以外は変えない。

### 11-1. 除外要件

除外要件は無い。

## 付録: 依頼に無く決めた項目

変更要件定義書 1-2 のとおり（cookie のブラウザ識別子、投票済みの画面と応答、cookie を消したブラウザの扱い、配色の値）。
