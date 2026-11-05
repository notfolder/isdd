# 変更要件定義書: 報酬ルーレット Web サイト（「景品」を「報酬」に統一）

本書は変更フロー（`isdd-spec`）で作成した変更要件定義書。正本 `docs/requirements.md` は書き換えない。変更は `isdd-build` の実装後レビューで正本へ反映する。
依頼文: `REQUEST.md`（変更依頼 2）。契約: `contract.md`。固定回答: `ANSWERS.md`。
区分: ID が変わる要件・シナリオは、旧い行を `[削除]`、新しい行を `[追加]` で書く。ID と意味が変わらず、文言だけを置き換えるものは「1-3. 用語と文言の置き換え」に一覧で書く（正本の本文を書き換える対象）。

## 1. 目的・前提

- 今回の変更の目的: 画面に見える「景品（prize）」の語を「報酬（reward）」に置き換える。ナビゲーションの見出し、ページのタイトルと見出し、ボタン、表の見出し、文言（「No prize」など）、当選記録の表示をすべて対象とする。抽選の仕組み、表示する情報、配色（ivory と dark green）、利用者名の必須、当選記録の利用者名表示は変えない。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

依頼と固定回答に無い決め事。ユーザー不在のため、最も単純な案で決めた。承認は ANSWERS.md の「承認はすべて与えられたもの」に従う。

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 画面に出す語 | 英語 UI は `prize` を `reward` に、`Prize` を `Reward` にする。日本語の文書は「景品」を「報酬」にする | 依頼の「prize を reward に」。画面の言語は英語（契約） | 承認済（ANSWERS.md により承認とみなす） |
| 旧い語が残らない範囲 | 画面に出る文言、ページのタイトル、見出し、表の見出し、メニュー、エラーの文言、初期データの名前と説明、ページの URL（`/prizes` → `/rewards`）、画面が呼ぶ API の URL（`/api/prizes` → `/api/rewards`）、起動時の表示（コンソール）、README | 依頼の「どこの画面にも見えない」を満たす最小の範囲。URL はブラウザのアドレス欄に出るため対象に含める | 承認済（ANSWERS.md により承認とみなす） |
| 内部の名前 | ID（`RQ-*`、`DS-*`）、クラス名（`PrizeRepository`）、テーブル名（`prizes`）、API の応答の JSON キー（`prize_name` など）、テスト関数名は変えない。画面を作る HTML と JavaScript は、ファイル名、要素の ID、関数名から `prize` の語を外す（`prizes.html` → `rewards.html`、`js/prizes.js` → `js/rewards.js`、`initPrizesPage` → `initRewardsPage`、`renderPrizeTable` → `renderRewardTable`、要素 ID `prize-message` → `reward-message`、`prize-rows` → `reward-rows`） | 画面に出ない内部名は変えない（ID・DB・API の契約を変えないため）。画面を作るファイルは、ソースを開いても「prize」が無いようにする（依頼の「prize を使わない」を画面の範囲で確かめるため） | 承認済（ANSWERS.md により承認とみなす） |
| 旧い URL の扱い | `/prizes` と `/api/prizes` の転送（リダイレクト）は作らない。旧い URL は 404 になる | 依頼に旧い URL の維持は無い。転送を作ると設計要素が増えるため（最小案） | 承認済（ANSWERS.md により承認とみなす） |
| 初期データの名前 | 「Grand Prize: $50 Gift Card」は「Grand Reward: $50 Gift Card」、はずれの説明「No prize this time」は「No reward this time」にする。他の名前は変えない | 画面に出る「prize」を消す最小の置き換え | 承認済（ANSWERS.md により承認とみなす） |
| 既存の DATA_DIR | 変更しない。初期データは景品（報酬）が 0 件のときだけ入るため、旧い名前の DB が残っていれば旧い名前が出る。契約どおり空の DATA_DIR で起動すれば新しい名前だけになる | 契約（空の DATA_DIR で起動）。既存データの書き換えは依頼に無い | 承認済（ANSWERS.md により承認とみなす） |
| 「You won」の文言 | 「You won: <報酬名>!」の形は変えない（語は既に含まない。中の名前が新しい名前になる） | 依頼の「You won: ...」は中身の名前の変更で足りる | 承認済（ANSWERS.md により承認とみなす） |

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照。業務課題（`RQ-BK-*`）と業務（`RQ-BZ-*`）の ID は変えない。業務の説明の中の「景品」は「報酬」に置き換える（1-3 の用語の置き換え）。

### 2-3. 見込み経営効果

変更なし（見込み経営効果は算定しない。既存要件定義書 2-3 を参照）。

## 3. 機能要件

### 3. 機能一覧

変更なし。機能（`RQ-FT-*`）の意味は変えない。機能の説明の中の「景品」は「報酬」に置き換える（1-3）。`RQ-FT-LIST-PRIZES` は ID を変えず、説明を「報酬一覧と当選確率を表示する」に置き換える。

### 3. 画面ごとの仕様（GUI）

- 報酬ルーレット画面（`RQ-UI-SPIN-SCREEN`）: 画面名を「Reward Wheel（報酬ルーレット画面）」の表記に変える。中身（主要要素、抽選の流れ）は変えない。
- 報酬一覧画面（`RQ-UI-PRIZE-LIST-SCREEN`）: 画面名を「Reward List（報酬一覧画面）」に変え、URL を `/rewards` にする。表の見出しは Reward、エラーは「Could not load rewards.」。
- 当選履歴画面（`RQ-UI-RECORDS-SCREEN`）: 表の見出しの「Prize」を「Reward」に変える（列の順と意味は変えない）。

### 3-1. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 3-2. 業務ルール

変更なし。規則の中身は変えない。文中の「景品」は「報酬」に置き換える（1-3）。

### 3-3. 外部連携

変更なし。外部連携は無い。

## 4. データ

### 4-1. データ要件一覧

変更なし。保存の仕組み（SQLite）と項目は変えない。データ項目の名前の表記（景品 → 報酬）は 1-3 の置き換えに従う。

### 4-2. 業務エンティティとデータ項目

変更なし（項目の名前だけ「景品」を「報酬」に置き換える。内部のテーブル名と項目名は変えない）。

### 4-3. CRUD テーブル

変更なし（エンティティ名の表記だけ置き換える）。

### 4-4. 状態遷移

変更なし。状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI の場合のみ）

[削除]・[追加] の行は、画面の名前、URL、表示する語のどれかが変わるもの。

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| [削除] `RQ-UI-SPIN-SCREEN` | 景品ルーレット画面（トップ） | 当選記録:Create、景品:Read（一覧） | 利用者名を入れてルーレットを回し、結果を見る | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] `RQ-UI-SPIN-SCREEN` | 報酬ルーレット画面（トップ、`/`。タイトルと見出しは Reward Wheel） | 当選記録:Create、報酬:Read（一覧） | 利用者名を入れてルーレットを回し、結果を見る | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] `RQ-UI-PRIZE-LIST-SCREEN` | 景品一覧画面 | 景品:Read（一覧） | 景品の名前、説明、当選確率を見る | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [追加] `RQ-UI-PRIZE-LIST-SCREEN` | 報酬一覧画面（`/rewards`。メニューは Reward List） | 報酬:Read（一覧） | 報酬の名前、説明、当選確率を見る | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [削除] `RQ-UI-RECORDS-SCREEN` | 当選履歴画面 | 当選記録:Read（一覧）、当選記録:検索 | 利用者名で自分の当選履歴を見る。各行に利用者名・景品名・当選日時を表示する | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] `RQ-UI-RECORDS-SCREEN` | 当選履歴画面 | 当選記録:Read（一覧）、当選記録:検索 | 利用者名で自分の当選履歴を見る。各行に利用者名・報酬名・当選日時を表示する（表の見出しは Player、Reward、Won at） | `RQ-BK-WINNING-RECORD-VIEW` |

- 画面遷移（[追加]）: 3 画面はそれぞれ共通のメニュー（Spin Wheel、Reward List、My Winning Records）から行き来できる。変更前の「Prize List」の項目は「Reward List」にする。

## 5. 非機能要件

| RQ-ID | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|
| `RQ-NF-COLOR-THEME-IVORY-GREEN` | 画面の見た目 | 変更なし（前回の変更で確定した配色）。文言の「景品」は「報酬」に置き換える | `RQ-BK-PRIZE-WHEEL-SPIN` | 依頼で指定した配色にならない |
| `RQ-NF-ENGLISH-UI` | 画面の言語 | 変更なし（画面の文言はすべて英語。今回の置き換え後の文言も英語。画面に「prize」を残さない） | `RQ-BK-PRIZE-WHEEL-SPIN` | 依頼者が英語の画面を確かめられない |

- 性能、利用人数、可用性、移行性、セキュリティ: 変更なし。既存要件定義書 5 のとおり。

## 6. 運用要件

変更なし。既存要件定義書 6 のとおり（`bash setup.sh`、`PORT=任意の番号 bash run.sh`、環境変数 `PORT` と `DATA_DIR`）。起動時のコンソール表示は「Reward wheel is running at ...」にする。

## 7. テスト用利用シナリオ

[削除] の行は旧いシナリオ、[追加] の行は新しいシナリオ。同じ `RQ-TS` ID を、旧い行（[削除]）と新しい行（[追加]）の 2 行で書く。変更の無いシナリオ（`RQ-TS-SPIN-AND-RECORD`、`RQ-TS-NAME-VALIDATION`、`RQ-TS-VIEW-OWN-RECORDS`、`RQ-TS-SEED-DATA`）は、表記だけを「1-3」の置き換えで正本に反映する。

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| [削除] `RQ-TS-VIEW-PRIZES` | 景品一覧に景品と当選確率が表示される | 初期データがある状態でサーバーが起動している | 1. 景品一覧画面を開く | 景品 7 件（はずれ 1 件を含む）の名前、説明、当選確率（%）が表示され、確率の合計は 100% になる | `RQ-FT-LIST-PRIZES`, `RQ-UI-PRIZE-LIST-SCREEN` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [追加] `RQ-TS-VIEW-PRIZES` | 報酬一覧に報酬と当選確率が表示される | 初期データがある状態でサーバーが起動している | 1. メニューの Reward List を開く（URL は `/rewards`） | 報酬 7 件（はずれ 1 件を含む）の名前、説明、当選確率（%）が表示され、確率の合計は 100% になる。表の見出しは Reward | `RQ-FT-LIST-PRIZES`, `RQ-UI-PRIZE-LIST-SCREEN` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [削除] `RQ-TS-NAVIGATION` | 3 画面のメニューで行き来でき、配色（背景 ivory、部品 dark green）と英語の文言が指定どおり | サーバーが起動している | 1. 景品ルーレット画面を開く。2. メニューで景品一覧、当選履歴、景品ルーレットの順に移る。3. 各画面の背景色と部品の色、文言を確かめる | 全画面でメニューから他の画面へ移れる。背景は #FFFFF0（ivory）、部品は #006400（dark green）で、#D3D3D3 と #8B0000 は使われない。文言は英語 | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] `RQ-TS-NAVIGATION` | 3 画面のメニューで行き来でき、配色（背景 ivory、部品 dark green）と英語の文言が指定どおり。「prize」の語が画面に無い | サーバーが起動している | 1. 報酬ルーレット画面を開く。2. メニューで Reward List、My Winning Records、Spin Wheel の順に移る。3. 各画面の背景色と部品の色、文言を確かめ、画面のどこにも「prize」の語が無いことを見る | 全画面でメニューから他の画面へ移れる。背景は #FFFFF0（ivory）、部品は #006400（dark green）。文言は英語で、画面に「prize」（大文字小文字を問わず）が無い | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |

## 8. 変更後の業務課題と要件の対応

業務課題は変更しない（`RQ-BK-PRIZE-WHEEL-SPIN`、`RQ-BK-PRIZE-LIST-PUBLISH`、`RQ-BK-WINNING-RECORD-VIEW`）。ID と意味が変わらない要件は、正本の本文の置き換えだけで有効になる。変更後に有効な要件（この文書で参照するもの全件）と、対応する業務課題は次のとおり。区分が「[削除]」の ID は、変更後は有効でない（同じ ID の [追加] 行を使う）。

| 区分 | 要件 ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|
| 変更なし | `RQ-FT-SPIN-WHEEL` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-DRAW-BY-WEIGHT` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-PLAYER-NAME-REQUIRED` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-RECORD-WINNING` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-FT-MISS-NOT-RECORDED` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-FT-LIST-PRIZES` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| 変更なし | `RQ-FT-VIEW-OWN-RECORDS` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-NF-COLOR-THEME-IVORY-GREEN` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-TS-SPIN-AND-RECORD` | `RQ-BK-PRIZE-WHEEL-SPIN`、`RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-TS-SEED-DATA` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| 変更なし | `RQ-TS-NAME-VALIDATION` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-TS-VIEW-OWN-RECORDS` | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] | `RQ-UI-SPIN-SCREEN` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] | `RQ-UI-PRIZE-LIST-SCREEN` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [追加] | `RQ-UI-RECORDS-SCREEN` | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] | `RQ-TS-VIEW-PRIZES` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [追加] | `RQ-TS-NAVIGATION` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] | `RQ-UI-SPIN-SCREEN`（旧い行。同じ ID の [追加] 行に置き換え） | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] | `RQ-UI-PRIZE-LIST-SCREEN`（同上） | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [削除] | `RQ-UI-RECORDS-SCREEN`（同上） | `RQ-BK-WINNING-RECORD-VIEW` |
| [削除] | `RQ-TS-VIEW-PRIZES`（同上） | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [削除] | `RQ-TS-NAVIGATION`（同上） | `RQ-BK-PRIZE-WHEEL-SPIN` |

### 1-3. 用語と文言の置き換え（ID と意味は変えない）

正本の本文に次の置き換えを適用する（正本の反映で、全章の本文を通読して行う）。

| 置き換え前 | 置き換え後 | 対象 |
|---|---|---|
| 景品（日本語の語） | 報酬 | 本文全般（用語定義の「景品」は「報酬」。旧称として「景品」を括弧で残してよい） |
| 景品ルーレット | 報酬ルーレット | 画面名、本文 |
| 景品一覧 | 報酬一覧 | 画面名、本文 |
| Prize List | Reward List | メニュー項目、見出し、画面名 |
| Prize Wheel | Reward Wheel | 画面のタイトルと見出し、README |
| Prize | Reward | 表の見出し（当選履歴と報酬一覧）、画面の文言 |
| Grand Prize: $50 Gift Card | Grand Reward: $50 Gift Card | 初期データの名前 |
| No prize this time | No reward this time | 初期データのはずれの説明 |
| Could not load prizes. | Could not load rewards. | エラーの文言 |
| `/prizes`（画面の URL） | `/rewards` | 画面の URL、メニューのリンク |
| `/api/prizes`（API の URL） | `/api/rewards` | 画面が呼ぶ API の URL |
| Prize wheel is running（起動時の表示） | Reward wheel is running | 起動時の表示 |

- ID（`RQ-*`、`DS-*`）、ファイル名、クラス名、テーブル名、JSON のキー、テスト関数名は置き換えない（1-2 の決め事）。
- 「prize」を含む ID（例 `RQ-FT-LIST-PRIZES`、`RQ-UI-PRIZE-LIST-SCREEN`）は ID のまま残す。説明文の中の語は「報酬」「Reward」に置き換える。
