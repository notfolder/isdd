# 変更要件定義書（既存の欠落関数の復元）

正本の要件定義書は `docs/requirements.md`。この変更は要件を増減しない。正本の要件が実装されるように、削除された関数・メソッドを既存コードへ戻す。

## 変更の概要

既存コードから次の 3 つが削除されている（コメントは残っている）。この変更は要件を増減しない（変更の区分: [追加] 0 件、[削除] 0 件）。正本の要件が実装されるように、削除された実装を既存コードへ戻す。

| 対象（削除された実装） | 種類 | 正本で受けている既存の要件 | 対応業務課題ID |
|---|---|---|---|
| `yamllint/parser.py` の `token_or_comment_generator` | 公開関数 | RQ-FT-PARSE-TOKENS、RQ-FT-LINT-YAML-BUFFER | RQ-BK-ENFORCE-STYLE-RULES |
| `yamllint/rules/indentation.py` の `check` | 公開関数（規則の入口） | RQ-FT-RULE-INDENTATION | RQ-BK-INDENTATION-CONSISTENCY |
| `yamllint/rules/indentation.py` の `Parent.__repr__` | 表示用のダンダーメソッド | RQ-FT-RULE-INDENTATION | RQ-BK-INDENTATION-CONSISTENCY |

この 3 つが無いと、リンタの検査（`linter.run`）が実行時に失敗する。要件の内容は正本のとおりで、変更しない。`Parent.__repr__` は内部の表示のため、新しい要件は作らない（PRD に無い機能は作らない）。

## 1. 目的・前提

変更なし。既存要件定義書 `docs/requirements.md` 1 を参照。

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照。

## 3. 機能要件

変更なし（[追加] の `RQ-FT`・`RQ-UI`・`RQ-EX` は無い）。既存要件定義書 `docs/requirements.md` 3 を参照。
既存の `RQ-FT-PARSE-TOKENS`・`RQ-FT-LINT-YAML-BUFFER`・`RQ-FT-RULE-INDENTATION` を、削除された実装で満たせるように戻す。

## 4. データ

変更なし。既存要件定義書 `docs/requirements.md` 4 を参照。

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` 5 を参照。

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` 6 を参照。

## 7. テスト用利用シナリオ

変更なし。既存要件定義書 `docs/requirements.md` 7 を参照。既存のシナリオ（`RQ-TS-*`）を確かめる E2E テストは、この変更の実装で作る（`change_detail_design.md` 8-2 の `DS-TS-*`）。

## 8. 変更後の業務課題と要件の対応表

変更なし。既存要件定義書 `docs/requirements.md` 2-2 と 3 の対応のとおり。

## 9. 除外要件

除外要件は無い。
