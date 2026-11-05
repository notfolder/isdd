# 変更要件定義書: 利用者に見える「景品（prize）」の表示語を「報酬（reward）」に置き換える

判定日: 2026-11-05 / 出典: REQUEST.md（変更 2）、ANSWERS.md（固定回答）、正本 `docs/requirements.md`（変更の基準）

本書は変更分だけを書く。正本 `docs/requirements.md` は書き換えない。

## 1. 目的・前提

- 今回の変更の目的: 利用者に見える英語の表示語を「prize」から「reward」に替える（ナビゲーション、ページのタイトルと見出し、ボタン、表の見出し、メッセージ、当選記録の表示）。「prize」「prizes」は画面の文言から消す。動作は変えない。
- 用語集: 日本語の業務用語「景品」は変えない（正本と設計書の日本語の説明はそのまま）。変えるのは利用者に見える英語の表示語だけ。対応は次の表のとおり。

| 旧（画面の英語） | 新（画面の英語） | 対象 |
|---|---|---|
| Prize List | Reward List | ナビゲーションのリンク、見出し、ページのタイトル |
| prize（件数、「to win a prize」） | reward | 件数の文、当選を促す文 |
| Prize（表の見出し、結果欄の項目名） | Reward | My Winnings の表、Spin の結果欄 |
| Prize wheel（ホイールの代替文） | Reward wheel | ホイールの代替文 |
| 「No prizes are available right now.」 | 「No rewards are available right now.」 | 景品 0 件のメッセージ |
| 「The prize list could not be loaded.」 | 「The reward list could not be loaded.」 | 読み込みの失敗のメッセージ |
| URL `/prizes` | URL `/rewards`（旧い `/prizes` は `/rewards` へ転送） | 画面の URL |

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 日本語の「景品」 | 業務用語として残す。画面の英語（利用者に見える文字）だけを「reward」にする | 依頼は「everywhere the user can see it」。日本語の文書は利用者に見えないため | 承認済（REQUEST.md の依頼、ANSWERS.md） |
| 表示語の対応 | 上の表のとおり。「Reward List」「Reward」「No rewards…」「reward list…」「Reward wheel」 | 依頼の語を英語の名詞として直した最小の形 | 承認済（同上） |
| URL `/prizes` | `/rewards` に替え、旧い `/prizes` は `/rewards` へ 301 で転送する | 依頼は「prize が画面から消える」ことを求める。アドレスバーの URL も利用者に見えるため。転送は旧いブックマークを壊さないため | 承認済（同上） |
| 公開 API のパスと JSON のキー | 変えない（`/api/prizes`、`/api/winnings` の `prize_name`、`/api/spins` の `prize` など） | API は画面の文言ではなく、画面と API の内部の約束。依頼の「behaviour stays the same」に従い、変えると既存の動作の範囲が広がるため | 承認済（同上） |
| 内部の名前（Python の関数名、DB のテーブル名と列名、テスト関数名、`DS-*` と `RQ-*` の ID） | 変えない | 利用者に見えない。ID は意味が変わらないので採番し直さない（`isdd-spec` の ID 規則） | 承認済（同上） |
| 記録の名前の表示 | 変えない（保存された名前をそのまま出す） | 依頼は表示語の変更だけ | 承認済（同上） |

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照（業務課題は既存の `RQ-BK-*` のまま）。

## 3. 機能要件

### 3-0. 変更の要約

| 区分 | RQ-ID | 内容 |
|---|---|---|
| 変更なし（ID と意味は同じ。表示語だけを 3-8 の表で置き換える） | 下の 3-8 の表に載せた RQ-ID | 表示語（英語）の置き換え |
| 変更なし | 上以外のすべての RQ-ID | 動作、規則、データは変えない |

- [追加] と [削除] の要件は無い。表示語の置き換えは要件の意味を変えないため、RQ-ID を採番し直さない。正本への反映は実装後レビューが行う（3-8 の表の箇所の英語の文言を置き換える）。

### 3-1. 帳票・出力ファイル

変更なし。

### 3-2. 業務ルール

変更なし。既存要件定義書 3-2 を参照（`RQ-FT-PRIZE-SELECTION-RULE` の表示メッセージだけが 3-8 の表のとおり変わる）。

### 3-3. 外部連携

変更なし（外部連携は無い）。

### 3-4. 画面共通（ナビゲーションと外観）

変更なし（リンク名だけが 3-8 の表のとおり変わる）。

### 3-5. 回す画面の名前入力

変更なし。

### 3-6. 当選記録の表示

変更なし（表の列名と結果欄の項目名だけが 3-8 の表のとおり変わる）。

### 3-7. 機能一覧

変更なし。

### 3-8. 表示語の置き換え（ID と意味は変えない）

| RQ-ID | 置き換える画面の英語（旧 → 新） |
|---|---|
| `RQ-UI-NAVIGATION-MENU` | 「Prize List」→「Reward List」（3 画面のリンク名）。リンク先の URL は `/rewards` |
| `RQ-UI-PRIZE-LIST-SCREEN` | 画面名「Prize List（`/prizes`）」→「Reward List（`/rewards`）」。見出し「Reward List」。件数の文は「N reward(s) to win on the wheel」。読み込み失敗は「The reward list could not be loaded.」。旧い `/prizes` は `/rewards` へ 301 で転送 |
| `RQ-UI-SPIN-SCREEN` | ホイールの代替文「Reward wheel」。結果欄の項目名「Prize」→「Reward」。説明文「see which reward you win」 |
| `RQ-UI-MY-WINNINGS-SCREEN` | 表の見出し「Prize」→「Reward」（列の順は Player、Reward、Date won） |
| `RQ-FT-WINNING-RECORD-DISPLAY` | 表示項目の「Prize」→「Reward」（My Winnings の列。結果欄の項目名） |
| `RQ-FT-PRIZE-SELECTION-RULE` | 0 件のときのメッセージ「No prizes are available right now.」→「No rewards are available right now.」（応答 409 は変えない） |
| `RQ-FT-VIEW-OWN-WINNINGS` | 記録が無いときの文「No winning records for this name yet. Spin the wheel to win a reward!」（「a prize」→「a reward」） |
| `RQ-FT-VIEW-PRIZE-LIST` | 読み込み失敗のメッセージ「The reward list could not be loaded.」 |

## 4. データ

変更なし（DB のテーブル名と列名は内部のまま）。

### 4-5. 画面一覧（GUI の場合のみ）

画面 `RQ-UI-PRIZE-LIST-SCREEN` の URL と表示名だけが変わる（3-8 参照）。画面の構成と機能は変わらない。

## 5. 非機能要件

変更なし。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

既存のシナリオは、手順と期待結果の英語（画面の文言、URL）だけが変わる。新しい [追加] の `RQ-FT`・`RQ-UI`・`RQ-EX` は無いので、第 7 章のシナリオは増減しない。次のシナリオの文言だけを置き換える。

| RQ-TS | 置き換える文言 |
|---|---|
| `RQ-TS-NAVIGATION-ALL-PAGES` | リンク名「Reward List」、URL `/rewards` |
| `RQ-TS-PRIZE-LIST-SHOWS-ALL` | 「Reward List を開く」、URL `/rewards` |
| `RQ-TS-RECORD-SHOWS-NAME-PRIZE-DATE` | My Winnings の表の列「Player、Reward、Date won」 |
| `RQ-TS-IVORY-DARK-GREEN-THEME` | 各画面の URL（`/rewards`） |

## 8. 承認の記録

- 1-2 の項目は、REQUEST.md の依頼と ANSWERS.md の固定回答で承認済とする（「承認はすべて与えられたもの」）。
- 除外要件は無し。
