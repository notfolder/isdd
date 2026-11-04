# 対応表（docs/trace_map.md）

設計 ID（`DS-*`）とソースコードの対応。書式と粒度は対応表のルールに従う（粒度は `function`）。要件 ID との対応は詳細設計書の第 11 章に書く。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-PACKAGE-INIT` | `yamllint/__init__.py` | パッケージの名前、版、説明の定数を定義する |
| `DS-MD-MAIN` | `yamllint/__main__.py` | python -m yamllint で CLI を起動する |
| `DS-MD-CLI` | `yamllint/cli.py` | CLI。引数の解析、設定の決定、ファイルの列挙、問題の表示、終了コード |
| `DS-CL-CLI-FORMAT` | `yamllint/cli.py::Format` | 問題の表示形式を並べたクラス（静的メソッドの集まり） |
| `DS-IF-CLI-COMMAND` | `yamllint/cli.py::run` | コマンド yamllint の入口（引数の仕様） |
| `DS-IF-PROBLEM-OUTPUT` | `yamllint/cli.py::show_problems` | 問題の出力形式（standard、colored、parsable、github） |
| `DS-FN-CLI-FORMAT-GITHUB` | `yamllint/cli.py::Format.github` | 問題を GitHub Actions のアノテーション形式の 1 行にする |
| `DS-FN-CLI-FORMAT-PARSABLE` | `yamllint/cli.py::Format.parsable` | 問題を「ファイル:行:列: [重大度] 説明」の 1 行の文字列にする |
| `DS-FN-CLI-FORMAT-STANDARD` | `yamllint/cli.py::Format.standard` | 問題を人が読む標準形式の 1 行にする（ファイル名を見出しとして付ける） |
| `DS-FN-CLI-FORMAT-STANDARD-COLOR` | `yamllint/cli.py::Format.standard_color` | 標準形式と同じ内容を、重大度ごとに色を付けて 1 行にする |
| `DS-FN-CLI-FIND-FILES-RECURSIVELY` | `yamllint/cli.py::find_files_recursively` | 指定されたファイルとディレクトリから、YAML として検査し、無視されていないファイルを列挙する |
| `DS-FN-CLI-FIND-PROJECT-CONFIG-FILEPATH` | `yamllint/cli.py::find_project_config_filepath` | カレントディレクトリから親へ、既定名（.yamllint など）の設定ファイルを探す |
| `DS-FN-CLI-RUN` | `yamllint/cli.py::run` | CLI の入口。引数を解析し、設定を決め、ファイルを検査して終了コードで終了する |
| `DS-FN-CLI-SHOW-PROBLEMS` | `yamllint/cli.py::show_problems` | 問題を指定の形式で標準出力に表示し、表示した中で最大の重大度を返す |
| `DS-FN-CLI-SUPPORTS-COLOR` | `yamllint/cli.py::supports_color` | 標準出力が色つきの表示に対応するかを判定する |
| `DS-MD-CONFIG` | `yamllint/config.py` | 設定の読み込み、解析、検証、拡張、無視パターン、組み込み設定の場所 |
| `DS-CL-CONFIG-YAML-LINT-CONFIG` | `yamllint/config.py::YamlLintConfig` | 規則設定（有効な規則、規則ごとの値、無視パターン、対象ファイルのパターン）を保持し、解析・検証する |
| `DS-CL-CONFIG-YAML-LINT-CONFIG-ERROR` | `yamllint/config.py::YamlLintConfigError` | 設定の誤りを表す例外 |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-ENABLED-RULES` | `yamllint/config.py::YamlLintConfig.enabled_rules` | 指定パスに対して有効な規則のモジュールの一覧を返す |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-EXTEND` | `yamllint/config.py::YamlLintConfig.extend` | 拡張元の設定を取り込み、自分の設定に無い規則値を既定として補う |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-IS-FILE-IGNORED` | `yamllint/config.py::YamlLintConfig.is_file_ignored` | 指定パスが無視パターンに一致するかを返す |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-IS-YAML-FILE` | `yamllint/config.py::YamlLintConfig.is_yaml_file` | 指定パスが検査対象の YAML ファイルのパターンに一致するかを返す |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-PARSE` | `yamllint/config.py::YamlLintConfig.parse` | 設定の YAML 文字列を解析し、規則の有効・無効と値を反映する |
| `DS-FN-CONFIG-YAML-LINT-CONFIG-VALIDATE` | `yamllint/config.py::YamlLintConfig.validate` | 取り込んだ設定の全体を検証し、誤りがあれば設定エラーにする |
| `DS-FN-CONFIG-GET-EXTENDED-CONFIG-FILE` | `yamllint/config.py::get_extended_config_file` | 組み込みの設定名（default、relaxed）から設定ファイルのパスを返す |
| `DS-FN-CONFIG-VALIDATE-RULE-CONF` | `yamllint/config.py::validate_rule_conf` | 1 つの規則の設定値を、規則の型定義と規則の VALIDATE に照らして検証する |
| `DS-MD-LINTER` | `yamllint/linter.py` | ライブラリの検査の中心。規則の適用、ディレクティブ、構文エラーの報告 |
| `DS-CL-LINTER-LINT-PROBLEM` | `yamllint/linter.py::LintProblem` | 問題 1 件（行、列、説明、規則名、重大度）を表す |
| `DS-IF-LIBRARY-API` | `yamllint/linter.py::run` | ライブラリの公開入口 linter.run |
| `DS-FN-LINTER-LINT-PROBLEM-MESSAGE` | `yamllint/linter.py::LintProblem.message` | 説明と規則名を合わせた利用者向けの文字列を返す |
| `DS-FN-LINTER-GET-COSMETIC-PROBLEMS` | `yamllint/linter.py::get_cosmetic_problems` | 有効な規則を字句・コメント・行の順に適用して問題を生成し、ディレクティブで抑止された問題を除く |
| `DS-FN-LINTER-GET-SYNTAX-ERROR` | `yamllint/linter.py::get_syntax_error` | YAML の構文エラーを問題 1 件にして返す（構文が正しければ None） |
| `DS-FN-LINTER-RUN` | `yamllint/linter.py::run` | ライブラリの入口。文字列またはストリームを検査し、問題の生成器を返す。無視されるファイルは空 |
| `DS-MD-PARSER` | `yamllint/parser.py` | PyYAML のトークンからコメントと行を含む字句の列を作る |
| `DS-CL-PARSER-COMMENT` | `yamllint/parser.py::Comment` | コメント 1 件（行、列、位置、前後の字句）を表す |
| `DS-CL-PARSER-LINE` | `yamllint/parser.py::Line` | 元テキストの 1 行（行番号、開始位置、終了位置）を表す |
| `DS-CL-PARSER-TOKEN` | `yamllint/parser.py::Token` | 字句 1 つと、その前後の字句（前、次、次の次）を保持する |
| `DS-FN-PARSER-COMMENT-IS-INLINE` | `yamllint/parser.py::Comment.is_inline` | コメントが値と同じ行にある行内コメントかを返す |
| `DS-FN-PARSER-LINE-CONTENT` | `yamllint/parser.py::Line.content` | 行の本文を返す |
| `DS-FN-PARSER-COMMENTS-BETWEEN-TOKENS` | `yamllint/parser.py::comments_between_tokens` | 2 つの字句の間にあるコメントを順に生成する |
| `DS-FN-PARSER-LINE-GENERATOR` | `yamllint/parser.py::line_generator` | バッファを行単位の Line の生成器にする |
| `DS-FN-PARSER-TOKEN-OR-COMMENT-OR-LINE-GENERATOR` | `yamllint/parser.py::token_or_comment_or_line_generator` | 字句・コメント・行を行番号の順に混ぜて生成する |
| `DS-MD-RULES-REGISTRY` | `yamllint/rules/__init__.py` | 規則 ID から規則モジュールを引く登録表 |
| `DS-FN-RULES-REGISTRY-GET` | `yamllint/rules/__init__.py::get` | 規則 ID から規則モジュールを返す。無い ID は ValueError |
| `DS-MD-RULE-ANCHORS` | `yamllint/rules/anchors.py` | 規則の定義 |
| `DS-FN-RULE-ANCHORS-CHECK` | `yamllint/rules/anchors.py::check` | 規則「anchors」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-BRACES` | `yamllint/rules/braces.py` | 規則の定義 |
| `DS-FN-RULE-BRACES-CHECK` | `yamllint/rules/braces.py::check` | 規則「braces」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-BRACKETS` | `yamllint/rules/brackets.py` | 規則の定義 |
| `DS-FN-RULE-BRACKETS-CHECK` | `yamllint/rules/brackets.py::check` | 規則「brackets」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-COLONS` | `yamllint/rules/colons.py` | 規則の定義 |
| `DS-FN-RULE-COLONS-CHECK` | `yamllint/rules/colons.py::check` | 規則「colons」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-COMMAS` | `yamllint/rules/commas.py` | 規則の定義 |
| `DS-FN-RULE-COMMAS-CHECK` | `yamllint/rules/commas.py::check` | 規則「commas」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-COMMENTS` | `yamllint/rules/comments.py` | 規則の定義 |
| `DS-FN-RULE-COMMENTS-CHECK` | `yamllint/rules/comments.py::check` | 規則「comments」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-COMMENTS-INDENTATION` | `yamllint/rules/comments_indentation.py` | 規則の定義 |
| `DS-FN-RULE-COMMENTS-INDENTATION-CHECK` | `yamllint/rules/comments_indentation.py::check` | 規則「comments_indentation」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULES-COMMON` | `yamllint/rules/common.py` | 規則が共通で使う空白・行・字句の補助関数 |
| `DS-FN-RULES-COMMON-GET-LINE-INDENT` | `yamllint/rules/common.py::get_line_indent` | 字句が始まる行の先頭の空白の数を返す |
| `DS-FN-RULES-COMMON-GET-REAL-END-LINE` | `yamllint/rules/common.py::get_real_end_line` | 字句が実際に終わる行の番号を返す（スカラーは次の行まで伸びることがある） |
| `DS-FN-RULES-COMMON-IS-EXPLICIT-KEY` | `yamllint/rules/common.py::is_explicit_key` | 字句が明示キー（? で始まるキー）かを返す |
| `DS-FN-RULES-COMMON-SPACES-AFTER` | `yamllint/rules/common.py::spaces_after` | 字句の直後の空白数を min と max で照合し、違反なら問題を返す |
| `DS-FN-RULES-COMMON-SPACES-BEFORE` | `yamllint/rules/common.py::spaces_before` | 字句の直前の空白数を min と max で照合し、違反なら問題を返す |
| `DS-MD-RULE-DOCUMENT-END` | `yamllint/rules/document_end.py` | 規則の定義 |
| `DS-FN-RULE-DOCUMENT-END-CHECK` | `yamllint/rules/document_end.py::check` | 規則「document_end」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-DOCUMENT-START` | `yamllint/rules/document_start.py` | 規則の定義 |
| `DS-FN-RULE-DOCUMENT-START-CHECK` | `yamllint/rules/document_start.py::check` | 規則「document_start」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-EMPTY-LINES` | `yamllint/rules/empty_lines.py` | 規則の定義 |
| `DS-FN-RULE-EMPTY-LINES-CHECK` | `yamllint/rules/empty_lines.py::check` | 規則「empty_lines」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-EMPTY-VALUES` | `yamllint/rules/empty_values.py` | 規則の定義 |
| `DS-FN-RULE-EMPTY-VALUES-CHECK` | `yamllint/rules/empty_values.py::check` | 規則「empty_values」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-FLOAT-VALUES` | `yamllint/rules/float_values.py` | 規則の定義 |
| `DS-FN-RULE-FLOAT-VALUES-CHECK` | `yamllint/rules/float_values.py::check` | 規則「float_values」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-HYPHENS` | `yamllint/rules/hyphens.py` | 規則の定義 |
| `DS-FN-RULE-HYPHENS-CHECK` | `yamllint/rules/hyphens.py::check` | 規則「hyphens」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-INDENTATION` | `yamllint/rules/indentation.py` | 規則の定義 |
| `DS-CL-RULE-INDENTATION-PARENT` | `yamllint/rules/indentation.py::Parent` | インデントの親（ブロックやフローの構造）の種類と期待するインデントを保持する |
| `DS-FN-RULE-INDENTATION-CHECK-SCALAR-INDENTATION` | `yamllint/rules/indentation.py::check_scalar_indentation` | 複数行のスカラー（引用符や複数行文字列）の継続行の字下げを、期待値と照合する |
| `DS-MD-RULE-KEY-DUPLICATES` | `yamllint/rules/key_duplicates.py` | 規則の定義 |
| `DS-CL-RULE-KEY-DUPLICATES-PARENT` | `yamllint/rules/key_duplicates.py::Parent` | マッピングの親を表し、そのマッピングで現れたキーを保持する |
| `DS-FN-RULE-KEY-DUPLICATES-CHECK` | `yamllint/rules/key_duplicates.py::check` | 規則「key_duplicates」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-KEY-ORDERING` | `yamllint/rules/key_ordering.py` | 規則の定義 |
| `DS-CL-RULE-KEY-ORDERING-PARENT` | `yamllint/rules/key_ordering.py::Parent` | マッピングの親を表し、キー順の検査に必要な状態を保持する |
| `DS-FN-RULE-KEY-ORDERING-CHECK` | `yamllint/rules/key_ordering.py::check` | 規則「key_ordering」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-LINE-LENGTH` | `yamllint/rules/line_length.py` | 規則の定義 |
| `DS-FN-RULE-LINE-LENGTH-CHECK` | `yamllint/rules/line_length.py::check` | 規則「line_length」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-FN-RULE-LINE-LENGTH-CHECK-INLINE-MAPPING` | `yamllint/rules/line_length.py::check_inline_mapping` | 行が空白を含むインラインのマッピングかを判定する（長さの例外判定に使う） |
| `DS-MD-RULE-NEW-LINE-AT-END-OF-FILE` | `yamllint/rules/new_line_at_end_of_file.py` | 規則の定義 |
| `DS-FN-RULE-NEW-LINE-AT-END-OF-FILE-CHECK` | `yamllint/rules/new_line_at_end_of_file.py::check` | 規則「new_line_at_end_of_file」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-NEW-LINES` | `yamllint/rules/new_lines.py` | 規則の定義 |
| `DS-FN-RULE-NEW-LINES-CHECK` | `yamllint/rules/new_lines.py::check` | 規則「new_lines」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-OCTAL-VALUES` | `yamllint/rules/octal_values.py` | 規則の定義 |
| `DS-FN-RULE-OCTAL-VALUES-CHECK` | `yamllint/rules/octal_values.py::check` | 規則「octal_values」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-QUOTED-STRINGS` | `yamllint/rules/quoted_strings.py` | 規則の定義 |
| `DS-FN-RULE-QUOTED-STRINGS-VALIDATE` | `yamllint/rules/quoted_strings.py::VALIDATE` | quoted-strings の設定値の組み合わせを検証し、誤りの説明を返す（問題が無ければ None） |
| `DS-FN-RULE-QUOTED-STRINGS-CHECK` | `yamllint/rules/quoted_strings.py::check` | 規則「quoted_strings」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-TRAILING-SPACES` | `yamllint/rules/trailing_spaces.py` | 規則の定義 |
| `DS-FN-RULE-TRAILING-SPACES-CHECK` | `yamllint/rules/trailing_spaces.py::check` | 規則「trailing_spaces」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-MD-RULE-TRUTHY` | `yamllint/rules/truthy.py` | 規則の定義 |
| `DS-FN-RULE-TRUTHY-CHECK` | `yamllint/rules/truthy.py::check` | 規則「truthy」の検査。規則の定義に従い、字句・行・コメントを検査して違反を問題として返す |
| `DS-FN-RULE-TRUTHY-YAML-SPEC-VERSION-FOR-DOCUMENT` | `yamllint/rules/truthy.py::yaml_spec_version_for_document` | 文書の YAML 仕様版（既定は 1.1）を返す |
| `DS-FN-PARSER-TOKEN-OR-COMMENT-GENERATOR` | `yamllint/parser.py::token_or_comment_generator` | 入力のバッファから字句を前後の字句つきで順に生成し、字句の間のコメントも生成する |
| `DS-FN-RULE-INDENTATION-CHECK` | `yamllint/rules/indentation.py::check` | インデント規則の入口。字句ごとに既存の `_check` を呼び、違反の問題を生成する |
| `DS-TS-LINT-BUFFER-PROBLEMS` | `e2e/test_scenarios.py::test_lint_buffer_problems` | E2E シナリオ |
| `DS-TS-REPORT-SYNTAX-ERRORS` | `e2e/test_scenarios.py::test_report_syntax_errors` | E2E シナリオ |
| `DS-TS-DIRECTIVES-DISABLE-RULES` | `e2e/test_scenarios.py::test_directives_disable_rules` | E2E シナリオ |
| `DS-TS-LOAD-CONFIG` | `e2e/test_scenarios.py::test_load_config` | E2E シナリオ |
| `DS-TS-CLI-RUN-AND-EXIT` | `e2e/test_scenarios.py::test_cli_run_and_exit` | E2E シナリオ |
| `DS-TS-PARSE-TOKENS-AND-COMMENTS` | `e2e/test_scenarios.py::test_parse_tokens_and_comments` | E2E シナリオ |
| `DS-TS-CHECK-INDENTATION` | `e2e/test_scenarios.py::test_check_indentation` | E2E シナリオ |
| `DS-TS-CHECK-LINE-LAYOUT` | `e2e/test_scenarios.py::test_check_line_layout` | E2E シナリオ |
| `DS-TS-CHECK-SPACING` | `e2e/test_scenarios.py::test_check_spacing` | E2E シナリオ |
| `DS-TS-CHECK-DOCUMENT-MARKERS` | `e2e/test_scenarios.py::test_check_document_markers` | E2E シナリオ |
| `DS-TS-CHECK-COMMENTS` | `e2e/test_scenarios.py::test_check_comments` | E2E シナリオ |
| `DS-TS-CHECK-VALUES` | `e2e/test_scenarios.py::test_check_values` | E2E シナリオ |
| `DS-TS-CHECK-KEYS` | `e2e/test_scenarios.py::test_check_keys` | E2E シナリオ |
