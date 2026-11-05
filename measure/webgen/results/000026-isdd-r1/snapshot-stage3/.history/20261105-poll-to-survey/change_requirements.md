# 変更要件定義書: Polls Website（投票サイト）— 画面の用語 poll を survey にする

作成日: 2026-11-05
フロー: 変更（isdd-spec）。変更の記録。正本 `docs/requirements.md` は書き換えない（反映は実装後レビューで行う）
入力: `REQUEST.md`（変更依頼 2）、`contract.md`、`ANSWERS.md`（ヒアリングへの固定回答）、正本 `docs/requirements.md`、前回の変更 `.history/20261105-theme-and-one-vote/`（正本へ反映済み）

凡例: 各要件項目に [追加] か [削除] を付ける。中身だけが変わる既存の要件は、同じ ID を [削除]（旧い文言の行）と [追加]（新しい文言の行）の 2 行に書く。変更の無い章・節は「変更なし。既存要件定義書 `docs/requirements.md` セクション[N] を参照」と書く。

---

## 1. 目的・前提

### 目的

依頼 2 は、既存の変更ではなく文言の変更である。利用者に見える「poll」「polls」の語を、すべて「survey」「surveys」に置き換える。対象は、ナビゲーションの表示、ページのタイトルと見出し、ボタン、メッセージ、結果画面、URL（アドレスバーに出るため）。振る舞い（1 ブラウザ 1 投票テーマ 1 回、確認、結果、配色）は変えない。

### 用語集

既存要件定義書 `docs/requirements.md` セクション 1 の用語集を参照。本変更で変わる用語:

| 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
|---|---|---|---|
| 投票テーマ（ポール）[変更] | 利用者に投票を求める質問。選択肢を複数持つ | 画面の英語名は「Survey」（旧「Poll」）。日本語の文書では従来どおり「投票テーマ」と書く（文書の語は変えない） | survey（画面の英語名） |

画面に表示する英語の語: 「Poll」「Polls」は使わない。「Survey」「Surveys」を使う（RQ-UI-SURVEY-WORDING）。

### システムの形態

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照（GUI）。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` セクション 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

今回の変更で、依頼文と回答に無いことを決めた項目。

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| URL の語 | 投票テーマの URL の `/polls/` を `/surveys/` に変える（`/surveys/<id>`、`/surveys/<id>/vote`、`/surveys/<id>/results`）。ブラウザのアドレスバーは利用者に見える | 依頼文「everywhere the user can see it」と「poll ... must not appear anywhere in the user interface」。アドレスバーも画面の一部とみなす | 承認済（ANSWERS.md で一任） |
| 旧い URL | 旧い `/polls/...` の URL から新しい URL への転送は作らない（404 になる）。利用者はトップページから入るため | 最小案。移行の要件は依頼に無い | 承認済（ANSWERS.md で一任） |
| 内部名 | 関数名、テーブル名（`polls`、`poll_options`、`poll_voters`）、要件 ID・設計 ID（`RQ-FT-*-POLL*`、`DS-*-POLL*` など）、テストの関数名は変えない。利用者に見えないため | 依頼文の対象は「user interface」。内部名を変えると変更範囲が広がり、既存の機能を壊す危険がある | 承認済（ANSWERS.md で一任） |
| DB ファイル名 | `DATA_DIR` の下の `polls.db` の名前は変えない | 利用者に見えない。名前を変えると既存の投票データが読めなくなるため | 承認済（ANSWERS.md で一任） |
| 文書の日本語の語 | 正本の日本語の文章（「投票テーマ」）は変えない。画面の英語名だけ変える（用語集に明記） | 依頼文は画面の文言の変更。文書の全面書き換えは変更の範囲を超える | 承認済（ANSWERS.md で一任） |
| 画面に出る語の範囲 | 画面の英語（ナビゲーション、サイト名、タイトル、見出し、説明文、ボタン、リンク、表の見出し、空の表示、404 の文言）のすべて。HTML のタイトルも含む。エラー文言は元々 poll を含まない | 依頼文「navigation labels, page titles and headings, buttons, messages and the results page」 | 承認済（依頼文の指定） |
| 配色 | 変更なし（前回の変更の RQ-UI-COLOR-THEME のまま） | 依頼文「Keep ... the light yellow / dark slate gray theme」 | 承認済（依頼文の指定） |
| 確認の方法 | 利用者に見える文字の検証は、E2E テストで全画面の HTML に語 `poll`（大文字小文字を問わず、`polls` を含む）が無いことを確かめる。URL を含む HTML 全体を対象にする | 依頼文「must not appear anywhere」を機械的に確かめるため | 承認済（ANSWERS.md で一任） |

---

## 2. 業務

### 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 の対象業務一覧を参照（RQ-BZ-POLL-VOTING。業務の ID は変えない）。

### 業務フロー

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 の業務フローを参照（業務の流れは同じ。画面の語だけが変わる）。

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 画面に「poll」の語が出ており、依頼の用語「survey」と違う [追加] | RQ-BZ-POLL-VOTING | 利用者に見える語はすべて「survey」（「poll」は出ない） | 画面の複数の箇所（ナビゲーション、タイトル、見出し、ボタン、結果画面、URL）に「poll」「Polls」が出ている（依頼文より） | 不明（用語のため KPI は無い） | 不明（依頼に業務影響の記述が無い。依頼の用語に合わせるため） |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| RQ-BK-SURVEY-TERMINOLOGY [追加] | 利用者に見える用語を依頼の用語（survey）に統一する | 画面に「poll」の語が出ている | 画面に「poll」「Polls」の語が出ない（目標値: 0 件。依頼の指定） | RQ-BZ-POLL-VOTING |

### 2-3. 見込み経営効果

変更なし。既存要件定義書 `docs/requirements.md` セクション 2-3 を参照（算定しない）。

---

## 3. 機能要件

- 入力データ: 変更なし（人手入力。投票の選択肢の選択）。外部連携は無い。
- 出力データ: 変更なし（画面に表示する投票テーマ、選択肢、票数、割合）。表示する語だけが変わる（RQ-UI-SURVEY-WORDING）。

### 全機能のユーザー利用フロー

変更なし（既存のフロー図の遷移は同じ）。図の中の表示名だけが変わる:

- [変更] 図の `Polls（一覧）` の表示名を `Surveys（一覧）` にする。

### システムの形態ごとの仕様（GUI）

画面ごとの 5 項目のうち、文言が変わるもの（画面の機能と遷移は変えない）。

- [追加] 共通: 用語（RQ-UI-SURVEY-WORDING）
  - 全画面の英語の表示から「poll」「Polls」を外し、「survey」「surveys」にする。URL の `/polls/` は `/surveys/` にする。
  - 対象: ナビゲーション（「Surveys」「Results」）、サイト名（ヘッダーの「Surveys」）、各ページのタイトル（「Surveys | ...」）、一覧の見出し「Surveys」と説明文と「No surveys yet.」、結果画面の「Vote on this survey」と「Back to surveys」、結果一覧の表の見出し「Survey」と説明文、404 画面の「Go to Surveys」。
- [変更] 画面: 投票テーマ一覧（RQ-UI-POLL-LIST-SCREEN。画面名は「Surveys」）
  - 見出し「Polls」→「Surveys」。説明文「Choose a poll to vote, or look at the results.」→「Choose a survey to vote, or look at the results.」。投票テーマが無いときの「No polls yet.」→「No surveys yet.」。
- [変更] 画面: 投票テーマの結果（RQ-UI-POLL-RESULTS-SCREEN）
  - 「Vote on this poll」→「Vote on this survey」、「Back to polls」→「Back to surveys」。
- [変更] 画面: 結果一覧（RQ-UI-RESULTS-OVERVIEW-SCREEN）
  - 表の見出し「Poll」→「Survey」。説明文「Totals and the leading option for every poll.」→「... every survey.」。「No polls yet.」→「No surveys yet.」。
- [変更] 404 画面（「Not found」）: リンク「Polls」→「Surveys」（「Go to Surveys」）。
- 他の画面（詳細・投票の操作、投票済みの表示、配色）: 文言の変更は上の語だけ。振る舞いは変わらない。

### 3-1. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 機能一覧

変更なし。機能一覧は既存のまま（ID は変えない。ID の中の POLL は内部の名前であり、機能の中身は変えない）。

### 3-2. 業務ルール

変更なし。投票の規則（1 ブラウザ 1 投票テーマ 1 回、不正な投票の拒否）は既存要件定義書 `docs/requirements.md` 3-2 と、前回の変更の 3-2 のとおり。

### 3-3. 外部連携

変更なし。外部連携は無い。

---

## 4. データ

### 4-1. データ要件一覧

変更なし。既存要件定義書 `docs/requirements.md` 4-1 を参照。保存先の `polls.db` の名前は変えない（1-2 の決め事）。

### 4-2. 業務エンティティとデータ項目

変更なし。エンティティ名（投票テーマ、選択肢、投票、投票者記録）は業務の名前のまま。画面の語だけが変わる。

### 4-3. CRUD テーブル（必須）

変更なし。

### 4-4. 状態遷移

変更なし。状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-UI-POLL-LIST-SCREEN [変更] | Surveys（投票テーマ一覧。旧: Polls） | 投票テーマ:Read（一覧） | 投票テーマを選ぶ | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-UI-POLL-DETAIL-SCREEN | 投票テーマの詳細・投票 | 変更なし | 選択肢を選んで投票する | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-UI-POLL-RESULTS-SCREEN | 投票テーマの結果 | 変更なし | 票数と割合を見る | RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-RESULTS-OVERVIEW-SCREEN | Results（全投票テーマの結果一覧） | 変更なし | 全投票テーマの結果をまとめて見る | RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-NAVIGATION-MENU [変更] | 共通ナビゲーション（メニューの語を変える） | 変更なし | 主要な画面へ移る | RQ-BK-ONLINE-VOTE-COLLECTION、RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-ALREADY-VOTED-MESSAGE | 投票テーマの詳細・投票（投票済みの状態） | 変更なし | 投票済みのブラウザに、投票できないことを知らせる | RQ-BK-ONE-VOTE-PER-BROWSER |
| RQ-UI-COLOR-THEME | 全画面（配色） | 無し（画面共通の見た目） | 全画面を指定の配色で表示する | RQ-BK-COLOR-THEME |
| RQ-UI-SURVEY-WORDING [追加] | 全画面（利用者に見える語） | 無し（画面共通の文言） | 全画面で「survey」の語を使い、「poll」の語を出さない | RQ-BK-SURVEY-TERMINOLOGY |

---

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 5 を参照。

---

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 6 を参照。起動の方法（`bash setup.sh`、`PORT=... bash run.sh`、`DATA_DIR`）は変えない。

---

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-NAVIGATE-MENU [削除] | （削除）旧い語のメニューで移ること | 削除理由: 文言を「Polls」から「Surveys」に変えるため、同じ ID の行を文言だけ差し替える | — | — | RQ-UI-NAVIGATION-MENU | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-TS-NAVIGATE-MENU [追加] | どの画面からも「Surveys」「Results」で主要な画面へ移れること | 初期データが入っている | 1. 一覧画面、詳細画面、結果画面、結果一覧画面で、それぞれ「Surveys」と「Results」を押す | 押したメニューの画面へ移り、現在の画面のメニュー項目が強調される | RQ-UI-NAVIGATION-MENU | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-TS-NO-POLL-WORD-IN-UI [追加] | 利用者に見える画面に「poll」の語が無いこと | 初期データが入っている。DB が空でも入る | 1. 一覧、詳細、結果、結果一覧、存在しない URL（404）の各画面の HTML を取得する。2. 投票した後の結果画面と、投票済みの詳細画面の HTML を取得する。3. 取得した各 HTML に、大文字小文字を問わず `poll` が含まれないか（`polls` を含む）を確かめる | 全 HTML に `poll` の語が無い。「Surveys」「survey」が使われている。URL は `/surveys/` で始まる | RQ-UI-SURVEY-WORDING | RQ-BK-SURVEY-TERMINOLOGY |

残りのシナリオ（一覧から詳細へ進む、投票テーマの項目の表示、1 回制限、不正な投票、結果、全結果の一覧、空の DATA_DIR の初期データ、配色）は変更なし（文言の語だけが変わる。シナリオの手順と期待の考え方は既存のまま）。既存要件定義書 `docs/requirements.md` 第 7 章を参照。

テストの対象外: 変更なし。

---

## 要件と業務課題の対応（変更後）

| 業務課題（RQ-BK） | 対応する要件（RQ-*） |
|---|---|
| RQ-BK-SURVEY-TERMINOLOGY [追加] | RQ-UI-SURVEY-WORDING |
| RQ-BK-ONLINE-VOTE-COLLECTION | 変更なし（既存の対応。RQ-UI-NAVIGATION-MENU は文言が変わるのみ） |
