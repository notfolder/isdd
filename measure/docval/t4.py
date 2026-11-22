#!/usr/bin/env python3
"""文書の価値の評価 4: 影響範囲の見積もり（60 機能の総務システム）。コードは変えずに、変更が及ぶ機能を挙げさせる。

  python3 measure/docval/t4.py --cond <big_code|big_notes|big_docs> --model <モデル> --run N
答えの鍵（直す必要がある機能の slug）と突き合わせて、拾えた割合（再現率）と当たっていた割合（適合率）を出す。
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from agentrun import run_claude_retry  # noqa: E402

MATERIAL = Path.home() / "isdd-measure-work" / "docval" / "material"
WORK = Path.home() / "isdd-measure-work" / "docval" / "work"
OUT = HERE.parent / "results" / "docval"
BIG = HERE.parent / "bigapp"
MANIFEST = json.loads((BIG / "hidden" / "manifest.json").read_text(encoding="utf-8"))
LOAN = sorted(m["slug"] for m in MANIFEST if m["family"] == "L")
REQ = sorted(m["slug"] for m in MANIFEST if m["family"] == "Q")
LEAVE = sorted(json.loads((BIG / "hidden" / "leave_need.json").read_text(encoding="utf-8")))
KEY = {"I1": LOAN, "I2": LEAVE, "I3": REQ, "I4": ["meeting_rooms"]}

PROMPT = """あなたは、この総務システム（機能は 60 個）の変更を計画する担当者です。作った人には連絡が取れません。
これから下の 4 つの変更が予定されています。着手する前に、それぞれの変更で**コードを直す必要がある機能**を、漏れなく、余分なく挙げてください。
作業ディレクトリにあるものがすべてです。

決まり:
- コードは変更しない。実行もしない（読むだけ）。インターネットは使わない。答えのファイルを 1 つ作るだけ。
- 機能は `app/modules/` の下のフォルダの名前（slug）で挙げる。共通の部分（`app/core/`）を直す必要があるときは `core` と書く。
- 「直す必要がある機能」とは、その変更の内容を満たすために、その機能のコード（Python・SQL・テンプレート）を書き換えなければならない機能のこと。今の書き方のままで変更後のきまりを満たす機能は挙げない。
- 作業ディレクトリ直下の impact.json に、{"I1": ["slug", ...], "I2": [...], "I3": [...], "I4": [...]} の形で書く。書き終えたら「完了」とだけ答える。

予定されている変更:
- I1: 貸出はどの種類でも、返却の期限から 3 日を過ぎたときに、はじめて期限を過ぎた扱いにする（期限の 3 日後までは今までの「貸出中」と同じ扱い）。期限を過ぎた貸出を持つ社員に貸さないきまりも、状態の表示も、これに合わせる。
- I2: 社員の状態に「休職中」（`leave`）を足す。休職中の社員は、貸出・予約・申請のどれも対象にできないようにする。（社員の状態を変える操作を `core` に足すのは前提としてよい。ここでは、休職中の社員を対象から外すために直す必要がある機能を挙げる。）
- I3: 申請はどの種類でも、税込みの金額の 1 円未満を、切り捨てではなく四捨五入にする。
- I4: 会議室の予約の時間の単位を、30 分から 15 分に変える。ほかの予約の単位は変えない。
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cond", required=True)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--run", type=int, default=1)
    a = p.parse_args()
    label = f"impact-{a.cond}-{a.model.split('-')[1]}-r{a.run}"
    out = OUT / f"{label}.json"
    if out.exists():
        print(label, "済み")
        return 0
    work = WORK / label
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(MATERIAL / a.cond, work, symlinks=False)
    started = time.time()
    data = run_claude_retry(work, PROMPT, a.model, "", 60)
    answers = {}
    try:
        answers = json.loads((work / "impact.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(label, "impact.json を読めない:", e)
    score = {}
    for qid, key in KEY.items():
        got = sorted(set(str(x) for x in (answers.get(qid) or [])) - {"core"})
        hit = sorted(set(got) & set(key))
        score[qid] = {"key": len(key), "listed": len(got), "hit": len(hit), "missed": sorted(set(key) - set(got)), "extra": sorted(set(got) - set(key)),
                      "recall": round(len(hit) / len(key), 3), "precision": round(len(hit) / len(got), 3) if got else 0.0}
    usage = data.get("usage") or {}
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, "cond": a.cond, "model": a.model, "run": a.run, "answers": answers, "score": score,
                               "wall_sec": round(time.time() - started, 1), "usage": usage, "cost_usd": data.get("total_cost_usd"),
                               "tool_uses": data.get("tool_uses"), "tool_names": data.get("tool_names"), "error": data.get("error")}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, {k: (v["hit"], v["key"], v["listed"]) for k, v in score.items()}, round(time.time() - started), "秒")
    return 0


if __name__ == "__main__":
    sys.exit(main())
