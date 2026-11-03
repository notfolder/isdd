# Hello World 出力システム 変更要件定義書（実行の入口と出力処理を分ける）

既存要件定義書: `docs/requirements.md`

## 1. 目的・前提

- システムの目的: 変更なし。既存要件定義書 `docs/requirements.md` セクション1 を参照
- 用語集（追加）

| 用語 | 業務上の意味 | 本案件での使用範囲 | 同義語/類義語 | 区分 |
|---|---|---|---|---|
| 実行の入口 | 利用者や CI が直接実行するスクリプト | `src/main.py` | エントリポイント | [追加] |

- システムの形態: 変更なし

### 1-1. 技術制約

変更なし。既存要件定義書 `docs/requirements.md` 1-1 を参照。

## 2. 業務

対象業務は変更なし（`RQ-BZ-OUTPUT-VERIFICATION`）。

### 2-1. 業務の問題（追加）

| 問題 | 対象業務（RQ-BZ） | あるべき姿 | 現状 | ギャップ（KPI） | 業務影響 |
|---|---|---|---|---|---|
| 検証スクリプトの入口と出力処理が 1 ファイルで、他の検証から出力処理を再利用できない | `RQ-BZ-OUTPUT-VERIFICATION` | 出力処理を他の検証スクリプトから呼べる | 入口と出力処理が同じファイルにある | 出力処理を再利用している検証の数: あるべき姿 2 以上、現状 0 | 検証ごとに出力処理を書き直している |

### 2-2. 業務課題一覧

既存の `RQ-BK-SHARED-VERIFICATION-SCRIPT` は変更なし。

| RQ-BK-ID | 業務課題（取り組むこと） | 解決する問題（2-1） | 解決後の状態（KPI の目標値） | 対象業務（RQ-BZ） | 区分 |
|---|---|---|---|---|---|
| `RQ-BK-REUSABLE-OUTPUT-MODULE` | 実行の入口と出力処理を別のファイルに分ける | 入口と出力処理が 1 ファイルで再利用できない | 出力処理を他の検証から import して使える | `RQ-BZ-OUTPUT-VERIFICATION` | [追加] |

### 2-3. 見込み経営効果

変更なし（追加の効果は算定しない）。

## 3. 機能要件

- 出力データ: 変更なし（固定文字列 "Hello, World!" を 1 行）
- 入力データ、CUI の引数と終了コード: 変更なし。ただし実行するスクリプトは `src/main.py` になる

| RQ-ID | カテゴリ | 機能名 | 対応業務課題ID（RQ-BK-*） | この機能が無いと何が困るか | 区分 |
|---|---|---|---|---|---|
| `RQ-FT-GET-HELLO-MESSAGE`（deprecated） | 業務機能 | 表示文字列の取得 | `RQ-BK-REUSABLE-OUTPUT-MODULE` | 挨拶文を定数で持つ要件に置き換えるため削除する | [削除] |
| `RQ-FT-GET-GREETING-MESSAGE` | 業務機能 | 挨拶文の取得（定数 GREETING に持つ "Hello, World!" を返す。他の検証からも同じ定数を参照できる） | `RQ-BK-SHARED-VERIFICATION-SCRIPT`, `RQ-BK-REUSABLE-OUTPUT-MODULE` | 検証ごとに文字列を書き直し、表示が食い違う | [追加] |
| `RQ-FT-RUN-FROM-ENTRY` | 業務機能 | 実行の入口（`src/main.py`）から出力処理を呼ぶ | `RQ-BK-REUSABLE-OUTPUT-MODULE` | 出力処理を import で再利用できない | [追加] |

### 3-1. 帳票・出力ファイル

変更なし。既存要件定義書 `docs/requirements.md` 3-1 を参照（`RQ-UI-HELLO-STDOUT-OUTPUT`）。

### 3-2. 業務ルール

業務ルールは無い。

### 3-3. 外部連携

外部連携は無い。

## 4. データ

変更なし。既存要件定義書 `docs/requirements.md` セクション4 を参照。

### 4-3. CRUD テーブル

業務エンティティが無いため対象外。

## 5. 非機能要件

変更なし。

## 6. 運用要件

変更なし。

## 7. テスト用利用シナリオ

変更なし。既存の `RQ-TS-VERIFY-HELLO-WORLD-OUTPUT` は `src/main.py` の実行で確かめる。

## 8. 業務課題と要件の対応表（変更後）

| RQ-BK-ID | 業務課題 | 対応要件ID |
|---|---|---|
| `RQ-BK-SHARED-VERIFICATION-SCRIPT` | 共通の検証スクリプトを用意する | `RQ-FT-GET-GREETING-MESSAGE`, `RQ-FT-PRINT-HELLO-WORLD`, `RQ-UI-HELLO-STDOUT-OUTPUT`, `RQ-DT-DB-NOT-REQUIRED`, `RQ-TS-VERIFY-HELLO-WORLD-OUTPUT` |
| `RQ-BK-REUSABLE-OUTPUT-MODULE` | 実行の入口と出力処理を分ける | `RQ-FT-GET-GREETING-MESSAGE`, `RQ-FT-RUN-FROM-ENTRY` |
