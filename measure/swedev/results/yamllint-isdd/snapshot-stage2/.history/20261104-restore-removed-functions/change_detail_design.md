# 変更設計書（既存の欠落関数の復元）

正本の詳細設計書は `docs/detail_design.md`。この変更は設計要素を増やすのではなく、正本に設計された 2 つの公開関数を既存コードへ戻す。`Parent` の表示用メソッドは、既存のインデントの親を表すクラスの責務の表示であり、設計 ID を持たない（ダンダーメソッドは対応表に載せない。`docs/trace_map.md` の規則）。

## 1. 言語・フレームワーク・アーキテクチャの選定

変更なし。既存設計 `docs/detail_design.md` セクション 1 を参照。

## 2. システム構成

変更なし。既存設計 `docs/detail_design.md` セクション 2 を参照。

## 3. データ設計

変更なし。既存設計 `docs/detail_design.md` セクション 3 を参照。

## 4. アーキテクチャ設計

### 4-1. 外部設計

変更なし。既存設計 `docs/detail_design.md` セクション 4-1 を参照。

### 4-2. 内部設計

[追加] 字句の列の作り方（`DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR`）。PyYAML の字句解析器を入力のバッファから作り、字句を 1 つずつ取り出す。各字句について、その前の字句、次の字句、次の次の字句を一緒に渡す。字句と字句の間のコメントは、既存の `comments_between_tokens` で取り出して、位置の順に渡す。構文の誤りは字句解析器の例外として呼び出し元へ伝える（リンタが構文エラーとして扱う）。

[追加] インデント規則の入口（`DS-FN-RULE-INDENTATION-CHECK`）。既存の `_check` へ引数をそのまま渡し、結果の問題を生成器として返す。規則の状態は、呼び出し元の文脈（`context`）に持つ。

## 5. クラス設計

変更なし。既存設計 `docs/detail_design.md` セクション 5 を参照。インデントの親を表すクラス（`Parent`）の表示用の文字列（`__repr__`）は、既存の責務（インデントの親の情報を保持する）の表示であり、責務は変えない。

## 6. エラーハンドリングとセキュリティ設計

変更なし。既存設計 `docs/detail_design.md` セクション 6 を参照。

## 7. コード設計

### 7-1. ディレクトリ構成とファイル

変更なし（新しいファイルは作らない。`parser.py` と `rules/indentation.py` に関数を戻す）。既存設計 `docs/detail_design.md` セクション 7-1 を参照。

### 7-2. 公開関数とメソッドの設計

| 区分 | DS-ID | 修飾名 | 役割 |
|---|---|---|---|
| [追加] | `DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR` | `yamllint/parser.py::token_or_comment_generator` | 入力のバッファから字句を前後の字句つきで順に生成し、字句の間のコメントも生成する |
| [追加] | `DS-FN-RULE-INDENTATION-CHECK` | `yamllint/rules/indentation.py::check` | インデント規則の入口。字句ごとに既存の `_check` を呼び、違反の問題を生成する |

依存の規則: 変更なし（無い）。

## 8. テスト設計

### 8-1. テストの種類と方針

変更なし。既存設計 `docs/detail_design.md` セクション 8-1 を参照。単体テストは `tests/`（既存のテストファイルが、削除された関数を import している）。

### 8-2. E2E テストのシナリオ

変更なし（E2E シナリオは既存の 13 件。この変更で E2E テストを初めて実装する）。既存設計 `docs/detail_design.md` セクション 8-2 を参照。

### 8-3. E2E の実行手段

変更なし。

### 8-4. E2E の実行コマンドと運用

変更なし。

## 9. 運用設計

変更なし。

## 10. ログ・監視・アラート・障害対応設計

変更なし。

## 11. 要件と設計の対応表

既存の対応は変更しない。次の行を [追加] する。

| DS-ID | 対応要件ID |
|---|---|
| [追加] `DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR` | `RQ-FT-PARSE-TOKENS`, `RQ-FT-LINT-YAML-BUFFER` |
| [追加] `DS-FN-RULE-INDENTATION-CHECK` | `RQ-FT-RULE-INDENTATION` |

### 11-1. 除外要件

除外要件は無い。

## 12. 正本への反映時の注意（実装後レビューへの引き継ぎ）

- 正本 `docs/detail_design.md` の「12. 現状の注記」と、`docs/requirements.md` の「8. 現状の注記」は、実装後に削除する（不足が解消するため）。
