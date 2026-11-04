#!/usr/bin/env python3
"""1 課題 × 1 群 × 1 回を 3 段通す（prepare → run → serve → grade → score）。結果の名前は <site>-<arm>-r<run>。

  python3 measure/webgen/drive.py --site 000010 --arm isdd --run 1 --work /tmp/webgen/work [--stages 1,2,3] [--votes 3]
      [--responder measure/ledger/webgen-000010.md]（計測 5: 段 1 だけ依頼者役で回す）
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sh(args):
    print("$", " ".join(args), flush=True)
    return subprocess.run([sys.executable, str(HERE / "webgen.py"), *args], check=False).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--run", type=int, required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--stages", default="1,2,3")
    ap.add_argument("--votes", type=int, default=3)
    ap.add_argument("--responder", default=None)
    ap.add_argument("--grader-model", default="claude-opus-5-5")
    a = ap.parse_args()
    label_arm = f"{a.arm}-r{a.run}"
    stages = [int(x) for x in a.stages.split(",")]
    summary = HERE / "results" / f"{a.site}-{label_arm}" / "summary.json"
    if summary.exists():
        d = json.loads(summary.read_text(encoding="utf-8"))
        if all(str(st) in d.get("stages", {}) and "score" in d["stages"][str(st)] for st in stages):
            print(f"[{a.site}-{label_arm}] already done; skip", flush=True)
            return 0
    for st in stages:
        prep = ["prepare", "--site", a.site, "--arm", label_arm, "--stage", str(st), "--work", a.work]
        if a.responder:
            prep.append("--no-answers")
        sh(prep)
        run = ["run", "--site", a.site, "--arm", label_arm, "--stage", str(st), "--work", a.work]
        if a.responder and st == 1:
            run += ["--responder", a.responder]
        sh(run)
        sh(["serve", "--site", a.site, "--arm", label_arm, "--stage", str(st), "--work", a.work])
        sh(["grade", "--site", a.site, "--arm", label_arm, "--stage", str(st), "--votes", str(a.votes), "--grader-model", a.grader_model])
        sh(["score", "--site", a.site, "--arm", label_arm, "--stage", str(st), "--votes", str(a.votes), "--grader-model", a.grader_model])
    return 0


if __name__ == "__main__":
    sys.exit(main())
