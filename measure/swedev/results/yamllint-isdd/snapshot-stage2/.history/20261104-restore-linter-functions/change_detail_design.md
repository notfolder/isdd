# 変更設計書（linter の欠落関数の復元）

正本の詳細設計書は `docs/detail_design.md`。この変更は設計要素を増やさない（[追加] 0 件）。既存の設計 ID（`DS-CL-LINTER-LINT-PROBLEM`、`DS-FN-LINTER-RUN`、`DS-IF-LIBRARY-API`）の実装を既存コードへ戻す。対応表（`docs/trace_map.md`）は変更しない。

## 1. 変更の範囲

`yamllint/linter.py` だけを変える。他のファイル、他の関数の挙動は変えない。

## 2. 設計要素の対応

| 復元する実装 | 実現する設計 ID | 扱い |
|---|---|---|
| `LintProblem.__init__` | `DS-CL-LINTER-LINT-PROBLEM`（クラス） | 対応表の既存行に含まれる（クラスの行） |
| `LintProblem.__eq__` | `DS-CL-LINTER-LINT-PROBLEM`（クラス） | ダンダーメソッドは対応表に行を作らない（既存の `Parent.__repr__` と同じ扱い） |
| `LintProblem.__lt__` | `DS-CL-LINTER-LINT-PROBLEM`（クラス） | 同上 |
| `_run` | `DS-FN-LINTER-RUN` の内部（設計 7-2 の規則により内部関数は DS-FN に載せない） | 対応表に行を作らない |
| `run` | `DS-FN-LINTER-RUN`、`DS-IF-LIBRARY-API` | 対応表の既存行 |

## 3. 復元する実装の振る舞い

### 3-1. LintProblem.__init__（DS-CL-LINTER-LINT-PROBLEM）

引数 `line`、`column`、`desc`（既定 `'<no description>'`）、`rule`（既定 `None`）を、同名の属性に入れる。`level` は `None` で初期化する（規則の検査の中で設定される）。

### 3-2. LintProblem.__eq__

相手が `LintProblem` でなければ `NotImplemented` を返す。同じ場合は、`line`、`column`、`rule` の 3 つが等しいときだけ真。`desc` と `level` は比べない（テストが説明の文言を書かずに比べられるようにするため）。

### 3-3. LintProblem.__lt__

`(line, column)` の組で比べる。`self` が `other` より前（行が小さい、または行が同じで列が小さい）なら真。

### 3-4. _run(buffer, conf, filepath)

1. `buffer` は添字で行を読めること（`assert` で確かめる）。
2. 先頭行（`parser.line_generator` の最初の行の本文）が `^#\s*yamllint disable-file\s*$` に一致すれば（`#` の後の空白の数と末尾の空白は問わない。既存の単体テストの表記に合わせる）、何も生成せず終わる。本文が `bytes` なら先に UTF-8 で復号する。
3. `get_syntax_error(buffer)` が問題を返せば、それ 1 件だけを生成して終わる（構文エラーを優先し、規則の問題を出さない）。
4. そうでなければ `get_cosmetic_problems(buffer, conf, filepath)` の問題を順に生成する。

### 3-5. run(input, conf, filepath=None)（DS-FN-LINTER-RUN、DS-IF-LIBRARY-API）

1. `filepath` が与えられ、`conf.is_file_ignored(filepath)` が真なら、空の生成器を返す（入力は読まない）。
2. 入力が `str` または `bytes` ならそのまま本文にする（`bytes` の復号は 3-4 で行う）。入力が `io.IOBase`（テキストストリーム）なら `read()` した文字列を本文にする。それ以外は `TypeError` を即座に送出する（生成器を作る前に判定する）。

> 正本との差: 正本の `DS-IF-LIBRARY-API` は「文字列かストリーム以外は型エラー」だが、既存の単体テスト（`tests/test_linter.py::test_run_on_bytes`、`test_run_on_non_ascii_chars`）は `bytes` を受け付けることを求める。このため `bytes` を受け付ける。正本への反映は実装後レビューで行う。
3. 本文と `conf`、`filepath` を `_run` に渡し、その生成器を返す。

## 4. 検証

- 単体テスト: `python -m pytest tests` が全件通る（復元前は 375 件が失敗している）。
- E2E: `python -m pytest e2e --junitxml=e2e/results/e2e.xml` が全件通る。
- 対応表: `bash scripts/isdd/check.sh --strict` でエラーが無いこと。

## 5. 依存の規則

無い。`scripts/isdd/dependencies.json` の規則は変えない。

## 6. 要件と設計の対応表

| DS-ID | 対応する要件 ID |
|---|---|
| `DS-CL-LINTER-LINT-PROBLEM` | `RQ-DT-LINT-PROBLEM`, `RQ-FT-LINT-YAML-BUFFER` |
| `DS-FN-LINTER-RUN` | `RQ-FT-LINT-YAML-BUFFER`, `RQ-FT-REPORT-SYNTAX-ERROR`, `RQ-FT-DIRECTIVE-DISABLE`, `RQ-UI-LIBRARY-API`, `RQ-TS-LINT-BUFFER-PROBLEMS` |
| `DS-IF-LIBRARY-API` | `RQ-UI-LIBRARY-API` |
