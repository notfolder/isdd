# 変更要件定義書（linter の欠落関数の復元）

正本の要件定義書は `docs/requirements.md`。この変更は要件を増減しない。正本の要件が実装されるように、削除されたメソッドと関数を既存コードへ戻す。

## 変更の概要

既存コード `yamllint/linter.py` から次の 5 つが削除されている（シグネチャと docstring は残っている。PRD の FOLDER STRUCTURE に挙がったもの）。変更の区分: [追加] 0 件、[削除] 0 件、[復元] 5 件。

| 対象（復元する実装） | 種類 | 正本で受けている既存の要件 | 対応業務課題ID |
|---|---|---|---|
| `yamllint/linter.py` の `LintProblem.__init__` | クラスのメソッド（初期化） | RQ-FT-LINT-YAML-BUFFER、RQ-FT-REPORT-SYNTAX-ERROR | RQ-BK-ENFORCE-STYLE-RULES |
| `yamllint/linter.py` の `LintProblem.__eq__` | クラスのメソッド（同一判定） | RQ-FT-LINT-YAML-BUFFER、RQ-TS-LINT-BUFFER-PROBLEMS の比較 | RQ-BK-REPORT-PROBLEMS-CI |
| `yamllint/linter.py` の `LintProblem.__lt__` | クラスのメソッド（順序） | RQ-FT-LINT-YAML-BUFFER（問題を行の順に返す） | RQ-BK-ENFORCE-STYLE-RULES |
| `yamllint/linter.py` の `_run` | 内部関数 | RQ-FT-LINT-YAML-BUFFER、RQ-FT-DIRECTIVE-DISABLE、RQ-FT-REPORT-SYNTAX-ERROR | RQ-BK-ENFORCE-STYLE-RULES |
| `yamllint/linter.py` の `run` | 公開関数（ライブラリの入口） | RQ-FT-LINT-YAML-BUFFER、RQ-UI-LIBRARY-API | RQ-BK-ENFORCE-STYLE-RULES |

この 5 つが無いと、CLI と検査（`linter.run`）が実行時に失敗する。要件の内容は正本のとおりで、変更しない。`_run` は内部関数のため、設計の公開関数の表（DS-FN）には載せない（正本の 7-2 の規則）。

## 1. 目的・前提

変更なし。既存要件定義書 `docs/requirements.md` 1 を参照。

## 2. 業務

変更なし。既存要件定義書 `docs/requirements.md` 2 を参照。

## 3. 機能要件

変更なし（[追加] の `RQ-FT`・`RQ-UI`・`RQ-EX` は無い）。既存の `RQ-FT-LINT-YAML-BUFFER`、`RQ-FT-REPORT-SYNTAX-ERROR`、`RQ-FT-DIRECTIVE-DISABLE`、`RQ-UI-LIBRARY-API` を、復元する実装で満たせるようにする。

## 4. データ

変更なし。既存要件定義書 `docs/requirements.md` 4 を参照。`LintProblem` の属性（line、column、desc、rule、level）は `RQ-DT-LINT-PROBLEM` のとおり。

## 5. 非機能要件

変更なし。既存要件定義書 `docs/requirements.md` 5 を参照。新しい依存は足さない（既存の `io`、`re`、`yaml`、`parser` だけを使う）。

## 6. 運用要件

変更なし。既存要件定義書 `docs/requirements.md` 6 を参照。

## 7. テスト用利用シナリオ

変更なし。既存要件定義書 `docs/requirements.md` 7 を参照。既存のシナリオ（`RQ-TS-*`）を確かめる E2E テストは、既存の `e2e/` で行う（この変更で新しいシナリオは増やさない）。

## 8. 変更後の業務課題と要件の対応表

変更なし。既存要件定義書 `docs/requirements.md` 2-2 と 3 の対応のとおり。

## 9. 除外要件

除外要件は無い。PRD に挙がった 5 つはすべて復元する。
