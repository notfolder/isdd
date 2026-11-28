#!/usr/bin/env python3
"""題材 workways（今の仕事のやり方の決まり）の採点。隠しテスト（measure/workways/hidden）をアプリに対して回す。

結果の JSON には、共通の項目に加えて次を入れる:
  ways          今のやり方の決まり W1〜W5 ごとに、実装に入ったか（share・short・long・limit・once。test_way_<名前> が通ったか）
  ways_count    主な指標。実装に入った W の数（0〜5）
  common        予約のアプリなら聞くことが多い決まり C1〜C3 ごとに、実装に入ったか（gap・hours・horizon）
  common_count  副の指標。実装に入った C の数（0〜3）
  categories    区分ごとの合格数（base: 基本の機能、way、common、edge: 決まりの境目）

使用方法:
  python3 measure/workways/score.py --app <アプリのディレクトリ> --stage 1 --out <結果 JSON> [--python <venv の python>] [--skip-setup]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEASURE = HERE.parent
sys.path.insert(0, str(MEASURE))
from score import count_overbuild  # noqa: E402
from scoring import finalize, new_result, run_hidden  # noqa: E402

WAYS = ("share", "short", "long", "limit", "once")
COMMON = ("gap", "hours", "horizon")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--python", default=str(MEASURE / ".venv" / "bin" / "python"))
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--timeout-min", type=int, default=30)
    args = parser.parse_args()
    app = Path(args.app).resolve()
    result = new_result(args.stage, app)
    started = time.time()
    if True:
        env = dict(os.environ, MEASURE_APP_DIR=str(app), MEASURE_STAGE=str(args.stage))
        if not args.skip_setup and (app / "setup.sh").exists():
            try:
                proc = subprocess.run(["bash", "setup.sh"], cwd=app, env=env, capture_output=True, text=True, timeout=1200)
                result["setup_ok"] = proc.returncode == 0
                if proc.returncode != 0:
                    result["error"] = "setup.sh failed:\n" + (proc.stdout + proc.stderr)[-3000:]
            except subprocess.TimeoutExpired:
                result["setup_ok"] = False
                result["error"] = "setup.sh timeout"
        if not (app / "run.sh").exists():
            result["error"] = (result["error"] or "") + "\nrun.sh が無い（契約違反）"
        run_hidden(args.python, HERE / "hidden", "stage1", env, args.timeout_min, result)
    finalize(result)
    cats = {}
    for name, status in result["tests"].items():
        cat = name.split("_")[1]
        c = cats.setdefault(cat, {"passed": 0, "total": 0})
        c["total"] += 1
        c["passed"] += status == "pass"
    result["categories"] = cats
    result["ways"] = {w: result["tests"].get(f"test_way_{w}") == "pass" for w in WAYS}
    result["ways_count"] = sum(result["ways"].values())
    result["common"] = {c: result["tests"].get(f"test_common_{c}") == "pass" for c in COMMON}
    result["common_count"] = sum(result["common"].values())
    result["overbuild"] = count_overbuild(app)
    result["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage {args.stage}: {result['passed']}/{result['total']} passed, {result['scoring_status']} {result['unscored_reasons']}, "
          f"ways={result['ways_count']}/5 common={result['common_count']}/3 categories={cats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
