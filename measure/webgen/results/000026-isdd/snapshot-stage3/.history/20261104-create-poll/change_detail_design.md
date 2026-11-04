# 変更設計書: 投票の作成ページ（Create poll）

本書は既存の詳細設計書 `docs/detail_design.md` への変更だけを書く。正本は書き換えない。区分は [追加] と [削除] の 2 つ。中身が変わる既存の要素は、同じ DS-ID の行を [削除]（旧い内容）と [追加]（新しい内容）に分けて書く。新しい要素は新しい DS-ID を [追加] で書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、Flask、SQLite）。技術は変えない。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。投票の作成は既存の Web サーバーとそのまま同じ DB を使う。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。投票の作成は既存の投票テーブル（`polls`）と選択肢テーブル（`options`）へ書く。説明（`description`）は画面に入力欄が無いため、空の文字列を入れる。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース

| DS-ID | 区分 | 画面・経路 | 目的 |
|---|---|---|---|
| `DS-IF-CREATE-POLL-PAGE` | [追加] | GET `/polls/new` | 投票の作成画面（質問の入力欄 1 つ、選択肢の入力欄 4 つ、Create poll ボタン） |
| `DS-IF-CREATE-POLL-ACTION` | [追加] | POST `/polls/new` | 投票の作成の受け付け（作成画面のフォームの送信先） |
| `DS-IF-POLLS-PAGE` | [削除] | GET `/` | 投票の一覧。全画面に共通の見た目（上部のナビゲーション Polls・Results、light yellow の背景、dark slate gray の部品）を含む |
| `DS-IF-POLLS-PAGE` | [追加] | GET `/` | 投票の一覧。全画面に共通の見た目（上部のナビゲーション Polls・Create poll・Results、light yellow の背景、dark slate gray の部品）を含む。ナビゲーションは全画面の共通部品（base テンプレート）で、各画面はそれを含む |
| `DS-IF-POLL-PAGE` | [追加] | GET `/polls/<poll_id>` | 投票の詳細。作成直後（`created=1` 付き）は「Your poll has been created.」を表示する（投票の詳細の表示は他は変更なし） |

（投票の受け付け、全投票の結果画面、404 の表示 の経路と目的は変更なし。）

#### インターフェース仕様

| DS-ID | 区分 | 入力とバリデーション | 出力 | エラー仕様 |
|---|---|---|---|---|
| `DS-IF-CREATE-POLL-PAGE` | [追加] | 無し | 空の入力欄（Question、Option 1 から Option 4）と Create poll ボタン | 無し |
| `DS-IF-CREATE-POLL-ACTION` | [追加] | 質問文と選択肢の前後の空白を除く。選択肢のうち空欄のものは無視する。判定の順は次のとおり。質問が空 → 「Please enter a question.」。質問が 200 文字超 → 「The question must be 200 characters or fewer.」。選択肢が 2 件未満 → 「Please enter at least two options.」。選択肢が 100 文字超 → 「Each option must be 100 characters or fewer.」。同じ文言の選択肢がある → 「Each option must be different.」 | 作成に成功したら投票の詳細へ 303 でリダイレクトし、`created=1` を付ける（「Your poll has been created.」を表示） | 不備があれば投票は作らず、作成画面を 400 で再表示する。入力した質問と選択肢の値を残し、理由を 1 つ画面に出す |
| `DS-IF-POLL-PAGE` | [削除] | poll_id は整数。存在しなければ 404（`DS-IF-NOT-FOUND`） | 質問文、説明、選択肢。投票済みなら選択肢のラジオボタンと Vote ボタンを disabled で出し、「You have already voted」と結果（票数と割合）を出す。未投票ならフォームを有効に出す | 存在しない投票は 404 |
| `DS-IF-POLL-PAGE` | [追加] | poll_id は整数。存在しなければ 404（`DS-IF-NOT-FOUND`）。`created=1` のときは作成直後の表示にする | 質問文、説明、選択肢。`created=1` のときは「Your poll has been created.」を最初に出す。投票済みなら選択肢のラジオボタンと Vote ボタンを disabled で出し、「You have already voted」と結果（票数と割合）を出す。未投票ならフォームを有効に出す | 存在しない投票は 404 |

（一覧、全投票の結果画面、投票の受け付けの入力・出力・エラー仕様は変更なし。）

#### 外部システム連携

変更なし。外部連携は無い。

### 4-2. 内部設計

#### 処理フロー（投票の作成）

1. 作成画面（`DS-IF-CREATE-POLL-PAGE`）を表示する。
2. 送信（`DS-IF-CREATE-POLL-ACTION`）を受けると、質問文と 4 つの選択肢の入力値から前後の空白を除き、空の選択肢を除く。
3. `DS-FN-CREATE-POLL` で判定する。不備があれば `InvalidPoll` を受けて、作成画面を 400 で再表示する（入力値を残す）。投票は作らない。
4. 不備が無ければ、1 つのトランザクションで投票を 1 件作り（説明は空）、入力された順に選択肢を 1 から順番の並び順で作る。
5. 作成した投票の番号で、投票の詳細へ 303 でリダイレクトし、`created=1` を付ける。

利用者の識別（`DS-FN-IDENTIFY-VOTER`）は使わない。作成は利用者を区別しない。Cookie は設定しない。

#### 各処理の役割

変更なし。利用者識別子の作成（利用者識別子の取得）、起動時の初期化（アプリの生成）、投票の受け付けは既存のまま。

## 5. クラス設計

| DS-ID | 区分 | 役割 |
|---|---|---|
| `DS-CL-VOTING-SERVICE` | [削除] | 投票の検証と集計（1 投票 1 票の記録、結果の集計） |
| `DS-CL-VOTING-SERVICE` | [追加] | 投票の検証と集計（1 投票 1 票の記録、結果の集計）と、投票の作成の検証と記録 |

- `VotingService` は既存のクラスに、投票の作成のメソッド `create_poll` を 1 つ足す。別のクラスは作らない（投票の業務ルールを 1 か所にまとめるため）。
- `DS-FN-CREATE-POLL` で投票の作成と例外 `InvalidPoll` を定める。

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照。作成画面の入力値は、既存と同じく Jinja2 の自動エスケープで表示する（HTML として解釈しない）。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。新しいファイルは作らない。

### 7-2. ファイル一覧

| ファイル | 役割 | DS-MD-ID | 実現する設計 ID |
|---|---|---|---|
| `app/voting.py` | 投票の業務ロジック（[追加] 投票の作成） | `DS-MD-VOTING` | `DS-CL-VOTING-SERVICE`, `DS-FN-CAST-VOTE`, `DS-FN-GET-POLL-RESULT`, `DS-FN-GET-ALL-RESULTS`, `DS-FN-CREATE-POLL` |
| `app/views.py` | 経路と画面の描画（[追加] 作成画面の 2 経路） | `DS-MD-VIEWS` | `DS-IF-POLLS-PAGE`, `DS-IF-POLL-PAGE`, `DS-IF-VOTE-ACTION`, `DS-IF-RESULTS-PAGE`, `DS-IF-NOT-FOUND`, `DS-FN-IDENTIFY-VOTER`, `DS-IF-CREATE-POLL-PAGE`, `DS-IF-CREATE-POLL-ACTION` |

- `app/templates/new_poll.html`（作成画面の描画）と `app/templates/base.html`（ナビゲーションの 3 項目）と `app/static/style.css`（入力欄の見た目）は非コードのファイルで、既存の設計どおり対応表の対象外。
- 上の表の `DS-MD-VOTING`、`DS-MD-VIEWS` の行は、実現する設計 ID の列だけを足す（区分は変更なし）。

### 対応表の粒度

`function`（既存のまま）。

### 依存の規則

変更なし。既存設計 `docs/detail_design.md` 7 章の依存の規則を参照。作成画面は既存の `app/` の中だけで実現する。

### コーディング規約

変更なし。既存設計 `docs/detail_design.md` 7 章を参照。

## 8. テスト設計

### 8-1. テストの種類と方針

- 単体テスト: `tests/test_voting.py` に投票の作成（`DS-FN-CREATE-POLL`）の正常系と不備の検証を足す（[追加]）。他の単体テストは変更なし。
- E2E: 投票の作成の全体（作成、投票、結果）と、不備の入力の扱いを確かめる（[追加]）。ナビゲーションのシナリオは 3 項目を確かめるよう変える（[削除] と [追加]）。
- 実行コマンドは既存のまま（8-4）。

### 8-2. E2E テストのシナリオ

| DS-ID | 区分 | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| `DS-TS-CREATE-POLL-E2E` | [追加] | 投票の作成から投票と結果まで | 初期データがある（DATA_DIR が空でよい） | 作成画面（GET `/polls/new`）を開き、質問と 2 件の選択肢を POST する。作成後の詳細の完了の文を確認し、選択肢を 1 つ選んで投票し、結果（GET `/results`）に新しい投票の質問と選択肢があり票数（0 または 1）が出ることを確認する | 作成の完了の文が出る。投票が記録される。結果に新しい投票が並ぶ |
| `DS-TS-REJECT-INVALID-POLL-E2E` | [追加] | 不備の入力では投票が作られない | 初期データがある | 質問を入れ、選択肢を 1 件だけ POST する。投票の一覧（GET `/`）の件数を、POST の前後で比べる | 400 で作成画面が再表示され、「Please enter at least two options.」が出る。入力した質問が残る。投票の件数は増えない |
| `DS-TS-NAVIGATION-E2E` | [削除] | ナビゲーション | 任意の画面 | 各画面の nav リンクを辿る | Polls と Results のリンクが全画面にある |
| `DS-TS-NAVIGATION-E2E` | [追加] | ナビゲーション | 任意の画面 | 各画面の nav リンクを辿る | Polls、Create poll、Results のリンクが全画面にあり、作成画面が開ける |

（他の `DS-TS-*` の行は変更なし。）

### 8-3. E2E の実行手段

変更なし。pytest、HTTP クライアントで実サーバーに接続（既存の承認どおり）。

### 8-4. E2E の実行コマンドと運用

変更なし。`.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`。単体テストは `.venv/bin/python -m pytest tests`。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。新しい設定や手順は無い。

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計 `docs/detail_design.md` セクション 10 を参照。

## 11. 要件と設計の対応表

| DS-ID | 区分 | 対応要件ID |
|---|---|---|
| `DS-IF-CREATE-POLL-PAGE` | [追加] | `RQ-UI-CREATE-POLL-SCREEN`, `RQ-FT-CREATE-POLL`, `RQ-NF-UI-LANGUAGE` |
| `DS-IF-CREATE-POLL-ACTION` | [追加] | `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-FN-CREATE-POLL` | [追加] | `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-CL-VOTING-SERVICE` | 変更なし（既存の対応に追加） | `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-MD-VOTING` | 変更なし（既存の対応に追加） | `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-MD-VIEWS` | [削除] | `RQ-UI-NAV-MENU` |
| `DS-MD-VIEWS` | [追加] | `RQ-UI-NAV-MENU-CREATE`, `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-IF-POLLS-PAGE` | [削除] | `RQ-UI-NAV-MENU` |
| `DS-IF-POLLS-PAGE` | [追加] | `RQ-UI-NAV-MENU-CREATE` |
| `DS-IF-POLL-PAGE` | [追加] | `RQ-FT-CREATE-POLL` |
| `DS-TS-UNIT-VOTING` | 変更なし（既存の対応に追加） | `RQ-FT-CREATE-POLL`, `RQ-FT-REJECT-INVALID-POLL` |
| `DS-TS-CREATE-POLL-E2E` | [追加] | `RQ-TS-CREATE-POLL` |
| `DS-TS-REJECT-INVALID-POLL-E2E` | [追加] | `RQ-TS-REJECT-INVALID-POLL` |
| `DS-TS-NAVIGATION-E2E` | [削除] | `RQ-TS-NAVIGATION` |
| `DS-TS-NAVIGATION-E2E` | [追加] | `RQ-TS-NAVIGATION` |
| `DS-FN-CAST-VOTE` | 変更なし（既存） | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-INVALID-VOTE`, `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-FT-REFUSE-REPEAT-VOTE` |
| `DS-FN-GET-POLL-RESULT` | 変更なし（既存） | `RQ-FT-SHOW-POLL-RESULT`, `RQ-FT-SHOW-RESULT-AFTER-VOTE` |
| `DS-FN-GET-ALL-RESULTS` | 変更なし（既存） | `RQ-FT-SHOW-ALL-RESULTS` |
| `DS-FN-IDENTIFY-VOTER` | 変更なし（既存） | `RQ-FT-ONE-VOTE-PER-POLL`, `RQ-NF-AUTH` |
| `DS-IF-VOTE-ACTION` | 変更なし（既存） | `RQ-FT-CAST-VOTE`, `RQ-FT-REJECT-INVALID-VOTE`, `RQ-FT-REFUSE-REPEAT-VOTE` |
| `DS-IF-RESULTS-PAGE` | 変更なし（既存） | `RQ-UI-RESULTS-SCREEN`, `RQ-FT-SHOW-ALL-RESULTS` |
| `DS-IF-NOT-FOUND` | 変更なし（既存） | `RQ-FT-SHOW-POLL-OPTIONS` |

注: `DS-TS-NAVIGATION-E2E` の 2 行（旧い行と新しい行）は、同じシナリオの検証する要件 ID を旧い 2 項目のナビゲーション（`RQ-UI-NAV-MENU`）から 3 項目のナビゲーション（`RQ-UI-NAV-MENU-CREATE`）へ変えたことを表す。`RQ-TS-NAVIGATION` の ID 自体は変えない。

### 11-1. 除外要件

除外要件は無い。
