# 変更設計書: 「poll」から「survey」への用語変更（Survey Website）

本書は変更の記録である。正本の `docs/detail_design.md` は書き換えない（実装後に `isdd-build` の実装後レビューが反映する）。
入力要件: 本ディレクトリの `change_requirements.md`。区分は各行の `[追加]` と `[削除]`。
DS-ID は変えない（内部の識別子。画面の用語だけを変える）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、Flask、SQLite のまま）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。構成要素は変えず、画面の文言、URL のパス、旧パスの転送を変える。

## 3. データ設計

### 3-1. データモデル

変更なし。既存設計 `docs/detail_design.md` セクション 3-1 を参照（テーブル `polls`、`options`、`votes` と列名は変えない）。

### 3-2. トランザクションと排他制御

変更なし。既存設計 `docs/detail_design.md` セクション 3-2 を参照。

### 3-3. 状態遷移

変更なし。既存設計 `docs/detail_design.md` セクション 3-3 を参照。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース（GUI）

画面一覧（すべて英語表示。上部のナビゲーションは「Surveys」「Results」）:

| DS-ID | 画面 | パス | 要素と機能 |
|---|---|---|---|
| [削除] `DS-IF-ROOT-REDIRECT` の転送先 | ルート | `GET /` | `/polls` へ 302 |
| [追加] `DS-IF-ROOT-REDIRECT` の転送先 | ルート | `GET /` | `/surveys` へ 302 |
| [削除] `DS-IF-POLL-LIST-SCREEN` | 投票一覧 | `GET /polls` | 見出し「Polls」、案内「Choose a poll to see its options and vote.」、投票テーマごとのカード。投票テーマが無いときは「No polls yet.」 |
| [追加] `DS-IF-POLL-LIST-SCREEN` | 調査一覧 | `GET /surveys` | 見出し「Surveys」、案内「Choose a survey to see its options and vote.」、調査ごとのカード。調査が無いときは「No surveys yet.」 |
| [削除] `DS-IF-POLL-VOTE-SCREEN` | 投票詳細・投票フォーム | `GET /polls/<id>` | パンくず「Polls」、投票済みの案内「You have already voted in this poll.」、結果へのリンク |
| [追加] `DS-IF-POLL-VOTE-SCREEN` | 調査詳細・投票フォーム | `GET /surveys/<id>` | パンくず「Surveys」、投票済みの案内「You have already voted in this survey.」、結果へのリンク「View results」。投票済みのときは選択肢と Vote を disabled にする（既存の動作） |
| [削除] `DS-IF-CAST-VOTE-ACTION` の URL | 投票の受付 | `POST /polls/<id>/vote` | 投票フォームの送信先 |
| [追加] `DS-IF-CAST-VOTE-ACTION` の URL | 投票の受付 | `POST /surveys/<id>/vote` | 投票フォームの送信先。誤りの文言は「The selected option is not valid for this survey.」、投票済みは「You have already voted in this survey.」 |
| [削除] `DS-IF-POLL-RESULTS-SCREEN` | 投票結果 | `GET /polls/<id>/results` | パンくず「Results」、「Vote in this poll」 |
| [追加] `DS-IF-POLL-RESULTS-SCREEN` | 調査結果 | `GET /surveys/<id>/results` | パンくず「Results」、「Vote in this survey」 |
| [削除] `DS-IF-RESULTS-LIST-SCREEN` の案内 | 結果一覧 | `GET /results` | 案内「Select a poll to see its vote counts.」、「No polls yet.」 |
| [追加] `DS-IF-RESULTS-LIST-SCREEN` の案内 | 結果一覧 | `GET /results` | 案内「Select a survey to see its vote counts.」、「No surveys yet.」。リンク先は `/surveys/<id>/results` |
| [追加] `DS-IF-LEGACY-POLL-REDIRECT` | 旧パスの転送 | `GET /polls`、`GET /polls/<path>` | 旧パスを `/surveys` と `/surveys/<path>` へ 302 で転送する（POST は転送しない。旧パスの投票フォームは新しい画面から送られるため）。UI は持たない |

画面の見た目: 変更なし（`DS-IF-COLOR-THEME` の配色は変えない）。
ナビゲーションの見出し: 「Polls」→「Surveys」、サイト名（ブラウザのタイトルと見出し）「Polls Website」→「Survey Website」。

#### インターフェース仕様（入力・バリデーション・出力・エラー）

| DS-ID | 入力とバリデーション | 出力 | エラー仕様 |
|---|---|---|---|
| [追加] `DS-IF-LEGACY-POLL-REDIRECT` | パスの後ろの部分（任意の文字列）をそのまま新しいパスに付ける | 302。Location は `/surveys` または `/surveys/<path>` | 転送先が存在しない場合は、転送先の画面が 404 を返す（既存の挙動） |

業務ルールとの対応: 投票の判定（`DS-FN-HAS-VOTED`、`DS-FN-CAST-VOTE`）と一意制約は変えない。`RQ-FT-LEGACY-POLL-URL` は `DS-IF-LEGACY-POLL-REDIRECT` が実現する。

外部システム連携: 変更なし（無し）。帳票・出力ファイル: 変更なし（無し）。

### 4-2. 内部設計

#### 旧パスの転送（`DS-IF-LEGACY-POLL-REDIRECT`）

[追加] 1. `/polls` で受けたら `/surveys` へ 302 で転送する。
[追加] 2. `/polls/<path>` で受けたら `/surveys/<path>` へ 302 で転送する（`<path>` は変えない）。
[追加] 3. GET だけを受け付ける（POST の旧パスは 405）。

#### 初期化、集計、その他

変更なし。既存設計 `docs/detail_design.md` セクション 4-2 を参照。

### 4-3. 外部システム連携

変更なし（無し）。

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照（クラスは `VoteError` のみ）。`VoteError` の文言（`MESSAGES`）だけを変える。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

変更なし。既存設計 `docs/detail_design.md` セクション 6-1 を参照。エラー文の文言（`polls.py` の `MESSAGES`）は「survey」に変える。

### 6-2. 認証 / 6-3. 認可 / 6-4. 監査ログ / 6-5. その他のセキュリティ対策

変更なし。既存設計 `docs/detail_design.md` セクション 6-2 から 6-5 を参照。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。既存設計 `docs/detail_design.md` セクション 7-1 を参照。

### 7-2. ファイル一覧

| ファイル | 役割 | 含まれるクラス・関数 | 実現する設計 ID |
|---|---|---|---|
| [追加] `src/web.py` | HTTP の画面と投票の受付（旧パスの転送を含む） | 既存の関数に加え `legacy_poll_redirect` | 既存の DS-ID に加え `DS-IF-LEGACY-POLL-REDIRECT` |
| 変更なし `src/polls.py` | 投票テーマの参照・投票・集計 | 既存のまま（`MESSAGES` の文言だけ変える） | `DS-MD-POLLS` 他 |
| 変更なし `src/templates/*.html`、`src/static/style.css`、`src/sample_data.py` | 画面の文言 | 対応表の対象外（既存の方針どおり） | — |

- [追加] 対応表の対象外のファイル: `src/templates/base.html`、`src/templates/poll_list.html`、`poll_detail.html`、`poll_results.html`、`results_list.html`（文言と URL の変更）。DS-MD を付けない。ファイル名は内部のまま変えない。
- 対応表の粒度: `function`（変更なし）。
- 依存の規則: 無い（変更なし）。
- [追加] 関数の追加: `src/web.py::legacy_poll_redirect` の 1 件（対応表に `DS-IF-LEGACY-POLL-REDIRECT` の行を入れる）。

### 7-3. 運用スクリプトの設計

変更なし。既存設計 `docs/detail_design.md` セクション 7-3 を参照。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` セクション 8-1 を参照。[追加] 単体・結合テスト（`tests/test_web.py`）で、旧パスの転送と新しいパスの表示を確かめる。

### 8-2. E2E テストのシナリオ

既存の `DS-TS-*` は、パスと文言を新しいものに読み替える（手順と期待結果は同じ）。新しい行を次のとおり追加する。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| [追加] `DS-TS-VERIFY-SURVEY-WORDING-E2E` | 4 画面に「poll」の語が無く、ナビゲーションが「Surveys」である（`RQ-TS-VERIFY-SURVEY-WORDING`） | 初期データ | `/surveys`、`/surveys/1`、`/surveys/1/results`、`/results` を開き、HTML を検査する。投票済みの詳細（`/surveys/3` に投票した後）も検査する | 各 HTML に `poll`（大文字小文字を問わず）が無い。ナビゲーションに「Surveys」と「Results」がある |
| [追加] `DS-TS-VERIFY-LEGACY-URL-E2E` | 旧パスが新しいパスへ転送される（`RQ-TS-VERIFY-LEGACY-URL`） | 初期データ | `/polls` と `/polls/1/results` を開く | 最終 URL が `/surveys` と `/surveys/1/results` で、200 |

`DS-TS-NAVIGATION-E2E` は、ナビゲーションの見出しを「Surveys」と読み替え、`href="/surveys"` を確かめる。

### 8-3. E2E の実行手段

変更なし。既存設計 `docs/detail_design.md` セクション 8-3 を参照。

### 8-4. E2E の実行コマンドと運用

変更なし。既存設計 `docs/detail_design.md` セクション 8-4 を参照。E2E の起動確認の URL は `/surveys` に変える。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計 `docs/detail_design.md` セクション 10 を参照。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| [追加] `DS-IF-LEGACY-POLL-REDIRECT` | `RQ-FT-LEGACY-POLL-URL` |
| [追加] `DS-IF-POLL-LIST-SCREEN`（URL と文言の変更） | `RQ-UI-POLL-LIST-SCREEN`、`RQ-UI-SURVEY-WORDING`、`RQ-FT-LIST-POLLS` |
| [追加] `DS-IF-POLL-VOTE-SCREEN`（URL と文言の変更） | `RQ-UI-POLL-DETAIL-SCREEN`、`RQ-UI-SURVEY-WORDING`、`RQ-FT-VIEW-POLL-OPTIONS`、`RQ-FT-LOCK-VOTE-CONTROLS` |
| [追加] `DS-IF-POLL-RESULTS-SCREEN`（URL と文言の変更） | `RQ-UI-POLL-RESULTS-SCREEN`、`RQ-UI-SURVEY-WORDING`、`RQ-FT-VIEW-RESULTS` |
| [追加] `DS-IF-RESULTS-LIST-SCREEN`（文言とリンクの変更） | `RQ-UI-RESULTS-LIST-SCREEN`、`RQ-UI-SURVEY-WORDING` |
| [追加] `DS-IF-CAST-VOTE-ACTION`（URL と文言の変更） | `RQ-FT-CAST-VOTE`、`RQ-FT-ONE-VOTE-PER-POLL`、`RQ-FT-VALIDATE-VOTE`、`RQ-UI-SURVEY-WORDING` |
| [追加] `DS-IF-ROOT-REDIRECT`（転送先の変更） | `RQ-UI-POLL-LIST-SCREEN`、`RQ-OP-START-LOCAL`、`RQ-UI-SURVEY-WORDING` |
| [追加] `DS-TS-VERIFY-SURVEY-WORDING-E2E` | `RQ-TS-VERIFY-SURVEY-WORDING` |
| [追加] `DS-TS-VERIFY-LEGACY-URL-E2E` | `RQ-TS-VERIFY-LEGACY-URL` |
| 変更なし（既存） `DS-FN-CAST-VOTE` | `RQ-FT-CAST-VOTE`、`RQ-FT-ONE-VOTE-PER-POLL`、`RQ-FT-VALIDATE-VOTE` |
| 変更なし（既存） `DS-FN-HAS-VOTED` | `RQ-FT-ONE-VOTE-PER-POLL` |
| 変更なし（既存） `DS-FN-GET-VOTER-TOKEN` | `RQ-NF-ANONYMOUS-USE` |
| 変更なし（既存） `DS-MD-WEB` | `RQ-UI-POLL-LIST-SCREEN`、`RQ-UI-POLL-DETAIL-SCREEN`、`RQ-UI-POLL-RESULTS-SCREEN`、`RQ-UI-RESULTS-LIST-SCREEN` |
| 変更なし（既存） `DS-MD-POLLS` | `RQ-FT-CAST-VOTE`、`RQ-FT-VIEW-RESULTS`、`RQ-FT-LIST-POLLS` |
| 変更なし（既存） `DS-TS-NAVIGATION-E2E` | `RQ-TS-NAVIGATION` |
| 変更なし（既存） `DS-IF-COLOR-THEME` | `RQ-UI-COLOR-THEME` |
| 変更なし（既存） `DS-MD-DB` | `RQ-DT-POLL-STORAGE` |

### 11-1. 除外要件

除外要件は無い。
