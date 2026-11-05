# 変更設計書: 配色の変更、名前必須のスピン欄、当選記録への名前の表示

- 作成日: 2026-11-05
- 入力: `change_requirements.md`（この変更の要件）、正本 `docs/requirements.md`・`docs/detail_design.md`（既存設計）
- 正本: `docs/detail_design.md`（書き換えない。反映は実装後に isdd-build の実装後レビューが行う）
- 記法: 設計要素は変えずに対応だけを変える行も含め、[追加] と [削除] を行を分けて書く。中身が変わる設計要素は、旧 ID を [削除]、新 ID を [追加] にする（同じ ID に中身の変更を載せない）

## 1. 最小設計と要件の除外

要件と設計の対応は、第 11 章の対応表（[追加] と [削除] の行）に書く。新しい要件は、名前欄の必須表示（RQ-UI-SPIN-NAME-FIELD）、当選記録の名前の表示（RQ-FT-SHOW-WINNING-DETAILS）、配色（RQ-NF-THEME-IVORY-GREEN）の 3 つ。

### 11-1. 除外要件

変更なし。この変更で除外する要件は無い。

## 2. 技術選定

変更なし。既存設計 `docs/detail_design.md` 第 1 章（Node.js 24、組み込み `http`、`node:sqlite`、静的な HTML・CSS・JavaScript）を引き継ぐ。外部パッケージは増やさない。

## 3. データ設計

### 3-1. データモデル

変更なし。既存設計 `docs/detail_design.md` 3-1 を参照（DB の表・列・索引は変えない。当選記録の名前は既に保存されている）。

### 3-2. トランザクションと排他制御

変更なし。

### 3-3. 状態遷移

変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース（画面）

| DS-IF | 画面・要素 | 機能 |
|---|---|---|
| DS-IF-SPIN-SCREEN [削除] | 旧: 見出し「Spin the Wheel」、名前の入力欄、Spin ボタン、ホイール、結果欄、エラー欄 | 削除理由: 依頼 2 で名前欄を必須にし、結果の表示に名前を加えるため。新しい ID に置き換える |
| DS-IF-SPIN-SCREEN-NAME-REQUIRED [追加] | 見出し「Spin the Wheel」。名前の入力欄（ラベルは「Your name (required)」。`required` の属性付き。最後に使った名前を入れる）と Spin ボタンを同じ行に置く。Spin を押したとき、前後の空白を除いた名前が 1〜30 文字でなければ、サーバーへ送らず、エラー欄に「Please enter your name (1-30 characters).」を出し、名前の欄にフォーカスを移す。ホイールは回らず、記録もしない。1〜30 文字ならサーバーへ送る（サーバーの検証は残る）。ホイール（景品ごとの扇形、同じ大きさ。扇形は dark green の 2 色を交互に使い、景品数が奇数のときは最後の扇形だけ別の濃い色にする。文字は扇形の中央に景品名）。結果カード（dark green の背景に白い文字。「You won」、景品名、「Recorded for 名前 at 日時」） | 名前を必須で入力して回し、結果（名前・景品名・日時）を表示する |
| DS-IF-MY-WINNINGS-SCREEN [削除] | 旧: 見出し「My Winnings」、名前の入力欄、Show my winnings ボタン、表（景品名、当選日時）、件数表示、エラー欄 | 削除理由: 表に名前の列を加えるため。新しい ID に置き換える |
| DS-IF-MY-WINNINGS-SCREEN-DETAILS [追加] | 見出し「My Winnings」、名前の入力欄、Show my winnings ボタン、表（列: 「Player」「Prize」「Won at」。各行に当選者の名前、景品名、当選日時）、件数表示、エラー欄 | 名前で絞った当選記録を、名前・景品・日時の 3 項目で見る |
| DS-IF-STYLESHEET [削除] | 旧: 背景 #e6e6e6（薄い灰色）、部品 #8b0000（濃い赤）、文字は白 | 削除理由: 依頼 1 の配色変更（背景 ivory、部品 dark green）。新しい ID に置き換える |
| DS-IF-THEME-STYLESHEET [追加] | 背景 #fffff0（ivory）。部品は #006400（dark green）: 上部メニュー、ボタン、見出し、カードの枠と結果カードの背景、表の見出し、フッター、ホイールの枠。ホバーと押下は同じ緑の濃い色（#004d1a か #00800f）。文字は白（部品上）と濃い灰色（背景上）。表の偶数行は薄い緑（#eef5ea）。エラー欄は白地に dark green の枠と濃い文字（赤は使わない）。幅の狭い画面でも崩れないレイアウト | 配色とレイアウト |

上部メニュー（3 画面への移動）と景品一覧の画面は、要素も機能も変更なし。配色だけが新しいスタイルシートに従う。

#### Web API（画面を支える内部 API。外部公開しない）

| DS-IF | メソッドとパス | 用途 | 入力 | 出力 | エラー |
|---|---|---|---|---|---|
| DS-IF-API-WINNINGS [削除] | GET /api/winnings?name=... | （旧）名前で絞った当選記録 | 旧のとおり | 200: `{"name", "winnings": [{"id", "prizeName", "wonAt"}]}` | 旧のとおり |
| DS-IF-API-WINNINGS-DETAILS [追加] | GET /api/winnings?name=... | 名前で絞った当選記録（新しい順、最大 100 件）。各記録に当選者の名前を含める | クエリ `name`（前後の空白を除いて 1〜30 文字） | 200: `{"name": "...", "winnings": [{"id", "playerName", "prizeName", "wonAt"}]}`。`playerName` は `name` と同じ（完全一致で絞るため） | 400: `{"error": "Please enter your name (1-30 characters)."}`（変更なし） |

抽選の API（POST /api/spin）と景品の API（GET /api/prizes）は変更なし。抽選の応答には既に `record.playerName` が入っている。

#### 外部システム連携・外部 DB 連携

変更なし。

#### 静的ファイル

静的ファイルの配り方は変更なし（ファイルの種類と経路の制限は既存のまま）。変わるのは中身の配色だけで、その要件の受け先は第 11 章の対応表に書く。

### 4-2. 内部設計

#### 処理フロー（抽選）

変更なし。サーバー側の抽選と検証は既存のまま（既存設計 4-2）。画面側で送信前に名前を検証する処理は、DS-IF-SPIN-SCREEN-NAME-REQUIRED の画面の仕様に含める（サーバーの処理は増えない）。

#### 各処理の役割

変更なし。`handleWinnings` は DS-IF-API-WINNINGS-DETAILS の応答形（`playerName` を各記録に入れる）を返すよう直す。`listWinningsByName` は変えない。

### 4-3. 状態遷移の処理

変更なし。

## 5. クラス設計

変更なし。

## 6. エラーハンドリングとセキュリティ設計

変更なし（既存設計 6）。名前の違反の扱い（抽選も記録もしない。文言「Please enter your name (1-30 characters).」）は変わらず、画面では送信前に止める動きが加わる（DS-IF-SPIN-SCREEN-NAME-REQUIRED）。

## 7. コード設計

### ファイル一覧（対応表の対象）

| ファイル | 役割 | 含まれる関数 | 実現する設計 ID |
|---|---|---|---|
| src/routes.js [削除] | 経路と応答 | handleWinnings | DS-IF-API-WINNINGS（対応表の行を書き換える） |
| src/routes.js [追加] | 経路と応答 | handleWinnings | DS-IF-API-WINNINGS-DETAILS（対応表の行の新しい ID） |

`src/server.js`、`src/spin.js`、`src/db.js` は変更なし。`public/`（index.html、style.css、app.js）は対応表の対象外（既存の扱いのまま）。

### 依存の規則

変更なし（依存の規則は無い）。

### コーディング規約

変更なし。

### 対応表

既存の対応表の行のうち、`handleWinnings` の行だけを新しい設計 ID に書き換える（上の [削除] と [追加] の行のとおり）。他の行は変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

- [削除] 非機能要件の検証: 配色・英語表示は E2E の中で HTML と CSS の文言を確かめる（DS-TS-NAVIGATE-SCREENS-E2E）
- [追加] 非機能要件の検証: 配色は DS-TS-THEME-COLORS-E2E で、CSS の値（背景 #fffff0、部品 #006400）と旧い値の不在を確かめる。英語表示は DS-TS-NAVIGATE-SCREENS-E2E のまま

### 8-2. E2E テストのシナリオ

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| DS-TS-NAVIGATE-SCREENS-E2E [削除] | 3 画面へメニューで移動できる。英語で配色の指定がある（RQ-TS-NAVIGATE-SCREENS） | 起動 | GET /、/style.css を取得し、メニューのリンク 3 件、見出し、配色の値を確かめる | 3 画面へのリンクがある。CSS に #e6e6e6 と #8b0000 がある |
| DS-TS-NAVIGATE-SCREENS-E2E [追加] | 3 画面へメニューで移動できる。英語で表示される（RQ-TS-NAVIGATE-SCREENS） | 起動 | GET / を取得し、メニューのリンク 3 件、見出し、`lang="en"` を確かめる | 3 画面へのリンクがある。英語の見出し |
| DS-TS-SPIN-NAME-REQUIRED-E2E [追加] | 名前欄が必須で Spin の隣にあり、空・31 文字では抽選も記録もされない（RQ-TS-SPIN-NAME-REQUIRED） | 初期データのある起動 | GET / の HTML で、名前の入力欄に `required` があり、Spin ボタンと同じ form の中にあることを確かめる。POST /api/spin に空の名前と 31 文字の名前を送る | HTML に required と Spin の同じ form がある。両方 400、同じ文言、記録の件数が変わらない |
| DS-TS-WINNING-DETAILS-E2E [追加] | 当選記録に名前・景品名・日時がすべて出る（RQ-TS-WINNING-DETAILS） | 初期データのある起動 | POST /api/spin `{"name":"Alice"}` → 201。GET /api/winnings?name=Alice。GET / の My Winnings の表の見出し | 各記録に playerName が Alice、prizeName、wonAt がある。見出しに Player、Prize、Won at がある |
| DS-TS-THEME-COLORS-E2E [追加] | 全画面が ivory 背景と dark green の部品（RQ-TS-THEME-COLORS） | 起動 | GET /style.css を取得し、背景 #fffff0、部品 #006400 を確かめる。#e6e6e6 と #8b0000 が無いことを確かめる | 背景と部品の値がある。旧い値が無い |
（上の表で、メニューの E2E は旧い行と新しい行を分けて書いた。他の E2E の行は変更なし。「自分の当選記録」の E2E は、応答の各記録に名前が増えるが、確かめる件数と順序は同じで、行は変えない。）

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし（既存のコマンド。E2E のファイルが増えるが、`e2e/*.test.js` で全件を実行する）。

画面の動き（名前が空のとき送信前に止まり、ホイールが回らないこと）は、E2E では HTTP で確かめられない。実装後に Chromium で手動確認し、結果を報告する（isdd-build の実装完了確認）。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| DS-IF-SPIN-SCREEN [削除] | RQ-UI-SPIN-SCREEN, RQ-NF-BROWSER-SUPPORT |
| DS-IF-SPIN-SCREEN-NAME-REQUIRED [追加] | RQ-UI-SPIN-SCREEN, RQ-UI-SPIN-NAME-FIELD, RQ-FT-NAME-REQUIRED, RQ-FT-SHOW-WINNING-DETAILS, RQ-NF-BROWSER-SUPPORT |
| DS-IF-MY-WINNINGS-SCREEN [削除] | RQ-UI-MY-WINNINGS-SCREEN |
| DS-IF-MY-WINNINGS-SCREEN-DETAILS [追加] | RQ-UI-MY-WINNINGS-SCREEN, RQ-FT-SHOW-WINNING-DETAILS |
| DS-IF-STYLESHEET [削除] | RQ-NF-VISUAL-STYLE, RQ-NF-BROWSER-SUPPORT |
| DS-IF-THEME-STYLESHEET [追加] | RQ-NF-THEME-IVORY-GREEN, RQ-NF-BROWSER-SUPPORT |
| DS-FN-SERVE-STATIC-FILE | RQ-NF-VISUAL-STYLE [削除]（対応の差し替え） |
| DS-FN-SERVE-STATIC-FILE | RQ-NF-THEME-IVORY-GREEN [追加]（対応の差し替え） |
| DS-IF-API-WINNINGS [削除] | RQ-FT-VIEW-OWN-WINNINGS |
| DS-IF-API-WINNINGS-DETAILS [追加] | RQ-FT-VIEW-OWN-WINNINGS, RQ-FT-SHOW-WINNING-DETAILS |
| DS-TS-NAVIGATE-SCREENS-E2E [削除] | RQ-TS-NAVIGATE-SCREENS |
| DS-TS-NAVIGATE-SCREENS-E2E [追加] | RQ-TS-NAVIGATE-SCREENS |
| DS-TS-SPIN-NAME-REQUIRED-E2E [追加] | RQ-TS-SPIN-NAME-REQUIRED |
| DS-TS-WINNING-DETAILS-E2E [追加] | RQ-TS-WINNING-DETAILS |
| DS-TS-THEME-COLORS-E2E [追加] | RQ-TS-THEME-COLORS |

変更しない既存の設計要素（上部メニュー、景品一覧、抽選と景品の API）の対応は、既存設計のまま。配色の変更は、新しいスタイルシートの要素の対応（上の表）が受ける。
