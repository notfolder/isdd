#!/usr/bin/env python3
"""題材ごとの全回の表を出す（needfit、extapi など、採点結果に categories を持つ題材）。

使用方法: python3 measure/taskreport.py <結果フォルダ名の頭（例: needfit-）> [--stage 1] [--json]
割り当てた回をすべて出す。未採点・基盤の障害・隠しテストに触れた回も消さない。
"""

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scoring import load_score, score_label  # noqa: E402


def arm_of(summary: dict) -> str:
    if summary.get("arm") == "control":
        return "数文つき" if summary.get("keep_notes") else ("一文つき" if summary.get("ask_first") else "バイブコーディング")
    return summary.get("arm", "?")


def rows(prefix: str, stage: str) -> list:
    out = []
    for path in sorted((HERE / "results").glob(f"{prefix}*/summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        info = (summary.get("stages") or {}).get(stage)
        if not info:
            continue
        score = load_score(path.parent / f"stage{stage}.json")
        conduct = info.get("conduct") or {}
        cats = score.get("categories") or {}
        out.append({"label": path.parent.name, "arm": arm_of(summary), "done": info.get("done"), "score": score_label(score),
                    "scored": score.get("scoring_status") == "scored", "scenario": score.get("scenario"),
                    "cats": {k: f"{v['passed']}/{v['total']}" for k, v in cats.items()}, "cats_raw": cats,
                    "unneeded": (score.get("unneeded") or {}).get("count") if score.get("unneeded") is not None else None,
                    "extra": {k: score.get(k) for k in ("metrics",) if score.get(k) is not None},
                    "cost": info.get("cost_usd"), "responder_cost": info.get("responder_cost_usd"), "wall_min": round((info.get("wall_sec") or 0) / 60, 1),
                    "rounds": info.get("rounds"), "questions": info.get("questions_rounds"), "skills": sorted(set(info.get("skills_called") or [])),
                    "procedure": conduct.get("procedure_evidence"), "infra_incomplete": conduct.get("infra_incomplete"),
                    "leaks": real_leaks(conduct.get("leak_hits") or [], path.parent.name, (summary.get("conditions") or {}).get("work")), "parent_refs": conduct.get("parent_dir_refs"),
                    "lines": (score.get("overbuild") or {}).get("lines"), "isdd_version": (summary.get("conditions") or {}).get("isdd_version"),
                    "task_sha": ((summary.get("conditions") or {}).get("task_digest") or {}).get("sha256", "")[:10],
                    "tests": score.get("tests") or {}, "unscored_reasons": score.get("unscored_reasons") or []})
    return out


def real_leaks(hits: list, label: str, work) -> int:
    """記録された「触れた」入力を、今の規則で数え直す。2026-11-23 夜までの実行器は、自分のフォルダ名の直後に「;」などが続く入力を
    ほかの回と数えていた。記録は入力の先頭 300 字なので、数え直しもその範囲で行う。"""
    sibling = re.compile(re.escape(str(work or "/Users/Shared/isdd-measure-work")) + r"/([A-Za-z0-9_.-]+)")
    return sum(1 for s in hits if str(HERE.parent) in s or any(m.group(1).rstrip(".") != label for m in sibling.finditer(s)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix")
    parser.add_argument("--stage", default="1")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    data = rows(args.prefix, args.stage)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return 0
    cat_names = sorted({k for r in data for k in r["cats"]})
    print("| 回 | 群 | 完了 | 合格 | シナリオ | " + " | ".join(cat_names) + " | 不要な機能 | 費用 | 依頼者役 | 分 | 往復 | 質問 | 行数 | 手順 | 障害 | 触れた |")
    print("|" + "---|" * (16 + len(cat_names)))
    for r in data:
        print(f"| {r['label']} | {r['arm']} | {r['done']} | {r['score']} | {r['scenario']} | " + " | ".join(r["cats"].get(c, "-") for c in cat_names) +
              f" | {r['unneeded']} | {r['cost']} | {r['responder_cost']} | {r['wall_min']} | {r['rounds']} | {r['questions']} | {r['lines']} | {r['procedure']} | {r['infra_incomplete']} | {r['leaks']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
