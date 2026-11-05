# 変更要件定義書: 配色の変更、回すときの名前の必須化、当選記録への名前の表示

判定日: 2026-11-05 / 出典: REQUEST.md（再依頼の変更 1・変更 2）、ANSWERS.md（固定回答）、正本 `docs/requirements.md`（変更の基準）

本書は変更分だけを書く。正本 `docs/requirements.md` は書き換えない。[追加] と [削除] の区分だけを使う。変更が無い章は「変更なし」と書く。

## 1. 目的・前提

- 今回の変更の目的: 配色を ivory（背景）と dark green（部品）に替える。ホイールを回すときは名前を必ず入れさせ、当選記録（スピン結果と My Winnings の表）には名前・景品名・当選日時を必ず出す。
- 用語集: 変更なし。既存要件定義書 `docs/requirements.md` 1 を参照。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 配色の具体値 | 背景は ivory（#FFFFF0）。部品は dark green（#006400）。ホイールの区画は dark green の濃淡（#006400 と #004D00）を交互に使い、奇数件のときの最後の区画は #1F5F1F にする。部品の上の文字は白（#FFFFFF）、背景の上の文字は #1A1A1A | 依頼の ivory と dark green を CSS の標準色名の値（ivory、darkgreen）から決めた。濃淡は既存の「dark red の濃淡 2 色」を同じ形で置き換えた | 承認済（REQUEST.md の再依頼で「承認はすべて与える」） |
| エラー文字の色 | エラー文字（名前の入力欄の下）は dark red を使わず、太字の #1A1A1A にして、枠の線に dark green を使う | 依頼で dark red を「すべて」置き換えるため。文字の強調は太字で行う | 承認済（同上） |
| 名前の入力欄の必須表示 | ラベルを「Your name (required)」にし、入力欄に `required` 属性と `aria-required="true"` を付ける。入力欄は Spin ボタンと同じ行に置く | 依頼の「required text field next to the spin control」を、表示と支援技術の両方で示す最小の形 | 承認済（同上） |
| 名前の規則 | 既存のまま（前後の空白を除き 1〜30 文字）。空、または 30 文字超のときは抽選せず、既存の文言を入力欄の下に出す | 依頼の「empty name shows a validation message and does not spin」は既存の規則で満たせるため、規則は変えない | 承認済（同上） |
| 当選記録の表示項目 | My Winnings の表は「Player」「Won at」「Prize」の 3 列（名前、当選日時、景品名）。スピン結果は景品名と説明に加え、名前と当選日時を表示する | 依頼の「every winning record must show the player's name together with the prize and the date」を満たす最小の形 | 承認済（同上） |
| 当選日時の書式 | 既存の書式（英語、日付は medium、時刻は short。利用者のブラウザの地域設定）をスピン結果にも使う | 既存の画面と書式をそろえるため | 承認済（同上） |
| 名前の表示 | 記録の名前は保存された値をそのまま出す（大文字小文字の違いも含めて、抽選したときの表記） | 当選記録は抽選時の事実のため、後で書き換えない | 承認済（同上） |

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照（対象業務 `RQ-BZ-PRIZE-DRAW`、業務課題 `RQ-BK-PRIZE-DRAW-WHEEL`、`RQ-BK-PRIZE-CATALOG-DISPLAY`、`RQ-BK-WINNING-HISTORY-RECORD`）。今回の変更は既存の業務課題に結びつく（新しい `RQ-BK-*` は採番しない）。

## 3. 機能要件

### 3-0. 変更の要約

| 区分 | RQ-ID | 内容 |
|---|---|---|
| [削除] | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` | 背景 light gray、部品 dark red の配色（意味が変わるため、新 ID で置き換える） |
| [追加] | `RQ-UI-IVORY-DARK-GREEN-THEME` | 背景 ivory、部品 dark green の配色 |
| [追加] | `RQ-UI-SPIN-NAME-FIELD` | 回す画面の、名前の必須入力欄（Spin と同じ行、必須表示、空のときは回さない） |
| [追加] | `RQ-UI-WINNING-RECORD-DISPLAY` | 当選記録の表示（名前・景品名・当選日時を必ず出す） |
| [削除] | `RQ-TS-THEME-COLORS` | 旧配色の検査（新配色の検査に置き換える） |
| [追加] | `RQ-TS-THEME-IVORY-DARK-GREEN` | 新配色の検査 |
| [追加] | `RQ-TS-SPIN-NAME-FIELD-REQUIRED` | 名前の必須入力欄の検査 |
| [追加] | `RQ-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` | 当選記録の表示項目の検査 |

### 3-1. 帳票・出力ファイル

変更なし。既存要件定義書 3-1 を参照。

### 3-2. 業務ルール

変更なし。既存要件定義書 3-2 を参照（`RQ-FT-PRIZE-SELECTION-RULE`、`RQ-FT-REQUIRE-PLAYER-NAME` は内容が変わらない）。

### 3-3. 外部連携

変更なし。既存要件定義書 3-3 を参照（外部連携は無い）。

### 3-4. 画面共通（ナビゲーションと外観）

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| [削除] `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` | 画面共通 | 背景 light gray（#D3D3D3）。ナビゲーション、ボタン、見出しの線、表の見出し、ホイールの区画、指針は dark red（#8B0000） | `RQ-BK-PRIZE-DRAW-WHEEL` | 依頼で指定された配色にならない |
| [追加] `RQ-UI-IVORY-DARK-GREEN-THEME` | 画面共通 | 全画面の背景は ivory（#FFFFF0）。ナビゲーション、ボタン、カード（景品のカード、入力欄のカード）、見出しの線、表の見出し、ホイールの区画と中心の円の縁、指針は dark green（#006400）。ホイールの区画は dark green の濃淡（#006400、#004D00）を交互に使う。部品の上の文字は白、背景の上の文字は #1A1A1A。light gray（#D3D3D3）と dark red（#8B0000）は使わない | `RQ-BK-PRIZE-DRAW-WHEEL`, `RQ-BK-PRIZE-CATALOG-DISPLAY`, `RQ-BK-WINNING-HISTORY-RECORD` | 依頼の配色（ivory の背景、dark green の部品）にならない |

### 3-5. 回す画面の名前入力（追加）

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| [追加] `RQ-UI-SPIN-NAME-FIELD` | 画面 | Spin the Wheel（`/`）で、名前の入力欄を Spin ボタンと同じ行に置く。ラベルは「Your name (required)」で、入力欄に `required` 属性と `aria-required="true"` を付ける。Spin を押したとき、名前が空、または 30 文字を超えるなら抽選せず、入力欄の下に次の文言を出す。空のときは「Please enter your name before spinning.」、31 文字以上のときは「Name must be 30 characters or fewer.」。文言は太字の #1A1A1A で表示する | `RQ-BK-PRIZE-DRAW-WHEEL` | 名前を入れずに回してしまい、誰の当選か分からない記録が残る |

### 3-6. 当選記録の表示（追加）

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| [追加] `RQ-UI-WINNING-RECORD-DISPLAY` | 画面 | 当選記録を表示する箇所は、名前・景品名・当選日時を必ず表示する。（a）My Winnings（`/my-winnings`）の表は、列を「Player」「Won at」「Prize」の順にし、各行に名前、当選日時、景品名を出す。（b）Spin the Wheel の結果欄は、景品名と説明に加えて、名前と当選日時を出す | `RQ-BK-WINNING-HISTORY-RECORD` | 当選記録を見ても、誰が・いつ当てたかが分からない |

- 画面（3-4 の既存の画面一覧）の変更: 名前の列の追加（My Winnings）と、当選日時の追加（スピン結果）だけで、画面の遷移と機能は変わらない。

### 3-7. 機能一覧

変更なし。既存要件定義書 3 の機能一覧（`RQ-FT-SPIN-WHEEL`、`RQ-FT-RECORD-WINNING`、`RQ-FT-VIEW-PRIZE-LIST`、`RQ-FT-VIEW-OWN-WINNINGS`）を参照。`RQ-FT-REQUIRE-PLAYER-NAME` の規則は既存のまま、画面の入力欄の表示を `RQ-UI-SPIN-NAME-FIELD` が受け持つ。

## 4. データ

### 4-1. データ要件一覧

変更なし。既存要件定義書 4-1 を参照（当選記録は名前を既に保存している）。

### 4-2. 業務エンティティとデータ項目

変更なし。既存要件定義書 4-2 を参照。

### 4-3. CRUD テーブル

変更なし。既存要件定義書 4-3 を参照（当選記録の検索で、名前を含む当選記録を返す点だけが変わる。CRUD の区分は変わらない）。

### 4-4. 状態遷移

変更なし。状態を持つエンティティは無い。

### 4-5. 画面一覧（GUI の場合のみ）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| `RQ-UI-SPIN-SCREEN` | Spin the Wheel（`/`） | 当選記録:Create、景品:Read（一覧） | 名前を入れてホイールを回し、景品を当てる。名前の入力欄の表示は `RQ-UI-SPIN-NAME-FIELD` による | `RQ-BK-PRIZE-DRAW-WHEEL`, `RQ-BK-WINNING-HISTORY-RECORD` |
| `RQ-UI-PRIZE-LIST-SCREEN` | Prize List（`/prizes`） | 景品:Read（一覧） | 景品の名前と説明を一覧で見せる | `RQ-BK-PRIZE-CATALOG-DISPLAY` |
| `RQ-UI-MY-WINNINGS-SCREEN` | My Winnings（`/my-winnings`） | 当選記録:Read（一覧）、当選記録:検索 | 名前で絞り込んだ自分の当選記録を新しい順に見せる。表の列は `RQ-UI-WINNING-RECORD-DISPLAY` による | `RQ-BK-WINNING-HISTORY-RECORD` |

画面の構成（遷移、ナビゲーション）は変わらない。

## 5. 非機能要件

変更なし。既存要件定義書 5 を参照。

## 6. 運用要件

変更なし。既存要件定義書 6 を参照。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| [削除] `RQ-TS-THEME-COLORS` | 背景 light gray、部品 dark red の指定がある | サーバーが起動している | 1. トップ画面のスタイルシートを取得する 2. 色の指定を確かめる | （旧い配色の検査。新配色の検査 `RQ-TS-THEME-IVORY-DARK-GREEN` に置き換える） | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` | `RQ-BK-PRIZE-DRAW-WHEEL` |
| [追加] `RQ-TS-THEME-IVORY-DARK-GREEN` | 背景 ivory、部品 dark green の指定があり、旧配色が無いこと | サーバーが起動している | 1. `/static/style.css` を取得する 2. 3 画面（`/`、`/prizes`、`/my-winnings`）が同じスタイルシートを読み込むか調べる 3. 旧配色の値が無いか調べる | スタイルシートに `#FFFFF0` と `#006400` があり、`#D3D3D3` と `#8B0000` が無い。3 画面とも `/static/style.css` を読み込む | `RQ-UI-IVORY-DARK-GREEN-THEME` | `RQ-BK-PRIZE-DRAW-WHEEL` |
| [追加] `RQ-TS-SPIN-NAME-FIELD-REQUIRED` | 名前の入力欄が Spin と同じ行にあり、必須と表示され、空のときは回らないこと | サーバーが起動している | 1. `/` の HTML を取得する 2. 名前の入力欄の属性とラベルを調べる 3. 名前を空にして `POST /api/spins` を呼ぶ | 2: 入力欄が Spin ボタンと同じフォームにあり、`required` 属性と `aria-required="true"` があり、ラベルが「Your name (required)」。3: 400 が返り、抽選の記録は増えない | `RQ-UI-SPIN-NAME-FIELD`, `RQ-FT-REQUIRE-PLAYER-NAME` | `RQ-BK-PRIZE-DRAW-WHEEL` |
| [追加] `RQ-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` | 当選記録に名前・景品名・当選日時が出ること | サーバーが起動し、初期データがある | 1. 名前「Alice」で `POST /api/spins` を呼ぶ 2. `GET /api/winnings?name=Alice` を呼ぶ 3. `/my-winnings` の表の見出しを調べる | 1 の結果の記録に名前・景品名・当選日時がある。2 の各行に `player_name`、`prize_name`、`won_at` がある。3 の表の見出しが「Player」「Won at」「Prize」の順 | `RQ-UI-WINNING-RECORD-DISPLAY` | `RQ-BK-WINNING-HISTORY-RECORD` |

- 上に載せていない既存のシナリオ（既存要件定義書 7 の 7 本）は、手順と期待結果が変わらないため変更なし。名前が各行に出ることは、上の `RQ-TS-WINNING-RECORD-SHOWS-NAME-PRIZE-DATE` で確かめる。

### 変更後の業務課題と要件の対応

| RQ-BK-ID | 業務課題 | 変更後の対応要件 |
|---|---|---|
| `RQ-BK-PRIZE-DRAW-WHEEL` | ホイールによる景品抽選の仕組み | `RQ-FT-SPIN-WHEEL`、`RQ-FT-PRIZE-SELECTION-RULE`、`RQ-FT-REQUIRE-PLAYER-NAME`、`RQ-UI-SPIN-SCREEN`、`RQ-UI-SPIN-NAME-FIELD`、`RQ-UI-IVORY-DARK-GREEN-THEME`（[追加]。旧配色の要件は 3-0 の [削除] のとおり外す） |
| `RQ-BK-PRIZE-CATALOG-DISPLAY` | 景品の一覧 | `RQ-FT-VIEW-PRIZE-LIST`、`RQ-UI-PRIZE-LIST-SCREEN`、`RQ-UI-IVORY-DARK-GREEN-THEME`（[追加]） |
| `RQ-BK-WINNING-HISTORY-RECORD` | 当選記録と名前での閲覧 | `RQ-FT-RECORD-WINNING`、`RQ-FT-VIEW-OWN-WINNINGS`、`RQ-UI-MY-WINNINGS-SCREEN`、`RQ-UI-WINNING-RECORD-DISPLAY`（[追加]）、`RQ-UI-IVORY-DARK-GREEN-THEME`（[追加]） |

---

## 8. 承認の記録

- 1-2 の項目は、REQUEST.md の再依頼に「承認はすべて与えられたもの」とあり、ANSWERS.md の固定回答で承認済とする。
- 除外要件は無し。
