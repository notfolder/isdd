# 変更設計書: 一覧の名前順の並べ替えと詳細画面の登録日時

- 対象の正本: `docs/detail_design.md`（正本は書き換えない。実装後に `isdd-build` が反映する）
- 対象の変更要件: `change_requirements.md`
- 区分: 設計要素ごとに [追加] [削除] を書く。中身が変わる既存の要素は旧要素を [削除] し、新要素を [追加] する。変更が無い章は「変更なし」と書く。

## 1. 最小設計と要件の除外

- 変更要件の [追加] 要件（`RQ-FT-SORT-SPECIES-LIST`、`RQ-FT-SHOW-SPECIES-RECORD-DATES`、`RQ-UI-SPECIES-LIST-SORT-CONTROL`、`RQ-UI-SPECIES-DETAIL-RECORD-DATES`、`RQ-TS-SORT-SPECIES-LIST`、`RQ-TS-SHOW-SPECIES-RECORD-DATES`）をすべて設計に反映する。要件の除外は無い。
- 並べ替えは検索の SQL を変えず、検索の結果を名前で並べ替える（検索の規則を変えないための最小の方法）。登録日時は保存済みの項目をそのまま表示する（新しい項目・新しい保存は作らない）。

## 2. 技術選定

- 変更なし。既存設計 `docs/detail_design.md` セクション 1 の技術（Python 3.12、Flask、SQLite）を引き継ぐ。

## 3. 外部連携の設計

- 変更なし（外部連携は無い）。

## 4. 設計書の書き方

### 4-1. 外部設計

#### 画面（GUI）

- 変更なし（画面の一覧と遷移は既存設計 `docs/detail_design.md` 4-1 のとおり）。ただし次の 2 つの部品を加える。

| 画面 | 経路 | 変更内容 |
|---|---|---|
| 一覧・検索・絞り込み画面（DS-IF-SPECIES-LIST-SCREEN） | `GET /` | 変更なし（ID を据え置く）。画面の検索の枠に、並べ替えの選択欄（DS-IF-SPECIES-LIST-SORT-CONTROL）を加える |
| 詳細画面（DS-IF-SPECIES-DETAIL-SCREEN） | `GET /species/<id>` | 変更なし（ID を据え置く）。項目の一覧の末尾に、登録日時と最終更新日時の行（DS-IF-SPECIES-DETAIL-RECORD-DATES）を加える |

| 設計要素 | 区分 | 内容 |
|---|---|---|
| 並べ替えの選択欄（DS-IF-SPECIES-LIST-SORT-CONTROL） | [追加] | 検索の枠の中の「Sort」の選択欄。選択肢は「Name (A to Z)」（値 `name_asc`、既定）と「Name (Z to A)」（値 `name_desc`）。選ぶと、検索欄と絞り込みの値を保ったまま一覧を送り直す（選択が変わった時点で検索フォームを送信する）。「Search」ボタンも従来どおり働く。「Clear」は並べ替えも既定に戻す |
| 登録日時と最終更新日時の行（DS-IF-SPECIES-DETAIL-RECORD-DATES） | [追加] | 項目の一覧の末尾に「Added」（保存されている登録日時）と「Last updated」（保存されている最終更新日時）を出す。保存値（UTC の ISO 8601 文字列）の年月日と時分（秒は出さない）を「YYYY-MM-DD HH:MM UTC」の形にする |

#### インターフェース仕様

| 経路 | 入力 | 出力 |
|---|---|---|
| `GET /` | クエリの `sort`（`name_asc` または `name_desc`）を追加。未指定、または他の値は `name_asc` として扱う | 検索・絞り込みの結果を、指定の順序で並べた一覧画面。選択欄の値は指定の値を保つ |

- 既存の入力（`q`、`kingdom`、`habitat`、`diet`、`conservation_status`、`notice`）と動作は変えない。

#### 外部システム連携

- 変更なし。

#### 外部 DB 連携

- 変更なし。

### 4-2. 内部設計

#### 処理フロー（一覧の並べ替え）

1. 一覧の要求から、並べ替えの値を読み取る。未指定・不正な値は `name_asc` にする（DS-FN-READ-SORT-ORDER）。
2. 既存の検索（DS-FN-SEARCH-SPECIES-RECORDS）で、キーワードと絞り込みの結果を得る。
3. 結果の行を、名前で並べ替える（DS-FN-SORT-SPECIES-ROWS）。名前は和名・一般名で、大文字小文字を区別しない。同じ名前のときは学名（空は後ろ）で比べる。`name_desc` のときは全体を逆順にする。
4. 並べ替えた行と、選んだ並べ替えの値を一覧画面に渡す（DS-FN-LIST-SPECIES-PAGE-SORTED）。

#### 処理の役割

| 処理 | 役割 |
|---|---|
| 並べ替えの値の読み取り（DS-FN-READ-SORT-ORDER） | クエリの `sort` を、許される値のどれかに決める |
| 行の並べ替え（DS-FN-SORT-SPECIES-ROWS） | 検索の結果を名前の昇順または降順に並べる純粋な関数（画面と DB に依存しない） |
| 一覧の処理（DS-FN-LIST-SPECIES-PAGE-SORTED） | 検索・絞り込みと並べ替えを組み合わせて、一覧画面を返す |

#### バッチ設計

- 変更なし（バッチは無い）。

#### イベント設計

- 変更なし（イベントは無い）。

## 5. クラス設計

- 変更なし。並べ替えは関数で実現する（クラスは増やさない）。

### クラス一覧・主要属性・クラス図・メッセージ

- 変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照。

## 6. エラーハンドリングとセキュリティ設計

- 変更なし。不正な並べ替えの値は、エラーにせず既定の順序として扱う（4-2 の処理の 1）。

## 7. コード設計

### ディレクトリ構成

- 追加: `app/sorting.py`（並べ替えの値と行の並べ替え）。他は既存設計 `docs/detail_design.md` 7 章のとおり。

### ファイル一覧

| ファイル | 区分 | 役割 | 含まれるクラス・関数 | 実現する設計 ID |
|---|---|---|---|---|
| `app/sorting.py` | [追加] | 並べ替えの値（`name_asc`、`name_desc`）と、行を名前で並べ替える | `SORT_ORDERS`、`sort_species_rows` | `DS-MD-SORTING`、`DS-FN-SORT-SPECIES-ROWS` |
| `app/routes.py` | 変更（ID は据え置き） | 並べ替えの値の読み取りを加え、一覧の処理を並べ替え対応にする | `read_sort_order`（追加）、`list_species`（並べ替え対応に変更） | `DS-FN-READ-SORT-ORDER`（[追加]）、`DS-FN-LIST-SPECIES-PAGE-SORTED`（[追加]。旧い ID の扱いは 11 章） |
| `app/templates/species_list.html` | 変更（ID は据え置き） | 検索の枠に並べ替えの選択欄を加える | — | `DS-IF-SPECIES-LIST-SORT-CONTROL`（[追加]） |
| `app/templates/species_detail.html` | 変更（ID は据え置き） | 項目の末尾に登録日時と最終更新日時の行を加える | — | `DS-IF-SPECIES-DETAIL-RECORD-DATES`（[追加]） |
| `app/static/style.css` | 変更なし | 選択欄は既存の入力欄の枠と色を使う | — | — |

対応表の粒度: `function`（既存のまま。`app/sorting.py` は公開関数 `sort_species_rows` と定数 `SORT_ORDERS` を対応表に載せる）。

- 旧い一覧の処理の ID は 11 章で [削除] する。新しい `DS-FN-LIST-SPECIES-PAGE-SORTED` は同じ関数 `app/routes.py::list_species` に対応し、対応表ではこの ID で結ぶ（関数名は変えない）。

### 依存の規則

- 既存の規則に一項目だけ足す: 依存元 `app/routes.py` の依存してよい先に `app/sorting.py` を加える。理由: 並べ替えは Flask と SQLite に依存しない純粋な関数で、画面の処理が保存の手段を直接扱うことにはならない。他の依存の規則（`app/routes.py` が `app/db.py` と `app/seed.py` に依存しないこと、ほかの元の規則）は変えない。`app/sorting.py` は他のどのモジュールにも依存しない。

### コーディング規約

- 変更なし。

### ID の扱い

- 変更なし。コードに ID は書かない。

## 8. テスト設計

### 8-1. テストの種類と方針

- 変更なし。並べ替えの規則（`sort_species_rows`）は単体テストで確かめる（テストファイルは `tests/test_sorting.py`、対応表の対象外）。

#### 単体テスト・結合テストの実行コマンド

- 変更なし。

### 8-2. E2E テストのシナリオ

| DS-ID | 区分 | テスト目的 | 前提 | 手順（要約） | 期待結果（要約） | 対応要件ID |
|---|---|---|---|---|---|---|
| `DS-TS-SORT-SPECIES-LIST` | [追加] | 並べ替えの昇順・降順、検索と絞り込みとの組み合わせ、Clear で既定に戻ること | サンプルが入っている | 一覧で既定が A to Z。Z to A に変えて Search。検索欄に `a`、Kingdom で Animalia を選んで Search。Clear を押す | 逆順になる。組み合わせた結果が選んだ順序で並ぶ。Clear 後は A to Z に戻る | `RQ-FT-SORT-SPECIES-LIST`、`RQ-UI-SPECIES-LIST-SORT-CONTROL` |
| `DS-TS-SHOW-SPECIES-RECORD-DATES` | [追加] | 一覧の各行から詳細へ行け、詳細に全項目と Added・Last updated が出ること | サンプルが入っている | 一覧の和名のリンクを開く。詳細の項目と日時の行を見る | 全項目と「Added」「Last updated」（UTC の年月日時分）が表示される | `RQ-FT-SHOW-SPECIES-RECORD-DATES`、`RQ-UI-SPECIES-DETAIL-RECORD-DATES` |

- 既存の E2E（`DS-TS-BROWSE-AND-VIEW-SPECIES`、`DS-TS-SEARCH-SPECIES-KEYWORD`、`DS-TS-FILTER-AND-COMBINE` ほか）は変更なし。全件を通すこと。

### 8-3. E2E の実行手段

- 変更なし（既存の `e2e/` の仕組みで、新しいテスト関数を追加する）。

### 8-4. E2E の実行コマンドと運用

- 変更なし。

## 9. 運用設計

- 変更なし（起動、初期化、設定、データ移行は既存のまま。新しい項目は無い）。

## 10. ログ・監視・アラート・障害対応設計

- 変更なし。

## 11. 要件と設計の対応表

| DS-ID | 区分 | 対応要件ID |
|---|---|---|
| `DS-MD-SORTING` | [追加] | `RQ-FT-SORT-SPECIES-LIST` |
| `DS-FN-SORT-SPECIES-ROWS` | [追加] | `RQ-FT-SORT-SPECIES-LIST` |
| `DS-FN-READ-SORT-ORDER` | [追加] | `RQ-FT-SORT-SPECIES-LIST` |
| `DS-FN-LIST-SPECIES-PAGE-SORTED` | [追加] | `RQ-FT-SORT-SPECIES-LIST` |
| `DS-IF-SPECIES-LIST-SORT-CONTROL` | [追加] | `RQ-UI-SPECIES-LIST-SORT-CONTROL`、`RQ-FT-SORT-SPECIES-LIST` |
| `DS-IF-SPECIES-DETAIL-RECORD-DATES` | [追加] | `RQ-UI-SPECIES-DETAIL-RECORD-DATES`、`RQ-FT-SHOW-SPECIES-RECORD-DATES` |
| `DS-TS-SORT-SPECIES-LIST` | [追加] | `RQ-TS-SORT-SPECIES-LIST` |
| `DS-TS-SHOW-SPECIES-RECORD-DATES` | [追加] | `RQ-TS-SHOW-SPECIES-RECORD-DATES` |
| `DS-FN-LIST-SPECIES-PAGE` | [削除] | 削除理由: 並べ替えの処理を加えた `DS-FN-LIST-SPECIES-PAGE-SORTED` に置き換えるため |
| `DS-FN-SEARCH-SPECIES-RECORDS` | 変更なし（既存） | `RQ-FT-SEARCH-SPECIES-KEYWORD`、`RQ-FT-FILTER-SPECIES-CRITERIA` |
| `DS-IF-SPECIES-LIST-SCREEN` | 変更なし（既存） | `RQ-UI-SPECIES-LIST-SCREEN` |
| `DS-IF-SPECIES-DETAIL-SCREEN` | 変更なし（既存） | `RQ-UI-SPECIES-DETAIL-SCREEN` |
| `DS-TS-BROWSE-AND-VIEW-SPECIES` | 変更なし（既存） | `RQ-TS-BROWSE-AND-VIEW-SPECIES` |
| `DS-TS-SEARCH-SPECIES-KEYWORD` | 変更なし（既存） | `RQ-TS-SEARCH-SPECIES-KEYWORD` |
| `DS-TS-FILTER-AND-COMBINE` | 変更なし（既存） | `RQ-TS-FILTER-AND-COMBINE` |

### 11-1. 除外要件

- 無し。
