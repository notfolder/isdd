# 要件定義書: 投票サイト（Polls Website）

## 1. 目的・前提

- システムの目的: 利用者が投票テーマ（poll）を一覧から選び、選択肢に投票し、投票結果を見られるようにする。
- 用語集

  | 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
  |---|---|---|---|
  | 投票テーマ（poll） | 質問文と、その選択肢の組 | 一覧・投票・結果の単位 | 投票、アンケート |
  | 選択肢（option） | 投票テーマの中で選べる答え | 1 投票テーマに 2 件以上 | 回答 |
  | 投票（vote） | 利用者が 1 つの選択肢を選んで送信した 1 回分の記録 | 集計の元データ | 票 |
  | 結果 | 選択肢ごとの票数と割合 | 結果画面 | 集計 |

- システムの形態: GUI（ブラウザで使う画面）。CUI・Web API・バッチは無い。

### 1-1. 技術制約（前提として記録する。要件ではないため ID は付与しない）

| 制約項目 | 内容 | 出どころ（誰がいつ答えたか） |
|---|---|---|
| 既存コードベース | 無し（新規開発） | ANSWERS.md（2026-11-05） |
| 配備先 | ローカルで `bash run.sh` により直接起動。コンテナは使わない | contract.md |
| チームの技術 | Python 3.12 か Node.js 24。無償のものだけ | ANSWERS.md、contract.md |
| ライセンスとコスト | 無償のライブラリだけ。外部サービス・有償 API は使わない | contract.md |
| 性能と規模の目安 | 利用者は少数。性能の目標は無し | ANSWERS.md |
| 画面の言語 | 英語 | contract.md |
| 初期データ | DATA_DIR が空でも、サンプルの投票テーマが表示される | contract.md |

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 投票の重複 | 投票テーマごとに、同じブラウザからの 2 回目以降の投票は記録しない。ブラウザは cookie `voter_id`（32 桁の乱数、HttpOnly、1 年）で区別する。ログインは無い。cookie を消したブラウザは別のブラウザ扱いになる | 依頼「one vote per poll per browser（cookie か local storage）」。直接の POST も防ぐため、サーバーが読める cookie を選んだ | 承認済（REQUEST.md の依頼） |
| 投票済みの送信 | 票を記録せず、投票画面を 200 で再表示し「You have already voted.」を表示する（直接の POST も同じ） | 依頼「must not be counted even if submitted directly」。エラー時の再表示は未選択時と同じ作り | 未確認（最小案） |
| 投票済みの投票画面 | 選択肢と送信ボタンを無効にし、「You have already voted.」と結果画面へのリンクを表示する | 依頼「the voting controls ... are disabled ... message is shown instead」 | 承認済（REQUEST.md の依頼） |
| 既存の票と投票者 | 投票者の記録が無いので、サンプルと変更前の票は移行しない。サンプルの投票テーマは誰でも 1 回投票できる | 既存の票に投票者の情報が無い | 未確認（最小案） |
| 選択肢を選ばずに送信 | 投票は記録せず、同じ画面に「Please select an option.」を表示する | 依頼「cast votes for selected options」から、未選択は投票できないと推測 | 未確認 |
| 存在しない投票テーマ | 「Poll not found.」の 404 画面を表示する | 最小案。URL の番号が不正な場合の扱い | 未確認 |
| 投票テーマの作成・編集・削除 | 作らない | 依頼は閲覧と投票と結果の表示のみ | 未確認 |
| 割合の表示 | 小数第 1 位まで（例: 41.7%）。票が 0 件のときは 0.0% | 最小案。結果を比べられる表示 | 未確認 |
| 初期データ | 投票テーマ 3 件、各 4 件・4 件・3 件の選択肢、各選択肢に初期の票を入れる（DATA_DIR の DB が無いときだけ投入） | contract.md の「sample content」要求 | 未確認 |
| 保存先 | DATA_DIR/polls.db（SQLite）。DATA_DIR 未指定時は `./data` | contract.md（DATA_DIR）と最小案 | 未確認 |
| 認証 | 無し（利用者の区別は無い） | ANSWERS.md「ログインは不要」 | 承認済（ANSWERS.md） |

## 2. 業務

- 対象業務一覧

  | RQ-BZ-ID | 業務名 | 業務の範囲 | 担当者 |
  |---|---|---|---|
  | `RQ-BZ-POLL-VOTING` | 投票（アンケート）の実施と集計 | 投票テーマの提示、選択肢への投票、結果の表示 | 一般の利用者 |

- 業務フロー

  ```mermaid
  graph TD
      A[投票テーマを一覧で見る] --> B[投票テーマを選ぶ]
      B --> C[選択肢を選んで送信する]
      C -->|未選択| B
      C -->|選択済み| D[投票が記録される]
      D --> E[結果を見る]
      A --> E
  ```

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 投票テーマを選んで投票できない | `RQ-BZ-POLL-VOTING` | 利用者が投票テーマを一覧から選び、選択肢に投票できる | 投票を受け付ける仕組みが無い（新規開発） | 不明（依頼に KPI の目標値は無い） | 意見を集められない |
| 投票結果が分からない | `RQ-BZ-POLL-VOTING` | 投票結果を選択肢ごとに確認できる | 結果を見る手段が無い（新規開発） | 不明（依頼に KPI の目標値は無い） | 投票の結論を共有できない |
| 同じ利用者が何度も投票でき、結果が偏る | `RQ-BZ-POLL-VOTING` | 投票テーマごとに、1 つのブラウザから 1 票だけ数えられる | 同じブラウザで何度でも投票できた（変更前） | 不明（依頼に KPI の目標値は無い） | 票数が利用者の意見の数を表さない |
| 画面の配色が依頼の配色と違う | `RQ-BZ-POLL-VOTING` | 背景 light yellow、部品 dark slate gray で表示される | 背景は白、部品は navy（変更前） | 不明（依頼に KPI の目標値は無い） | 依頼の見た目と合わない |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| `RQ-BK-POLL-BROWSING` | 投票テーマを一覧で見られるようにし、選べるようにする | 投票テーマを選んで投票できない | 全投票テーマが一覧に表示される（目標値は不明） | `RQ-BZ-POLL-VOTING` |
| `RQ-BK-VOTE-SUBMISSION` | 選んだ選択肢に投票できるようにする | 投票テーマを選んで投票できない | 選んだ選択肢に 1 票が記録される（目標値は不明） | `RQ-BZ-POLL-VOTING` |
| `RQ-BK-RESULT-VISIBILITY` | 投票結果を集計して見られるようにする | 投票結果が分からない | 選択肢ごとの票数と割合が表示される（目標値は不明） | `RQ-BZ-POLL-VOTING` |
| `RQ-BK-ONE-VOTE-PER-POLL` | 投票テーマごとに、同じブラウザからは 1 票だけ数える | 同じ利用者が何度も投票でき、結果が偏る | 2 回目以降の投票は数えられず、「You have already voted.」が表示される（目標値は不明） | `RQ-BZ-POLL-VOTING` |
| `RQ-BK-THEME-COLORS` | 全画面を依頼の配色（背景 light yellow、部品 dark slate gray）で表示する | 画面の配色が依頼の配色と違う | 全画面の背景が light yellow、部品が dark slate gray（目標値は不明） | `RQ-BZ-POLL-VOTING` |

### 2-3. 見込み経営効果

見込み経営効果は算定しない（理由: 依頼に金額・時間の目安が無く、効果の根拠となる現状の数値が無いため）。

## 3. 機能要件

- 入力データ: 人手入力（投票の選択肢の選択）。外部連携は無い。出力データは画面の表示のみ。
- 利用フロー: 業務フロー（2 節）と同じ。全機能のフローは次のとおり。

  ```mermaid
  graph TD
      H[投票テーマ一覧] --> V[投票画面]
      V -->|選択して送信| R[投票テーマの結果画面]
      V -->|未選択で送信| V
      H --> AR[全体の結果画面]
      AR --> R
      R --> V
  ```

- システムの形態: GUI。画面遷移は 4-5 の画面一覧と上の図のとおり。

- 機能一覧

  | RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
  |---|---|---|---|---|
  | `RQ-FT-LIST-POLLS` | 業務機能 | 投票テーマの一覧を表示する | `RQ-BK-POLL-BROWSING` | 投票テーマを見つけて選べない |
  | `RQ-FT-SHOW-POLL-OPTIONS` | 業務機能 | 投票テーマの質問と選択肢を表示する | `RQ-BK-POLL-BROWSING`, `RQ-BK-VOTE-SUBMISSION` | 何に投票するのかが分からない |
  | `RQ-FT-CAST-VOTE` | 業務機能 | 選んだ選択肢に 1 票を記録する | `RQ-BK-VOTE-SUBMISSION` | 投票ができない |
  | `RQ-FT-REJECT-EMPTY-VOTE` | 業務機能 | 選択肢を選ばずに送信されたら投票を記録せず、エラーを表示する | `RQ-BK-VOTE-SUBMISSION` | 空の投票が記録されて結果が狂う |
  | `RQ-FT-SHOW-POLL-RESULTS` | 業務機能 | 1 つの投票テーマについて、選択肢ごとの票数と割合を表示する | `RQ-BK-RESULT-VISIBILITY` | 投票テーマごとの結果が分からない |
  | `RQ-FT-SHOW-ALL-RESULTS` | 業務機能 | 全投票テーマの結果を 1 画面に一覧表示する | `RQ-BK-RESULT-VISIBILITY` | 全体の結果を比べられない |
| `RQ-FT-ONE-VOTE-PER-POLL` | 業務機能 | 投票テーマごとに、同じブラウザからの 2 回目以降の投票を記録しない（画面からの送信も直接の送信も同じ） | `RQ-BK-ONE-VOTE-PER-POLL` | 同じ利用者の票が何度も数えられ、結果が偏る |

### 3-1. 帳票・出力ファイル

帳票・出力ファイルは無い。結果は画面に表示する（4-5 の RQ-UI 画面）。

### 3-2. 業務ルール

| RQ-ID | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-FT-REJECT-EMPTY-VOTE` | 未選択の投票は受け付けない | 投票の送信時に選択肢が 1 つも選ばれていなければ、票を記録しない | 同じ投票画面に「Please select an option.」を表示する | `RQ-BK-VOTE-SUBMISSION` |
| `RQ-FT-ONE-VOTE-PER-POLL` | 投票テーマごとに 1 ブラウザ 1 票 | 投票の送信時に、同じブラウザ識別子が同じ投票テーマの投票済み記録に既にあれば、票を記録しない（画面からの送信も直接の送信も同じ） | 投票画面を 200 で再表示し「You have already voted.」を表示する。票の合計は変えない | `RQ-BK-ONE-VOTE-PER-POLL` |

（上記以外の業務ルールは無い。投票の重複は上の RQ-FT-ONE-VOTE-PER-POLL で扱う。）

### 3-3. 外部連携

外部連携は無い。

## 4. データ

### 4-1. データ要件一覧

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-DT-SQLITE-STORAGE` | 内部データ | 投票テーマ・選択肢・投票は DATA_DIR の SQLite ファイル（polls.db）に保存する。保持期間は無期限 | `RQ-BK-VOTE-SUBMISSION` | 再起動すると投票が消え、結果が残らない |
| `RQ-DT-SAMPLE-DATA` | 内部データ | DB に投票テーマが 1 件も無いとき、サンプルの投票テーマ 3 件と初期の票を投入する | `RQ-BK-POLL-BROWSING` | DATA_DIR が空だと画面に何も出ず、機能を試せない |
| `RQ-DT-BROWSER-BALLOT` | 内部データ | 投票テーマごとに、投票済みのブラウザ識別子を DATA_DIR の SQLite（`ballots` テーブル）に保存する。保持期間は無期限。ブラウザ側は cookie `voter_id` に識別子を持つ | `RQ-BK-ONE-VOTE-PER-POLL` | 投票済みか判定できず、同じブラウザの 2 回目を防げない |

- 外部 DB は使わない。DB の必要性: 投票は少数・単純な参照関係で、SQLite で十分（初期件数 3 件、1 年後の想定も数十件程度）。

### 4-2. 業務エンティティとデータ項目

| RQ-ID | カテゴリ | 業務エンティティ名 | 対応業務課題ID（RQ-BK-*） | この業務エンティティが無いと何が困るか |
|---|---|---|---|---|
| `RQ-DT-POLL` | 業務データ | 投票テーマ（Poll） | `RQ-BK-POLL-BROWSING` | 何を投票するか表せない |
| `RQ-DT-OPTION` | 業務データ | 選択肢（Option） | `RQ-BK-VOTE-SUBMISSION` | 選べる答えを表せない |
| `RQ-DT-VOTE` | 業務データ | 投票（Vote） | `RQ-BK-VOTE-SUBMISSION`, `RQ-BK-RESULT-VISIBILITY` | 票を記録できず、結果を集計できない |
| `RQ-DT-BALLOT` | 業務データ | 投票済み記録（Ballot）: 投票テーマ × ブラウザ識別子 | `RQ-BK-ONE-VOTE-PER-POLL` | 投票済みかを表せない |

| エンティティ名 | 項目名 | 業務上の意味 | 必須 | 形式・桁 | 値の範囲・制約 | 例 |
|---|---|---|---|---|---|---|
| 投票テーマ | id | 識別子 | ○ | 整数（自動採番） | 一意 | 1 |
| 投票テーマ | question | 質問文 | ○ | 文字列 | 1〜200 文字 | What is your favourite programming language? |
| 選択肢 | id | 識別子 | ○ | 整数（自動採番） | 一意 | 1 |
| 選択肢 | poll_id | 投票テーマへの参照 | ○ | 整数 | 存在する投票テーマの id | 1 |
| 選択肢 | text | 選択肢の文言 | ○ | 文字列 | 1〜100 文字 | Python |
| 選択肢 | position | 表示順 | ○ | 整数 | 1 以上、同じ投票テーマ内で一意 | 1 |
| 投票 | id | 識別子 | ○ | 整数（自動採番） | 一意 | 1 |
| 投票 | option_id | 選ばれた選択肢への参照 | ○ | 整数 | 存在する選択肢の id | 1 |
| 投票 | created_at | 投票日時 | ○ | 日時（UTC、ISO 8601） | — | 2026-11-05T09:00:00+00:00 |
| 投票済み記録 | poll_id | 投票テーマへの参照 | ○ | 整数 | 存在する投票テーマの id。voter_id との組で一意 | 1 |
| 投票済み記録 | voter_id | ブラウザ識別子 | ○ | 文字列（32 桁の 16 進数） | 組 (poll_id, voter_id) で一意 | 5d986d9517a24f0780d19875c979cd35 |
| 投票済み記録 | created_at | 記録日時 | ○ | 日時（UTC、ISO 8601） | — | 2026-11-05T09:00:00+00:00 |

### 4-3. CRUD テーブル（必須）

| エンティティ名 | Create | Read（一覧） | Read（詳細） | 検索 | Update | Delete | 備考 |
|---|---|---|---|---|---|---|---|
| 投票テーマ | × | ○ | ○ | × | × | × | 作成はサンプルデータ投入のみ（画面からは作らない） |
| 選択肢 | × | ○ | ○ | × | × | × | 投票テーマの画面に表示 |
| 投票 | ○ | × | × | × | × | × | 投票の送信で 1 件追加。個別の一覧は無く、結果は集計して表示 |
| 投票済み記録 | ○ | × | ○ | × | × | × | 投票の送信で 1 件追加（投票と同じトランザクション）。投票画面の表示と送信で、投票テーマ × ブラウザ識別子の 1 件を探す |

- 同時更新・排他制御が必要な操作: 同じブラウザからの同時の投票送信。投票済み記録の一意制約（投票テーマ, ブラウザ識別子）で、1 件だけ記録される。既存の行は更新しない。
- トランザクション: 投票の 1 件追加と投票済み記録の追加は 1 トランザクションで行う。初期データ投入は 1 トランザクションで行う。

### 4-4. 状態遷移

状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-UI-POLL-LIST-SCREEN` | 投票テーマ一覧（`/`） | 投票テーマ:Read（一覧） | 投票テーマを一覧し、投票画面と結果画面へのリンクを置く | `RQ-BK-POLL-BROWSING` |
| `RQ-UI-POLL-VOTE-SCREEN` | 投票画面（`/polls/<id>`） | 選択肢:Read（一覧）、投票:Create | 質問と選択肢を表示し、1 つ選んで送信する | `RQ-BK-VOTE-SUBMISSION` |
| `RQ-UI-VOTED-STATE` | 投票画面（`/polls/<id>`）の投票済みの状態 | 投票済み記録:Read（1 件の検索）、選択肢:Read（一覧） | そのブラウザが投票済みの投票テーマは、選択肢と送信ボタンを無効にし、「You have already voted.」と結果画面へのリンクを表示する | `RQ-BK-ONE-VOTE-PER-POLL` |
| `RQ-UI-POLL-RESULT-SCREEN` | 投票テーマの結果画面（`/polls/<id>/results`） | 投票:Read（集計）、選択肢:Read（一覧） | 選択肢ごとの票数と割合を表示する。投票直後は投票済みの通知を出す | `RQ-BK-RESULT-VISIBILITY` |
| `RQ-UI-ALL-RESULTS-SCREEN` | 全体の結果画面（`/results`） | 投票:Read（集計）、投票テーマ:Read（一覧） | 全投票テーマの結果を一覧する | `RQ-BK-RESULT-VISIBILITY` |
| `RQ-UI-NAVIGATION-MENU` | 共通の案内メニュー（全画面の上部） | — | 「Polls」「Results」への移動を全画面で示す | `RQ-BK-POLL-BROWSING` |

- 画面は全て英語で表示する。配色は `RQ-NF-COLOR-THEME` のとおり、背景は light yellow（#FFFFE0）、部品（ナビゲーションバー、ボタン、カードの枠、見出し、結果の棒グラフ）は dark slate gray（#2F4F4F）で表示する。

## 5. 非機能要件

| RQ-ID | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-NF-ANONYMOUS-ACCESS` | 利用者・アクセス経路 | 利用者は一般の利用者で、ログイン無しで全画面を使える。アクセスはローカルホストの HTTP（127.0.0.1） | `RQ-BK-VOTE-SUBMISSION` | ログインが必要と誤解され、投票を試せない |
| `RQ-NF-COLOR-THEME` | 見た目 | 全画面の背景は light yellow（`#FFFFE0`）、部品（案内メニュー、見出し、ボタン、カードの枠、表の罫線、棒グラフ）は dark slate gray（`#2F4F4F`）で表示する。白と navy は使わない（部品の上の文字は白） | `RQ-BK-THEME-COLORS` | 依頼の配色で表示されず、見た目の依頼を満たせない |

- 性能: 目標値は無い。
- 利用人数: 少数（同時接続の目安は無い）。
- 可用性: 要求は無い。
- 移行性: 移行は無い。
- セキュリティ: 認証は無い（上の RQ-NF-ANONYMOUS-ACCESS）。権限の区別は無い。監査証跡は無い。

## 6. 運用要件

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-OP-START-WITH-SCRIPTS` | 起動 | `bash setup.sh` で依存を用意し、`PORT=<番号> bash run.sh` で Web サーバーを前面で起動する。PORT 未指定時は 8000、DATA_DIR 未指定時は `./data` | `RQ-BK-POLL-BROWSING` | 起動手順が分からず、サイトを開けない |

- ログ: ログは必要ないため、ログの内容と保存期間の記述は行わない。
- 監査ログ: 無し。
- 監視・アラート: 監視・アラートは必要ないため、監視・アラートの内容と対応方法の記述は行わない。
- バックアップと復旧: バックアップは必要ない。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| `RQ-TS-BROWSE-POLLS` | 投票テーマ一覧と案内メニューを確かめる | DATA_DIR が空で起動済み | 1. ルートを開く 2. 案内メニューの Polls と Results を確認する | サンプルの投票テーマが 3 件表示され、メニューが全画面にある | `RQ-FT-LIST-POLLS`, `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-NAVIGATION-MENU` | `RQ-BK-POLL-BROWSING` |
| `RQ-TS-VOTE-FOR-OPTION` | 選択肢に投票し、結果に反映されることを確かめる | 起動済み | 1. 投票テーマ 1 を開く 2. 選択肢 Go を選んで送信する 3. 結果画面を見る | 質問と選択肢が表示され、送信後に結果画面で Go の票数が 1 増え、割合が表示される | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-FT-CAST-VOTE`, `RQ-FT-SHOW-POLL-RESULTS`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN` | `RQ-BK-VOTE-SUBMISSION`, `RQ-BK-RESULT-VISIBILITY` |
| `RQ-TS-REJECT-EMPTY-VOTE` | 未選択の送信が拒否されることを確かめる | 起動済み | 1. 投票テーマ 1 を開く 2. 選択肢を選ばずに送信する | 「Please select an option.」が表示され、票の合計は変わらない | `RQ-FT-REJECT-EMPTY-VOTE`, `RQ-UI-POLL-VOTE-SCREEN` | `RQ-BK-VOTE-SUBMISSION` |
| `RQ-TS-VIEW-ALL-RESULTS` | 全体の結果画面を確かめる | 起動済み | 1. Results を開く | 3 件の投票テーマの選択肢ごとの票数と割合が表示される | `RQ-FT-SHOW-ALL-RESULTS`, `RQ-UI-ALL-RESULTS-SCREEN` | `RQ-BK-RESULT-VISIBILITY` |
| `RQ-TS-OPEN-UNKNOWN-POLL` | 存在しない投票テーマの扱いを確かめる | 起動済み | 1. `/polls/9999` を開く | 「Poll not found.」の 404 画面が表示される | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-UI-POLL-VOTE-SCREEN` | `RQ-BK-POLL-BROWSING` |
| `RQ-TS-ANONYMOUS-ACCESS` | ログイン無しで全画面を使えることを確かめる | 起動済み | 1. ログイン画面を経ずに `/`、`/polls/1`、`/polls/1/results`、`/results` を開く | すべて認証なしで 200 で表示される | `RQ-NF-ANONYMOUS-ACCESS` | `RQ-BK-VOTE-SUBMISSION` |
| `RQ-TS-SEED-SAMPLE-DATA` | 空の DATA_DIR で初期データが入ることを確かめる | DATA_DIR が空 | 1. DATA_DIR を空にして起動する 2. ルートを開く | サンプルの投票テーマ 3 件と初期の票が表示される | `RQ-DT-SAMPLE-DATA` | `RQ-BK-POLL-BROWSING` |
| `RQ-TS-ONE-VOTE-PER-POLL` | 同じブラウザからの 2 回目の投票が数えられないことを確かめる | 起動済み（投票者の記録が無い新しいブラウザ） | 1. 投票テーマ 2 を開き、選択肢 Go を選んで送信する 2. 同じブラウザで投票テーマ 2 を開く 3. 同じブラウザから選択肢を指定して直接 POST する 4. 結果画面で票の合計を見る | 2 の画面で選択肢と送信ボタンが無効で「You have already voted.」が表示される。3 の応答は「You have already voted.」を含み、4 の票の合計は 1 回目の送信後と同じ | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-VOTED-STATE`, `RQ-DT-BROWSER-BALLOT` | `RQ-BK-ONE-VOTE-PER-POLL` |
| `RQ-TS-THEME-COLORS` | 全画面が指定の配色で表示されることを確かめる | 起動済み | 1. `/` を開く 2. `/polls/1`、`/polls/1/results`、`/results` を開く | どの画面も背景が `#FFFFE0`、部品の色が `#2F4F4F` で、白・navy の背景色が使われない | `RQ-NF-COLOR-THEME` | `RQ-BK-THEME-COLORS` |

- GUI の全画面（4-5）を網羅する: 一覧、投票、結果、全体の結果。全機能（3 節）を網羅する。

## 8. 整合確認

- 業務課題（RQ-BK-POLL-BROWSING・VOTE-SUBMISSION・RESULT-VISIBILITY・ONE-VOTE-PER-POLL・THEME-COLORS）はすべて機能・データ・画面・非機能要件に結びつく。
- 外部連携は無いため、外部連携の確認は無い。
