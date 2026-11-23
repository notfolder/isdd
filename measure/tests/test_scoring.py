#!/usr/bin/env python3
"""採点の共通部品（measure/scoring.py）の単体テスト。モデルもブラウザも動かさない。

  python3 -m unittest discover -s measure/tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scoring  # noqa: E402

JUNIT = """<?xml version="1.0"?><testsuites><testsuite name="pytest" tests="{n}">{cases}</testsuite></testsuites>"""


def case(classname, name, child=""):
    return f'<testcase classname="{classname}" name="{name}">{child}</testcase>'


def write_xml(tmp, cases):
    path = Path(tmp) / "junit.xml"
    path.write_text(JUNIT.format(n=len(cases), cases="".join(cases)), encoding="utf-8")
    return path


class ParseTest(unittest.TestCase):
    def test_collect_output_gives_ids_and_ignores_summary_lines(self):
        out = "test_a.py::test_one[chromium]\ntest_a.py::TestX::test_two\n\n2/5 tests collected (3 deselected) in 0.1s\n"
        self.assertEqual(scoring.parse_collect(out), ["test_a.py::test_one[chromium]", "test_a.py::TestX::test_two"])

    def test_junit_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = write_xml(tmp, [case("test_a", "test_ok"), case("test_a", "test_ng", "<failure/>"),
                                  case("test_a", "test_err", "<error/>"), case("test_a", "test_skip", "<skipped/>")])
            got = {name: status for _, name, status in scoring.parse_junit(xml)}
        self.assertEqual(got, {"test_ok": "pass", "test_ng": "fail", "test_err": "fail", "test_skip": "skip"})


class JudgeRunTest(unittest.TestCase):
    def judge(self, expected, cases, returncode=1, timed_out=False):
        with tempfile.TemporaryDirectory() as tmp:
            parsed = None if cases is None else scoring.parse_junit(write_xml(tmp, cases))
        return scoring.judge_run(expected, parsed, returncode, timed_out)

    def test_all_tests_present_is_scored_even_when_tests_fail(self):
        # アプリが起動せず全部落ちたのは「不合格」で、採点はできている
        j = self.judge(["a.py::test_1", "a.py::test_2"], [case("a", "test_1", "<error/>"), case("a", "test_2", "<error/>")], returncode=1)
        self.assertEqual(j["reasons"], [])
        self.assertEqual(j["tests"], {"test_1": "fail", "test_2": "fail"})

    def test_missing_xml_is_unscored(self):
        j = self.judge(["a.py::test_1"], None, returncode=1)
        self.assertTrue(any("XML が無い" in r for r in j["reasons"]))
        self.assertEqual(j["not_run"], ["test_1"])

    def test_timeout_is_unscored(self):
        j = self.judge(["a.py::test_1"], None, returncode=None, timed_out=True)
        self.assertTrue(any("時間切れ" in r for r in j["reasons"]))

    def test_bad_exit_code_is_unscored(self):
        for rc in (2, 3, 4, 5):
            j = self.judge(["a.py::test_1"], [case("a", "test_1")], returncode=rc)
            self.assertTrue(any(f"終了コードが {rc}" in r for r in j["reasons"]), rc)

    def test_test_missing_from_results_is_unscored_and_listed(self):
        j = self.judge(["a.py::test_1", "a.py::test_2"], [case("a", "test_1")], returncode=0)
        self.assertEqual(j["not_run"], ["test_2"])
        self.assertTrue(any("結果が無いテストが 1 件" in r for r in j["reasons"]))

    def test_same_name_in_two_files_is_unscored(self):
        # 名前だけをキーにすると片方が上書きされる
        j = self.judge(["a.py::test_1", "b.py::test_1"], [case("a", "test_1"), case("b", "test_1", "<failure/>")], returncode=1)
        self.assertTrue(any("同じ名前" in r for r in j["reasons"]))
        self.assertEqual(j["test_ids"], {"a::test_1": "pass", "b::test_1": "fail"})

    def test_collection_error_entry_is_unscored(self):
        # 収集に失敗すると、テストの代わりにモジュール名の error が 1 件だけ出る
        j = self.judge(["a.py::test_1", "a.py::test_2"], [case("", "a", "<error/>")], returncode=2)
        self.assertTrue(any("数えたテストに無い結果" in r for r in j["reasons"]))
        self.assertEqual(j["not_run"], ["test_1", "test_2"])

    def test_uncounted_expected_is_unscored(self):
        j = self.judge(None, [case("a", "test_1")], returncode=0)
        self.assertTrue(any("数えられなかった" in r for r in j["reasons"]))

    def test_zero_expected_is_unscored(self):
        j = self.judge([], [], returncode=5)
        self.assertTrue(any("0 件" in r for r in j["reasons"]))


class MergeTest(unittest.TestCase):
    def test_result_without_any_run_is_unscored(self):
        r = scoring.new_result(1, "/app")
        self.assertEqual(r["scoring_status"], scoring.UNSCORED)

    def test_two_runs_are_added_up(self):
        r = scoring.new_result(4, "/app")
        scoring.merge_run(r, scoring.judge_run(["a.py::t1"], [("a::t1", "t1", "pass")], 0, False), 0, "x/hidden")
        scoring.merge_run(r, scoring.judge_run(["b.py::t2"], [("b::t2", "t2", "fail")], 1, False), 1, "y/hidden")
        self.assertEqual((r["passed"], r["total"], r["expected_total"], r["scoring_status"]), (1, 2, 2, scoring.SCORED))
        self.assertEqual([x["returncode"] for x in r["pytest_runs"]], [0, 1])

    def test_same_name_across_runs_is_unscored(self):
        r = scoring.new_result(4, "/app")
        scoring.merge_run(r, scoring.judge_run(["a.py::t1"], [("a::t1", "t1", "pass")], 0, False), 0, "x/hidden")
        scoring.merge_run(r, scoring.judge_run(["b.py::t1"], [("b::t1", "t1", "fail")], 1, False), 1, "y/hidden")
        self.assertEqual(r["scoring_status"], scoring.UNSCORED)

    def test_one_unscored_run_makes_whole_unscored(self):
        r = scoring.new_result(4, "/app")
        scoring.merge_run(r, scoring.judge_run(["a.py::t1"], [("a::t1", "t1", "pass")], 0, False), 0, "x/hidden")
        scoring.merge_run(r, scoring.judge_run(["b.py::t2"], None, None, True), None, "y/hidden")
        self.assertEqual(r["scoring_status"], scoring.UNSCORED)
        self.assertEqual(r["not_run"], ["t2"])


class LoadScoreTest(unittest.TestCase):
    def test_missing_file_is_unscored(self):
        s = scoring.load_score("/nonexistent/stage1.json")
        self.assertEqual(s["scoring_status"], scoring.UNSCORED)
        self.assertIsNone(s["passed"])

    def test_broken_file_is_unscored(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.json"
            p.write_text("{", encoding="utf-8")
            self.assertEqual(scoring.load_score(p)["scoring_status"], scoring.UNSCORED)

    def test_old_format_with_tests_is_scored_and_without_tests_is_unscored(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "s.json"
            p.write_text(json.dumps({"tests": {"t1": "pass"}, "passed": 1, "total": 1}), encoding="utf-8")
            self.assertEqual(scoring.load_score(p)["scoring_status"], scoring.SCORED)
            p.write_text(json.dumps({"tests": {}, "passed": 0, "total": 0}), encoding="utf-8")
            self.assertEqual(scoring.load_score(p)["scoring_status"], scoring.UNSCORED)

    def test_stage_fields_and_label(self):
        info = scoring.stage_fields(scoring.load_score("/nonexistent/stage1.json"))
        self.assertEqual(scoring.score_label(info), "未採点")
        self.assertEqual(scoring.score_label({"passed": 3, "total": 8, "scoring_status": "scored"}), "3/8")
        self.assertEqual(scoring.score_label({"passed": 3, "total": 8}), "3/8")  # 前の形の summary.json


class CompareStagesTest(unittest.TestCase):
    def test_regression_and_not_run_are_separate(self):
        prev = {"t1": "pass", "t2": "pass", "t3": "pass", "t4": "fail"}
        now = {"t1": "pass", "t2": "fail", "t4": "fail", "t5": "pass"}
        got = scoring.compare_stages(prev, now)
        self.assertEqual(got, {"regressions": ["t2"], "not_run_after_pass": ["t3"]})

    def test_skipped_after_pass_is_regression(self):
        self.assertEqual(scoring.compare_stages({"t1": "pass"}, {"t1": "skip"})["regressions"], ["t1"])

    def test_unscored_stage_shows_all_as_not_run(self):
        got = scoring.compare_stages({"t1": "pass", "t2": "pass"}, {})
        self.assertEqual(got, {"regressions": [], "not_run_after_pass": ["t1", "t2"]})


class VoteTest(unittest.TestCase):
    IDS = ["F1", "F2"]

    def test_point_vote_needs_all_ids_and_allowed_points(self):
        ok = scoring.valid_point_vote
        self.assertTrue(ok({"F1": 2, "F2": 0}, self.IDS))
        self.assertFalse(ok({"F1": 2}, self.IDS))                 # 質問が欠けている
        self.assertFalse(ok({"F1": 2, "F2": 0, "F3": 1}, self.IDS))  # 知らない質問
        self.assertFalse(ok({"F1": 3, "F2": 0}, self.IDS))        # 決めていない点
        self.assertFalse(ok({"F1": "2", "F2": 0}, self.IDS))      # 文字列
        self.assertFalse(ok({"F1": True, "F2": 0}, self.IDS))
        self.assertFalse(ok({}, self.IDS))
        self.assertFalse(ok(None, self.IDS))

    def test_found_vote(self):
        ok = scoring.valid_found_vote
        known = {"M1": "", "M2": ""}
        self.assertTrue(ok({"found": ["M1"], "other": 0}, known))
        self.assertTrue(ok({"found": [], "other": 2}, known))
        self.assertFalse(ok({"found": ["M9"], "other": 0}, known))
        self.assertFalse(ok({"found": ["M1"]}, known))
        self.assertFalse(ok({"found": "M1", "other": 0}, known))
        self.assertFalse(ok({"found": [], "other": -1}, known))
        self.assertFalse(ok(None, known))

    def test_parse_json_object(self):
        self.assertEqual(scoring.parse_json_object('前置き {"F1": 2} 後書き'), {"F1": 2})
        self.assertIsNone(scoring.parse_json_object("採点できません"))
        self.assertIsNone(scoring.parse_json_object('{"F1": '))

    def test_collect_votes_drops_broken_and_asks_again(self):
        answers = iter([{}, {"F1": 2, "F2": 1}, None, {"F1": 2, "F2": 0}, {"F1": 0, "F2": 0}])
        votes, rejected = scoring.collect_votes(lambda: next(answers), lambda v: scoring.valid_point_vote(v, self.IDS))
        self.assertEqual(len(votes), 3)
        self.assertEqual(rejected, [{}, None])
        self.assertEqual(scoring.median_points(votes, self.IDS), {"F1": 2, "F2": 0})

    def test_collect_votes_gives_up_without_fixing_points(self):
        calls = []
        votes, rejected = scoring.collect_votes(lambda: calls.append(1) or {}, lambda v: scoring.valid_point_vote(v, self.IDS), max_tries=6)
        self.assertIsNone(votes)
        self.assertEqual((len(calls), len(rejected)), (6, 6))

    def test_broken_vote_is_not_counted_as_zero(self):
        # 前の作りでは、壊れた応答 1 件が 0 点として数えられ、2・0・壊れ の中央の値が 0 になった
        answers = iter([{"F1": 2, "F2": 2}, {}, {"F1": 0, "F2": 2}, {"F1": 2, "F2": 2}])
        votes, _ = scoring.collect_votes(lambda: next(answers), lambda v: scoring.valid_point_vote(v, self.IDS))
        self.assertEqual(scoring.median_points(votes, self.IDS)["F1"], 2)


if __name__ == "__main__":
    unittest.main()
