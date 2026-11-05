# 変更設計書: 利用者に見える「poll」を「survey」に変える

- 入力: `change_requirements.md`（同じディレクトリ）と正本 `docs/requirements.md`・`docs/detail_design.md`
- 記号: 設計要素は [追加] か [削除] の区分を付ける。設計 ID は変えないため、名称・経路・文言だけが変わる要素は [変更] と書く（[変更] の行は対応表の判定に使わない。ID は正本の要素のまま有効）。
- 正本は書き換えない。反映は実装後に isdd-build が行う。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。DB のファイル名（`polls.db`）と表名（`polls`・`options`・`votes`・`ballots`）は変えない。既存の DATA_DIR のデータをそのまま読む。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 経路（[変更] DS-IF-POLL-LIST-PAGE・DS-IF-POLL-RESULT-PAGE・DS-IF-POLL-VOTE-PAGE-ONE-VOTE・DS-IF-VOTE-SUBMIT-ONE-VOTE）

| 経路 | 旧 | 新 | 備考 |
|---|---|---|---|
| 一覧 | `/` | `/`（変更なし） | — |
| 投票画面 | `/polls/<id>` | `/surveys/<id>` | DS-IF-POLL-VOTE-PAGE-ONE-VOTE |
| 投票の送信 | `/polls/<id>/vote` | `/surveys/<id>/vote` | DS-IF-VOTE-SUBMIT-ONE-VOTE |
| 投票テーマの結果 | `/polls/<id>/results` | `/surveys/<id>/results` | DS-IF-POLL-RESULT-PAGE |
| 全体の結果 | `/results` | `/results`（変更なし） | DS-IF-ALL-RESULTS-PAGE |

- 旧い経路（`/polls/...`）は転送しない。`/polls/...` は既存の 404 の画面になる（DS-FN-RENDER-NOT-FOUND）。
- 投票の送信の成功時の転送先は `/surveys/<id>/results?voted=1`。投票済みの応答、未選択の応答、404 の仕様は変えない。

#### 表示する文字（[変更] DS-FN-RENDER-LAYOUT・DS-IF-NAVIGATION-MENU・DS-FN-RENDER-POLL-LIST・DS-FN-RENDER-POLL-RESULTS・DS-FN-RENDER-ALL-RESULTS・DS-FN-RENDER-VOTE-PAGE-ONE-VOTE・DS-FN-RENDER-NOT-FOUND）

| 場所 | 旧 | 新 |
|---|---|---|
| ページのタイトルの末尾（共通の枠） | `… - Polls` | `… - Surveys` |
| 案内メニューのリンク | Polls / Results | Surveys / Results |
| 一覧の見出し | Polls | Surveys |
| 一覧が空のとき | No polls available. | No surveys available. |
| 一覧のボタン・リンク | Vote / View results（変更なし） | Vote / View results（変更なし。リンク先のみ変わる） |
| 結果画面のリンク | Vote on this poll | Vote on this survey |
| 投票画面の戻るリンク | Back to polls | Back to surveys |
| 404 の本文（投票テーマが無い） | Poll not found. | Survey not found. |
| 全体の結果画面の詳細リンク | Details（変更なし。リンク先のみ変わる） | Details |

- 変更なし: 「Results」「Vote」「Submit vote」「You have already voted.」「Please select an option.」「Not found」の文言。
- 配色（DS-IF-COLOR-THEME）は変えない。

### 4-2. 内部設計

- 処理フローは変えない。
- 経路の振り分けの正規表現（`web.py` の定数）は `/surveys/(\d+)`、`/surveys/(\d+)/results`、`/surveys/(\d+)/vote` に変える。定数名も `SURVEY_*` に変える（対応表の対象外。設計要素ではない）。
- 起動時のコンソール表示（DS-FN-MAIN）は「Surveys is running at …」に変える。

### 4-3. バッチ設計

無し。

## 5. クラス設計

変更なし。`PollService`・`PollRequestHandler`・`PollNotFoundError` などのクラス名・責務は変えない（コードの内部の識別子であり、利用者に見えない）。

## 6. エラーハンドリングとセキュリティ設計

- 変更: 投票テーマが無いときの 404 の本文（上の表）。それ以外は変えない。

## 7. コード設計

- ディレクトリ構成: 変更なし（ファイルは増やさない）。
- 依存の規則: 変更なし。

### 7-1. ファイルごとの変更

| ファイル | 区分 | 設計 ID | 内容 |
|---|---|---|---|
| `src/views.py` | [変更] | `DS-FN-RENDER-LAYOUT` | ページのタイトルの末尾を「Surveys」に |
| `src/views.py` | [変更] | `DS-IF-NAVIGATION-MENU` | 案内メニューのリンク（Surveys / Results） |
| `src/views.py` | [変更] | `DS-FN-RENDER-POLL-LIST` | 見出し、空の文言、リンク先（`/surveys/...`） |
| `src/views.py` | [変更] | `DS-FN-RENDER-POLL-RESULTS` | リンク先（`/surveys/...`）、「Vote on this survey」 |
| `src/views.py` | [変更] | `DS-FN-RENDER-ALL-RESULTS` | 詳細リンク先（`/surveys/<id>/results`） |
| `src/views.py` | [変更] | `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | 送信先（`/surveys/<id>/vote`）、「Back to surveys」 |
| `src/views.py` | [変更] | `DS-FN-RENDER-NOT-FOUND` | 戻るリンクの文言（「Back to surveys」）は呼び出し側の文言の表示に従う（画面の枠は変えない） |
| `src/web.py` | [変更] | `DS-FN-DISPATCH-GET-REQUEST` | 経路の正規表現を `/surveys/...` に |
| `src/web.py` | [変更] | `DS-FN-DISPATCH-POST-REQUEST` | 投票の送信の経路を `/surveys/<id>/vote` に |
| `src/web.py` | 変更なし | `DS-IF-POLL-LIST-PAGE` | 経路 `/` は同じ。描画の文言は views の要素で変わる |
| `src/web.py` | [変更] | `DS-IF-POLL-RESULT-PAGE` | 経路 `/surveys/<id>/results`。404 の文言「Survey not found.」 |
| `src/web.py` | 変更なし | `DS-IF-ALL-RESULTS-PAGE` | 経路 `/results` は同じ。描画の文言は views の要素で変わる |
| `src/web.py` | [変更] | `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | 経路 `/surveys/<id>`。404 の文言「Survey not found.」 |
| `src/web.py` | [変更] | `DS-IF-VOTE-SUBMIT-ONE-VOTE` | 経路 `/surveys/<id>/vote`、成功時の転送先 `/surveys/<id>/results?voted=1`、404 の文言 |
| `src/app.py` | [変更] | `DS-FN-MAIN` | 起動時の表示「Surveys is running at …」 |
| `src/poll_service.py`・`src/storage.py` | 変更なし | — | 業務処理と保存は変えない |

- 変更なしの要素: 配色（DS-IF-COLOR-THEME）、経路 `/results` の処理、投票・投票済みの業務処理、DB の表と関数。

## 8. テスト設計

### 8-1. テストの種類と方針

- 変更: 単体テストは `tests/unit/test_views.py` の文言・経路の期待値を新しい名称に合わせる。E2E は既存のテストの URL と文言を新しい名称にする。
- 変更なし: テストの種類、実行手段（E2E は `e2e/` で直接実行、結果は `e2e/results/`）。

### 8-2. E2E テストのシナリオ（変更分）

| DS-ID | 区分 | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| [追加] `DS-TS-SURVEY-TERMINOLOGY-E2E` | 追加 | 利用者に見える文字と URL に poll・polls が無いこと | 起動済み | `/`、`/surveys/1`、`/surveys/1/results`、`/results` を開き、本文の文字（タグを除く）に poll・polls（大文字・小文字を問わない）が無いことを確かめる。`/polls/1` を開き 404 になることを確かめる | 4 画面に poll・polls の語が無い。`/polls/1` は 404 |
| [変更] 既存の E2E（`DS-TS-BROWSE-POLLS-E2E` など 9 本） | 変更 | 既存の目的は変えない | 起動済み | URL を `/surveys/...` に、期待する文言を「Surveys」「Survey not found.」「No surveys available.」などに読み替える | 同じ観点で合格する |

- 既存のテスト関数名（`test_browse_polls` など）は変えない（対応表の修飾名を変えないため）。
- 新しい関数: `PollsE2ETest.test_survey_terminology`（ファイル `e2e/test_polls_e2e.py`）。

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。`python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml`。

## 9. 運用設計

変更なし。`PORT`・`DATA_DIR` は既存のまま。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

区分の書式: [追加] の行は新しい対応。[変更] の行は、設計要素の対応要件は変えず、名称・経路・文言だけが変わるものを示す（対応表の判定に使う行。対応する要件 ID は変えない）。

| DS-ID | 対応要件ID |
|---|---|
| [追加] `DS-MD-VIEWS` | `RQ-NF-SURVEY-TERMINOLOGY`, `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-NAVIGATION-MENU` |
| [追加] `DS-MD-WEB` | `RQ-NF-SURVEY-TERMINOLOGY`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN` |
| [追加] `DS-TS-SURVEY-TERMINOLOGY-E2E` | `RQ-TS-SURVEY-TERMINOLOGY`, `RQ-NF-SURVEY-TERMINOLOGY` |
| [変更] `DS-FN-RENDER-LAYOUT` | `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-UI-ALL-RESULTS-SCREEN`, `RQ-NF-SURVEY-TERMINOLOGY` |
| [変更] `DS-IF-NAVIGATION-MENU` | `RQ-UI-NAVIGATION-MENU`, `RQ-NF-SURVEY-TERMINOLOGY` |
| [変更] `DS-FN-RENDER-POLL-LIST` | `RQ-FT-LIST-POLLS`, `RQ-UI-POLL-LIST-SCREEN` |
| [変更] `DS-FN-RENDER-POLL-RESULTS` | `RQ-FT-SHOW-POLL-RESULTS`, `RQ-UI-POLL-RESULT-SCREEN` |
| [変更] `DS-FN-RENDER-ALL-RESULTS` | `RQ-UI-ALL-RESULTS-SCREEN` |
| [変更] `DS-FN-RENDER-VOTE-PAGE-ONE-VOTE` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-VOTED-STATE` |
| [変更] `DS-FN-RENDER-NOT-FOUND` | `RQ-FT-SHOW-POLL-OPTIONS`, `RQ-UI-POLL-VOTE-SCREEN` |
| [変更] `DS-FN-DISPATCH-GET-REQUEST` | `RQ-UI-POLL-LIST-SCREEN`, `RQ-UI-POLL-RESULT-SCREEN`, `RQ-UI-POLL-VOTE-SCREEN` |
| [変更] `DS-FN-DISPATCH-POST-REQUEST` | `RQ-FT-CAST-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-UI-POLL-VOTE-SCREEN` |
| [変更] `DS-IF-POLL-LIST-PAGE` | `RQ-FT-LIST-POLLS`, `RQ-UI-POLL-LIST-SCREEN` |
| [変更] `DS-IF-POLL-RESULT-PAGE` | `RQ-FT-SHOW-POLL-RESULTS`, `RQ-UI-POLL-RESULT-SCREEN` |
| [変更] `DS-IF-ALL-RESULTS-PAGE` | `RQ-UI-ALL-RESULTS-SCREEN` |
| [変更] `DS-IF-POLL-VOTE-PAGE-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-UI-VOTED-STATE`, `RQ-FT-ONE-VOTE-PER-POLL` |
| [変更] `DS-IF-VOTE-SUBMIT-ONE-VOTE` | `RQ-UI-POLL-VOTE-SCREEN`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-FT-CAST-VOTE` |
| [変更] `DS-FN-MAIN` | `RQ-OP-START-WITH-SCRIPTS` |
| [変更] `DS-IF-COLOR-THEME` | `RQ-NF-COLOR-THEME` |
| [変更] `DS-TS-BROWSE-POLLS-E2E` | `RQ-TS-BROWSE-POLLS`, `RQ-FT-LIST-POLLS` |
| [変更] `DS-TS-ANONYMOUS-ACCESS-E2E` | `RQ-TS-ANONYMOUS-ACCESS`, `RQ-NF-ANONYMOUS-ACCESS` |

### 11-1. 除外要件

除外要件は無い。
