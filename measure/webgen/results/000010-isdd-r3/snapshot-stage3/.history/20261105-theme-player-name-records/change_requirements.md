# 変更要件定義書: 景品ルーレット Web サイト（配色の変更、利用者名の必須化、当選履歴への利用者名の表示）

本書は変更フロー（`isdd-spec`）で作成した変更要件定義書。正本 `docs/requirements.md` は書き換えない。変更は `isdd-build` の実装後レビューで正本へ反映する。
依頼文: `REQUEST.md`（変更依頼 1）。契約: `contract.md`。固定回答: `ANSWERS.md`。
区分: 変更する要件は、旧い要件を `[削除]`、新しい要件を `[追加]` で書く。意味が変わる要件は新しい `RQ-*` ID を採番する。

## 1. 目的・前提

- 今回の変更の目的: 画面の配色を ivory と dark green に変え、抽選には利用者名の入力を必須にし、当選履歴の各行に利用者名・景品名・当選日時を並べる。その他の機能（景品一覧、当選履歴の絞り込み、はずれの扱い、初期データ、起動方法）は変えない。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

依頼と固定回答に無い決め事。ユーザー不在のため、最も単純な案で決めた。承認は ANSWERS.md の「承認はすべて与えられたもの」に従う。

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 配色の具体値 | 背景は ivory（`#FFFFF0`）。部品（ボタン、メニュー、見出し帯、表の見出し、パネルの上の枠、ルーレットの区分の一方）は dark green（`#006400`）。ルーレットのもう一方の区分と表の地は白（`#FFFFFF`）。文字は既存どおり濃い灰色 `#222222`（light gray ではなく本文の文字色）| 依頼の色名を CSS の標準色名で表す。白は依頼の light gray の置き換えに使わない（light gray を残さないため）| 承認済（ANSWERS.md により承認とみなす） |
| 検証・エラーの文字色 | 検証メッセージと通信エラーの文字は dark green の太字にする | 依頼が dark red を全画面から外すよう求めるため。赤系の文字は残さない | 承認済（ANSWERS.md により承認とみなす） |
| 利用者名欄の位置 | 景品ルーレット画面で、利用者名の入力欄を抽選ボタン（Spin）の左隣に同じ行で置く | 依頼の「next to the spin control」を満たす最小の配置 | 承認済（ANSWERS.md により承認とみなす） |
| 空欄で回したときの文言 | 既存の「Please enter a name of 1 to 20 characters.」を使う（新しい文言を増やさない） | 既存の規則違反の文言を再利用する最小の扱い。サーバーの 400 の文言と同じ | 承認済（ANSWERS.md により承認とみなす） |
| 抽選の開始の止め方 | 利用者名が規則に合わないときは、画面から抽選の要求（API）を送らず、ルーレットを回さない。サーバー側の検証（400）は残す | 依頼の「does not spin」を画面で確実にする最小の方法 | 承認済（ANSWERS.md により承認とみなす） |
| 当選履歴の列の順 | 利用者名（Player）、景品名（Prize）、当選日時（Won at）の順 | 依頼の「利用者名と一緒に景品と日付」を先頭から並べる最小の形 | 承認済（ANSWERS.md により承認とみなす） |
| 当選履歴 API の項目 | 各要素に `player_name`（利用者名）を追加する。既存の項目（id、prize_name、won_at）は変えない。値は絞り込みに使った利用者名（完全一致のため記録の利用者名と同じ） | 画面が利用者名を出すために必要な最小の変更。DB の変更は無し | 承認済（ANSWERS.md により承認とみなす） |
| ルーレットの区分の色 | dark green と白を交互に使う（区分の文字は白と dark green） | 配色の規則（部品は dark green）と読みやすさの両立 | 承認済（ANSWERS.md により承認とみなす） |
| 既存データ | 既存の当選記録（`DATA_DIR` の SQLite）は変えない。列は既に利用者名を持つため、DB の移行は無い | 依頼に保存データの変更は無い | 承認済（ANSWERS.md により承認とみなす） |

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照。今回の変更は既存の 3 つの業務課題（`RQ-BK-PRIZE-WHEEL-SPIN`、`RQ-BK-PRIZE-LIST-PUBLISH`、`RQ-BK-WINNING-RECORD-VIEW`）の解決の仕方を変えるもので、新しい業務課題と業務の問題は足さない。

### 2-3. 見込み経営効果

変更なし（見込み経営効果は算定しない。既存要件定義書 2-3 を参照）。

## 3. 機能要件

### 3. 機能一覧

変更なし。既存の機能（`RQ-FT-SPIN-WHEEL`、`RQ-FT-DRAW-BY-WEIGHT`、`RQ-FT-PLAYER-NAME-REQUIRED`、`RQ-FT-RECORD-WINNING`、`RQ-FT-MISS-NOT-RECORDED`、`RQ-FT-LIST-PRIZES`、`RQ-FT-VIEW-OWN-RECORDS`）は、既存要件定義書 3 のまま有効。`RQ-FT-PLAYER-NAME-REQUIRED` は「利用者名が規則に合わなければ抽選しない」という意味が変わらないため、ID も内容も変えない。今回の変更の「空欄で回せない」画面の振る舞いは、新しい画面要件 `RQ-UI-SPIN-NAME-FIELD` で定める。

### 3. 画面ごとの仕様（GUI）

- 景品ルーレット画面（`RQ-UI-SPIN-SCREEN`）: 変更なし。主要要素（共通メニュー、利用者名の入力欄、抽選ボタン、ルーレット、結果の表示欄）は同じ。利用者名欄の位置と動きは `RQ-UI-SPIN-NAME-FIELD` で定める。
- 景品一覧画面（`RQ-UI-PRIZE-LIST-SCREEN`）: 変更なし。配色だけ `RQ-NF-COLOR-THEME-IVORY-GREEN` に従う。
- 当選履歴画面: 旧い画面要件は 4-5 画面一覧で区分を付けて置き換える（旧い ID は廃止し、新しい ID を採番する）。

### 3-1. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 3-2. 業務ルール

変更なし。既存要件定義書 3-2 のとおり（`RQ-FT-PLAYER-NAME-REQUIRED` の規則違反は抽選せず、規則の文言を表示し、当選記録を残さない）。

### 3-3. 外部連携

変更なし。外部連携は無い。

## 4. データ

### 4-1. データ要件一覧

変更なし。当選記録は既に利用者名を持つため、保存の仕組みは変えない。

### 4-2. 業務エンティティとデータ項目

変更なし。

### 4-3. CRUD テーブル

変更なし。

### 4-4. 状態遷移

変更なし。状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI の場合のみ）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| [追加] `RQ-UI-SPIN-NAME-FIELD` | 景品ルーレット画面の利用者名欄（抽選ボタンの横） | 当選記録:Create（抽選の前提） | 抽選ボタンの横に必須の利用者名欄を置き、規則に合わない名前では回さない | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] `RQ-UI-MY-RECORDS-SCREEN` | 当選履歴画面 | 当選記録:Read（一覧）、当選記録:検索 | 利用者名で自分の当選履歴を見る | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] `RQ-UI-RECORDS-SCREEN` | 当選履歴画面 | 当選記録:Read（一覧）、当選記録:検索 | 利用者名で自分の当選履歴を見る。各行に利用者名・景品名・当選日時を表示する | `RQ-BK-WINNING-RECORD-VIEW` |

- [追加] 画面遷移: 変更なし（3 画面はそれぞれ共通のメニューで行き来できる）。

## 5. 非機能要件

| RQ-ID | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|
| [削除] `RQ-NF-COLOR-THEME` | 画面の見た目 | 画面の背景は light gray（#D3D3D3）、部品（ボタン、メニュー、ルーレットの区分）は dark red（#8B0000）を使う | `RQ-BK-PRIZE-WHEEL-SPIN` | 依頼で指定した配色にならない（依頼により削除。新しい配色は下の `RQ-NF-COLOR-THEME-IVORY-GREEN`） |
| [追加] `RQ-NF-COLOR-THEME-IVORY-GREEN` | 画面の見た目 | 画面の背景は ivory（#FFFFF0）、部品（ボタン、メニュー、見出し帯、表の見出し、パネルの上の枠、ルーレットの区分の一方、検証とエラーの文字）は dark green（#006400）を使う。light gray（#D3D3D3）と dark red（#8B0000）は、どの画面でも使わない | `RQ-BK-PRIZE-WHEEL-SPIN` | 依頼で指定した配色にならない |
| `RQ-NF-ENGLISH-UI` | 画面の言語 | 変更なし（画面の文言はすべて英語。今回追加する文言も英語） | `RQ-BK-PRIZE-WHEEL-SPIN` | 依頼者が英語の画面を確かめられない |

- 性能、利用人数、可用性、移行性、セキュリティ: 変更なし。既存要件定義書 5 のとおり。

## 6. 運用要件

変更なし。既存要件定義書 6 のとおり（`bash setup.sh`、`PORT=任意の番号 bash run.sh`、環境変数 `PORT` と `DATA_DIR`）。

## 7. テスト用利用シナリオ

[削除] の行は旧いシナリオ、[追加] の行は新しいシナリオ。同じ `RQ-TS` ID を、旧い行（[削除]）と新しい行（[追加]）の 2 行で書く。`RQ-TS-SPIN-AND-RECORD`、`RQ-TS-VIEW-PRIZES`、`RQ-TS-SEED-DATA` は変更なし。

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| [削除] `RQ-TS-NAME-VALIDATION` | 利用者名の規則違反では抽選されず、記録も残らない | 初期データがある状態でサーバーが起動している | 1. 利用者名を空欄にして抽選する。2. 空白だけで抽選する。3. 21 文字の名前で抽選する。4. それぞれの結果と当選履歴を確かめる | 3 回とも抽選されず、規則の文言が表示される。当選記録は増えない | `RQ-FT-PLAYER-NAME-REQUIRED`, `RQ-UI-SPIN-SCREEN` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] `RQ-TS-NAME-VALIDATION` | 利用者名が空・空白・21 文字のときは回らず、規則の文言が出て、当選記録も増えない | 初期データがある状態でサーバーが起動している | 1. 景品ルーレット画面で利用者名を空欄にして Spin を押す。2. 空白だけにして Spin を押す。3. 21 文字の名前にして Spin を押す。4. 3 回とも、ルーレットが回らず入力欄の下に規則の文言が出ることを見る。5. 当選履歴画面で、どの名前にも新しい記録が増えていないことを見る | 3 回とも回転せず、入力欄の下に「Please enter a name of 1 to 20 characters.」が出る。当選記録は増えない。サーバーに同じ入力を送ると 400 と同じ文言が返る | `RQ-FT-PLAYER-NAME-REQUIRED`, `RQ-UI-SPIN-NAME-FIELD` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] `RQ-TS-VIEW-OWN-RECORDS` | 利用者名で絞り込んだ当選履歴だけが表示される | 「Sample Player」の初期記録がある | 1. 当選履歴画面で「Sample Player」を入れて表示する。2. 「Nobody Here」を入れて表示する | 1. では初期の 2 件が新しい順に出る。2. では「No winning records yet.」が出る | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-MY-RECORDS-SCREEN` | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] `RQ-TS-VIEW-OWN-RECORDS` | 利用者名で絞り込んだ当選履歴だけが、利用者名・景品名・当選日時つきで表示される | 「Sample Player」の初期記録がある | 1. 当選履歴画面で「Sample Player」を入れて表示する。2. 一覧の各行の利用者名、景品名、当選日時を見る。3. 「Nobody Here」を入れて表示する | 1. では初期の 2 件が、利用者名・景品名・当選日時つきで新しい順に出る。3. では「No winning records yet.」が出る | `RQ-FT-VIEW-OWN-RECORDS`, `RQ-UI-RECORDS-SCREEN` | `RQ-BK-WINNING-RECORD-VIEW` |
| [削除] `RQ-TS-NAVIGATION` | 3 画面のメニューで行き来でき、配色と英語の文言が指定どおり | サーバーが起動している | 1. 景品ルーレット画面を開く。2. メニューで景品一覧、当選履歴、景品ルーレットの順に移る。3. 各画面の背景色と部品の色、文言を確かめる | 全画面でメニューから他の画面へ移れる。背景は #D3D3D3、部品は #8B0000 で、文言は英語 | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-MY-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME`, `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] `RQ-TS-NAVIGATION` | 3 画面のメニューで行き来でき、配色（背景 ivory、部品 dark green）と英語の文言が指定どおり | サーバーが起動している | 1. 景品ルーレット画面を開く。2. メニューで景品一覧、当選履歴、景品ルーレットの順に移る。3. 各画面の背景色と部品の色、文言を確かめる | 全画面でメニューから他の画面へ移れる。背景は #FFFFF0（ivory）、部品は #006400（dark green）で、#D3D3D3 と #8B0000 は使われない。文言は英語 | `RQ-UI-SPIN-SCREEN`, `RQ-UI-PRIZE-LIST-SCREEN`, `RQ-UI-RECORDS-SCREEN`, `RQ-NF-COLOR-THEME-IVORY-GREEN`, `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |

## 8. 変更後の業務課題と要件の対応

業務課題は変更しない（`RQ-BK-PRIZE-WHEEL-SPIN`、`RQ-BK-PRIZE-LIST-PUBLISH`、`RQ-BK-WINNING-RECORD-VIEW`）。変更後に有効な要件（この文書で参照するもの全件）と、対応する業務課題は次のとおり。区分が「変更なし」の行は既存要件定義書の内容がそのまま有効。区分が「[削除]」の ID は、変更後は有効でない（置き換え先の ID を使う）。

| 区分 | 要件 ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|
| 変更なし | `RQ-FT-SPIN-WHEEL` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-DRAW-BY-WEIGHT` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-PLAYER-NAME-REQUIRED` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-FT-RECORD-WINNING` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-FT-MISS-NOT-RECORDED` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-FT-LIST-PRIZES` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| 変更なし | `RQ-FT-VIEW-OWN-RECORDS` | `RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-UI-SPIN-SCREEN` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-UI-PRIZE-LIST-SCREEN` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| 変更なし | `RQ-NF-ENGLISH-UI` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| 変更なし | `RQ-TS-SPIN-AND-RECORD` | `RQ-BK-PRIZE-WHEEL-SPIN`、`RQ-BK-WINNING-RECORD-VIEW` |
| 変更なし | `RQ-TS-VIEW-PRIZES` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| 変更なし | `RQ-TS-SEED-DATA` | `RQ-BK-PRIZE-LIST-PUBLISH` |
| [追加] | `RQ-UI-SPIN-NAME-FIELD` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] | `RQ-UI-RECORDS-SCREEN` | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] | `RQ-NF-COLOR-THEME-IVORY-GREEN` | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] | `RQ-TS-NAME-VALIDATION`（新しい行） | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [追加] | `RQ-TS-VIEW-OWN-RECORDS`（新しい行） | `RQ-BK-WINNING-RECORD-VIEW` |
| [追加] | `RQ-TS-NAVIGATION`（新しい行） | `RQ-BK-PRIZE-WHEEL-SPIN` |
| [削除] | `RQ-UI-MY-RECORDS-SCREEN`（`RQ-UI-RECORDS-SCREEN` に置き換え） | `RQ-BK-WINNING-RECORD-VIEW` |
| [削除] | `RQ-NF-COLOR-THEME`（`RQ-NF-COLOR-THEME-IVORY-GREEN` に置き換え） | `RQ-BK-PRIZE-WHEEL-SPIN` |

- 削除する ID を参照していた `RQ-TS`（`RQ-TS-NAVIGATION`、`RQ-TS-NAME-VALIDATION`、`RQ-TS-VIEW-OWN-RECORDS`）は、第 7 章で旧い行を [削除]、新しい行を [追加] にした（ID は同じで、検証する要件 ID の列だけが変わる）。
