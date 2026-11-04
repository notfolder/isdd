# 実装タスク（linter の欠落関数の復元）

入力: `change_requirements.md`（要件は増減しない）と `change_detail_design.md`（[追加] 0 件、[復元] 5 件）。

## 1. yamllint/linter.py に復元する

1. `LintProblem.__init__`、`__eq__`、`__lt__` を `LintProblem` クラスの `message` の後に書く（変更設計書 3-1〜3-3）。
2. `_run` を `get_cosmetic_problems` の後、`get_syntax_error` の前に書く（変更設計書 3-4）。
3. `run` を `_run` の後に書く（変更設計書 3-5）。
- 完了条件: `.venv/bin/python -m pytest tests -q` が失敗 0 件。ただし既存の他の挙動は変えない。

## 2. 検証

1. `.venv/bin/python -m pytest tests -q` が全件通る。
2. `e2e/` の E2E テストを回す: `.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml`。全件通る。
3. `bash scripts/isdd/check.sh --strict`。対応表と依存の規則でエラー 0 件。受け入れ判定の結果を報告に書く（この変更の時点の正本は `docs/active_change` 経由で重ねて読まれる）。

## 3. 完了の確認（isdd-build の実装後レビューで行う）

- 変更要件定義書の 5 件が復元され、単体テストと E2E テストが通ったことを報告に書く。
- 実装後レビューで、変更内容を正本（`docs/requirements.md`・`docs/detail_design.md`）へ反映するかを判定し、`docs/active_change` を削除する。
