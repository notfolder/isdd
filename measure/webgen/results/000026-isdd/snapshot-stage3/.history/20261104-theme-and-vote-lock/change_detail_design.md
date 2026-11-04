# 変更設計書: 配色の変更と投票済みの投票の操作無効化

本書は既存の詳細設計書 `docs/detail_design.md` への変更だけを書く。正本は書き換えない。区分は [追加] と [削除] の 2 つ。中身が変わる既存の要素は、同じ DS-ID の行を [削除]（旧い内容）と [追加]（新しい内容）に分けて書く。新しい要素は新しい DS-ID を [追加] で書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、Flask、SQLite）。技術は変えない。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。票の保存（1 投票 1 票の一意制約）は既存のまま使う。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース

| DS-ID | 区分 | 画面・経路 | 目的 |
|---|---|---|---|
| `DS-IF-POLLS-PAGE` | [削除] | GET `/` | 投票の一覧。全画面に共通の見た目（上部のナビゲーション Polls・Results、白背景、ネイビーの部品）を含む |
| `DS-IF-POLLS-PAGE` | [追加] | GET `/` | 投票の一覧。全画面に共通の見た目（上部のナビゲーション Polls・Results、light yellow の背景、dark slate gray の部品）を含む |
| `DS-IF-POLL-PAGE` | [削除] | GET `/polls/<poll_id>` | 投票の詳細。未投票なら投票フォーム、投票済みなら結果 |
| `DS-IF-POLL-PAGE` | [追加] | GET `/polls/<poll_id>` | 投票の詳細。未投票なら投票フォーム、投票済みなら選択肢と Vote を無効にした表示に「You have already voted」を出し、結果を表示する |

（投票の受け付け、全投票の結果画面、404 の表示 の経路と目的は変更なし。）

#### インターフェース仕様

| DS-ID | 区分 | 入力とバリデーション | 出力 | エラー仕様 |
|---|---|---|---|---|
| `DS-IF-POLL-PAGE` | [削除] | poll_id は整数。存在しなければ 404（404 の表示） | 質問文、説明、選択肢。投票済みなら結果（票数と割合） | 存在しない投票は 404 |
| `DS-IF-POLL-PAGE` | [追加] | poll_id は整数。存在しなければ 404（404 の表示） | 質問文、説明、選択肢。投票済みなら、選択肢のラジオボタンと Vote ボタンを disabled で出し、「You have already voted」を表示し、結果（票数と割合）を出す。未投票ならフォームを有効に出す。初回の投票の直後は「Thank you for your vote.」も出す | 存在しない投票は 404 |
| `DS-IF-VOTE-ACTION` | [削除] | option_id のフォーム値が無い、または整数でない → 「Please choose an option.」。option_id がその投票に属さない → 「That option is not part of this poll.」。投票が存在しない → 404 | 成功時は投票の詳細へ 303 でリダイレクト（結果が表示される）。投票済みなら票を作らず同じリダイレクト（1 投票 1 票） | エラー時は投票の詳細を 400 で再表示し、エラー文を画面に出す。票は作らない |
| `DS-IF-VOTE-ACTION` | [追加] | option_id のフォーム値が無い、または整数でない → 「Please choose an option.」。option_id がその投票に属さない → 「That option is not part of this poll.」。投票が存在しない → 404 | 初めての投票が成功したときは投票の詳細へ 303 でリダイレクト（「Thank you for your vote.」付き）。投票済みの利用者の送信は票を作らず、「Thank you」の付かない同じ投票の詳細へ 303 でリダイレクトする（そこで「You have already voted」と結果が出る） | エラー時は投票の詳細を 400 で再表示し、エラー文を画面に出す。票は作らない |

（一覧と全投票の結果画面の入力・出力・エラー仕様は、一覧の「投票 0 件」と結果の表示を除き変更なし。）

#### 外部システム連携

変更なし。外部連携は無い。

### 4-2. 内部設計

#### 処理フロー（投票）の変更点

既存の処理フロー（`docs/detail_design.md` 4-2）の「この利用者の票があるか」が「ある」の分岐を次のとおりに変える。

- 変更前: 票は作らず、投票の詳細へリダイレクトする（表示は「Thank you」の付く結果表示）。
- 変更後: 票は作らず、「Thank you」の付かない投票の詳細へリダイレクトする。詳細画面は投票済みの表示（操作の無効、「You have already voted」、結果）を出す。

一意制約で失敗した場合も、同じ分岐（「Thank you」の付かない投票の詳細）へ行く。

#### 各処理の役割

変更なし。利用者識別子の作成（利用者識別子の取得）、起動時の初期化（アプリの生成）は既存のまま。

## 5. クラス設計

変更なし。`VotingService.cast_vote` は既存のまま「already_voted」を返す。投票サービス（VotingService） と 投票の記録 の振る舞いは変えない。

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。新しいファイルは作らない。

### 7-2. ファイル一覧

変更なし。既存設計 `docs/detail_design.md` 7-2 を参照。テンプレート（`app/templates/*.html`）と `app/static/style.css` は、既存の設計どおり対応表の対象外（非コードのファイル）。

### 対応表の粒度・依存の規則

変更なし（粒度は `function`、依存の規則は「無い」ではなく既存設計 7 章のとおり）。

### コーディング規約

変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

- 変更なし（単体テスト リポジトリ（PollRepository）、投票サービス（VotingService）、初期データの投入、実行コマンドは既存のまま）。
- 配色は `DS-TS-THEME-E2E` で確かめる（指定の値を変更）。投票済みの表示は `DS-TS-VOTED-POLL-STATE-E2E` で確かめる（追加）。

### 8-2. E2E テストのシナリオ

| DS-ID | 区分 | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|---|
| `DS-TS-ONE-VOTE-E2E` | [削除] | 1 投票 1 票 | 投票済みの利用者 | 同じ投票に別の選択肢で POST | 票は増えず、既存の結果が表示される |
| `DS-TS-ONE-VOTE-E2E` | [追加] | 1 投票 1 票 | 投票済みの利用者 | 同じ投票に別の選択肢で POST | 票は増えず、「Thank you」は出ず、「You have already voted」と既存の結果が表示される |
| `DS-TS-THEME-E2E` | [削除] | 配色 | 任意 | `style.css` と base の内容を取得 | 背景 `#ffffff`、部品 `#000080` の指定がある |
| `DS-TS-THEME-E2E` | [追加] | 配色 | 任意 | `style.css` と base の内容を取得 | 背景 `#FFFFE0`、部品 `#2F4F4F` の指定があり、`#ffffff` と `#000080` の指定が無い |
| `DS-TS-VOTED-POLL-STATE-E2E` | [追加] | 投票済みの投票は操作できない | 投票済みの利用者（Cookie を保持） | 投票の詳細を GET し、同じ投票へ別の選択肢で POST し、詳細を再度 GET する | 詳細に disabled の選択肢と Vote があり、「You have already voted」と結果が出る。POST で票は増えず「Thank you」は出ない |

（他の `DS-TS-*` の行は変更なし。）

### 8-3. E2E の実行手段

変更なし。pytest、HTTP クライアントで実サーバーに接続（既存の承認どおり）。

### 8-4. E2E の実行コマンドと運用

変更なし。`.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計 `docs/detail_design.md` セクション 10 を参照。

## 11. 要件と設計の対応表

| DS-ID | 区分 | 対応要件ID |
|---|---|---|
| `DS-IF-POLLS-PAGE` | [削除] | `RQ-NF-VISUAL-THEME` |
| `DS-IF-POLLS-PAGE` | [追加] | `RQ-NF-SLATE-THEME` |
| `DS-IF-POLL-PAGE` | [追加] | `RQ-UI-VOTED-POLL-STATE`, `RQ-FT-DISABLE-VOTE-AFTER-VOTE` |
| `DS-IF-VOTE-ACTION` | [追加] | `RQ-FT-REFUSE-REPEAT-VOTE` |
| `DS-FN-CAST-VOTE` | 変更なし（既存の対応に追加） | `RQ-FT-REFUSE-REPEAT-VOTE` |
| `DS-TS-ONE-VOTE-E2E` | 変更なし（既存の対応） | `RQ-TS-ONE-VOTE-PER-POLL` |
| `DS-TS-THEME-E2E` | [削除] | `RQ-TS-THEME` |
| `DS-TS-THEME-E2E` | [追加] | `RQ-TS-THEME` |
| `DS-TS-VOTED-POLL-STATE-E2E` | [追加] | `RQ-TS-VOTED-POLL-STATE` |

注: 上の行のうち、`DS-TS-THEME-E2E` の [削除] と [追加] は、同じシナリオの検証する要件 ID を旧い配色の要件（`RQ-NF-VISUAL-THEME`）から新しい配色の要件（`RQ-NF-SLATE-THEME`）へ変えたことを表す。`RQ-TS-THEME` の ID 自体は変えない。

### 11-1. 除外要件

除外要件は無い。
