"""acceptance_checker.py の単体テスト（trace-map-rules.md「受け入れ判定」、design-chapters.md 8-4 の規則から書く）"""

import os
import time
import unittest

from helpers import TempDirMixin, run_script, write

REQ = """
## 3. 機能要件

| RQ-ID | 機能名 | 対応業務課題ID |
|---|---|---|
| `RQ-FT-CREATE-ORDER` | 注文 | `RQ-BK-X` |
| `RQ-FT-CANCEL-ORDER` | 取消 | `RQ-BK-X` |
| `RQ-UI-ORDER-SCREEN` | 画面 | `RQ-BK-X` |
| `RQ-NF-RESPONSE-1S` | 応答 | `RQ-BK-X` |

## 7. テスト用利用シナリオ

| RQ-ID | テスト目的 | 前提条件 | テスト手順 | 期待される結果 | 検証する要件ID | 対応業務課題ID（RQ-BK-*） |
|---|---|---|---|---|---|---|
| `RQ-TS-VERIFY-ORDER` | 注文 | 無し | 注文する | 登録される | `RQ-FT-CREATE-ORDER`, `RQ-UI-ORDER-SCREEN` | `RQ-BK-X` |
| `RQ-TS-VERIFY-CANCEL` | 取消 | 注文あり | 取り消す | 消える | `RQ-FT-CANCEL-ORDER` | `RQ-BK-X` |
"""

DESIGN = """
### 8-2. E2E テストのシナリオ

| DS-ID | 目的 |
|---|---|
| `DS-TS-ORDER-E2E` | 注文 |
| `DS-TS-CANCEL-E2E` | 取消 |
| `DS-TS-RESPONSE-TIME` | 応答時間 |

## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| `DS-TS-ORDER-E2E` | `RQ-TS-VERIFY-ORDER` |
| `DS-TS-CANCEL-E2E` | `RQ-TS-VERIFY-CANCEL` |
| `DS-TS-RESPONSE-TIME` | `RQ-NF-RESPONSE-1S` |

### 11-1. 除外要件

| RQ-ID | 除外理由 | 吸収先 DS-ID | 承認日 |
|---|---|---|---|
"""

MAP = """
| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-TS-ORDER-E2E` | `e2e/test_order.py::test_create_order` | |
| `DS-TS-CANCEL-E2E` | `e2e/test_order.py::TestCancel.test_cancel_order` | |
| `DS-TS-RESPONSE-TIME` | `e2e/test_perf.py` | ファイル単位 |
"""


ALL_PASS = [("e2e.test_order", "test_create_order", "pass"),
            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
            ("e2e.test_perf", "test_response", "pass")]


def junit(cases, timestamp="2030-01-01T00:00:00"):
    """pytest 形式の JUnit XML。cases は (classname, name, status) の並び"""
    body = ""
    for classname, name, status in cases:
        inner = ""
        if status == "fail":
            inner = '<failure message="x">boom</failure>'
        elif status == "skip":
            inner = '<skipped message="s"/>'
        body += f'<testcase classname="{classname}" name="{name}" time="0.1">{inner}</testcase>'
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest" timestamp="{timestamp}" tests="{len(cases)}">{body}</testsuite></testsuites>'


class AcceptanceCheckerTest(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        write(self.tmp, "docs/requirements.md", REQ)
        write(self.tmp, "docs/detail_design.md", DESIGN)
        write(self.tmp, "docs/trace_map.md", MAP)
        write(self.tmp, "e2e/test_order.py", "def test_create_order():\n    pass\n")
        write(self.tmp, "e2e/test_perf.py", "def test_response():\n    pass\n")

    def run_checker(self, *extra):
        return run_script("acceptance_checker.py",
                          ["docs/requirements.md", "docs/detail_design.md", "docs/trace_map.md",
                           "--junit", "e2e/results/*.xml", "--tests", "e2e", *extra], cwd=self.tmp)

    def write_results(self, cases):
        write(self.tmp, "e2e/results/e2e.xml", junit(cases))

    # 全部通れば DS-TS は合格、要件は実装済み。RQ-NF → DS-TS の直接の経路も表に出る
    def test_all_pass_is_implemented(self):
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                            ("e2e.test_perf", "test_response[fast]", "pass")])
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("### 要件ごとの実装済み判定", out)
        for rq in ("RQ-FT-CREATE-ORDER", "RQ-FT-CANCEL-ORDER", "RQ-UI-ORDER-SCREEN", "RQ-NF-RESPONSE-1S"):
            self.assertRegex(out, rf"\| `{rq}` \|.*\| 実装済み \|")
        self.assertIn("合格 3 / 不合格 0 / 未実行 0", out)

    # 失敗した testcase に結ぶ DS-TS は不合格、その要件は不合格。既定では終了コード 0、--strict で 1
    def test_failure_marks_requirement_and_strict_fails(self):
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "fail"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"\| `RQ-FT-CANCEL-ORDER` \|.*\| 不合格 \|")
        self.assertRegex(out, r"\| `RQ-FT-CREATE-ORDER` \|.*\| 実装済み \|")
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 1, out)

    # 結べる testcase が無い DS-TS は未実行、要件は未検証。XML が無ければ全部未実行
    def test_missing_results_are_unverified(self):
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)
        self.assertIn("JUnit XML が 1 つも無い", out)
        self.assertIn("未実行 3", out)
        self.assertRegex(out, r"\| `RQ-FT-CREATE-ORDER` \|.*\| 未検証 \|")
        self.write_results([("e2e.test_order", "test_create_order", "pass")])
        code, out = self.run_checker()
        self.assertIn("DS-TS-CANCEL-E2E: 未実行", out)
        self.assertIn("DS-TS-ORDER-E2E: 合格", out)

    # ファイルだけを指す行は、そのファイルの testcase が全部通れば合格、1 件でも落ちれば不合格
    def test_file_level_row_aggregates_file_testcases(self):
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                            ("e2e.test_perf", "test_response", "pass"),
                            ("e2e.test_perf", "test_response_slow", "fail")])
        code, out = self.run_checker()
        self.assertIn("DS-TS-RESPONSE-TIME: 不合格", out)
        self.assertRegex(out, r"\| `RQ-NF-RESPONSE-1S` \|.*\| 不合格 \|")

    # 結果ファイルがコードより古ければ要再実行（--strict で失敗）
    def test_stale_results_require_rerun(self):
        write(self.tmp, "e2e/results/e2e.xml", junit([("e2e.test_order", "test_create_order", "pass"),
                                                      ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                                                      ("e2e.test_perf", "test_response", "pass")],
                                                     timestamp="2000-01-01T00:00:00"))
        code, out = self.run_checker("--src", "e2e", "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("要再実行", out)

    # 除外要件（11-1）も判定の対象に残る（設計をまとめても検証は残る）。go test（classname がパッケージ）は名前だけで結ぶ。Java はクラス名.メソッド名で結ぶ
    def test_exclusion_keeps_verification_and_other_frameworks(self):
        write(self.tmp, "docs/detail_design.md", DESIGN + "| `RQ-UI-ORDER-SCREEN` | 画面は注文の設計で実現済み | `DS-TS-ORDER-E2E` | 2026-01-01 |\n")
        write(self.tmp, "docs/trace_map.md", """
        | DS-ID | 修飾名 | 備考 |
        |---|---|---|
        | `DS-TS-ORDER-E2E` | `e2e/order_test.go::TestCreateOrder` | |
        | `DS-TS-CANCEL-E2E` | `e2e/OrderTest.java::OrderTest.testCancel` | |
        | `DS-TS-RESPONSE-TIME` | `e2e/test_perf.py` | |
        """)
        self.write_results([("example.com/app/e2e", "TestCreateOrder/sub1", "pass"),
                            ("com.example.OrderTest", "testCancel", "pass"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"\| `RQ-UI-ORDER-SCREEN` \|.*\| 実装済み \|")

    # requirement-exclusion.md 5: 除外した要件を確かめるシナリオが無くなっていれば、その要件は未検証（--strict で失敗）。
    # 11-1 に RQ-TS を書いてシナリオごと除外した文書には警告を出す
    def test_excluded_requirement_without_scenario_is_unverified(self):
        write(self.tmp, "docs/requirements.md", REQ.replace("`RQ-FT-CREATE-ORDER`, `RQ-UI-ORDER-SCREEN`", "`RQ-FT-CREATE-ORDER`"))
        write(self.tmp, "docs/detail_design.md", DESIGN + "| `RQ-UI-ORDER-SCREEN` | 画面は注文の設計で実現済み | `DS-TS-ORDER-E2E` | 2026-01-01 |\n"
              "| `RQ-TS-VERIFY-SCREEN` | 画面だけを確かめるシナリオ | `DS-TS-ORDER-E2E` | 2026-01-01 |\n")
        self.write_results(ALL_PASS)
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 1, out)
        self.assertRegex(out, r"\| `RQ-UI-ORDER-SCREEN` \|.*\| 未検証 \|")
        self.assertIn("シナリオは除外できない", out)

    # trace-map-rules.md「受け入れ判定」: 1 つの DS-TS に 2 行あり、片方の結果しか無ければ未実行（1 行の合格でほかの行を隠さない）
    def test_ds_ts_with_two_rows_needs_both_results(self):
        write(self.tmp, "docs/trace_map.md", MAP + "| `DS-TS-ORDER-E2E` | `e2e/test_order.py::test_create_order_twice` | |\n")
        self.write_results(ALL_PASS)
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("DS-TS-ORDER-E2E: 未実行", out)
        self.assertRegex(out, r"\| `RQ-FT-CREATE-ORDER` \|.*\| 未検証 \|")

    # 同: 結んだ testcase に skipped が混ざる行は未実行（skip を合格に含めない）
    def test_pass_and_skip_mixed_is_not_run(self):
        self.write_results([("e2e.test_order", "test_create_order[a]", "pass"),
                            ("e2e.test_order", "test_create_order[b]", "skip"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("DS-TS-ORDER-E2E: 未実行", out)
        self.assertIn("skipped の testcase がある行", out)
        self.assertIn("DS-TS-CANCEL-E2E: 合格", out)

    # 同: 鮮度は testcase を出した XML ごとに見る。古い合格の XML に、無関係な新しい XML を足しても要再実行のまま
    def test_old_results_stay_stale_when_unrelated_new_xml_is_added(self):
        write(self.tmp, "e2e/results/e2e.xml", junit(ALL_PASS, timestamp="2000-01-01T00:00:00"))
        write(self.tmp, "e2e/results/other.xml", junit([("e2e.test_other", "test_unrelated", "pass")], timestamp="2099-01-01T00:00:00"))
        code, out = self.run_checker("--src", "e2e", "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("DS-TS-ORDER-E2E: 要再実行", out)

    # 同: 同じ testcase が複数の XML にあれば新しいほうを使う（回し直した結果で、古い不合格を上書きする）
    def test_newer_result_of_same_testcase_wins(self):
        failed = [(c, n, "fail") for c, n, _ in ALL_PASS]
        write(self.tmp, "e2e/results/old.xml", junit(failed, timestamp="2029-01-01T00:00:00"))
        write(self.tmp, "e2e/results/new.xml", junit(ALL_PASS, timestamp="2030-01-01T00:00:00"))
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("合格 3 / 不合格 0", out)

    # design-chapters.md 8-5: RQ-DT・RQ-OP・RQ-NF も表に出す。テストの経路があれば E2E の結果、8-5 にあれば手動の確認、
    # どちらも無ければ「検証方法なし」。未確認と検証方法なしは --strict でも失敗にしない（既存の文書を止めない）
    def test_data_and_operation_requirements_are_listed(self):
        write(self.tmp, "docs/requirements.md", REQ.rstrip() + "\n" + "\n".join([
            "| `RQ-TS-VERIFY-RETENTION` | 保持 | 無し | 1 年後に確かめる | 消えている | `RQ-DT-ORDER-RETENTION` | `RQ-BK-X` |",
            "", "## 4. データ", "",
            "| RQ-ID | 内容 | 対応業務課題ID |", "|---|---|---|",
            "| `RQ-DT-ORDER-RETENTION` | 保持期間 | `RQ-BK-X` |",
            "| `RQ-DT-ORDER-ENTITY` | 注文 | `RQ-BK-X` |",
            "", "## 6. 運用要件", "",
            "| RQ-ID | 内容 | 対応業務課題ID |", "|---|---|---|",
            "| `RQ-OP-BACKUP-DAILY` | バックアップ | `RQ-BK-X` |",
            "| `RQ-OP-RESTORE-DRILL` | 復旧 | `RQ-BK-X` |", ""]))
        write(self.tmp, "docs/detail_design.md", DESIGN.replace("## 11. 要件と設計の対応表", """### 8-5. テスト以外で確かめる要件

        | RQ-ID | 確認方法 | 確認結果 | 確認日 |
        |---|---|---|---|
        | `RQ-OP-BACKUP-DAILY` | cron の設定を読む | 確認済み | 2026-01-10 |
        | `RQ-OP-RESTORE-DRILL` | 復旧の演習 | 未確認 | ― |

        ## 11. 要件と設計の対応表""").replace("| `DS-TS-RESPONSE-TIME` | `RQ-NF-RESPONSE-1S` |",
                                         "| `DS-TS-RESPONSE-TIME` | `RQ-NF-RESPONSE-1S` |\n| `DS-TS-CANCEL-E2E` | `RQ-TS-VERIFY-RETENTION` |"))
        self.write_results(ALL_PASS)
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"\| `RQ-DT-ORDER-RETENTION` \|.*\| 実装済み \|")
        self.assertRegex(out, r"\| `RQ-DT-ORDER-ENTITY` \|.*\| 検証方法なし \|")
        self.assertRegex(out, r"\| `RQ-OP-BACKUP-DAILY` \|.*手動: cron の設定を読む.*\| 確認済み（手動） \|")
        self.assertRegex(out, r"\| `RQ-OP-RESTORE-DRILL` \|.*\| 未確認（手動） \|")
        self.assertIn("確認済み（手動） 1 / 未確認（手動） 1 / 検証方法なし 1", out)
        self.assertIn("実装済み 5 / 不合格 0 / 未検証 0（全 8）", out)

    # 進行中の変更: 変更要件定義書・変更設計書の [追加] の行を重ね、[削除] の行は読まない
    def test_active_change_overlay(self):
        write(self.tmp, "docs/active_change", ".history/20260101-add-refund\n")
        write(self.tmp, ".history/20260101-add-refund/change_requirements.md", """
        | RQ-ID | 区分 | 内容 | 対応業務課題ID |
        |---|---|---|---|
        | `RQ-FT-REFUND-ORDER` | [追加] | 返金 | `RQ-BK-X` |

        ## 7. テスト用利用シナリオ

        | RQ-ID | 区分 | テスト目的 | 検証する要件ID | 対応業務課題ID |
        |---|---|---|---|---|
        | `RQ-TS-VERIFY-REFUND` | [追加] | 返金 | `RQ-FT-REFUND-ORDER` | `RQ-BK-X` |
        """)
        write(self.tmp, ".history/20260101-add-refund/change_detail_design.md", """
        ### 8-2. E2E テストのシナリオ

        | 区分 | DS-ID | 目的 |
        |---|---|---|
        | [追加] | `DS-TS-REFUND-E2E` | 返金 |
        | [削除] | `DS-TS-RESPONSE-TIME` | 応答時間 |

        ## 11. 要件と設計の対応表

        | 区分 | DS-ID | 対応要件ID |
        |---|---|---|
        | [追加] | `DS-TS-REFUND-E2E` | `RQ-TS-VERIFY-REFUND` |
        """)
        write(self.tmp, "docs/trace_map.md", MAP + "| `DS-TS-REFUND-E2E` | `e2e/test_order.py::test_refund_order` | |\n")
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                            ("e2e.test_order", "test_refund_order", "pass"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker("--active-change", "docs/active_change", "--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("進行中の変更", out)
        self.assertRegex(out, r"\| `RQ-FT-REFUND-ORDER` \|.*\| 実装済み \|")

    # 不具合修正で文書を変えない場合は bug_report.md だけがある。正本だけで判定する（spec-bugfix.md）
    def test_bug_report_only_change_uses_canonical(self):
        write(self.tmp, "docs/active_change", ".history/20260601-fix-total\n")
        write(self.tmp, ".history/20260601-fix-total/bug_report.md", "# 不具合の記録\n")
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_order.TestCancel", "test_cancel_order", "pass"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker("--active-change", "docs/active_change", "--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("不具合修正", out)

    # 進行中の変更で [削除] にした要件・RQ-TS・DS-TS は判定の対象から外す（消す要件にテストを求めない）
    def test_active_change_deletion_drops_requirements(self):
        write(self.tmp, "docs/active_change", ".history/20260101-drop-cancel\n")
        write(self.tmp, ".history/20260101-drop-cancel/change_requirements.md", """
        | RQ-ID | 区分 | 内容 | 対応業務課題ID |
        |---|---|---|---|
        | `RQ-FT-CANCEL-ORDER` | [削除] | 取消 | `RQ-BK-X` |

        ## 7. テスト用利用シナリオ

        | RQ-ID | 区分 | テスト目的 | 検証する要件ID | 対応業務課題ID |
        |---|---|---|---|---|
        | `RQ-TS-VERIFY-CANCEL` | [削除] | 取消 | `RQ-FT-CANCEL-ORDER` | `RQ-BK-X` |
        """)
        write(self.tmp, ".history/20260101-drop-cancel/change_detail_design.md", """
        ### 8-2. E2E テストのシナリオ

        | 区分 | DS-ID | 目的 |
        |---|---|---|
        | [削除] | `DS-TS-CANCEL-E2E` | 取消 |

        ## 11. 要件と設計の対応表

        | 区分 | DS-ID | 対応要件ID |
        |---|---|---|
        | [削除] | `DS-TS-CANCEL-E2E` | `RQ-TS-VERIFY-CANCEL` |
        | [削除] | `DS-TS-ORDER-E2E` | `RQ-TS-VERIFY-ORDER` |
        | [追加] | `DS-TS-ORDER-E2E` | `RQ-TS-VERIFY-ORDER`, `RQ-NF-RESPONSE-1S` |
        """)
        write(self.tmp, "docs/trace_map.md", """
        | DS-ID | 修飾名 | 備考 |
        |---|---|---|
        | `DS-TS-ORDER-E2E` | `e2e/test_order.py::test_create_order` | |
        | `DS-TS-RESPONSE-TIME` | `e2e/test_perf.py` | ファイル単位 |
        """)
        self.write_results([("e2e.test_order", "test_create_order", "pass"),
                            ("e2e.test_perf", "test_response", "pass")])
        code, out = self.run_checker("--active-change", "docs/active_change", "--strict")
        self.assertEqual(code, 0, out)
        table = out.split("### 要件ごとの実装済み判定")[1]
        self.assertNotIn("RQ-FT-CANCEL-ORDER", table)
        self.assertNotIn("DS-TS-CANCEL-E2E", out.split("DS-TS ごとの判定")[1])
        # [削除] と [追加] の両方に現れる DS-TS-ORDER-E2E は対応の差し替えなので残る
        self.assertRegex(out, r"\| `RQ-FT-CREATE-ORDER` \|.*\| 実装済み \|")

    # design-chapters.md 8-4: pytest が無い Python では unittest_junit.py が JUnit XML を出し、受け入れ判定が読める
    def test_unittest_junit_runner_output_is_readable(self):
        write(self.tmp, "e2e/test_order.py", """
        import unittest

        class TestCancel(unittest.TestCase):
            def test_cancel_order(self):
                pass

        def load_tests(loader, tests, pattern):
            return tests
        """)
        write(self.tmp, "e2e/test_create.py", """
        import unittest

        class TestCreate(unittest.TestCase):
            def test_create_order(self):
                pass
        """)
        write(self.tmp, "e2e/test_perf.py", """
        import unittest

        class TestPerf(unittest.TestCase):
            def test_response(self):
                pass
        """)
        write(self.tmp, "docs/trace_map.md", """
        | DS-ID | 修飾名 | 備考 |
        |---|---|---|
        | `DS-TS-ORDER-E2E` | `e2e/test_create.py::TestCreate.test_create_order` | |
        | `DS-TS-CANCEL-E2E` | `e2e/test_order.py::test_cancel_order` | クラス名を省いた形 |
        | `DS-TS-RESPONSE-TIME` | `e2e/test_perf.py` | ファイル単位 |
        """)
        code, out = run_script("unittest_junit.py", ["-s", "e2e", "-o", "e2e/results/e2e.xml"], cwd=self.tmp)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.tmp / "e2e" / "results" / "e2e.xml").exists())
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("合格 3 / 不合格 0", out)

    # テストディレクトリが無ければ判定を省く（E2E の有無は implementation_completeness_checker.py が確かめる）
    def test_missing_test_dir_skips_judgement(self):
        import shutil
        shutil.rmtree(self.tmp / "e2e")
        code, out = self.run_checker("--strict")
        self.assertEqual(code, 0, out)
        self.assertIn("受け入れ判定を省く", out)


if __name__ == "__main__":
    unittest.main()
