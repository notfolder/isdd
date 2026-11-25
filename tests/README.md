# 単体テストと、文書の規則との対応

チェッカーは `shared/references/` の文書の規則を読む側なので、テストは**文書の規則から**書く。
規則を足したり変えたりしたら、この表に行を足し、対応するテストを書く（2026-11-03、変更設計書の「対応だけの差し替え」を
チェッカーが削除扱いにした見逃しを受けて決めた）。

実行: `python3 -m unittest discover -s tests -t tests -q`（複数の Python の版で回すなら `bash tools/test_pythons.sh`）。

## 変更フローの書き方（design-chapters.md「変更フローで足すこと」、id-definitions.md「変更管理ルール」）

| 規則 | チェッカー | テスト |
|---|---|---|
| すべての設計要素に [追加] か [削除] を書く。中身が変わる要素は旧要素を [削除]、新要素を [追加] | trace_map_checker | `test_active_change_adds_design_ids`、`test_active_change_deleted_id_left_in_map_is_warning` |
| 要件との対応だけを差し替える要素は、第 11 章で同じ ID を [削除]（旧い対応）と [追加]（新しい対応）の 2 行に書く。要素は残る | trace_map_checker | `test_mapping_only_change_is_not_a_deletion` |
| ファイルを消してクラスを別のファイルへ移すと、第 7 章の旧い行が [削除]、新しい行が [追加]。クラスは残る | trace_map_checker | `test_id_on_unchanged_row_is_not_a_deletion_and_mixed_row_warns`（同じ判定） |
| 変更しない既存の設計 ID でも変更要件を受けるものは「変更なし（既存）」の行で書く | trace_map_checker | `test_id_on_unchanged_row_is_not_a_deletion_and_mixed_row_warns` |
| 旧要素を [削除]、新要素を [追加] に**分けて**書く（同じ行に両方書かない） | trace_map_checker、rq_ds_link_checker | `test_id_on_unchanged_row_is_not_a_deletion_and_mixed_row_warns`（警告）、`test_mixed_tag_line_is_read_as_active` |
| 変更設計書の [削除] 行は読まない。正本には区分を書かない（正本の「[削除]」の文字は内容） | rq_ds_link_checker、trace_map_checker | `test_deleted_lines_are_ignored_in_change_documents`、`test_canonical_line_with_literal_deleted_word_is_kept` |
| 変更設計書が既存の要件を参照しても、`--base` の正本にあれば未定義参照にしない | rq_ds_link_checker | `test_base_requirements_resolve_existing_references` |
| `docs/active_change` が無ければ正本だけで判定する。指す先に変更設計書が無ければエラー | trace_map_checker | `test_absent_pointer_checks_canonical_only`、`test_active_change_pointer_to_missing_design_is_error` |
| 不具合修正で設計を変えない場合は、変更のディレクトリに `bug_report.md` だけがある。変更設計書が無くてもエラーにせず、正本だけで判定する（spec-bugfix.md） | trace_map_checker、acceptance_checker | `test_bug_report_without_change_design_checks_canonical_only`、`test_bug_report_only_change_uses_canonical` |
| 要件の意味が変わる場合は旧 ID を `deprecated`（[削除]）にし、新 ID を [追加] する | rq_integrity_checker | `test_change_document_skips_bz_check`（区分の検出） |

## 要件定義書の章立て（requirements-chapters.md、hearing-rules.md「依頼文に無い決め事」）

| 規則 | チェッカー | テスト |
|---|---|---|
| 「1-2. 依頼に無く自分で決めた項目」の節を必ず置く（無ければ「無し」）。変更要件定義書も同じ | rq_integrity_checker | `test_missing_decided_items_section_fails`、`test_valid_document_passes` |

## 対応表の書式と粒度（trace-map-rules.md）

| 規則 | チェッカー | テスト |
|---|---|---|
| 列は DS-ID・修飾名・備考。`DS-MD` の行はファイルパスだけ、それ以外は `::名前` | trace_map_checker | `test_complete_map_passes_strict`、`test_ds_md_must_point_to_file` |
| 対応表の修飾名がコードに無ければエラー。設計書に無い DS-ID はエラー | trace_map_checker | `test_renamed_function_is_error`、`test_unknown_ds_id_is_error` |
| コードの公開要素が対応表に無ければ警告。内部関数とテストファイルは対象外 | trace_map_checker | `test_unregistered_public_function_is_warning`、`test_private_and_test_files_are_ignored` |
| 粒度 `class` では、クラスかファイルが登録済みなら公開関数を未登録と扱わない。設計書の `DS-FN` は粒度にかかわらず要る | trace_map_checker | `test_class_granularity_accepts_unmapped_methods` |
| 第 7 章の「実現する設計 ID」（`DS-MD` と同じ行の ID）は対応表に要る | trace_map_checker | `test_code_realized_id_on_ds_md_row_must_be_mapped` |
| E2E シナリオ（`DS-TS`）はテスト関数に結ぶ。テストファイルを指せるのは `DS-TS` の行だけ。テストディレクトリがあるのに 8-2 の `DS-TS` が無ければ警告 | trace_map_checker | `test_ds_ts_row_points_to_test_function`、`test_non_ts_row_must_not_point_to_test_file` |
| 言語ごとの確認の深さ（TS のアロー関数、記号を取れない言語はファイルの存在だけ） | trace_map_checker | `test_typescript_arrow_function_is_symbol`、`test_file_only_language_is_not_checked_for_symbols` |
| 走査の範囲は `--src`（ディレクトリかファイル）と `--exclude`（相対パスのグロブ）で決める。範囲の外は未登録にならない | trace_map_checker、dependency_checker | `test_source_file_as_scope_limits_scan`、`test_exclude_glob_skips_files`、`test_source_file_as_scope_checks_only_that_file` |

## 依存の規則（trace-map-rules.md「依存の規則」、design-chapters.md 第 7 章）

| 規則 | チェッカー | テスト |
|---|---|---|
| 規則が空、または規則ファイルが無ければ合格 | dependency_checker | `test_empty_rules_pass`、`test_missing_rules_file_passes` |
| `deny` は外部モジュール名（先頭一致）とプロジェクト内のパス。相対 import と絶対 import を解決する | dependency_checker | `test_python_deny_external_module`、`test_python_deny_project_dir_resolves_relative_and_absolute_imports` |
| `allow` は `from` 自身と allow 以外のプロジェクト内への依存を違反にし、外部モジュールは制限しない | dependency_checker | `test_python_allow_limits_project_imports_only` |
| TypeScript の相対 import、Go のモジュールパス、読めない言語は確認対象外 | dependency_checker | `test_typescript_relative_import_is_resolved`、`test_go_module_import_is_resolved`、`test_unknown_language_is_not_checked` |
| `isdd-setup` は `dependencies.json` の雛形を無いときだけ作り、`check.sh` が対応表チェックと依存チェックの両方を実行する | isdd_setup | `test_dependency_rules_template_created_and_kept`、`test_check_sh_runs_both_checkers_with_tests_and_granularity`、`test_check_sh_fails_on_dependency_violation` |

## 要件と設計の対応（design-chapters.md 第 11 章、requirement-exclusion.md）

| 規則 | チェッカー | テスト |
|---|---|---|
| 対応は第 11 章「要件と設計の対応表」の表だけで持つ。ほかの章の設計 ID が表に無ければ問題。表の章が無ければ問題 | rq_ds_link_checker | `test_short_ids_mapped_only_in_mapping_chapter_pass`、`test_design_id_missing_from_mapping_chapter_fails`、`test_mapping_outside_mapping_chapter_is_ignored`、`test_missing_mapping_chapter_fails` |
| `RQ-BK`・`RQ-BZ`・`RQ-EF` は設計の対応を求めない | rq_ds_link_checker | `test_context_ids_need_no_design` |
| 対応の無い要件 ID・設計 ID、要件定義書に無い要件 ID への参照は問題 | rq_ds_link_checker | `test_unmapped_requirement_fails`、`test_unmapped_design_fails`、`test_undefined_reference_fails` |
| 「11-1. 除外要件」の要件 ID には対応を求めない。節は次の見出しで終わる | rq_ds_link_checker | `test_excluded_requirement_is_not_unmapped`、`test_exclusion_section_ends_at_next_heading` |

## 要件 ID（id-definitions.md、requirements-chapters.md）

| 規則 | チェッカー | テスト |
|---|---|---|
| `RQ-BK`・`RQ-BZ` 以外の要件には同じ行に `RQ-BK` を書く。対応する要件の無い `RQ-BK` は問題 | rq_integrity_checker | `tests/test_rq_integrity_checker.py` の各テスト |
| カテゴリの書式。変更要件定義書では `RQ-BZ` の存在確認を省く | rq_integrity_checker | 同上 |
| `RQ-FT`・`RQ-UI`・`RQ-EX` は第 7 章のいずれかのシナリオ（`RQ-TS`）の「検証する要件ID」に現れる。`RQ-NF`・`RQ-DT`・`RQ-OP` には求めない | rq_integrity_checker | `test_feature_without_scenario_fails`、`test_missing_verify_column_is_reported`、`test_non_feature_categories_do_not_need_scenario` |
| 「検証する要件ID」列の ID は `RQ-BK` との対応に数えない。正本でこの列にだけ現れる ID は未定義の参照 | rq_integrity_checker | `test_verify_column_does_not_count_as_bk_mapping` |
| 変更要件定義書では [追加] の `RQ-FT`・`RQ-UI`・`RQ-EX` にだけ `RQ-TS` を求める。列だけの差し替えは同じ `RQ-TS` を [削除]・[追加] の 2 行で書く。[削除] の行は数えない | rq_integrity_checker | `test_change_document_requires_scenario_for_added_features_only`、`test_change_document_does_not_require_bz` |
| 不具合の記録（見出し「不具合の記録」）は既存の要件 ID を引用するだけの文書。`RQ-BZ`・1-2 の節・受け入れテストの網羅を求めず、`RQ-BK` との対応は求める。`--base` があれば、引用した ID が正本に無いとエラー。[追加] の行があればエラー（spec-bugfix.md） | rq_integrity_checker | `test_bug_report_citing_existing_requirement_passes`、`test_bug_report_without_base_still_passes`、`test_bug_report_citing_unknown_requirement_fails`、`test_bug_report_with_added_row_fails`、`test_bug_report_without_bk_fails` |

## 受け入れ判定（trace-map-rules.md「受け入れ判定」、design-chapters.md 8-4、requirement-exclusion.md）

| 規則 | チェッカー | テスト |
|---|---|---|
| `DS-TS` ごとに合格・不合格・未実行を判定し、要件（`RQ-TS` 経由、`RQ-NF`・`RQ-DT`・`RQ-OP` は第 11 章から直接も）ごとに実装済み・不合格・未検証を Markdown の表で出す | acceptance_checker | `test_all_pass_is_implemented`、`test_failure_marks_requirement_and_strict_fails`、`test_missing_results_are_unverified` |
| テストファイルだけを指す行は、そのファイルの testcase が全部通れば合格 | acceptance_checker | `test_file_level_row_aggregates_file_testcases` |
| XML がコードより古ければ要再実行。既定は警告だけ、`--strict` で失敗 | acceptance_checker | `test_stale_results_require_rerun`、`test_failure_marks_requirement_and_strict_fails` |
| 除外要件（11-1）も判定の対象に残す（設計をまとめても検証は残る）。除外した要件を確かめるシナリオが無ければ未検証、11-1 に `RQ-TS` があれば警告。go test は名前だけ、JUnit（Java）はクラス名.メソッド名で結ぶ | acceptance_checker | `test_exclusion_keeps_verification_and_other_frameworks`、`test_excluded_requirement_without_scenario_is_unverified` |
| `DS-TS` は対応表の行ごとに判定してからまとめる。結果の無い行が 1 行でもあれば未実行、skipped が混ざる行は未実行 | acceptance_checker | `test_ds_ts_with_two_rows_needs_both_results`、`test_pass_and_skip_mixed_is_not_run` |
| 鮮度は testcase を出した XML ごとに見る（古い合格に無関係な新しい XML を足しても要再実行）。同じ testcase が複数の XML にあれば新しいほうを使う | acceptance_checker | `test_old_results_stay_stale_when_unrelated_new_xml_is_added`、`test_newer_result_of_same_testcase_wins` |
| `RQ-NF`・`RQ-DT`・`RQ-OP` も要件ごとの表に出す。テストの経路があれば E2E の結果、設計書 8-5 にあれば「確認済み（手動）」「未確認（手動）」、どちらも無ければ「検証方法なし」。未確認と検証方法なしは `--strict` でも失敗にしない（design-chapters.md 8-5） | acceptance_checker | `test_data_and_operation_requirements_are_listed` |
| `docs/active_change` があれば変更要件定義書・変更設計書の [追加] の行を重ね、[削除] の行にだけ現れる要件・RQ-TS・DS-TS は判定の対象から外す（[削除] と [追加] の両方に現れる ID は差し替えなので残す） | acceptance_checker | `test_active_change_overlay`、`test_active_change_deletion_drops_requirements` |
| pytest が無い Python では `unittest_junit.py` が JUnit XML を出す。テストディレクトリが無ければ判定を省く | unittest_junit、acceptance_checker | `test_unittest_junit_runner_output_is_readable`、`test_missing_test_dir_skips_judgement` |
| `check.sh` は受け入れ判定を `--junit "<E2E>/results/*.xml"` で呼び、`.gitignore` に `<E2E>/results/` を 1 回だけ足す。既定では止めず `--strict` で失敗 | isdd_setup | `test_check_sh_runs_acceptance_checker_and_ignores_results`、`test_check_sh_acceptance_is_warning_unless_strict` |

## 実装完了チェックと複製（design-tasks-rules.md、CLAUDE.md）

| 規則 | 対象 | テスト |
|---|---|---|
| docker compose・初期ユーザー・E2E の要否は `completeness.json` の実行形態・認証・外部連携で切り替える | implementation_completeness_checker | `tests/test_implementation_completeness_checker.py` |
| `skills/` の複製は `shared/` と一致させる。`metadata.version` は全スキルで揃える。リポジトリ直下の `LICENSE` を各スキルの直下へ複製する | tools/build_skills.py | `tests/test_build_skills.py` |

## 分かっている限界（テストで守っていないこと）

- 変更要件定義書だけでは、要件をすべて消した業務課題を「対応する要件が無い `RQ-BK`」として報告できない（変更文書は変えない要件を書かないため）。正本へ反映した後に `rq_integrity_checker.py docs/requirements.md` を実行して拾う（build-review.md の手順 10）。
