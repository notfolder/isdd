# 変更要件定義書: 利用者に見える「poll」を「survey」に変える

- 元の依頼: `REQUEST.md`（変更依頼 2）
- 正本: `docs/requirements.md`（変更はまだ正本に反映しない。実装後に isdd-build が反映する）
- 記号: [追加] は新しく入る要件、[変更] は中身（名称・パス・文言）だけが変わる要件。[削除] は取り除く要件（この変更では無し）。変えない要件は書かない。
- 要件 ID（`RQ-*`）は変えない。ID は内部の識別子で、利用者には見えない。ID を変えると対応表と既存の記録が壊れるため。

## 1. 目的・前提

- 変更の目的: 利用者に見える文字から「poll」「polls」の語を無くし、概念を「survey」（日本語の正本では「アンケート」）と呼ぶ。動作は変えない。
- 用語集（正本 1 の用語表を次のとおり変える）

  | 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 |
  |---|---|---|---|
  | 投票テーマ（poll） → **アンケート（survey）** | 質問文と、その選択肢の組 | 一覧・投票・結果の単位 | 投票、投票テーマ（旧称） |

  選択肢（option）、投票（vote）、結果は変えない。

- 用語の適用範囲（正本の反映時に適用する規則）: 正本の本文の「投票テーマ」は「アンケート」に、URL の `/polls` は `/surveys` に置き換える。英語の `poll` を画面の文字として使う箇所は `survey` に変える。ID・コードの識別子・DB のファイル名は変えない（1-2 の表）。

### 1-1. 技術制約

変更なし。正本 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 変える範囲 | 利用者に見える文字すべて（案内メニュー、ページのタイトル、見出し、ボタン、リンク、メッセージ、404 の文言）と、ブラウザのアドレスバーに出る URL のパス（`/polls/...` → `/surveys/...`） | 依頼「navigation labels, page titles and headings, buttons, messages and the results page」と「The word 'poll' / 'polls' must not appear anywhere in the user interface」。アドレスバーも利用者に見える | 承認済（REQUEST.md の依頼）。URL の変更は未確認（最小案） |
| 旧い URL | 転送（リダイレクト）は作らず、`/polls/...` は 404 になる | 転送を足すと新しい設計要素と経路が増えるため。依頼は名称変更で、動作の追加を求めていない | 未確認（最小案） |
| 変えないもの（内部） | 要件 ID・設計 ID、コードの識別子（`PollService` など）、DB のファイル名 `polls.db` と表名、cookie `voter_id` | 利用者に見えない。DB 名を変えると既存の DATA_DIR のデータを読めなくなる | 未確認（最小案） |
| コンソールの起動メッセージと README | 「Surveys is running at …」に変え、README の画面の説明も「Surveys」に変える | 利用者（起動する人）が見る文字。説明と実装を一致させるため | 未確認（最小案） |
| 初期データの文言 | サンプルの質問文・選択肢は変えない（`poll` の語を含まないことを確かめる） | 依頼「behaviour stays the same」。初期データは利用者の操作対象で、語の変更は不要 | 未確認（最小案） |
| 日本語の正本の用語 | 正本の「投票テーマ（poll）」を「アンケート（survey）」に置き換える（1 の用語の適用範囲） | 正本と画面の用語を揃えるため。ID は変えない | 未確認（最小案） |
| 新しい非機能要件 | 利用者に見える文字に `poll`・`polls` を使わないことを、要件（`RQ-NF-SURVEY-TERMINOLOGY`）と E2E のシナリオ（`RQ-TS-SURVEY-TERMINOLOGY`）で確かめる | 依頼の「must not appear anywhere in the user interface」を、確かめられる要件にするため | 未確認（最小案） |

## 2. 業務

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| [追加] 画面の用語（poll）が依頼の用語（survey）と違う | `RQ-BZ-POLL-VOTING` | 利用者に見える文字が「survey」「アンケート」で統一されている | 案内メニュー、見出し、ボタン、URL に「poll」が出る（変更前） | 不明（依頼に KPI の目標値は無い） | 依頼の用語と合わず、利用者が「poll」を別の言葉と感じる |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| [追加] `RQ-BK-SURVEY-NAMING` | 利用者に見える用語を「survey」（アンケート）に揃える | 画面の用語（poll）が依頼の用語（survey）と違う | 利用者に見える文字と URL に「poll」「polls」が無い（目標値は不明） | `RQ-BZ-POLL-VOTING` |

### 2-3. 見込み経営効果

変更なし。正本 2-3 を参照（算定しない）。

## 3. 機能要件

### 3-1. 帳票・出力ファイル

変更なし。

### 3-2. 業務ルール

変更なし。投票、一票ルール、未選択の扱いは従来どおり（名称だけ変わる）。

### 3-3. 外部連携

変更なし（外部連携は無い）。

### 機能の一覧（変更分）

機能の中身（投票、結果、一票ルール）は変えない。名称だけ次のとおり変える。

| RQ-ID | 区分 | 機能名（変更後） | 変更内容 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-FT-LIST-POLLS` | [変更] | アンケートの一覧を表示する | 機能名の「投票テーマ」を「アンケート」に | `RQ-BK-POLL-BROWSING` |
| `RQ-FT-SHOW-POLL-OPTIONS` | [変更] | アンケートの質問と選択肢を表示する | 同上 | `RQ-BK-POLL-BROWSING`, `RQ-BK-VOTE-SUBMISSION` |
| `RQ-FT-SHOW-POLL-RESULTS` | [変更] | 1 つのアンケートについて、選択肢ごとの票数と割合を表示する | 同上 | `RQ-BK-RESULT-VISIBILITY` |
| `RQ-FT-ONE-VOTE-PER-POLL` | [変更] | アンケートごとに、同じブラウザからの 2 回目以降の投票を記録しない（画面からの送信も直接の送信も同じ） | 同上（ID は `PER-POLL` のまま） | `RQ-BK-ONE-VOTE-PER-POLL` |

## 4. データ

### 4-1. データ要件一覧

変更なし。DB のファイル名 `polls.db`、表名 `polls`・`options`・`votes`・`ballots` は変えない（利用者に見えず、既存データを守るため）。

### 4-2. 業務エンティティとデータ項目

変更なし。「投票テーマ（Poll）」は「アンケート（Survey）」と読み替える（用語のみ。項目は変えない）。

### 4-3. CRUD テーブル（必須）

変更なし。

### 4-4. 状態遷移

変更なし。

### 4-5. 画面一覧（GUI）

| RQ-ID | 区分 | 画面名（変更後） | 経路（変更後） | 変更内容 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|
| `RQ-UI-POLL-LIST-SCREEN` | [変更] | アンケート一覧（`/`） | `/` | 見出し「Surveys」、空の時「No surveys available.」、リンク先を `/surveys/<id>` と `/surveys/<id>/results` に | `RQ-BK-POLL-BROWSING` |
| `RQ-UI-POLL-VOTE-SCREEN` | [変更] | アンケートの投票画面（`/surveys/<id>`） | `/surveys/<id>`、送信は `/surveys/<id>/vote` | 経路、「Back to surveys」、404 の文言「Survey not found.」 | `RQ-BK-VOTE-SUBMISSION` |
| `RQ-UI-VOTED-STATE` | [変更] | 投票画面（`/surveys/<id>`）の投票済みの状態 | `/surveys/<id>` | 経路のみ。文言「You have already voted.」は変えない | `RQ-BK-ONE-VOTE-PER-POLL` |
| `RQ-UI-POLL-RESULT-SCREEN` | [変更] | アンケートの結果画面（`/surveys/<id>/results`） | `/surveys/<id>/results` | 経路、リンク「Vote on this survey」、見出し、404 の文言 | `RQ-BK-RESULT-VISIBILITY` |
| `RQ-UI-NAVIGATION-MENU` | [変更] | 共通の案内メニュー（全画面の上部） | — | 「Surveys」「Results」への移動（「Polls」を「Surveys」に） | `RQ-BK-POLL-BROWSING` |
| `RQ-UI-ALL-RESULTS-SCREEN` | [変更] | 全体の結果画面（`/results`） | `/results` | 経路は変えない。各アンケートの「Details」リンク先を `/surveys/<id>/results` に | `RQ-BK-RESULT-VISIBILITY` |

- 画面の英語の文言は、上の変更内容と `RQ-NF-SURVEY-TERMINOLOGY` を満たすこと。
- 「Results」「Vote」「Back to …」など、「poll」を含まない文言は変えない。

## 5. 非機能要件

| RQ-ID | 区分 | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-NF-COLOR-THEME` | 変更なし | 全画面の配色（light yellow / dark slate gray） | `RQ-BK-THEME-COLORS` | — |
| [追加] `RQ-NF-SURVEY-TERMINOLOGY` | 見た目・用語 | 利用者に見える文字（画面の文字、ページのタイトル、ボタン、リンク、メッセージ、URL のパス）に「poll」「polls」の語（大文字・小文字を問わない）を使わない。内部のファイル名・コードの識別子は対象外 | `RQ-BK-SURVEY-NAMING` | 依頼の用語に揃わず、利用者が「poll」の語を見る |

- 変更なし: 性能、利用人数、可用性、移行性、セキュリティ（認証は無い）、匿名アクセス（正本 5 章）は変えない。

## 6. 運用要件

変更なし。起動方法（`bash setup.sh`、`PORT=<番号> bash run.sh`、DATA_DIR）は変えない。

## 7. テスト用利用シナリオ

既存のシナリオの手順と期待結果の URL・文言を、新しい名称に読み替える（`/polls/...` → `/surveys/...`、「Polls」→「Surveys」、「Poll not found.」→「Survey not found.」）。シナリオの ID と「検証する要件ID」は変えない。

| RQ-ID | 区分 | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|---|
| [追加] `RQ-TS-SURVEY-TERMINOLOGY` | 追加 | 利用者に見える文字と URL に「poll」が無いことを確かめる | 起動済み | 1. `/` を開き、ページの文字（タイトル、案内メニュー、見出し、リンク、ボタン）に poll・polls が無いことを確かめる 2. `/surveys/1`、`/surveys/1/results`、`/results` を開き、同じ確認をする 3. `/polls/1` を開く | 1・2 のどの画面にも poll・polls の語が無い。3 は 404 になる | `RQ-NF-SURVEY-TERMINOLOGY`, `RQ-UI-NAVIGATION-MENU`, `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN` | `RQ-BK-SURVEY-NAMING` |

- 正本 7 章の既存の 9 シナリオは、手順の URL と期待結果の文言だけが変わる（区分は変えない。ID は変えない）。

## 8. 整合確認

- 業務課題 `RQ-BK-SURVEY-NAMING` は、非機能要件 `RQ-NF-SURVEY-TERMINOLOGY` とシナリオ `RQ-TS-SURVEY-TERMINOLOGY` に結びつく。
- 変更の影響: 投票・集計・一票ルールの動作は変わらない。変わるのは文字と URL のパスだけ。旧い URL（`/polls/...`）は 404 になる（1-2）。
- 正本との矛盾: 正本の「投票テーマ（poll）」「/polls」の記述は、この変更の反映（実装後の isdd-build）で「アンケート」「/surveys」に置き換える。正本の ID は変えない。
- 外部連携: 無し。
