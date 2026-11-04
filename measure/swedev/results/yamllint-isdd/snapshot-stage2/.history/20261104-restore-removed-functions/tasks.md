# 実装タスク（既存の欠落関数の復元）

入力: `change_requirements.md`（要件は増減しない）と `change_detail_design.md`（[追加] 2 件の公開関数、E2E の実装）。
isdd-build は上から順に実行する。

## 0. isdd-setup 導入確認タスク

- `scripts/isdd/check.sh` と `scripts/isdd/completeness.json` が有ることを確かめる（導入済み: isdd v2.2.0、実行形態 library、認証なし、外部連携なし、対応表の粒度 function）
- 完了条件: `bash scripts/isdd/check.sh` が実行でき、`scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書と一致していること

## 0-2. 進行中の変更の登録確認タスク

- `docs/active_change` の 1 行目が `.history/20261104-restore-removed-functions/` を指していることを確認する。正本（`docs/requirements.md`・`docs/detail_design.md`）には変更を反映しない
- 完了条件: `bash scripts/isdd/check.sh` の出力に「進行中の変更」の行があり、`rq_ds_link_checker.py .history/20261104-restore-removed-functions/change_requirements.md .history/20261104-restore-removed-functions/change_detail_design.md --base docs/requirements.md` が合格すること

## 1. 公開関数 token_or_comment_generator の実装

- 設計 ID: `DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR`（`yamllint/parser.py::token_or_comment_generator`）
- 内容: 変更設計書 4-2 と 7-2 のとおり。既存の `comments_between_tokens` と `Token` を使う。字句の前後の字句を渡す。モジュールの既存の import に依存を足すときは、既存の依存（PyYAML）だけを使う
- 完了条件: `python3 -m pytest tests/test_parser.py` が全件通過すること

## 2. 公開関数 check とメソッド Parent.__repr__ の実装

- 設計 ID: `DS-FN-RULE-INDENTATION-CHECK`（`yamllint/rules/indentation.py::check`）。`Parent.__repr__` は `DS-CL-RULE-INDENTATION-PARENT` の表示（対応表には載せない）
- 内容: `check` は `_check` へ引数を渡す。`Parent.__repr__` は既存のモジュール定数 `labels` を型の添字で引き、`"{ラベル}:{インデント}"` を返す（`__repr__` の docstring のとおり）
- 完了条件: `python3 -m pytest tests/rules/test_indentation.py` が全件通過すること

## 3. E2E テストの実装（DS-TS 13 件）

- 設計: `change_detail_design.md` 8-2 と `docs/detail_design.md` 8-2（`DS-TS-*` 13 件）。公開関数（`yamllint.cli.run`、`yamllint.linter.run`、`yamllint.config.YamlLintConfig`、`yamllint.parser` の関数）を呼ぶ pytest のテストを `e2e/` に書く
- 1 つの `DS-TS-*` につき 1 つ以上のテスト関数。テスト関数の名前は `test_` で始め、DS-TS の名前を反映する
- 完了条件: `python3 -m pytest e2e` が全件通過すること（「テストが失敗したら修正と再実行」の対象は実装のみ。テストの期待結果は 8-2 の表に従う）

## 4. 対応表（docs/trace_map.md）更新タスク

- 変更設計書 7-2 の [追加] 2 件を対応表に登録する。`DS-TS-*` 13 件を `e2e/...::テスト関数` の行で登録する（書式は対応表のルール）
- 完了条件: `bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件で通ること

## 5. 実装完了確認の必須固定タスク

1. **対応表（docs/trace_map.md）更新タスク**: 上の 4 と同じ。`bash scripts/isdd/check.sh --strict` がエラー 0 件・警告 0 件
2. **起動確認タスク**（実行形態 library）: 詳細設計書 9 の導入手順（`pip install -e .` で入れる）のあと、`yamllint --version` と `python3 -m yamllint --version` がエラーなく終わること。完了条件: 両方が終了コード 0 で終わること
3. **単体テスト全件通過タスク**: `python3 -m pytest tests`。完了条件: FAIL が 0 件
4. **E2E テスト全件通過タスク**: `python3 -m pytest e2e --junitxml=e2e/results/e2e.xml`。完了条件: FAIL が 0 件。その後 `bash scripts/isdd/check.sh --strict` の受け入れ判定が全要件「実装済み」
5. **README.md 記載タスク**: 既存の README.rst に導入と使い方が書かれている。実装完了チェックが README.md を要求するため、README.md を新しく作るかは isdd-build の完了報告で判断を仰ぐ（作るまでは未達として残す）
   - 完了条件: README.md を読むだけで起動方法が分かること（作成の判断の結果を報告に書く）
6. **実装完了チェックタスク**: `python3 scripts/isdd/implementation_completeness_checker.py .`。完了条件: 全項目が OK（README.md の項目は 5 の判断の結果を報告に書く）

## 6. 変更点の実装確認

- 変更設計書の [追加] 2 件（`DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR`、`DS-FN-RULE-INDENTATION-CHECK`）が実装され、対応表に登録されていること
- 変更要件定義書の既存要件（`RQ-FT-PARSE-TOKENS`、`RQ-FT-LINT-YAML-BUFFER`、`RQ-FT-RULE-INDENTATION`）が受け入れ判定で「実装済み」になること
- 完了条件: 上の確認がすべて満たされ、結果を報告に書いたこと
