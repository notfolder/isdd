# 変更要件定義書: 配色の変更と登録画面の項目の変更

- 対象の正本: `docs/requirements.md`（正本は書き換えない。実装後に `isdd-build` が反映する）
- 依頼: `REQUEST.md`（英語）の変更要求 1（配色）と 2（Add species の項目）
- 区分: 変更する要件だけを [追加] [削除] で書く。変更が無い章は「変更なし」と書く。
- 判断の記録: 依頼文の「Add species の項目（名前、生息環境、食性、説明）だけで登録できること」と既存の必須項目（学名、界、保全状況）の矛盾は、ANSWERS.md の固定回答（「依頼の文章から最も単純に決める」）に従い、学名・界・綱・保全状況・平均体長を任意にすることで解いた。既存の一覧・検索・絞り込み・詳細の機能は変えない。

## 1. 目的・前提

- 変更の目的: 配色を依頼のものに変え、登録画面を依頼の項目で登録できるようにする。
- 変更なし。既存要件定義書 `docs/requirements.md` セクション 1 を参照。

### 用語集

- 変更なし。既存要件定義書 `docs/requirements.md` セクション 1（用語集）を参照。
- [追加] 名前: 登録画面の「Name」。生物種の和名・一般名（`common_name`）と同じ項目を指す。
- [追加] 必須項目: 登録・修正で空にできない項目。名前、生息環境、食性。

## 1-1. 技術制約

- 変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

## 2. 業務

### 2-1. 業務の問題

- 変更なし。既存要件定義書 `docs/requirements.md` 2-1 を参照。

### 2-2. 業務課題一覧

- 変更なし。既存要件定義書 `docs/requirements.md` 2-2 を参照。
- 変更後の業務課題と要件の対応: 配色は一覧の業務課題、登録項目は登録・修正・削除の業務課題に対応する（既存と同じ業務課題）。

### 2-3. 見込み経営効果

- 変更なし。既存要件定義書 `docs/requirements.md` 2-3 を参照。

## 3. 機能要件

### 機能一覧

| RQ-ID | 区分 | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか |
|---|---|---|---|---|---|
| `RQ-FT-CREATE-SPECIES-RECORD` | [削除] | マスタ管理 | 生物種を 1 件登録する（削除理由: 必須項目が変わり、登録の項目の規則を `RQ-FT-ADD-SPECIES-FORM` に置き換えるため） | `RQ-BK-MAINTAIN-SPECIES-RECORDS` | — |
| `RQ-FT-ADD-SPECIES-FORM` | [追加] | マスタ管理 | 案内メニューの「Add species」から登録画面を開き、名前、生息環境、食性、説明を入力して 1 件登録する。名前、生息環境、食性は必須で、説明と他の項目（学名、界、綱、保全状況、平均体長）は任意。保存した種は一覧に加わり、キーワード検索と絞り込みで見つかる | `RQ-BK-MAINTAIN-SPECIES-RECORDS` | 依頼の項目で新しい種を登録できない |
| `RQ-FT-VALIDATE-SPECIES-RECORD` | [削除] | 業務機能 | 登録・修正時に業務ルールを確かめる（削除理由: 学名が任意になり、学名の規則を `RQ-FT-VALIDATE-SPECIES-FORM` に置き換えるため） | `RQ-BK-MAINTAIN-SPECIES-RECORDS` | — |
| `RQ-FT-VALIDATE-SPECIES-FORM` | [追加] | 業務機能 | 登録・修正時に、必須項目の入力、選択肢の値、文字数と数値の規則、学名が入力された場合の一意性を確かめる。違反は画面に理由を示し、保存しない | `RQ-BK-MAINTAIN-SPECIES-RECORDS` | 必須項目の空や不正な値が混入する。学名の重複が登録される |

- 変更なし（既存要件定義書 `docs/requirements.md` 3 章の他の機能: 一覧、詳細、検索、絞り込み、組み合わせ、修正、削除）。修正は登録と同じ規則（`RQ-FT-VALIDATE-SPECIES-FORM`）で検証する。

### 3-1. 帳票・出力ファイル

- 変更なし。既存要件定義書 `docs/requirements.md` 3-1 を参照。

### 3-2. 業務ルール

| RQ-ID | 区分 | ルール名 | 内容（条件と結果） | 違反時・エラー時の業務上の扱い | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|
| `RQ-FT-VALIDATE-SPECIES-RECORD` | [削除] | 学名の一意性（旧） | 学名は必須で、他の種と重複してはならない | — | — |
| `RQ-FT-VALIDATE-SPECIES-FORM` | [追加] | 学名の一意性（新） | 学名は任意。入力された場合だけ、前後の空白を除き大文字小文字を区別せず、登録済みの他の種と重複してはならない。修正の場合は自分自身を除いて判定する | 重複する学名の登録・修正は保存せず、同じ入力画面に「This scientific name is already registered.」と表示する | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |
| `RQ-FT-VALIDATE-SPECIES-FORM` | [追加] | 必須項目（新） | 名前、生息環境、食性は必須。界、保全状況、綱、平均体長、説明は任意（空のまま保存できる） | 必須項目が空の場合は保存せず、その項目の下に「Please fill in this field.」等の英語のメッセージを表示する | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |

### 3-3. 外部連携

- 変更なし。既存要件定義書 `docs/requirements.md` 3-3 を参照。

## 4. データ

### 4-1. データ要件一覧

- 変更なし。既存要件定義書 4-1 を参照（SQLite での保存は変わらない）。

### 4-2. 業務エンティティとデータ項目

- 変更: 生物種のデータ項目のうち、次の必須の扱いを変える。他の項目は既存要件定義書 4-2 のとおり。

| エンティティ名 | 区分 | 項目名 | 必須 | 形式・桁 | 値の範囲・制約 |
|---|---|---|---|---|---|
| 生物種 | [削除] | 学名 | 必須 | 文字列、1〜100 文字 | 業務ルール（3-2）に従い一意 |
| 生物種 | [追加] | 学名 | 任意 | 文字列、1〜100 文字（空は保存しない＝NULL） | 入力された場合だけ 3-2 の業務ルールに従い一意 |
| 生物種 | [削除] | 界 | 必須 | 選択式 | Animalia 等 6 種のいずれか |
| 生物種 | [追加] | 界 | 任意 | 選択式 | Animalia 等 6 種のいずれか、または空（NULL） |
| 生物種 | [削除] | 保全状況 | 必須 | 選択式 | IUCN の 8 区分のいずれか |
| 生物種 | [追加] | 保全状況 | 任意 | 選択式 | IUCN の 8 区分のいずれか、または空（NULL） |
| 生物種 | [追加] | 和名・一般名（登録画面の「Name」） | 必須 | 文字列、1〜100 文字 | — |

- サンプル（既存の 12 件）は、すべての項目を持つままにする（既存の行の値は変えない）。

### 4-3. CRUD テーブル

- 変更なし。既存要件定義書 `docs/requirements.md` 4-3 を参照（生物種は変更の有無にかかわらず 1 エンティティで、Create・Read・Update・Delete は既存のとおり）。

### 4-4. 状態遷移

- 変更なし。既存要件定義書 4-4 を参照（状態を持つエンティティは無い）。

### 4-5. 画面一覧

| RQ-ID | 区分 | 画面名 | 対応する CRUD 操作 | 主な機能・目的 | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|
| `RQ-UI-SPECIES-FORM-SCREEN` | 変更なし | 生物種の登録・修正画面 | 生物種:Create、生物種:Update | 項目の入力と保存、入力エラーの表示。項目の必須の扱いは `RQ-FT-ADD-SPECIES-FORM` と `RQ-FT-VALIDATE-SPECIES-FORM` に従う | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |

- 他の画面（一覧、詳細、削除確認）は変更なし。

## 5. 非機能要件

| RQ-ID | 区分 | カテゴリ | 非機能要件名 | 対応業務課題ID（RQ-BK-*） | この非機能要件が無いと何が困るか |
|---|---|---|---|---|---|
| `RQ-NF-VISUAL-THEME-LINEN-MAROON` | [削除] | 利用者・アクセス | 画面の配色（linen と maroon。削除理由: 依頼で honeydew と dark olive green に変わったため） | `RQ-BK-BROWSE-SPECIES-LIST` | — |
| `RQ-NF-VISUAL-THEME-HONEYDEW-OLIVE` | [追加] | 利用者・アクセス | 画面の配色。背景（body）は honeydew（`#F0FFF0`）。すべての画面部品（案内メニュー、ボタン、リンク、表の見出し、入力欄の枠、バッジ、削除確認の枠など）は dark olive green（`#556B2F`）。部品の上の文字は白（`#FFFFFF`）。 | `RQ-BK-BROWSE-SPECIES-LIST` | 依頼された配色で画面を見てもらえない |
| `RQ-NF-ANONYMOUS-LOCAL-ACCESS` | 変更なし | 利用者・アクセス | 認証無しで、ローカルの `127.0.0.1` からだけ使う | `RQ-BK-BROWSE-SPECIES-LIST` | 既存のまま |

- 画面の言語は英語のまま（変更なし）。

## 6. 運用要件

| RQ-ID | 区分 | 種別 | 内容 | 対応業務課題ID（RQ-BK-*） | この要件が無いと何が困るか |
|---|---|---|---|---|---|
| `RQ-OP-MIGRATE-EXISTING-DATABASE` | [追加] | データ移行 | 既存の `DATA_DIR/species.db`（学名、界、保全状況が必須の旧い定義）がある場合、起動時にデータを失わず新しい定義（上の 4-2 の任意項目）へ移す。移行は 1 回だけ行い、移行後に既存の行を変えない。既に新しい定義なら何もしない | `RQ-BK-MAINTAIN-SPECIES-RECORDS` | 既存の利用者のデータが消える、または新しい登録ができない |
- 変更なし（起動、サンプルデータ、ログ・監視・バックアップの不要の各要件）。既存要件定義書 6 章を参照。

## 7. テスト用利用シナリオ

| RQ-ID | 区分 | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|---|
| `RQ-TS-CREATE-SPECIES-RECORD` | [削除] | 旧い登録の確認（削除理由: `RQ-TS-ADD-SPECIES-FORM` に置き換え） | — | — | — | `RQ-FT-CREATE-SPECIES-RECORD`、`RQ-FT-VALIDATE-SPECIES-RECORD`、`RQ-UI-SPECIES-FORM-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |
| `RQ-TS-ADD-SPECIES-FORM` | [追加] | 「Add species」の登録を画面から確かめ、一覧、検索、絞り込みに出ることを確かめる。学名の重複の規則も確かめる | サンプルが入っている | 案内メニューの「Add species」を開く。Name に `Test Gecko`、Habitat に `Terrestrial`、Diet に `Carnivore`、Description に `A test entry.` を入れて Save する。次に一覧で `Test Gecko` を探す。検索欄に `gecko` を入れて検索する。Habitat で `Terrestrial`、Diet で `Carnivore` を選んで絞り込む。もう一度 Add species から、学名に `panthera leo`（既存の Panthera leo と大文字小文字違い）を入れ、名前、生息環境、食性を入れて Save する | 1 回目は詳細に移り、一覧・検索・絞り込みに `Test Gecko` が出る。2 回目は保存されず、学名の欄の下に「This scientific name is already registered.」が出て、入力値が残る | `RQ-FT-ADD-SPECIES-FORM`、`RQ-FT-VALIDATE-SPECIES-FORM`、`RQ-UI-SPECIES-FORM-SCREEN`、`RQ-UI-GLOBAL-NAVIGATION` | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |
| `RQ-TS-UPDATE-SPECIES-RECORD` | [削除] | 修正の確認（旧い検証する要件 ID の列） | 登録済みの種が 1 件ある | — | — | `RQ-FT-UPDATE-SPECIES-RECORD`、`RQ-FT-VALIDATE-SPECIES-RECORD`、`RQ-UI-SPECIES-FORM-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |
| `RQ-TS-UPDATE-SPECIES-RECORD` | [追加] | 修正を確かめる（検証する要件 ID の列を新しくした。手順と期待結果は変えない） | 登録済みの種が 1 件ある | 詳細画面から修正画面を開き、Name を変えて保存する。修正画面で自分自身の学名をそのまま保存する | 詳細に変更後の名前が出る。自分自身の学名は重複とされず保存される | `RQ-FT-UPDATE-SPECIES-RECORD`、`RQ-FT-VALIDATE-SPECIES-FORM`、`RQ-UI-SPECIES-FORM-SCREEN` | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |
| `RQ-TS-THEME-LINEN-MAROON` | [削除] | 旧い配色の確認（削除理由: 配色を変えるため） | — | — | — | `RQ-NF-VISUAL-THEME-LINEN-MAROON`、`RQ-UI-GLOBAL-NAVIGATION` | `RQ-BK-BROWSE-SPECIES-LIST` |
| `RQ-TS-THEME-HONEYDEW-OLIVE` | [追加] | 新しい配色を確かめる | サンプルが入っている | 一覧、詳細、登録画面を開く | 背景が honeydew（`#F0FFF0`）で、案内メニュー、ボタン、リンク、表の見出しが dark olive green（`#556B2F`）で表示される | `RQ-NF-VISUAL-THEME-HONEYDEW-OLIVE`、`RQ-UI-GLOBAL-NAVIGATION` | `RQ-BK-BROWSE-SPECIES-LIST` |
| `RQ-TS-MIGRATE-EXISTING-DATABASE` | [追加] | 旧い定義の既存データベースを移行し、データが残ることを確かめる | 旧い定義の `species.db` に 1 件の種がある | 旧い定義のファイルを DATA_DIR に置いて起動し、一覧を開く。学名を空にして新しい種を登録する | 既存の種が一覧に残る。学名が空の登録が保存される | `RQ-OP-MIGRATE-EXISTING-DATABASE`、`RQ-FT-ADD-SPECIES-FORM` | `RQ-BK-MAINTAIN-SPECIES-RECORDS` |

- 変更なし: 起動、一覧と詳細、検索、絞り込みと組み合わせ、削除のシナリオ（既存要件定義書 7 章を参照）。

## 変更後の業務課題と要件の対応

- 業務課題の一覧は変更なし（既存要件定義書 2-2）。変更した要件はすべて既存の業務課題に対応する。
