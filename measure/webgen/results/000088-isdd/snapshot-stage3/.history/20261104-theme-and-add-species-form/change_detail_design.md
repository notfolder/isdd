# 変更設計書: 配色の変更と登録画面の項目の変更

- 対象の正本: `docs/detail_design.md`（正本は書き換えない。実装後に `isdd-build` が反映する）
- 対象の変更要件: `change_requirements.md`
- 区分: 変更する要素だけを [追加] [削除] で書く。変更が無い章は「変更なし」と書く。設計要素の ID は、中身（責務）が変わらなければ変えない。対応だけが変わるものは第 11 章の行を [削除]（旧い対応）と [追加]（新しい対応）で分けて書く。

## 1. 言語・フレームワーク・アーキテクチャの選定

- 変更なし。既存設計書 `docs/detail_design.md` 第 1 章（Python 3.12、Flask、SQLite）を引き継ぐ。変更要件の技術制約と矛盾しない。

## 2. システム構成

- 変更なし。既存設計書 `docs/detail_design.md` 第 2 章を参照。

## 3. データ設計

### 3-1. データモデル

- 変更（テーブル `species` の定義）。次の 3 カラムを NULL 可にする。他のカラムは既存のまま。
  - `scientific_name`: NULL 可。値がある場合だけ長さ 1〜100、UNIQUE（COLLATE NOCASE。SQLite の UNIQUE は NULL を重複とみなさないため、学名が空の種は複数あってよい）。
  - `kingdom`: NULL 可。値がある場合は 6 種のいずれか（CHECK は `kingdom IS NULL OR kingdom IN (...)`）。
  - `conservation_status`: NULL 可。値がある場合は 8 種のいずれか（CHECK は同様）。
- `common_name`（名前）と `habitat`、`diet` は NOT NULL のまま。`description` は既存どおり NULL 可。
- 変更（移行）: 既存の `species` 表が旧い定義（上の 3 カラムが NOT NULL）のときは、起動時に 1 回だけ作り直す。手順は次のとおり（1 つのトランザクションで行う）。
  1. 新しい定義で `species_new` を作る。
  2. `species` の全行を `species_new` へ同じ値のまま写す。
  3. `species` を削除し、`species_new` を `species` へ改名する。
  4. 旧い定義かどうかは、`PRAGMA table_info(species)` で上の 3 カラムの NOT NULL を見て判定する。新しい定義なら何もしない。
- 変更（データの扱い）: 空の任意項目は NULL で保存する（空文字で保存しない）。

リレーション図: 変更なし（単一のテーブル）。

### 3-2. トランザクションと排他制御

- 変更なし。既存設計書 3-2 を参照。移行だけは 3-1 の手順を 1 つのトランザクションで行う。

### 3-3. 状態遷移

- 変更なし。

## 4. アーキテクチャ設計

### 4-1. 外部設計

#### 画面（GUI）

- 変更（登録・修正画面 `DS-IF-SPECIES-FORM-SCREEN`）。見出しは既存どおり（「Add species」「Edit species」）。項目は次のとおり。
  - Name（必須。`common_name` に保存する。画面の表示名だけを「Name」にする）
  - Habitat（必須。選択欄）
  - Diet（必須。選択欄）
  - Description（任意。複数行）
  - Scientific name、Kingdom、Class、Conservation status、Average length (cm)（任意。空のまま保存できる）
  - 必須の項目には「*」を付ける。Save ボタンと Cancel は既存どおり。
- 変更なし: 一覧、詳細、削除確認、案内メニュー（既存設計書 4-1 を参照）。
- 変更（詳細と一覧の表示）: 学名、界、保全状況が空の種は、その欄に「—」を出す。

#### インターフェース仕様

- 変更（登録と修正の入力）: 項目の規則は次のとおり。前後の空白は除く。
  - Name: 空、または 100 文字超はエラー。エラーメッセージは「Name is required and must be at most 100 characters.」
  - Habitat、Diet: 空、または選択肢以外はエラー（「Please select a value from the list.」）。
  - Scientific name: 空は許す。値がある場合は 100 文字超と、他の種との重複（大文字小文字を区別しない。修正は自分自身を除く）をエラーにする（重複の文言は既存どおり「This scientific name is already registered.」）。
  - Kingdom、Conservation status: 空は許す。値がある場合は選択肢の値のみ。
  - Class、Average length、Description: 既存の規則のまま。空は許す。
- 変更（エラー仕様の表）: 学名の「空、または 100 文字超」の行を、「100 文字超」だけに変える。名前の行（和名）の文言を「Name is required and must be at most 100 characters.」にする。ほかの行は変えない。

### 4-2. 内部設計

#### 処理の役割

- 変更（検証、`DS-FN-VALIDATE-SPECIES-FORM`）: 4-1 のインターフェース仕様の規則を確かめる。学名の必須判定を外し、学名がある場合だけ重複を判定する。
- 変更（入力の読み取り、`DS-FN-PARSE-SPECIES-FORM`）: 前後の空白を除き、空の任意項目を NULL にして `SpeciesForm` に写す。
- 変更（保存、`DS-FN-INSERT-SPECIES-RECORD`、`DS-FN-UPDATE-SPECIES-RECORD`）: NULL を含む値をそのまま保存する。
- 追加（移行、`DS-FN-MIGRATE-SPECIES-TABLE`）: 3-1 の移行を行う。`DS-FN-ENSURE-DATABASE-SCHEMA` から呼ぶ。新しい定義なら何もしない。

#### 処理フロー（登録）

- 変更なし（既存の流れのまま）。ただし「各項目を検証する」の中身は 4-2 の検証の変更に従う。学名の重複判定は、学名がある場合だけ行う。

## 5. クラス設計

- 変更なし（`SpeciesForm` の属性はそのまま。学名、界、保全状況の属性の値が空でありうるだけ）。

## 6. エラーハンドリングとセキュリティ設計

- 変更（エラーの扱い）: 4-1 のエラーメッセージに従う。移行に失敗したら起動を止め、利用者にはコンソールの英語のメッセージを出す（画面は出さない）。
- 変更なし: 認証、認可、監査ログ、その他のセキュリティ対策。

## 7. コード設計

### ディレクトリ構成・ファイル一覧

- 変更（ファイル一覧の説明だけ）: `app/static/style.css` は配色を honeydew と dark olive green に変える（色は `:root` の変数）。`app/db.py` に移行の関数を足す（`DS-FN-MIGRATE-SPECIES-TABLE`）。`app/templates/species_form.html` は項目の必須の表示と名前の表示を変える。テンプレートはソースファイルではないため DS-MD は付けない。
- 変更なし: ほかのファイル。

### 依存の規則

- 変更なし。既存設計書 7 章の依存の規則（`scripts/isdd/dependencies.json`）をそのまま守る。

### コーディング規約・ID の扱い

- 変更なし。

## 8. テスト設計

### 8-1. テストの種類と方針

- 変更なし。

### 8-2. E2E テストのシナリオ

- 変更（削除）: 旧い登録のシナリオ（学名の重複を含む、登録の E2E）は削除する。
- 変更（追加）: `DS-TS-ADD-SPECIES-FORM` を `RQ-TS-ADD-SPECIES-FORM` に対応させる。手順は変更要件定義書 7 章の `RQ-TS-ADD-SPECIES-FORM` のとおり。HTTP で実サーバーに POST する（`/species/new`）。確かめる内容は、新しい種が `/`、`/?q=gecko`、`/?habitat=Terrestrial&diet=Carnivore` に出ること、同じ学名（大小違い）の 2 回目が 200 で重複のエラーを返し、保存されないこと。
- 変更（削除と追加）: 旧い配色のシナリオは削除し、`DS-TS-THEME-HONEYDEW-OLIVE` を追加する（`RQ-TS-THEME-HONEYDEW-OLIVE`）。期待結果は `/static/style.css` の背景が `#F0FFF0`、部品が `#556B2F` であり、HTML がそれを読み込むこと。
- 追加: `DS-TS-MIGRATE-EXISTING-DATABASE`（`RQ-TS-MIGRATE-EXISTING-DATABASE`）。旧い定義の SQLite ファイルを作って起動し、既存の 1 件が残ること、学名を空にした登録が 302 で保存されることを確かめる。
- 変更なし: 修正のシナリオ（手順と期待結果は同じ。検証する要件 ID だけが変わる）、その他のシナリオ。

### 8-3. E2E の実行手段

- 変更なし。

### 8-4. E2E の実行コマンドと運用

- 変更なし。

## 9. 運用設計

### 起動方式・初期化

- 変更なし（起動は `bash run.sh`、サンプルは空のときだけ入れる）。

### データ移行

- 変更（追加）: 起動時に旧い定義の `species` 表を新しい定義へ移す（3-1 の手順）。移行は既存の行を変えない。移行の対象は `DATA_DIR/species.db` だけ。

## 10. ログ・監視・アラート・障害対応設計

- 変更なし。

## 11. 要件と設計の対応表

変更の対応は次のとおり。中身が変わらない設計要素は ID を変えず、対応の行だけを [削除]（旧い対応）と [追加]（新しい対応）で分けて書く。

| DS-ID | 対応要件ID |
|---|---|
| `DS-FN-MIGRATE-SPECIES-TABLE` | [追加] `RQ-OP-MIGRATE-EXISTING-DATABASE` |
| `DS-FN-ENSURE-DATABASE-SCHEMA` | [追加] `RQ-OP-MIGRATE-EXISTING-DATABASE` |
| `DS-SC-SPECIES-TABLE` | [追加] `RQ-OP-MIGRATE-EXISTING-DATABASE` |
| `DS-MD-REPOSITORY` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-MD-REPOSITORY` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-CL-SPECIES-REPOSITORY` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-CL-SPECIES-REPOSITORY` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-FN-FIND-SPECIES-ID-BY-SCIENTIFIC-NAME` | [削除] `RQ-FT-VALIDATE-SPECIES-RECORD` |
| `DS-FN-FIND-SPECIES-ID-BY-SCIENTIFIC-NAME` | [追加] `RQ-FT-VALIDATE-SPECIES-FORM` |
| `DS-FN-INSERT-SPECIES-RECORD` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-FN-INSERT-SPECIES-RECORD` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-MD-VALIDATION` | [削除] `RQ-FT-VALIDATE-SPECIES-RECORD`、`RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-MD-VALIDATION` | [追加] `RQ-FT-VALIDATE-SPECIES-FORM`、`RQ-FT-ADD-SPECIES-FORM` |
| `DS-CL-SPECIES-FORM` | [削除] `RQ-FT-VALIDATE-SPECIES-RECORD` |
| `DS-CL-SPECIES-FORM` | [追加] `RQ-FT-VALIDATE-SPECIES-FORM` |
| `DS-FN-PARSE-SPECIES-FORM` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-FN-PARSE-SPECIES-FORM` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-FN-VALIDATE-SPECIES-FORM` | [削除] `RQ-FT-VALIDATE-SPECIES-RECORD` |
| `DS-FN-VALIDATE-SPECIES-FORM` | [追加] `RQ-FT-VALIDATE-SPECIES-FORM` |
| `DS-MD-ROUTES` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-MD-ROUTES` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-FN-SHOW-CREATE-FORM-PAGE` | [削除] `RQ-FT-CREATE-SPECIES-RECORD` |
| `DS-FN-SHOW-CREATE-FORM-PAGE` | [追加] `RQ-FT-ADD-SPECIES-FORM` |
| `DS-FN-SUBMIT-CREATE-FORM` | [削除] `RQ-FT-CREATE-SPECIES-RECORD`、`RQ-FT-VALIDATE-SPECIES-RECORD` |
| `DS-FN-SUBMIT-CREATE-FORM` | [追加] `RQ-FT-ADD-SPECIES-FORM`、`RQ-FT-VALIDATE-SPECIES-FORM` |
| `DS-FN-SUBMIT-EDIT-FORM` | [削除] `RQ-FT-VALIDATE-SPECIES-RECORD` |
| `DS-FN-SUBMIT-EDIT-FORM` | [追加] `RQ-FT-VALIDATE-SPECIES-FORM` |
| `DS-IF-SPECIES-FORM-SCREEN` | 変更なし（既存） `RQ-UI-SPECIES-FORM-SCREEN` |
| `DS-TS-CREATE-SPECIES-RECORD` | [削除] `RQ-TS-CREATE-SPECIES-RECORD` |
| `DS-TS-ADD-SPECIES-FORM` | [追加] `RQ-TS-ADD-SPECIES-FORM` |
| `DS-TS-THEME-LINEN-MAROON` | [削除] `RQ-TS-THEME-LINEN-MAROON`、`RQ-NF-VISUAL-THEME-LINEN-MAROON` |
| `DS-TS-THEME-HONEYDEW-OLIVE` | [追加] `RQ-TS-THEME-HONEYDEW-OLIVE`、`RQ-NF-VISUAL-THEME-HONEYDEW-OLIVE` |
| `DS-TS-MIGRATE-EXISTING-DATABASE` | [追加] `RQ-TS-MIGRATE-EXISTING-DATABASE`、`RQ-OP-MIGRATE-EXISTING-DATABASE` |
| `DS-FN-UPDATE-SPECIES-RECORD` | 変更なし（既存） `RQ-FT-UPDATE-SPECIES-RECORD` |
| `DS-TS-UPDATE-SPECIES-RECORD` | 変更なし（既存） `RQ-TS-UPDATE-SPECIES-RECORD` |
| `DS-IF-SPECIES-LIST-SCREEN` | 変更なし（既存） `RQ-UI-SPECIES-LIST-SCREEN` |
| `DS-IF-SPECIES-DETAIL-SCREEN` | 変更なし（既存） `RQ-UI-SPECIES-DETAIL-SCREEN` |
| `DS-IF-SPECIES-DELETE-CONFIRM-SCREEN` | 変更なし（既存） `RQ-UI-SPECIES-DELETE-CONFIRM-SCREEN` |
| `DS-IF-GLOBAL-NAVIGATION` | 変更なし（既存） `RQ-UI-GLOBAL-NAVIGATION` |
| `DS-OP-START-SERVER` | 変更なし（既存） `RQ-NF-ANONYMOUS-LOCAL-ACCESS` |

- 変更なし（既存）: 下の行は中身も対応も変わらない既存の設計要素。

### 11-1. 除外要件

- 除外要件は無い。
