# 変更設計書: 配色の変更と投票操作の無効化（Polls Website）

本書は変更の記録である。正本の `docs/detail_design.md` は書き換えない（実装後に `isdd-build` の実装後レビューが反映する）。
入力要件: 本ディレクトリの `change_requirements.md`。区分は各行の `[追加]` と `[削除]`。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照（Python 3.12、Flask 3.1.3、SQLite のまま）。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。構成要素は変えず、画面テンプレートと CSS の中身だけを変える（`DS-IF-COLOR-THEME`、`DS-IF-POLL-VOTE-SCREEN` の 4-1 を参照）。

## 3. データ設計

### 3-1. データモデル

変更なし。既存設計 `docs/detail_design.md` セクション 3-1 を参照（テーブル、列、一意制約は変えない）。

### 3-2. トランザクションと排他制御

変更なし。既存設計 `docs/detail_design.md` セクション 3-2 を参照。投票の判定は既存の `DS-FN-HAS-VOTED` と一意制約（`DS-FN-CAST-VOTE`）をそのまま使う。

### 3-3. 状態遷移

変更なし。既存設計 `docs/detail_design.md` セクション 3-3 を参照。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 利用者向けインターフェース（GUI）

画面一覧（すべて英語表示。上部にナビゲーション「Polls」「Results」を表示）:

| DS-ID | 画面 | パス | 要素と機能 |
|---|---|---|---|
| [削除] `DS-IF-POLL-DETAIL-SCREEN` | 投票詳細・投票フォーム | `GET /polls/<id>` | タイトル、説明、選択肢のラジオボタン、「Vote」ボタン。投票済みのときはボタンを出さず「You have already voted in this poll.」と結果へのリンクを表示。存在しない ID は 404 |
| [追加] `DS-IF-POLL-VOTE-SCREEN` | 投票詳細・投票フォーム | `GET /polls/<id>` | タイトル、説明、選択肢のラジオボタン、「Vote」ボタン。投票済みのときは、選択肢と Vote を disabled（無効）で表示し、「You have already voted in this poll.」と結果へのリンクを表示する。投票の受付で失敗したときは、同じ画面にエラー文（赤字）を表示する。存在しない ID は 404 |
| [追加] `DS-IF-COLOR-THEME` | 全画面（共通の配色） | （全画面） | 背景は `#FFFFE0`（light yellow）。ナビゲーション、見出し、カード、ボタン、表の見出し、棒グラフの棒と枠、フィールドセットの枠は `#2F4F4F`（dark slate gray）。カードとナビゲーションの文字は `#FFFFE0`。白（`#ffffff`）と navy（`#000080`）は使わない。エラー文の赤（`#8b0000`）だけは例外。`src/static/style.css` と `src/templates/base.html` が実現する |

画面の見た目:

[削除] 画面の見た目: 白背景。ナビゲーション帯、見出し、ボタン、棒グラフの棒は navy（#000080）。HTML テンプレートと CSS は `DS-IF-*` の画面の一部として扱い、対応表の対象外（ファイルには DS-MD を付けない）。
[追加] 画面の見た目（`DS-IF-COLOR-THEME`）: 背景は light yellow（#FFFFE0）。部品（ナビゲーション帯、見出し、カード、ボタン、表の見出し、棒グラフ、枠）は dark slate gray（#2F4F4F）。HTML テンプレートと CSS は対応表の対象外（ファイルには DS-MD を付けない）。

#### インターフェース仕様（入力・バリデーション・出力・エラー）

| DS-ID | 入力とバリデーション | 出力 | エラー仕様 |
|---|---|---|---|
| [削除] `DS-IF-POLL-DETAIL-SCREEN` | パス `id` は整数。存在しなければ 404 | 投票詳細の HTML（200） | 存在しない ID は 404 |
| [追加] `DS-IF-POLL-VOTE-SCREEN` | パス `id` は整数。存在しなければ 404。投票用 Cookie が無い、または形式が不正なら未投票として扱う | 投票詳細の HTML（200）。投票済みなら選択肢と Vote を disabled にし、「You have already voted in this poll.」を表示する | 存在しない ID は 404 |
| [追加] `DS-IF-COLOR-THEME` | 入力なし | CSS（`/static/style.css`）と HTML の配色 | 例外なし |

業務ルールとの対応: [追加] `RQ-FT-LOCK-VOTE-CONTROLS` は `DS-IF-POLL-VOTE-SCREEN` が `DS-FN-HAS-VOTED` で投票済みを判定し、選択肢と Vote を disabled で表示する。二重投票の拒否（`RQ-FT-ONE-VOTE-PER-POLL`）は `DS-IF-CAST-VOTE-ACTION` の 409 と `DS-FN-CAST-VOTE` の一意制約による既存の仕組みのまま変えない。

外部システム連携: 変更なし（無し）。帳票・出力ファイル: 変更なし（無し）。

### 4-2. 内部設計

#### 投票テーマの詳細画面の処理（`DS-IF-POLL-VOTE-SCREEN`）

[追加] 1. パスの投票テーマを取得する。無ければ 404。
[追加] 2. Cookie の投票者識別子を読む（`DS-FN-GET-VOTER-TOKEN`）。識別子が無ければ未投票とみなす。
[追加] 3. `DS-FN-HAS-VOTED` で、その投票テーマに投票済みかを判定する。
[追加] 4. 投票済みなら、選択肢のラジオボタンと Vote ボタンに disabled を付け、「You have already voted in this poll.」を表示する。未投票なら従来どおり操作を出す。

#### 投票の受付での再表示（`DS-IF-CAST-VOTE-ACTION`）

[追加] 失敗して投票詳細を再表示するときも、`DS-FN-HAS-VOTED` で投票済みかを判定し直し、その結果で表示を決める。
[追加] 投票済み（409）のときは、再表示の画面も `DS-IF-POLL-VOTE-SCREEN` の投票済みの表示（disabled と案内文）にする。未選択・不正（400）で投票済みの投票テーマに送られた場合も、投票済みの表示にする。
[追加] 投票は保存しない（従来どおり）。票数は変わらない。

#### 初期化、集計、その他

変更なし。既存設計 `docs/detail_design.md` セクション 4-2 を参照。

### 4-3. 外部システム連携

変更なし（無し）。

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照（クラスは `VoteError` のみ）。

## 6. エラーハンドリングとセキュリティ設計

### 6-1. エラーハンドリング

変更なし。既存設計 `docs/detail_design.md` セクション 6-1 を参照。投票済みでの再投票の見え方は 4-1 の `DS-IF-POLL-VOTE-SCREEN` に書く。

### 6-2. 認証 / 6-3. 認可 / 6-4. 監査ログ

変更なし。既存設計 `docs/detail_design.md` セクション 6-2 から 6-4 を参照。

### 6-5. その他のセキュリティ対策

変更なし。既存設計 `docs/detail_design.md` セクション 6-5 を参照。投票の受け付けは POST だけのまま、投票済みの判定はサーバー側で行う（画面の disabled は表示だけの対策で、二重投票の防止は `DS-FN-CAST-VOTE` の一意制約が担う）。

## 7. コード設計

### 7-1. ディレクトリ構成

変更なし。既存設計 `docs/detail_design.md` セクション 7-1 を参照。

### 7-2. ファイル一覧

| ファイル | 役割 | 含まれるクラス・関数 | 実現する設計 ID |
|---|---|---|---|
| [削除] `src/web.py` | HTTP の画面と投票の受付 | `root_redirect`、`poll_list_page`、`poll_detail_page`、`cast_vote_action`、`poll_results_page`、`results_list_page` | `DS-MD-WEB`、`DS-IF-ROOT-REDIRECT`、`DS-IF-POLL-LIST-SCREEN`、`DS-IF-POLL-DETAIL-SCREEN`、`DS-IF-CAST-VOTE-ACTION`、`DS-IF-POLL-RESULTS-SCREEN`、`DS-IF-RESULTS-LIST-SCREEN` |
| [追加] `src/web.py` | HTTP の画面と投票の受付 | `root_redirect`、`poll_list_page`、`poll_detail_page`、`cast_vote_action`、`poll_results_page`、`results_list_page` | `DS-MD-WEB`、`DS-IF-ROOT-REDIRECT`、`DS-IF-POLL-LIST-SCREEN`、`DS-IF-POLL-VOTE-SCREEN`、`DS-IF-CAST-VOTE-ACTION`、`DS-IF-POLL-RESULTS-SCREEN`、`DS-IF-RESULTS-LIST-SCREEN` |

- [追加] 対応表の対象外のファイル: `src/templates/poll_detail.html`（`DS-IF-POLL-VOTE-SCREEN` の見た目）、`src/templates/base.html` と `src/static/style.css`（`DS-IF-COLOR-THEME`）。DS-MD を付けず、7-2 の表にも載せない（既存の方針どおり）。
- 対応表の粒度: `function`（変更なし）。
- 依存の規則: 無い（変更なし）。
- [追加] 関数の増減は無い（既存の `poll_detail_page` と `cast_vote_action` の中身だけを変える）。

### 7-3. 運用スクリプトの設計

変更なし。既存設計 `docs/detail_design.md` セクション 7-3 を参照。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` セクション 8-1 を参照。[追加] 単体・結合テスト（`tests/test_web.py`）で、投票済みの詳細画面の disabled と案内文、未選択で投票済みのときの表示を確かめる。

### 8-2. E2E テストのシナリオ

既存の `DS-TS-*` は変えない。新しい行を次のとおり追加する。

| DS-ID | 目的 | 前提条件 | 手順 | 期待結果 |
|---|---|---|---|---|
| [追加] `DS-TS-VERIFY-VOTE-LOCK-E2E` | 投票済みの投票テーマで操作が無効になり、直接の 2 回目の投票を数えない（`RQ-TS-VERIFY-VOTE-LOCK`） | 同じ Cookie で未投票のテーマに 1 票投じた後 | 同じテーマの詳細を開く → 選択肢と Vote の disabled と案内文を確かめる → 同じテーマへ別の選択肢を POST | 選択肢と Vote に disabled、「You have already voted in this poll.」、POST は 409、票数は変わらない |
| [追加] `DS-TS-VERIFY-COLOR-THEME-E2E` | 全画面の配色が依頼の指定どおり（`RQ-TS-VERIFY-COLOR-THEME`） | 初期データ | `/polls`、`/polls/1`、`/polls/1/results`、`/results` を開き、読み込む CSS の配色を確かめる | CSS に `#FFFFE0` と `#2F4F4F` があり、`#ffffff` と `#000080` が無い |

### 8-3. E2E の実行手段

変更なし。既存設計 `docs/detail_design.md` セクション 8-3 を参照。

### 8-4. E2E の実行コマンドと運用

変更なし。既存設計 `docs/detail_design.md` セクション 8-4 を参照。`test_navigation` の配色の確認は `DS-TS-VERIFY-COLOR-THEME-E2E` へ移す（ナビゲーションの確認は `DS-TS-NAVIGATION-E2E` に残す）。

## 9. 運用設計

変更なし。既存設計 `docs/detail_design.md` セクション 9 を参照。

## 10. ログ・監視・アラート・障害対応設計

変更なし。既存設計 `docs/detail_design.md` セクション 10 を参照。

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| [削除] `DS-IF-POLL-DETAIL-SCREEN` | `RQ-UI-POLL-DETAIL-SCREEN`、`RQ-FT-VIEW-POLL-OPTIONS` |
| [追加] `DS-IF-POLL-VOTE-SCREEN` | `RQ-UI-POLL-DETAIL-SCREEN`、`RQ-FT-VIEW-POLL-OPTIONS`、`RQ-FT-LOCK-VOTE-CONTROLS` |
| [追加] `DS-IF-COLOR-THEME` | `RQ-UI-COLOR-THEME` |
| [追加] `DS-TS-VERIFY-VOTE-LOCK-E2E` | `RQ-TS-VERIFY-VOTE-LOCK` |
| [追加] `DS-TS-VERIFY-COLOR-THEME-E2E` | `RQ-TS-VERIFY-COLOR-THEME` |
| 変更なし（既存） `DS-IF-CAST-VOTE-ACTION` | `RQ-FT-CAST-VOTE`、`RQ-FT-ONE-VOTE-PER-POLL`、`RQ-FT-VALIDATE-VOTE` |
| 変更なし（既存） `DS-FN-CAST-VOTE` | `RQ-FT-CAST-VOTE`、`RQ-FT-ONE-VOTE-PER-POLL`、`RQ-FT-VALIDATE-VOTE` |
| 変更なし（既存） `DS-FN-HAS-VOTED` | `RQ-FT-ONE-VOTE-PER-POLL` |
| 変更なし（既存） `DS-FN-GET-VOTER-TOKEN` | `RQ-NF-ANONYMOUS-USE` |
| 変更なし（既存） `DS-MD-WEB` | `RQ-UI-POLL-LIST-SCREEN`、`RQ-UI-POLL-DETAIL-SCREEN`、`RQ-UI-POLL-RESULTS-SCREEN`、`RQ-UI-RESULTS-LIST-SCREEN` |
| 変更なし（既存） `DS-IF-ROOT-REDIRECT` | `RQ-UI-POLL-LIST-SCREEN`、`RQ-OP-START-LOCAL` |
| 変更なし（既存） `DS-IF-POLL-LIST-SCREEN` | `RQ-UI-POLL-LIST-SCREEN`、`RQ-FT-LIST-POLLS` |
| 変更なし（既存） `DS-IF-POLL-RESULTS-SCREEN` | `RQ-UI-POLL-RESULTS-SCREEN`、`RQ-FT-VIEW-RESULTS` |
| 変更なし（既存） `DS-IF-RESULTS-LIST-SCREEN` | `RQ-UI-RESULTS-LIST-SCREEN` |
| 変更なし（既存） `DS-TS-NAVIGATION-E2E` | `RQ-TS-NAVIGATION` |

既存の DS-ID は上の「変更なし（既存）」の行で、正本の対応をそのまま示す。

### 11-1. 除外要件

除外要件は無い。
