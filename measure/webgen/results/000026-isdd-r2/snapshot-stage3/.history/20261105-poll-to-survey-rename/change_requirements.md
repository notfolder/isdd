# 変更要件定義書: 「poll」から「survey」への用語変更（Survey Website）

本書は変更の記録である。正本の `docs/requirements.md` は書き換えない（実装後に `isdd-build` の実装後レビューが反映する）。
依頼の出どころ: `REQUEST.md`（変更 2）。区分は各行の `[追加]` と `[削除]`。
要件 ID（`RQ-*`）と設計 ID（`DS-*`）は変えない。ID は利用者の画面に出ない内部の識別子であり、変えると対応表の全行を書き換えることになるため。

## 1. 目的・前提

### 目的

利用者の画面に見える「poll（投票テーマ）」の語を「survey（調査）」に置き換える。画面の見出し、ナビゲーション、ボタン、案内文、結果画面、ブラウザのタイトル、URL のパスを対象とする。振る舞い（一人一票、確認つきの投票、結果、light yellow と dark slate gray の配色）は変えない。

既存の目的（`docs/requirements.md` 1）は変わらない。

### 用語集

[追加] 利用者の画面の用語: 「投票テーマ」は画面では「survey」と呼ぶ。内部の名前（テーブル名 `polls`、Python の名前、要件 ID の `POLL`）は変えない。画面に出ない名前は変更の対象外。

### システムの形態

変更なし。既存要件定義書 `docs/requirements.md` 1 を参照（GUI）。

### 1-1. 技術制約（前提として記録する。要件ではないため ID は付与しない）

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照（この変更で技術制約は増えない）。

### 1-2. 依頼に無く自分で決めた項目（必須）

| 項目 | 決めた内容 | 根拠（最小案か、依頼のどこから推測したか） | 承認（承認済 / 未確認） |
|---|---|---|---|
| URL のパス | `/polls` を `/surveys` に変える（`/polls/<id>` は `/surveys/<id>`、`/polls/<id>/vote` は `/surveys/<id>/vote`、`/polls/<id>/results` は `/surveys/<id>/results`）。ブラウザのアドレス欄も利用者に見えるため | 依頼の「'poll' must not appear anywhere in the user interface」。アドレス欄の `poll` も UI に含むと読む | 承認済（ANSWERS.md により承認したものとして進める） |
| 旧 URL の転送 | `/polls` 系の旧パスは新しいパスへ 302 で転送する（ブックマークや外部からのリンクを壊さないため） | 依頼の「Behaviour stays the same」。URL を変えても既存の行き先は残す最小案。転送先は UI に出ない | 承認済（ANSWERS.md により承認したものとして進める） |
| 内部の名前 | テーブル `polls`、Python の名前（`polls.py`、`poll_list_page` など）、要件 ID と設計 ID は変えない | 依頼の範囲は「user can see」。内部の名前を変えると対応表とテストの全件を書き換えることになり、振る舞いも変わらない | 承認済（ANSWERS.md により承認したものとして進める） |
| サイト名 | 「Polls Website」を「Survey Website」にする（ブラウザのタイトルとナビゲーションの見出し） | 依頼の「page titles」。サイト名も poll を含むため置き換える | 承認済（ANSWERS.md により承認したものとして進める） |
| 文言の対応 | 「Polls」→「Surveys」（ナビゲーションと一覧の見出し）、「poll」→「survey」（案内文とボタン）、「Choose a poll」→「Choose a survey」、「No polls yet.」→「No surveys yet.」、「Vote in this poll」→「Vote in this survey」、「You have already voted in this poll.」→「You have already voted in this survey.」、「The selected option is not valid for this poll.」→「The selected option is not valid for this survey.」 | 依頼の「rename the concept 'poll' to 'survey'」を文言に機械的に当てはめた最小案。「You have already voted」の語句は残す | 承認済（ANSWERS.md により承認したものとして進める） |
| 利用者の画面の用語の確認方法 | 各画面の HTML に `poll`（大文字小文字を問わず）が出ないことを E2E で確かめる | 依頼の「must not appear anywhere」を検査できる形にする | 承認済（ANSWERS.md により承認したものとして進める） |

## 2. 業務

### 2-0. 対象業務一覧

変更なし。既存要件定義書 `docs/requirements.md` 2-0 を参照（業務は `RQ-BZ-POLLING` のまま）。

### 業務フロー

変更なし。既存要件定義書 `docs/requirements.md` 3（業務フロー）を参照。画面の名前と URL が変わるだけで、流れは同じ。

### 2-1. 業務の問題（あるべき姿と現状のギャップ）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 利用者の画面に「poll」の語が出ており、依頼の用語「survey」と違う | `RQ-BZ-POLLING` | 利用者の画面の用語は「survey」に統一され、「poll」が出ない | 見出し、ナビゲーション、案内文、アドレス欄に「poll」が出る | 「poll」を含む画面の箇所（全画面、件数は実装時に数える） | 依頼の用語で利用者に提供できない |

### 2-2. 業務課題一覧（必須）

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） |
|---|---|---|---|---|
| [追加] `RQ-BK-SURVEY-WORDING` | 利用者の画面の用語を依頼の用語（survey）に統一する | 画面に「poll」の語が出ている | 利用者の画面（HTML とアドレス欄）に「poll」が出ない（目標値は 0 件） | `RQ-BZ-POLLING` |

既存の業務課題（`RQ-BK-BROWSE-POLLS`、`RQ-BK-CAST-VOTES`、`RQ-BK-SHOW-RESULTS`、`RQ-BK-COLOR-THEME`）は変えない。旧 URL の転送は既存の `RQ-BK-BROWSE-POLLS`（既存のリンクから閲覧できること）に結びつける。

### 2-3. 見込み経営効果

変更なし。既存要件定義書 `docs/requirements.md` 2-3 を参照（見込み効果は算定しない）。

## 3. 機能要件

### 入力データと出力データ

変更なし。既存要件定義書 `docs/requirements.md` 3 を参照。

### 利用者の利用フロー

変更なし。既存要件定義書 `docs/requirements.md` 3 を参照。画面名は「Surveys」になる。

### 画面遷移図

変更なし（遷移の形は同じ。ラベルとパスだけが変わる）。既存要件定義書 `docs/requirements.md` 3 を参照。

### 機能一覧

| RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
|---|---|---|---|---|
| [追加] `RQ-FT-LEGACY-POLL-URL` | 業務機能 | 旧パス（`/polls` 系）を開くと、同じ内容の新しいパス（`/surveys` 系）へ転送する | `RQ-BK-BROWSE-POLLS` | 既存のブックマークや外部のリンクを開いた利用者が、404 で行き先を失う |

既存の機能（調査の一覧と詳細、投票、二重投票の拒否、入力の検査、結果の表示、投票済みの無効化）は変えない。

### 3-1. 帳票・出力ファイル

変更なし。既存要件定義書 `docs/requirements.md` 3-1 を参照（帳票・出力ファイルは無い）。

### 3-2. 業務ルール

変更なし。既存要件定義書 `docs/requirements.md` 3-2 を参照。投票の判定とエラーの条件は変えず、表示の文言だけを変える。

### 3-3. 外部連携

変更なし。既存要件定義書 `docs/requirements.md` 3-3 を参照（外部連携は無い）。

## 4. データ

### 4-1. データ要件一覧

変更なし。既存要件定義書 `docs/requirements.md` 4-1 を参照（テーブルと保存は変えない。`RQ-DT-POLL-STORAGE` の SQLite のファイル名 `polls.db` も変えない）。

### 4-2. 業務エンティティとデータ項目

変更なし。既存要件定義書 `docs/requirements.md` 4-2 を参照。投票テーマの項目名は内部のまま（画面の表示名だけが「survey」になる）。

### 4-3. CRUD テーブル（必須）

変更なし。既存要件定義書 `docs/requirements.md` 4-3 を参照。

### 4-4. 状態遷移

変更なし。既存要件定義書 `docs/requirements.md` 4-4 を参照（状態を持つエンティティは無い）。

### 4-5. 画面一覧（GUI）

| RQ-ID | 画面名 | 対応する CRUD 操作（エンティティ名:操作種別） | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|
| [追加] `RQ-UI-SURVEY-WORDING` | 全画面（用語と URL のパス） | なし（表示のみ） | 利用者の画面に「poll」「polls」を出さない。ナビゲーションの見出しは「Surveys」、サイト名は「Survey Website」、一覧の見出しは「Surveys」、結果一覧と詳細の案内文は「survey」を使う。URL のパスは `/surveys` 系にする（`/` は `/surveys` へ転送する） | `RQ-BK-SURVEY-WORDING` |

[削除] `RQ-UI-POLL-LIST-SCREEN` の画面名と URL: 「Polls」、`/polls`。
[追加] `RQ-UI-POLL-LIST-SCREEN` の画面名と URL: 「Surveys」、`/surveys`。
[削除] `RQ-UI-POLL-DETAIL-SCREEN` の URL: `/polls/<id>`。投票の操作の URL: `/polls/<id>/vote`。
[追加] `RQ-UI-POLL-DETAIL-SCREEN` の URL: `/surveys/<id>`。投票の操作の URL: `/surveys/<id>/vote`。
[削除] `RQ-UI-POLL-RESULTS-SCREEN` の URL: `/polls/<id>/results`。
[追加] `RQ-UI-POLL-RESULTS-SCREEN` の URL: `/surveys/<id>/results`。
[削除] 画面共通のナビゲーション: 「Polls」（投票一覧）と「Results」（結果一覧）。
[追加] 画面共通のナビゲーション: 「Surveys」（調査一覧）と「Results」（結果一覧）。配色は `RQ-UI-COLOR-THEME` に従う。

既存の 4 画面の機能と目的は変えない（画面の名前と URL の表記だけを変える）。画面の名前の表記は `RQ-UI-SURVEY-WORDING` に従う。

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` 5 を参照。

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` 6 を参照。

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| [追加] `RQ-TS-VERIFY-SURVEY-WORDING` | 利用者の画面に「poll」の語が無く、ナビゲーションが「Surveys」である | 初期データがある | `/surveys`、`/surveys/1`、`/surveys/1/results`、`/results` を開き、各 HTML に `poll`（大文字小文字を問わず）が無いことと、ナビゲーションに「Surveys」があることを確かめる。投票後の案内文（「You have already voted in this survey.」）も確かめる | 4 画面の HTML に `poll` が無い。ナビゲーションに「Surveys」と「Results」がある | `RQ-UI-SURVEY-WORDING`、`RQ-UI-POLL-LIST-SCREEN`、`RQ-UI-POLL-DETAIL-SCREEN`、`RQ-UI-POLL-RESULTS-SCREEN`、`RQ-UI-RESULTS-LIST-SCREEN` | `RQ-BK-SURVEY-WORDING` |
| [追加] `RQ-TS-VERIFY-LEGACY-URL` | 旧パスからの移動が新しいパスへ転送される | 初期データがある | `/polls` と `/polls/1/results` を開く | `/polls` は `/surveys` へ、`/polls/1/results` は `/surveys/1/results` へ転送され、200 で表示される | `RQ-FT-LEGACY-POLL-URL`、`RQ-UI-POLL-LIST-SCREEN` | `RQ-BK-BROWSE-POLLS` |

既存のシナリオは、URL と画面の名前の表記を新しいものに読み替えるだけで、手順と期待結果は変えない。`RQ-TS-NAVIGATION` の「Polls」は「Surveys」に読み替える。

## 8. 変更後の業務課題と要件の対応表

| RQ-BK-ID | 対応する要件 | 区分 |
|---|---|---|
| `RQ-BK-SURVEY-WORDING` | `RQ-UI-SURVEY-WORDING` | [追加] |
| `RQ-BK-BROWSE-POLLS` | `RQ-FT-LEGACY-POLL-URL`（追加分）。既存の `RQ-FT-LIST-POLLS`、`RQ-FT-VIEW-POLL-OPTIONS` は変えない | 既存 + [追加] |

## 9. 廃止（deprecated）する要件 ID

無し。要件の意味は変わらないため、既存の要件 ID は廃止しない。

## 10. 変更の影響範囲

- 画面: 全画面の用語（`RQ-UI-SURVEY-WORDING`）。URL のパス（全画面の URL。`RQ-UI-POLL-LIST-SCREEN`、`RQ-UI-POLL-DETAIL-SCREEN`、`RQ-UI-POLL-RESULTS-SCREEN`）。旧パスの転送（`RQ-FT-LEGACY-POLL-URL`）。
- データ: 変更なし。テーブル名、項目名、保存先のファイル名は変えない。
- 外部連携、非機能、運用: 変更なし。`README.md` の説明（起動方法と画面の名前）を合わせる。
