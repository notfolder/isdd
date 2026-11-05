# 変更要件定義書: 「prize（景品）」を「reward（報酬）」へ用語変更

- 作成日: 2026-11-05
- フロー: 変更（既存の要件定義書 `docs/requirements.md` と詳細設計書 `docs/detail_design.md` がある）
- 正本: `docs/requirements.md`（書き換えない。反映は実装後に isdd-build の実装後レビューが行う）
- 出典: REQUEST.md（変更依頼 2）、contract.md（契約）、ANSWERS.md（ヒアリングへの固定回答）
- 記法: 要件の意味は変えず、画面に出る言葉だけを変える。要件 ID は据え置くため [追加] も [削除] も無い。文言の変更は「文言変更」と書く

## 変更の内容（依頼の要約）

利用者の画面に見える「prize / prizes」の語を、すべて「reward / rewards」にする。対象は、上部メニューの名前、画面の見出し、表の見出し、説明文、ホイールの表示、ボタン、メッセージ（「You won」の結果、「No prize」系の文）、当選記録の表。動作は変えない。名前必須、名前ごとの記録、ivory と dark green の配色は残す。

変更後、画面（HTML・画面の文言・アドレスバーに出る URL）に「prize」の語が無いこと。

## 1. 業務の問題と業務課題

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| 要件 ID の扱い | RQ-ID・DS-ID は据え置く（`RQ-FT-VIEW-PRIZE-LIST` など、ID の中の PRIZE は残す） | ID は内部の識別子で画面に出ない。要件の意味が変わらない（語の置き換えだけ）ため、ID 規則の「意味が変わる場合だけ新 ID」に当てはまらない。ID を変えると対応表と全章の参照を書き換えることになり、変更の範囲が広がる | 承認済（ANSWERS.md の範囲で決定） |
| API・データ・コードの名前 | `/api/prizes`、JSON のキー（`prize`、`prizeName`）、DB の表名（`prize`、`winning_record.prize_name`）、関数名（`listPrizes` など）は据え置く | 画面に出ない。依頼の「the user interface」の範囲に入らない。動作と互換性を保つため | 承認済（ANSWERS.md の範囲で決定） |
| 画面のルート | 上部メニューのリンク先 `#/prizes` を `#/rewards` にする | アドレスバーに出る URL は画面に見える。旧 URL は残さない（表示を変えるだけで、旧 URL の互換は要らない） | 承認済（ANSWERS.md の範囲で決定） |
| 初期のサンプル名 | 「Grand Prize Headphones」を「Grand Reward Headphones」にする。他の景品名に語は無い | 初期データは画面に出る。DATA_DIR が空のとき入るのは契約上の初期データ | 承認済（ANSWERS.md の範囲で決定） |
| 既存の DATA_DIR のデータ | 既に保存された旧名（「Grand Prize Headphones」など）は書き換えない | 初期データは DATA_DIR が空のときだけ入る既存の動き。移行処理を足すと動作の変更になるため。契約では空の DATA_DIR で起動する | 承認済（ANSWERS.md の範囲で決定） |
| 日本語の説明文 | 正本の日本語の「景品」は「報酬」に書き換える（英語の画面語と合わせる） | 正本は画面の語と対応させて読むため。意味は同じ | 承認済（ANSWERS.md の範囲で決定） |
| 確認方法 | 画面の語の確認は、HTML と画面の文言（API のメッセージを含む）に「prize」が無いことを E2E で見る。新しい E2E は `DS-TS-REWARD-WORDING-E2E` の 1 本 | 依頼の「must not appear anywhere in the user interface」を機械的に確かめるため | 承認済（ANSWERS.md の範囲で決定） |

## 2. 業務

### 2-1. 業務の問題（変更で扱うギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 画面の言葉（prize）が依頼の用語（reward）と違う | RQ-BZ-PRIZE-DRAW | 画面のすべての語が reward に統一されている | 上部メニュー・見出し・表の見出し・メッセージ・サンプル名に prize の語が出る | 数値の記載無し（依頼文に無し） | 依頼の用語と一致しない |

### 2-2. 業務課題一覧

変更なし。既存要件定義書 `docs/requirements.md` 2-2 の業務課題は、そのまま（業務の中身は変えない。語だけを変える）。

### 2-3. 見込み経営効果

変更なし。見込み経営効果は算定しない。

## 3. 機能要件

### 3-1. 機能一覧の変更

文言変更のみ。機能は増えも減りもしない。

| RQ-ID | 変更の内容 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|
| RQ-FT-VIEW-PRIZE-LIST | 機能名の表示を「Reward List」（景品一覧 → 報酬一覧）。動作は変えない | RQ-BK-SHOW-PRIZES |
| RQ-FT-WEIGHTED-DRAW | 「No prizes are available.」→「No rewards are available.」（景品が 0 件のときの文言） | RQ-BK-SPIN-DRAW |
| RQ-FT-SHOW-WINNING-DETAILS | 表の見出し「Prize」→「Reward」（名前・報酬・日時） | RQ-BK-SHOW-WINNER |
| RQ-FT-SPIN-WHEEL | ホイールの表示語（aria-label「Reward wheel」）と、結果の「You won」の後の報酬名 | RQ-BK-SPIN-DRAW |

### 3-2. 帳票・出力ファイル

変更なし。帳票・出力ファイルは無い。

### 3-3. 業務ルール

文言変更のみ。業務ルールの中身は変えない。RQ-FT-WEIGHTED-DRAW の文言だけを 3-1 のとおり変える。

### 3-4. 外部連携

変更なし。外部連携は無い。

### 3-5. 画面共通のナビゲーション

文言変更のみ。上部メニューのリンク名を「Reward List」にし、リンク先を `#/rewards` にする（RQ-UI-NAVIGATION-MENU）。メニューの 3 画面と強調の動きは変えない。

## 4. データ

### 4-1. データ要件一覧

文言変更のみ。保存する項目と DB の構造は変えない。初期サンプルの景品名（`Grand Prize Headphones` → `Grand Reward Headphones`）だけが変わる（RQ-DT-PRIZE）。

### 4-2. 業務エンティティとデータ項目

変更なし。エンティティ名（景品）と項目名は、内部の識別子として据え置く。

### 4-3. CRUD テーブル

変更なし。

### 4-4. 状態遷移

変更なし。

### 4-5. 画面一覧（GUI の場合のみ）

文言変更のみ。

| RQ-ID | 変更の内容 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|
| RQ-UI-PRIZE-LIST-SCREEN | 画面名と見出しを「Reward List」（報酬一覧画面）、表の見出しを「Reward」にする | RQ-BK-SHOW-PRIZES |
| RQ-UI-SPIN-SCREEN | 結果欄の「You won」の後の報酬名、ホイールの表示語 | RQ-BK-SPIN-DRAW |
| RQ-UI-MY-WINNINGS-SCREEN | 表の見出し「Reward」 | RQ-BK-TRACK-WINNINGS |
| RQ-UI-NAVIGATION-MENU | メニューのリンク名「Reward List」、リンク先 `#/rewards` | RQ-BK-SHOW-PRIZES, RQ-BK-SPIN-DRAW, RQ-BK-TRACK-WINNINGS |

## 5. 非機能要件

文言変更のみ。RQ-NF-UI-LANGUAGE-EN（画面の文言はすべて英語）は、変更後の語（reward）で満たす。RQ-NF-THEME-IVORY-GREEN は変更なし。

| RQ-ID | 区分 | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|---|
| RQ-NF-UI-LANGUAGE-EN | 文言変更 | 画面 | 画面の文言はすべて英語（契約）。新しい語は reward | RQ-BK-SHOW-PRIZES | 指定の言語で表示されず、採点で使えない |

## 6. 運用要件

変更なし。既存要件定義書 第 6 章を参照。

## 7. テスト用利用シナリオ

既存のシナリオの確かめる内容は変わらない。文言の変更を確かめるため、次の 1 本を足す（[追加]）。

| RQ-ID | 区分 | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|---|
| [追加] RQ-TS-REWARD-WORDING | 追加 | 画面の語が reward に統一され、prize が画面に出ないこと | 起動直後 | 1. 3 画面の HTML を開き、上部メニュー・見出し・表の見出しを見る。2. 景品一覧の画面を開き、報酬一覧の見出しと表の見出しを見る | 1. 上部メニューに「Reward List」があり、HTML のどこにも prize の語が無い。2. 見出しは「Reward List」、表の見出しは「Reward」。`#/rewards` で開ける | RQ-UI-NAVIGATION-MENU, RQ-UI-PRIZE-LIST-SCREEN, RQ-FT-SHOW-WINNING-DETAILS | RQ-BK-SHOW-PRIZES |

注: 追加の RQ-ID は `RQ-TS-REWARD-WORDING` の 1 件だけ。RQ-FT・RQ-UI・RQ-NF は増やさないので、正本の要件の数は変わらない。

## 8. 変更後の業務課題と要件の対応

変更なし。対応の ID は据え置く。文言変更の要件（RQ-DT-PRIZE を含む）の業務課題は次のとおり。

| RQ-ID | 対応業務課題ID（RQ-BK-*） |
|---|---|
| RQ-DT-PRIZE | RQ-BK-SPIN-DRAW, RQ-BK-SHOW-PRIZES |
| RQ-NF-THEME-IVORY-GREEN | RQ-BK-THEME-STYLE |

## 確認事項

- 承認を求める項目は 1-2 の表のとおり。ANSWERS.md により承認は与えられている。
