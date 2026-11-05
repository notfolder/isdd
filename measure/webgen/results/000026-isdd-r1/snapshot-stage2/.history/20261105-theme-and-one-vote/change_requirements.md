# 変更要件定義書: Polls Website（投票サイト）— 配色の変更と、1 ブラウザ 1 回の投票

作成日: 2026-11-05
フロー: 変更（isdd-spec）。変更の記録。正本 `docs/requirements.md` は書き換えない（反映は実装後レビューで行う）
入力: `REQUEST.md`（変更依頼 1）、`contract.md`、`ANSWERS.md`（ヒアリングへの固定回答）、正本 `docs/requirements.md`

凡例: 各要件項目に [追加] か [削除] を付ける。変更の無い章・節は「変更なし。既存要件定義書 `docs/requirements.md` セクション[N] を参照」と書く。

---

## 1. 目的・前提

### 目的

依頼 1 の 2 点を反映する。(1) 画面の配色を、背景 light yellow、部品（ボタン・カード・見出し・ヘッダー）dark slate gray にする。(2) 投票は、1 つの投票テーマにつき、同じブラウザから 1 回だけ数える。投票済みの投票テーマでは投票の操作を無効にし、「You have already voted」を表示する。直接送信された 2 回目も数えない。

### 用語集

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 の用語集を参照。本変更で追加する用語:

| 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
|---|---|---|---|
| 投票者記録 | ブラウザ（投票者 ID）が、どの投票テーマに投票済みかを示す記録 | 投票の判定、データ | voter record |
| 投票者 ID | ブラウザに保存する識別子（Cookie の値）。利用者の識別ではなく、ブラウザの識別 | 投票の判定、データ | voter id |

### システムの形態

変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照（GUI）。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` セクション 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

今回の変更で、依頼文と回答に無いことを決めた項目。

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 投票者の識別 | ブラウザの Cookie `voter_id` に、ランダムな 32 桁の英数字（UUID 形式の 16 進数）を保存する。HttpOnly、SameSite=Lax、Path=/、有効期間 1 年。ログインは作らない | 依頼文「cookie or local storage」のうち、サーバーで投票済みを判定できる Cookie を選ぶ（直接送信も制限するため） | 承認済（ANSWERS.md で一任） |
| 投票済みの範囲 | 投票者記録は投票テーマごとに持つ。同じブラウザは、投票済みの投票テーマには投票できず、他の投票テーマには投票できる | 依頼文「per poll per browser」 | 承認済（依頼文の指定） |
| Cookie を消した場合 | Cookie を消す、またはシークレットウィンドウで開くと、同じ端末でも再び投票できる | 依頼文「browser」の単位（ブラウザごとの制限）。ログインが無いため、これ以上の識別はしない | 承認済（ANSWERS.md で一任） |
| 投票済みへの直接送信 | 投票済みの投票テーマに、投票者 ID 付きで送信しても記録しない。HTTP 409 で詳細画面を再表示し、「You have already voted」を出す。票数は変えない | 依頼文「A second vote must not be counted even if submitted directly」 | 承認済（依頼文の指定） |
| 変更前の票 | 変更前の票には投票者記録が無いので、変更後はどのブラウザも同じ投票テーマに 1 回投票できる。既存の票は消さない | 最小案。既存データの移行は依頼に無い | 承認済（ANSWERS.md で一任） |
| 投票済みの表示 | 詳細画面の選択肢（ラジオボタン）と「Vote」ボタンを無効にし、「You have already voted」を表示する。「View results」のリンクは有効のまま | 依頼文「voting controls of that poll are disabled ... and the message ... is shown」。結果は見られる方がよいため | 承認済（依頼文の指定） |
| 配色の値 | 背景 light yellow = `#FFFFE0`（CSS の lightyellow）。部品 dark slate gray = `#2F4F4F`（CSS の darkslategray）。本文の文字色も `#2F4F4F`。部品の上の文字は `#FFFFE0`。エラー文言の赤（`#8B0000`）は意味の色としてそのまま使う | 依頼文の色名を CSS の名前付き色の値にした。白と navy は全画面から外す | 承認済（依頼文の指定。値は CSS の名前付き色） |
| 既存の画面の記述 | 正本 `docs/requirements.md` 本文の「白」「navy」の記述（1-2、3 の画面・ナビゲーションの説明）は、RQ-UI-COLOR-THEME の値に読み替える。正本反映の際に本文を直す | 依頼文「replacing white / navy everywhere」 | 承認済（依頼文の指定） |
| 期限切れの投票者記録 | 投票者記録の削除の機能は作らない。保持期間は無期限 | 最小案。削除の要件は依頼に無い | 承認済（ANSWERS.md で一任） |

---

## 2. 業務

### 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 の対象業務一覧を参照（RQ-BZ-POLL-VOTING）。

### 業務フロー

変更なし。既存要件定義書 `docs/requirements.md` セクション 2 の業務フローを参照。

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 同じブラウザから同じ投票テーマに何度でも投票でき、結果が偏る [追加] | RQ-BZ-POLL-VOTING | 1 つの投票テーマには、ブラウザ 1 台につき 1 票が入る | 同じブラウザから何度でも投票でき、1 人が結果を偏らせられる（依頼文より） | 不明（依頼に数値が無いため、KPI は算定しない） | 投票結果の公平さが保てない（依頼文の「1 回に制限」から推測） |
| 配色が依頼の指定と違う [追加] | RQ-BZ-POLL-VOTING | 全画面が指定の配色（背景 light yellow、部品 dark slate gray）で表示される | 背景は白、部品は navy で表示される（正本の配色の記述による） | 不明（配色のため KPI は無い） | 不明（依頼に業務影響の記述が無い） |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| RQ-BK-ONE-VOTE-PER-BROWSER [追加] | 1 つの投票テーマに対し、同じブラウザからの投票を 1 回に限って数える | 同じブラウザから何度でも投票でき、結果が偏る | 同じブラウザからの 2 回目以降は数えられず、投票済みであることが画面に出る（目標値: 不明。依頼に無し） | RQ-BZ-POLL-VOTING |
| RQ-BK-COLOR-THEME [追加] | 全画面の配色を依頼の指定どおりにする | 配色が依頼の指定と違う | 全画面が指定の配色で表示される（目標値: 不明。依頼に無し） | RQ-BZ-POLL-VOTING |

### 2-3. 見込み経営効果

変更なし。既存要件定義書 `docs/requirements.md` セクション 2-3 を参照（算定しない）。

---

## 3. 機能要件

- 入力データ: 変更なし（人手入力。投票の選択肢の選択）。外部連携は無い。
- 出力データ: 変更なし（画面に表示する投票テーマ、選択肢、票数、割合）。

### 全機能のユーザー利用フロー

変更なし（既存のフロー図を参照）。ただし次の遷移が [追加] される。

- [追加] 投票済みのブラウザで投票テーマの詳細画面を開くと、投票の操作が無効な詳細画面（「You have already voted」）が表示される。結果画面へは「View results」で移れる（RQ-UI-ALREADY-VOTED-MESSAGE）。

業務フローとの対応: 業務フローの「選択肢を選んで投票する」は RQ-FT-CAST-VOTE と RQ-FT-ONE-VOTE-PER-POLL に対応する（変更後）。

### システムの形態ごとの仕様（GUI）

画面ごとの 5 項目のうち、変更するもの。

- 画面: 投票テーマの詳細・投票（RQ-UI-POLL-DETAIL-SCREEN）
  - [追加] 状態「投票済み」: RQ-UI-ALREADY-VOTED-MESSAGE を参照。投票済みのとき、選択肢と「Vote」ボタンを無効にし、「You have already voted」を表示する。エラー時の見え方（未選択の送信）は変わらない。
- 共通: 配色（RQ-UI-COLOR-THEME）
  - [追加] 全画面の背景は light yellow（`#FFFFE0`）。部品（ヘッダー、ナビゲーション、見出し、ボタン、カード、表の見出し、結果の横棒）は dark slate gray（`#2F4F4F`）。本文の文字は `#2F4F4F`、部品の上の文字は `#FFFFE0`。正本の「白」「navy」の記述はこの値に読み替える。
- 他の画面（一覧・結果・結果一覧・Not found）: 項目の変更は無い。配色のみ RQ-UI-COLOR-THEME に従う。

### 3-1. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 機能一覧

変更なし。機能一覧（RQ-FT-BROWSE-POLLS、RQ-FT-VIEW-POLL-OPTIONS、RQ-FT-CAST-VOTE、RQ-FT-VIEW-RESULTS、RQ-FT-VIEW-ALL-RESULTS）は既存のまま。投票の回数に関する規則は 3-2 で変える。

### 3-2. 業務ルール

| RQ-ID | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-FT-REJECT-INVALID-VOTE | 不正な投票を受け付けない | 変更なし（既存要件定義書 `docs/requirements.md` 3-2 を参照） | 変更なし | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-FT-COUNT-EVERY-VOTE [削除] | 投票は回数に関係なく数える | 削除理由: 依頼 2（1 ブラウザ 1 投票テーマ 1 回）と矛盾するため。不要になる RQ-BK-*: 無し（RQ-BK-ONLINE-VOTE-COLLECTION は他の要件で残る） | 変更後は RQ-FT-ONE-VOTE-PER-POLL に置き換える | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-FT-ONE-VOTE-PER-POLL [追加] | 同じブラウザは同じ投票テーマに 1 回だけ投票できる | 条件: 投票者 ID の投票者記録に、その投票テーマが既にある。結果: 投票を記録しない（票数は変わらない）。別の投票テーマへの投票は制限しない。投票者 ID は ブラウザの Cookie で判定する（1-2 の決め事）。投票が記録されたとき、同じ投票者 ID の投票者記録を 1 件追加する | 2 回目以降は HTTP 409 で投票テーマの詳細画面を再表示し、「You have already voted」を出す（RQ-UI-ALREADY-VOTED-MESSAGE）。Cookie を消したブラウザは新しい投票者として扱う | RQ-BK-ONE-VOTE-PER-BROWSER |

### 3-3. 外部連携

変更なし。外部連携は無い。

---

## 4. データ

### 4-1. データ要件一覧

変更なし。既存要件定義書 `docs/requirements.md` 4-1 を参照。投票者記録も RQ-DT-LOCAL-SQLITE-STORAGE の `polls.db` に保存する（保存先は変わらない）。

### 4-2. 業務エンティティとデータ項目

| RQ-ID | カテゴリ | 業務エンティティ名 | 対応業務課題ID（RQ-BK-*） | この業務エンティティが無いと何が困るか |
|---|---|---|---|---|
| RQ-DT-VOTER-RECORD [追加] | データ | 投票者記録（VoterRecord） | RQ-BK-ONE-VOTE-PER-BROWSER | 同じブラウザの投票済みを判定できず、1 回制限を守れない |

既存のエンティティ（RQ-DT-POLL、RQ-DT-POLL-OPTION、RQ-DT-VOTE）は変更なし。

| エンティティ名 | 項目名 | 業務上の意味 | 必須 | 形式・桁 | 値の範囲・制約 | 例 |
|---|---|---|---|---|---|---|
| 投票者記録 [追加] | 投票テーマ ID | 投票済みの投票テーマ | 必須 | 整数 | 存在する投票テーマの ID。投票者 ID と合わせて一意 | 1 |
| 投票者記録 [追加] | 投票者 ID | ブラウザの識別子（Cookie `voter_id` の値） | 必須 | 文字列 32 桁（英小文字と数字） | 投票者 ID と投票テーマ ID の組で一意 | 3f9c2a7b1d4e4f0a9b8c7d6e5f4a3b2c |
| 投票者記録 [追加] | 投票日時 | 投票を受け付けた時刻 | 必須 | 日時（UTC、ISO 8601 形式の文字列） | 自動で入る | 2026-11-05T10:00:00Z |

### 4-3. CRUD テーブル（必須）

| エンティティ名 | Create | Read（一覧） | Read（詳細） | 検索 | Update | Delete | 備考 |
|---|---|---|---|---|---|---|---|
| 投票テーマ（Poll） | × | ○ | ○ | × | × | × | 変更なし |
| 選択肢（PollOption） | × | ○ | ○ | × | × | × | 変更なし |
| 投票（Vote） | ○ | △ | × | × | × | × | 変更なし（Create は 1 件の追加。投票者記録と同じ 1 トランザクションで行う） |
| 投票者記録（VoterRecord）[追加] | ○ | × | ○ | × | × | × | Create は投票の記録と同時（1 件の追加）。Read（詳細）は投票済みかの判定だけ（投票テーマ ID と投票者 ID の組）。Delete の機能は作らない |

### 4-4. 状態遷移

変更なし。状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| RQ-UI-POLL-LIST-SCREEN | Polls（投票テーマ一覧） | 変更なし | 投票テーマを選ぶ | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-UI-POLL-DETAIL-SCREEN | 投票テーマの詳細・投票 | 変更なし | 選択肢を選んで投票する | RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-UI-POLL-RESULTS-SCREEN | 投票テーマの結果 | 変更なし | 票数と割合を見る | RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-RESULTS-OVERVIEW-SCREEN | Results（全投票テーマの結果一覧） | 変更なし | 全投票テーマの結果をまとめて見る | RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-NAVIGATION-MENU | 共通ナビゲーション | 変更なし（配色のみ RQ-UI-COLOR-THEME） | 主要な画面へ移る | RQ-BK-ONLINE-VOTE-COLLECTION、RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-UI-ALREADY-VOTED-MESSAGE [追加] | 投票テーマの詳細・投票（投票済みの状態） | 投票者記録:Read（詳細）、投票テーマ:Read（詳細）、選択肢:Read（一覧） | 投票済みのブラウザに、投票できないことを知らせる | RQ-BK-ONE-VOTE-PER-BROWSER |
| RQ-UI-COLOR-THEME [追加] | 全画面（配色） | 無し（画面共通の見た目） | 全画面を指定の配色で表示する | RQ-BK-COLOR-THEME |

---

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 5 を参照。

---

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` セクション 6 を参照。

---

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| RQ-TS-CAST-VOTE-AND-VIEW-RESULT [削除] | （削除）投票後に 2 回目も票が増えること | 削除理由: 2 回目の投票でも 1 票ずつ増えるという旧い規則（RQ-FT-COUNT-EVERY-VOTE）を検証しているため。不要になる RQ-BK-*: 無し | — | — | RQ-FT-COUNT-EVERY-VOTE（削除） | RQ-BK-ONLINE-VOTE-COLLECTION、RQ-BK-RESULTS-PUBLIC-VIEW |
| RQ-TS-CAST-VOTE-ONCE-PER-POLL [追加] | 1 回目の投票は数えられ、同じブラウザの 2 回目は数えられないこと。別のブラウザの投票は数えられること | 初期データが入っている。投票前の票数を控える | 1. 詳細画面で選択肢を 1 つ選び「Vote」を押す。2. 結果画面を見る。3. 同じ投票テーマの詳細画面を開く。4. 同じブラウザで、同じ投票テーマへ同じ選択肢を直接送信する（Cookie 付き）。5. Cookie の無い別のブラウザで同じ選択肢を送信する | 1 で「Thank you for voting.」と票数 +1。3 で投票の操作が無効で「You have already voted」。4 は 409 で票数は変わらない。5 は票数が +1（別のブラウザとして数える） | RQ-FT-CAST-VOTE、RQ-FT-VIEW-RESULTS、RQ-FT-ONE-VOTE-PER-POLL、RQ-UI-POLL-RESULTS-SCREEN、RQ-UI-ALREADY-VOTED-MESSAGE | RQ-BK-ONE-VOTE-PER-BROWSER、RQ-BK-ONLINE-VOTE-COLLECTION |
| RQ-TS-COLOR-THEME [追加] | 全画面が指定の配色で表示されること | 初期データが入っている | 1. 一覧、詳細、結果、結果一覧の各画面を開く。2. 表示用のスタイルシートの色を確かめる | 背景が #FFFFE0（light yellow）。ヘッダー、ボタン、カード、見出し、結果の横棒が #2F4F4F（dark slate gray）。白（#FFFFFF）と navy（#000080）が無い | RQ-UI-COLOR-THEME | RQ-BK-COLOR-THEME |

残りのシナリオ（一覧から詳細へ進む、投票テーマの項目の表示、不正な投票、全結果の一覧、メニュー、空の DATA_DIR の初期データ）は変更なし。既存要件定義書 `docs/requirements.md` 第 7 章を参照。

テストの対象外: 変更なし（投票テーマの作成・編集・削除）。

---

## 要件と業務課題の対応（変更後）

| 業務課題（RQ-BK） | 対応する要件（RQ-*） |
|---|---|
| RQ-BK-ONLINE-VOTE-COLLECTION | RQ-FT-BROWSE-POLLS、RQ-FT-VIEW-POLL-OPTIONS、RQ-FT-CAST-VOTE、RQ-FT-REJECT-INVALID-VOTE、RQ-FT-ONE-VOTE-PER-POLL [追加]、RQ-UI-POLL-LIST-SCREEN、RQ-UI-POLL-DETAIL-SCREEN、RQ-UI-NAVIGATION-MENU、RQ-DT-LOCAL-SQLITE-STORAGE、RQ-DT-SAMPLE-DATA-ON-EMPTY、RQ-DT-POLL、RQ-DT-POLL-OPTION、RQ-DT-VOTE |
| RQ-BK-RESULTS-PUBLIC-VIEW | RQ-FT-VIEW-RESULTS、RQ-FT-VIEW-ALL-RESULTS、RQ-UI-POLL-RESULTS-SCREEN、RQ-UI-RESULTS-OVERVIEW-SCREEN、RQ-UI-NAVIGATION-MENU、RQ-DT-VOTE、RQ-DT-LOCAL-SQLITE-STORAGE |
| RQ-BK-ONE-VOTE-PER-BROWSER [追加] | RQ-FT-ONE-VOTE-PER-POLL、RQ-UI-ALREADY-VOTED-MESSAGE、RQ-DT-VOTER-RECORD |
| RQ-BK-COLOR-THEME [追加] | RQ-UI-COLOR-THEME |

（[削除] の RQ-FT-COUNT-EVERY-VOTE は RQ-BK-ONLINE-VOTE-COLLECTION の対応から外す。）
