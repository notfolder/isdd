# 変更要件定義書: 配色の変更、名前欄の必須化、当選記録の表示項目

判定日: 2026-11-05 / 出典: REQUEST.md（依頼文）、contract.md（契約）、ANSWERS.md（ユーザー不在時の固定回答）/ 正本: `docs/requirements.md`（変更の前の要件）

## 1. 目的・前提

- 変更の目的: 次の 3 点を既存のサイトに加える。
  1. 配色を、背景は ivory、部品（ボタン、カード、見出し、ナビゲーション）は dark green にする。light gray と dark red は全面的に置き換える。
  2. Spin（回す）には利用者の名前が要る。名前の入力欄を Spin ボタンの隣に必須の項目として置き、名前が空のまま Spin を押したら検証の文言を出して回さない。
  3. すべての当選記録の表示（当選直後の結果と My Winnings の一覧）に、名前・景品名・当選日時を必ず含める。
- 変更しないこと: 景品一覧、名前による当選記録の絞り込み、新しい順の並び、初期データ、起動方法（既存の要件のとおり）。
- 用語集: 変更なし。既存要件定義書 `docs/requirements.md` 1 を参照。
- システムの形態: 変更なし（GUI）。

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 配色の具体値 | 背景は ivory（#FFFFF0）。部品は dark green（#006400）。ホイールの区画は #006400 と #003300 を交互に使い、区画数が奇数のときの最後の区画だけ #004A1F を使う。区画の文字は白 | 依頼の「ivory」「dark green」を CSS の標準色名の値にした。区画は同系色の濃淡で区別する | 承認済（ANSWERS.md） |
| カード・見出し・ボタンの扱い | カード（景品のカード、入力の枠）、見出し、ボタン、ナビゲーション、表の見出しの背景は dark green、文字は白。入力欄と表の本体は白のまま | 依頼の「component styling (buttons, cards, headers)」を満たし、入力欄の文字を読みやすく保つ | 承認済（ANSWERS.md） |
| エラー文字の色 | dark green の太字 | 依頼で dark red を全面的に置き換えるため | 承認済（ANSWERS.md） |
| 名前欄の位置と表示 | 名前の入力欄を Spin ボタンと同じ行に置く。ラベルは「Your name (required)」。入力欄に required の属性を付ける | 依頼の「a required text field next to the spin control」を、そのまま形にした | 承認済（ANSWERS.md） |
| 空の名前で Spin を押したときの動作 | 検証の文言「Please enter your name before spinning.」を名前欄の下に出し、回さず、抽選も記録もしない。31 文字以上も同じ扱いで「Name must be 30 characters or fewer.」 | 既存の動作（既存要件の名前の規則）と同じ。依頼の「shows a validation message and does not spin」を満たす | 承認済（ANSWERS.md） |
| 当選結果の表示 | 当選したら、結果欄に景品名（見出し）と、名前・景品名・当選日時（ブラウザの地域形式、英語表記）を表示する | 依頼の「every winning record must show the player's name together with the prize and the date」 | 承認済（ANSWERS.md） |
| 当選記録の表の列 | 列は Player、Prize、Date won の順。Date won には当選日時を表示する（既存の表示形式を使う） | 依頼の「existing records views included」。名前の列を足し、日付の列の見出しを内容に合わせた | 承認済（ANSWERS.md） |
| 既存の名前の検査 | 空・30 文字超の検査と、検査に通らないと回さない動作は変えない | 既に満たしている（既存要件の名前の規則）。変えると既存の機能を壊すため | 承認済（ANSWERS.md） |

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照。業務課題は変えず、今回の変更は既存の業務課題（抽選、当選記録）に結びつく。

### 2-1. 業務の問題

変更なし。

### 2-2. 業務課題一覧

変更なし。

### 2-3. 見込み経営効果

変更なし（見込み経営効果は算定しない）。

## 3. 機能要件

- 入力データと出力データ: 変更なし（人手入力は名前とホイールを回す操作。出力は画面の表示だけ）。
- 利用フロー（全機能）: 変更なし。ホイール画面で、名前が空または 31 文字以上なら回さずに案内する点は既存の流れのとおり。
- システムの形態ごとの仕様（GUI）: 次の画面仕様を変える。

  - 画面: Spin the Wheel（`/`）
    - 主要要素（変更）: 名前の入力欄を Spin ボタンと同じ行に置く。入力欄のラベルは「Your name (required)」。入力欄に required の属性を付ける。
    - 表示項目（変更）: 当選したら、景品名（見出し）、名前、景品名、当選日時（ブラウザの地域形式）を結果欄に表示する。
    - エラー時の見え方: 変更なし。
  - 画面: My Winnings（`/my-winnings`）
    - 表示項目（変更）: 当選記録の表の列を Player（名前）、Prize（景品名）、Date won（当選日時）にする。
  - 画面の配色（変更）: 全画面で背景は ivory、部品は dark green（1-2 の表のとおり）。

- 機能一覧

  | RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
  |---|---|---|---|---|
  | [追加] `RQ-FT-WINNING-RECORD-DISPLAY` | 業務機能 | 当選記録を表示するときは、名前・景品名・当選日時の 3 つを必ず表示する（当選直後の結果と、My Winnings の一覧） | `RQ-BK-WINNING-HISTORY-RECORD` | 誰の当選か、いつの当選かが分からず、記録として役に立たない |

### 3-1. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 3-2. 業務ルール

変更なし。回すときの名前の規則（既存要件）は既存のままで、名前の検査と、検査に通らないと回さない動作を変えない。

### 3-3. 外部連携

変更なし。外部連携は無い。

### 3-4. 画面共通（ナビゲーションと外観）

| RQ-ID | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|
| [削除] `RQ-UI-LIGHT-GRAY-DARK-RED-THEME` | 画面共通 | 削除理由: 配色を ivory と dark green に変えるため、この要件の内容（light gray と dark red）は使わない。不要になる `RQ-BK-*` は無い（同じ業務課題 `RQ-BK-PRIZE-DRAW-WHEEL` は新しい要件が引き続き受ける） | `RQ-BK-PRIZE-DRAW-WHEEL` | 依頼の配色にならない（削除） |
| [追加] `RQ-UI-IVORY-DARK-GREEN-THEME` | 画面共通 | 全画面の背景は ivory（#FFFFF0）。ナビゲーション、ボタン、カード、見出し、表の見出し、ホイールの区画と指針、エラーの文字は dark green（#006400）。light gray と dark red は使わない | `RQ-BK-PRIZE-DRAW-WHEEL` | 依頼で指定された配色にならない |
| [追加] `RQ-UI-SPIN-NAME-FIELD` | 画面共通（Spin the Wheel 画面） | 名前の入力欄を Spin ボタンの隣（同じ行）に置き、必須の項目として示す（ラベルに「required」と書き、required の属性を付ける）。空で Spin を押したら、名前欄の下に検証の文言を出して回さない | `RQ-BK-PRIZE-DRAW-WHEEL`, `RQ-BK-WINNING-HISTORY-RECORD` | 名前を入れずに回してしまい、誰の当選か分からない記録になる |

## 4. データ

変更なし。既存要件定義書 `docs/requirements.md` 4 を参照。当選記録の項目（名前、景品名、当選日時）は既に保存されており、今回は表示だけを変える。CRUD テーブル（4-3）、状態遷移（4-4）、画面一覧（4-5）も変更なし。

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` 5 を参照。

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` 6 を参照。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| [追加] `RQ-TS-SPIN-NAME-FIELD` | 名前の入力欄が Spin の隣に必須の項目として置かれ、空では回らないこと | サーバーが起動している | 1. トップ画面を開く 2. 名前の入力欄と Spin ボタンの位置と属性を確かめる 3. 名前を空にして Spin を押す | 入力欄は Spin ボタンと同じ行にあり、required の属性がある。空で Spin を押すと検証の文言が出て、結果は出ない | `RQ-UI-SPIN-NAME-FIELD` | `RQ-BK-PRIZE-DRAW-WHEEL`, `RQ-BK-WINNING-HISTORY-RECORD` |
| [追加] `RQ-TS-RECORD-SHOWS-NAME-PRIZE-DATE` | 当選記録の表示に、名前・景品名・当選日時が必ず含まれること | 初期データがある（名前「Sample Player」の記録 3 件） | 1. 名前「Alice」で 1 回回す 2. 結果の応答の記録を確かめる 3. My Winnings の表の列を確かめる 4. My Winnings で「Sample Player」を表示する | 2 の記録に名前、景品名、当選日時がある。3 の表の列は Player、Prize、Date won。4 の各行に名前、景品名、当選日時が出る | `RQ-FT-WINNING-RECORD-DISPLAY`, `RQ-UI-MY-WINNINGS-SCREEN` | `RQ-BK-WINNING-HISTORY-RECORD` |
| [削除] `RQ-TS-THEME-COLORS` | 削除理由: 配色の要件（`RQ-UI-LIGHT-GRAY-DARK-RED-THEME`）を外すため、このシナリオも外す。下の新しいシナリオが引き継ぐ | ― | ― | ― | `RQ-UI-LIGHT-GRAY-DARK-RED-THEME`（削除） | `RQ-BK-PRIZE-DRAW-WHEEL` |
| [追加] `RQ-TS-IVORY-DARK-GREEN-THEME` | 背景は ivory、部品は dark green で、light gray と dark red が使われていないこと | サーバーが起動している | 1. 3 つの画面それぞれを開く 2. スタイルシートの色の指定を確かめる | スタイルシートに ivory（#FFFFF0）と dark green（#006400）があり、#D3D3D3 と #8B0000 が無い。各画面がそのスタイルシートを読み込む | `RQ-UI-IVORY-DARK-GREEN-THEME` | `RQ-BK-PRIZE-DRAW-WHEEL` |

- すべての [追加] の `RQ-FT`・`RQ-UI`・`RQ-EX` は、上の [追加] のシナリオのいずれかの「検証する要件ID」に現れる。
- 既存のシナリオは変えない。
