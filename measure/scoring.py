#!/usr/bin/env python3
"""採点の共通部品。「採点できなかった」を「不合格」と分けて記録する。

題材ごとの score.py、実行器（run.py・stage.py・rescore.py）、AI の採点（docval/）が使う。標準ライブラリだけで動く。

採点結果の JSON に足す項目:
  scoring_status   "scored"（採点できた）か "unscored"（採点できなかった。点を使わず、採点し直す）
  unscored_reasons 採点できなかった理由の一覧
  expected_total   回すはずだったテストの数（pytest --collect-only で数える）
  not_run          回すはずだったのに結果が無いテスト
  test_ids         「ファイル::名前」の形の識別子と結果
  pytest_runs      pytest を起こした回ごとの終了コード

アプリが起動しない、機能が足りないなどでテストが落ちるのは「不合格」で、scored のまま。
pytest が途中で止まった、結果の XML が無い、回すはずのテストが結果に無い、名前が重なって上書きされた、は「採点できなかった」。
"""

import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

SCORED = "scored"
UNSCORED = "unscored"
# pytest の終了コード: 0 全部合格、1 落ちたテストがある。2 中断、3 内部エラー、4 使い方の誤り、5 テストが 1 本も無い
PYTEST_OK = (0, 1)


def parse_collect(stdout: str) -> list:
    """pytest --collect-only -q の出力から、テストの識別子（ファイル::名前）を取り出す。"""
    return [line.strip() for line in stdout.splitlines() if "::" in line and not line.startswith(" ") and " " not in line.split("::")[0]]


def short_name(test_id: str) -> str:
    """「ファイル::クラス::名前[引数]」から、JUnit の testcase の name に当たる「名前[引数]」を取り出す。"""
    return test_id.split("::")[-1]


def parse_junit(xml_path) -> list:
    """JUnit XML を読み、(識別子, 名前, 結果) の一覧を返す。識別子は「classname::name」。"""
    cases = []
    for tc in ET.parse(str(xml_path)).getroot().iter("testcase"):
        status = "pass"
        for child in tc:
            if child.tag in ("failure", "error"):
                status = "fail"
                break
            if child.tag == "skipped":
                status = "skip"
        name = tc.get("name") or ""
        cases.append((f"{tc.get('classname') or ''}::{name}", name, status))
    return cases


def judge_run(expected_ids, cases, returncode, timed_out: bool, where: str = "") -> dict:
    """pytest 1 回分について、採点できたかを判定する。

    expected_ids: 回すはずだったテストの識別子（数えられなかったら None）
    cases: parse_junit の結果（XML が無ければ None）
    returns: {"tests": {名前: 結果}, "test_ids": {識別子: 結果}, "expected": 件数か None, "not_run": [...], "reasons": [...]}
    """
    tag = f"（{where}）" if where else ""
    reasons = []
    tests, test_ids = {}, {}
    if timed_out:
        reasons.append(f"pytest が時間切れ{tag}")
    elif returncode not in PYTEST_OK:
        reasons.append(f"pytest の終了コードが {returncode}{tag}")
    if cases is None:
        reasons.append(f"結果の XML が無い{tag}")
        cases = []
    for test_id, name, status in cases:
        test_ids[test_id] = status
        tests[name] = status
    dup = sorted(n for n, c in Counter(name for _, name, _ in cases).items() if c > 1)
    if dup:
        reasons.append(f"同じ名前のテストが複数ある{tag}: {', '.join(dup[:5])}")
    not_run = []
    if expected_ids is None:
        reasons.append(f"回すはずのテストを数えられなかった{tag}")
    else:
        want = Counter(short_name(t) for t in expected_ids)
        got = Counter(name for _, name, _ in cases)
        not_run = sorted((want - got).elements())
        extra = sorted((got - want).elements())
        if not expected_ids:
            reasons.append(f"回すはずのテストが 0 件{tag}")
        if not_run:
            reasons.append(f"結果が無いテストが {len(not_run)} 件{tag}: {', '.join(not_run[:5])}")
        if extra:
            reasons.append(f"数えたテストに無い結果が {len(extra)} 件{tag}: {', '.join(extra[:5])}")
    return {"tests": tests, "test_ids": test_ids, "expected": None if expected_ids is None else len(expected_ids), "not_run": not_run, "reasons": reasons}


def new_result(stage, app) -> dict:
    return {"stage": stage, "app": str(app), "tests": {}, "passed": 0, "total": 0, "setup_ok": None, "error": None,
            "scoring_status": UNSCORED, "unscored_reasons": ["pytest を回していない"], "expected_total": 0, "not_run": [], "test_ids": {}, "pytest_runs": []}


def run_hidden(python: str, hidden: Path, marks: str, env: dict, timeout_min: int, result: dict) -> None:
    """隠しテストを 1 回回し、result（new_result の形）に足す。1 つの採点で複数回呼んでよい。"""
    where = f"{hidden.parent.name}/{hidden.name}"
    base = [python, "-m", "pytest", str(hidden), "-q", "-p", "no:cacheprovider"] + (["-m", marks] if marks else [])
    expected = None
    try:
        col = subprocess.run(base + ["--collect-only"], cwd=hidden, env=env, capture_output=True, text=True, timeout=300)
        if col.returncode in (0, 5):
            expected = parse_collect(col.stdout)
        else:
            result["collect_tail"] = (col.stdout + col.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        pass
    returncode, timed_out, cases = None, False, None
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "junit.xml"
        try:
            proc = subprocess.run(base + [f"--junitxml={xml}"], cwd=hidden, env=env, capture_output=True, text=True, timeout=timeout_min * 60)
            returncode = proc.returncode
            result["pytest_tail"] = result.get("pytest_tail", "") + (proc.stdout + proc.stderr)[-4000:]
        except subprocess.TimeoutExpired as e:
            timed_out = True
            result["error"] = (result.get("error") or "") + f"\npytest timeout ({timeout_min} min): {where}"
            result["pytest_tail"] = result.get("pytest_tail", "") + ((e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace"))[-4000:]
        if xml.exists():
            try:
                cases = parse_junit(xml)
            except ET.ParseError:
                cases = None
    merge_run(result, judge_run(expected, cases, returncode, timed_out, where), returncode, where)


def merge_run(result: dict, judged: dict, returncode, where: str = "") -> None:
    """judge_run の結果を、採点全体の result に足す。別の回と同じ名前のテストがあれば、採点できなかったとする。"""
    if result.get("unscored_reasons") == ["pytest を回していない"]:
        result["unscored_reasons"] = []
    overlap = sorted(set(result["tests"]) & set(judged["tests"]))
    if overlap:
        result["unscored_reasons"].append(f"別の回と同じ名前のテストがある（{where}）: {', '.join(overlap[:5])}")
    result["tests"].update(judged["tests"])
    result["test_ids"].update({f"{where}/{k}" if where else k: v for k, v in judged["test_ids"].items()})
    result["expected_total"] += judged["expected"] or 0
    result["not_run"] += judged["not_run"]
    result["unscored_reasons"] += judged["reasons"]
    result["pytest_runs"].append({"where": where, "returncode": returncode, "expected": judged["expected"], "results": len(judged["tests"])})
    finalize(result)


def finalize(result: dict) -> dict:
    result["total"] = len(result["tests"])
    result["passed"] = sum(1 for v in result["tests"].values() if v == "pass")
    result["scoring_status"] = UNSCORED if result["unscored_reasons"] else SCORED
    return result


def load_score(out_json) -> dict:
    """採点結果の JSON を読む。無い、壊れている、古い形（scoring_status が無い）も扱う。"""
    path = Path(out_json)
    if not path.exists():
        return {"tests": {}, "passed": None, "total": None, "scoring_status": UNSCORED, "unscored_reasons": ["採点結果のファイルが無い（採点器が落ちた）"], "not_run": []}
    try:
        score = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {"tests": {}, "passed": None, "total": None, "scoring_status": UNSCORED, "unscored_reasons": ["採点結果のファイルを読めない"], "not_run": []}
    if "scoring_status" not in score:  # この部品を使う前の採点器が書いた結果
        reasons = [] if score.get("tests") else ["テストの結果が 0 件"]
        score.update({"scoring_status": UNSCORED if reasons else SCORED, "unscored_reasons": reasons, "not_run": []})
    return score


def stage_fields(score: dict) -> dict:
    """採点結果から、summary.json の段の項目を作る。採点できなかった段は、合格数を点として使わない目印を付ける。"""
    return {"passed": score.get("passed"), "total": score.get("total"), "tests": score.get("tests") or {}, "overbuild": score.get("overbuild"),
            "score_error": score.get("error"), "scoring_status": score.get("scoring_status", UNSCORED),
            "unscored_reasons": score.get("unscored_reasons") or [], "expected_total": score.get("expected_total"), "not_run": score.get("not_run") or []}


def compare_stages(prev_tests: dict, now_tests: dict) -> dict:
    """前の段で合格したテストが、今の段でどうなったか。

    regressions: 今の段で回して、合格しなかったもの（退行）
    not_run_after_pass: 今の段の結果に無いもの（未実行。退行とは分けて出す）
    """
    passed_before = [t for t, v in (prev_tests or {}).items() if v == "pass"]
    return {"regressions": sorted(t for t in passed_before if t in now_tests and now_tests[t] != "pass"),
            "not_run_after_pass": sorted(t for t in passed_before if t not in now_tests)}


def score_label(info: dict) -> str:
    """表に出す合格数。採点できなかった段は「未採点」と出す。"""
    if info.get("scoring_status", SCORED) == UNSCORED:
        return "未採点"
    return f"{info.get('passed')}/{info.get('total')}"


# ---- AI の採点（3 人の多数決） ----

def valid_point_vote(vote, ids, allowed=(0, 1, 2)) -> bool:
    """採点者の応答が、全部の質問に、決められた点を付けているか。"""
    if not isinstance(vote, dict) or set(vote) != set(ids):
        return False
    return all(isinstance(v, int) and not isinstance(v, bool) and v in allowed for v in vote.values())


def valid_found_vote(vote, known) -> bool:
    """採点者の応答が {"found": [知っている番号…], "other": 0 以上の整数} の形か。"""
    if not isinstance(vote, dict) or not isinstance(vote.get("found"), list):
        return False
    other = vote.get("other")
    return all(m in known for m in vote["found"]) and isinstance(other, int) and not isinstance(other, bool) and other >= 0


def parse_json_object(text: str):
    """応答の文字列から JSON のオブジェクトを取り出す。取り出せなければ None。"""
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except ValueError:
        return None


def collect_votes(ask, is_valid, need: int = 3, max_tries: int = 6):
    """ask() を呼んで、形の正しい応答を need 件集める。集まらなければ (None, 捨てた応答) を返す。

    形の壊れた応答を 0 点として数えないため、捨てて聞き直す。max_tries 回で need 件に届かなければ、点を確定しない。
    """
    votes, rejected = [], []
    for _ in range(max_tries):
        vote = ask()
        if is_valid(vote):
            votes.append(vote)
            if len(votes) == need:
                return votes, rejected
        else:
            rejected.append(vote)
    return None, rejected


def median_points(votes, ids) -> dict:
    """質問ごとに、採点者の点の中央の値を取る（3 人なら多数決に当たる）。"""
    return {i: sorted(v[i] for v in votes)[len(votes) // 2] for i in ids}
