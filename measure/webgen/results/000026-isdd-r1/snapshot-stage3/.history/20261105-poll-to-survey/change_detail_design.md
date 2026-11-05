# 変更設計書: Polls Website（投票サイト）— 画面の用語 poll を survey にする

作成日: 2026-11-05
フロー: 変更（isdd-spec）。変更の記録。正本 `docs/detail_design.md` は書き換えない（反映は実装後レビューで行う）
入力: `.history/20261105-poll-to-survey/change_requirements.md`（変更要件定義書）、正本 `docs/requirements.md`・`docs/detail_design.md`

凡例: 各設計要素に [追加] か [削除] を付ける。中身（URL、画面の文言）だけが変わる既存の要素は、同じ ID を [削除]（旧い内容の行）と [追加]（新しい内容の行）の 2 行に書く。変更の無い章は「変更なし。既存設計 `docs/detail_design.md` セクション[N] を参照」と書く。

---

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、Flask 3.1.3、SQLite）。追加の依存は無い。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

### 3-1. データモデル

変更なし。テーブル名（`polls`、`poll_options`、`votes`、`poll_voters`）と保存先（`DATA_DIR/polls.db`）は変えない（内部名。1-2 の決め事）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。状態を持つエンティティは無い。

---

## 4. アーキテクチャ設計

### 4-1. 外部設計

利用者向けインターフェース（画面と HTTP のルート）。URL の `/polls/` を `/surveys/` に変え、画面の語を変える。ID は変えず、中身が変わる行は [削除]（旧い内容）と [追加]（新しい内容）の 2 行にする。処理（関数）と入出力の形式は変わらない。

| DS-ID | 種類 | URL | 処理（関数） | 入力 | 出力 |
|---|---|---|---|---|---|
| DS-IF-NAVIGATION-MENU [削除] | 共通部品 | 全画面 | `provide_navigation` | 現在の URL（endpoint） | 「Polls」「Results」のリンクと、現在の画面の強調 |
| DS-IF-NAVIGATION-MENU [追加] | 共通部品 | 全画面 | `provide_navigation` | 現在の URL（endpoint） | 「Surveys」「Results」のリンクと、現在の画面の強調。サイト名（ヘッダー）も「Surveys」。文言の変更の理由は RQ-UI-SURVEY-WORDING |
| DS-IF-POLL-LIST-SCREEN [削除] | 画面 | GET `/` | `show_poll_list` | なし | 投票テーマ一覧（HTML）。見出し「Polls」 |
| DS-IF-POLL-LIST-SCREEN [追加] | 画面 | GET `/` | `show_poll_list` | なし | 投票テーマ一覧（HTML）。見出し「Surveys」、説明「Choose a survey to vote, or look at the results.」、無いときは「No surveys yet.」 |
| DS-IF-POLL-DETAIL-SCREEN [削除] | 画面 | GET `/polls/<poll_id>` | `show_poll_detail` | URL の `poll_id`（整数） | 質問文と選択肢のラジオボタン、「Vote」ボタン（HTML）。投票済みの状態は DS-IF-ALREADY-VOTED-STATE |
| DS-IF-POLL-DETAIL-SCREEN [追加] | 画面 | GET `/surveys/<poll_id>` | `show_poll_detail` | URL の `poll_id`（整数） | 質問文と選択肢のラジオボタン、「Vote」ボタン（HTML）。投票済みの状態は DS-IF-ALREADY-VOTED-STATE。URL の語だけが変わる |
| DS-IF-VOTE-SUBMIT-ONCE [削除] | 送信 | POST `/polls/<poll_id>/vote` | `submit_vote` | Cookie `voter_id`（任意）、フォーム `option_id`（整数） | 成功: 303 で `/polls/<poll_id>/results?voted=1` へ移動。投票済み: 409 で詳細画面を再表示し「You have already voted」。未選択・不正・属さない選択肢: 400 で詳細画面を再表示し「Please select one option before you vote.」。いずれも投票者 ID の Cookie を付ける |
| DS-IF-VOTE-SUBMIT-ONCE [追加] | 送信 | POST `/surveys/<poll_id>/vote` | `submit_vote` | Cookie `voter_id`（任意）、フォーム `option_id`（整数） | 成功: 303 で `/surveys/<poll_id>/results?voted=1` へ移動。投票済み・未選択・不正・属さない選択肢の応答は旧い行と同じ（URL の語だけが変わる）。いずれも投票者 ID の Cookie を付ける |
| DS-IF-ALREADY-VOTED-STATE [削除] | 画面の状態 | GET `/polls/<poll_id>`（`show_poll_detail`） | Cookie `voter_id`（任意） | URL の `poll_id` | 投票済みのとき、選択肢のラジオボタンと「Vote」ボタンを無効にし、「You have already voted」を表示する。「View results」は有効のまま |
| DS-IF-ALREADY-VOTED-STATE [追加] | 画面の状態 | GET `/surveys/<poll_id>`（`show_poll_detail`） | Cookie `voter_id`（任意） | URL の `poll_id` | 投票済みのとき、選択肢のラジオボタンと「Vote」ボタンを無効にし、「You have already voted」を表示する。「View results」は有効のまま。URL の語だけが変わる |
| DS-IF-POLL-RESULTS-SCREEN [削除] | 画面 | GET `/polls/<poll_id>/results` | `show_poll_results` | URL の `poll_id`、クエリ `voted`（任意） | 票数・割合・総票数の表（HTML）。`voted=1` のとき「Thank you for voting.」。リンクは「Vote on this poll」「Back to polls」 |
| DS-IF-POLL-RESULTS-SCREEN [追加] | 画面 | GET `/surveys/<poll_id>/results` | `show_poll_results` | URL の `poll_id`、クエリ `voted`（任意） | 票数・割合・総票数の表（HTML）。`voted=1` のとき「Thank you for voting.」。リンクは「Vote on this survey」「Back to surveys」 |
| DS-IF-RESULTS-OVERVIEW-SCREEN [削除] | 画面 | GET `/results` | `show_results_overview` | なし | 全投票テーマの一覧表（HTML）。表の見出し「Poll」、説明「Totals and the leading option for every poll.」、無いときは「No polls yet.」 |
| DS-IF-RESULTS-OVERVIEW-SCREEN [追加] | 画面 | GET `/results` | `show_results_overview` | なし | 全投票テーマの一覧表（HTML）。表の見出し「Survey」、説明「Totals and the leading option for every survey.」、無いときは「No surveys yet.」 |

入力の検証とエラー仕様（既存の表。変更の行だけ）:

| 対象 | 検証 | 失敗時 |
|---|---|---|
| 投票テーマの存在（URL） [削除] | `poll_id` が存在しない | 404（`handle_not_found`。「Not found」画面と「Polls」へのリンク） |
| 投票テーマの存在（URL） [追加] | `poll_id` が存在しない | 404（`handle_not_found`。「Not found」画面と「Surveys」へのリンク） |

外部システム連携: 無し。外部 DB 連携: 無し。

### 4-2. 内部設計

処理フロー（変更なし）。URL の表記だけが `/surveys/` に変わる（4-1）。処理の順序と分岐は既存の設計どおり。

各処理の役割: 変更なし（関数の名前、引数、戻り値は変えない。テンプレートの文言だけを変える）。

バッチ設計: 変更なし。

---

## 5. クラス設計

変更なし。クラスは無い（モジュールの関数だけで構成する）。

---

## 6. エラーハンドリングとセキュリティ設計

### エラーハンドリング

既存の表のうち、文言だけが変わる行（[削除] と [追加] の 2 行）:

| 想定エラー | 利用者への見え方 | ログ | 処理 |
|---|---|---|---|
| 投票テーマが存在しない [削除] | 「Not found」画面（404）と「Polls」へのリンク | 無し | 処理を終える |
| 投票テーマが存在しない [追加] | 「Not found」画面（404）と「Surveys」へのリンク | 無し | 処理を終える |

既存の他の行は変更なし。

### 認証

変更なし（認証は無い）。

### 認可

変更なし。

### 監査ログ

変更なし。無い。

### その他のセキュリティ対策

変更なし。

---

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。新しいファイルは作らない。`src/web/app.py`（URL の規則とナビゲーションの表示名）と `src/web/templates/` の文言（`base.html`、`poll_list.html`、`poll_results.html`、`results_overview.html`、`not_found.html`）を変える。テンプレートのファイル名と変数名（`poll`）は変えない（内部の名前）。

### 7-2. ファイル一覧

変更なし（ファイルの役割と設計 ID の対応は既存のまま。`docs/detail_design.md` 7-2 を参照）。`src/store/db.py` は変えない。

### 7-3. 対応表の粒度

変更なし。`function`。

### 7-4. 依存の規則

変更なし。`scripts/isdd/dependencies.json` は変更しない。

### 7-5. コーディング規約

変更なし。

---

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし（単体テストは `tests/test_store.py` のまま。E2E は `e2e/test_site.py` の文言と URL の期待値を新しい語に合わせ、1 件を追加する）。

### 8-2. E2E テストのシナリオ

要件定義書 7 章の変更分を、1 対 1 で DS-TS にする。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| DS-TS-NAVIGATE-MENU [削除] | （削除）「Polls」のメニューで移ること | — | — | 文言の変更の理由: 「Polls」を「Surveys」に変えるため、同じ ID の行を文言だけ差し替える |
| DS-TS-NAVIGATE-MENU [追加] | どの画面からも「Surveys」「Results」で主要な画面へ移れること（RQ-TS-NAVIGATE-MENU） | 初期データがある | 一覧、詳細、結果、結果一覧の各画面で「Surveys」と「Results」を押す | 押した画面へ移り、現在の画面のメニュー項目が強調される |
| DS-TS-NO-POLL-WORD-IN-UI [追加] | 利用者に見える画面に「poll」の語が無いこと（RQ-TS-NO-POLL-WORD-IN-UI） | 初期データがある（空の DATA_DIR でも入る） | 一覧、詳細、結果、結果一覧、存在しない URL（404）の HTML を取得する。投票した後の結果画面と、投票済みの詳細画面の HTML を取得する。取得した各 HTML に、大文字小文字を問わず `poll` が含まれないことを確かめる | どの HTML にも `poll` が無い。「Surveys」「survey」が使われ、URL は `/surveys/` で始まる |

残りの E2E シナリオ（一覧から詳細へ進む、投票テーマの項目の表示、不正な投票、全結果の一覧、空の DATA_DIR の初期データ、1 回制限、配色）は変更なし。手順の語（「Polls」→「Surveys」、`/polls/` → `/surveys/`）だけを読み替える。既存設計 `docs/detail_design.md` セクション 8-2 を参照。

### 8-3. E2E の実行手段

変更なし。unittest と urllib（標準ライブラリ）で実サーバーに HTTP で問い合わせる。

### 8-4. E2E の実行コマンドと運用

変更なし。

```bash
.venv/bin/python scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml
```

---

## 9. 運用設計

変更なし。`setup.sh`・`run.sh`、環境変数 `PORT`・`DATA_DIR`、保存先 `polls.db` は既存のまま。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

---

## 11. 要件と設計の対応表

変更要件定義書にある既存の要件 ID（変更しない要件）は、既存の設計要素の「変更なし（既存）」の行で受ける。ここには変更の行と、その既存の受け手だけを書く。

| DS-ID | 対応要件ID |
|---|---|
| `DS-IF-NAVIGATION-MENU` [削除] | `RQ-UI-NAVIGATION-MENU` |
| `DS-IF-NAVIGATION-MENU` [追加] | `RQ-UI-NAVIGATION-MENU`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-POLL-LIST-SCREEN` [削除] | `RQ-UI-POLL-LIST-SCREEN`, `RQ-FT-BROWSE-POLLS` |
| `DS-IF-POLL-LIST-SCREEN` [追加] | `RQ-UI-POLL-LIST-SCREEN`, `RQ-FT-BROWSE-POLLS`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-POLL-DETAIL-SCREEN` [削除] | `RQ-UI-POLL-DETAIL-SCREEN`, `RQ-FT-VIEW-POLL-OPTIONS` |
| `DS-IF-POLL-DETAIL-SCREEN` [追加] | `RQ-UI-POLL-DETAIL-SCREEN`, `RQ-FT-VIEW-POLL-OPTIONS`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-VOTE-SUBMIT-ONCE` [削除] | `RQ-UI-POLL-DETAIL-SCREEN`, `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-INVALID-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-ALREADY-VOTED-MESSAGE` |
| `DS-IF-VOTE-SUBMIT-ONCE` [追加] | `RQ-UI-POLL-DETAIL-SCREEN`, `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-INVALID-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-ALREADY-VOTED-MESSAGE`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-ALREADY-VOTED-STATE` [削除] | `RQ-UI-ALREADY-VOTED-MESSAGE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| `DS-IF-ALREADY-VOTED-STATE` [追加] | `RQ-UI-ALREADY-VOTED-MESSAGE`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-POLL-RESULTS-SCREEN` [削除] | `RQ-UI-POLL-RESULTS-SCREEN`, `RQ-FT-VIEW-RESULTS` |
| `DS-IF-POLL-RESULTS-SCREEN` [追加] | `RQ-UI-POLL-RESULTS-SCREEN`, `RQ-FT-VIEW-RESULTS`, `RQ-UI-SURVEY-WORDING` |
| `DS-IF-RESULTS-OVERVIEW-SCREEN` [削除] | `RQ-UI-RESULTS-OVERVIEW-SCREEN`, `RQ-FT-VIEW-ALL-RESULTS` |
| `DS-IF-RESULTS-OVERVIEW-SCREEN` [追加] | `RQ-UI-RESULTS-OVERVIEW-SCREEN`, `RQ-FT-VIEW-ALL-RESULTS`, `RQ-UI-SURVEY-WORDING` |
| `DS-TS-NAVIGATE-MENU` [削除] | `RQ-TS-NAVIGATE-MENU` |
| `DS-TS-NAVIGATE-MENU` [追加] | `RQ-TS-NAVIGATE-MENU` |
| `DS-TS-NO-POLL-WORD-IN-UI` [追加] | `RQ-TS-NO-POLL-WORD-IN-UI` |
| `DS-SC-POLL` 変更なし（既存） | `RQ-DT-POLL` |
| `DS-SC-POLL-OPTION` 変更なし（既存） | `RQ-DT-POLL-OPTION` |
| `DS-MD-STORE` 変更なし（既存） | `RQ-DT-LOCAL-SQLITE-STORAGE` |
| `DS-FN-SEED-SAMPLE-POLLS` 変更なし（既存） | `RQ-DT-SAMPLE-DATA-ON-EMPTY` |
| `DS-FN-HANDLE-NOT-FOUND` 変更なし（既存） | `RQ-UI-SURVEY-WORDING`（404 画面の文言。関数は変えない） |
| `DS-IF-COLOR-THEME` 変更なし（既存） | `RQ-UI-COLOR-THEME` |

### 11-1. 除外要件

除外要件は無い。
