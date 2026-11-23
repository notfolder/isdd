#!/usr/bin/env python3
"""題材 extapi（外部連携）の採点。隠しテスト（measure/extapi/hidden）を、アプリに対して回す。

段 1 は stage1 のテスト、段 2 は stage1 と stage2 のテスト（連携先は v2 だけ）。採点用の連携先は hidden/conftest.py が起こす。

使用方法:
  python3 measure/extapi/score.py --app <アプリのディレクトリ> --stage 1 --out <結果 JSON> [--python <venv の python>] [--skip-setup]
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--python", default=str(MEASURE / ".venv" / "bin" / "python"))
    parser.add_argument("--skip-setup", action="store_true")
    parser.add_argument("--timeout-min", type=int, default=40)
    args = parser.parse_args()
    app = Path(args.app).resolve()
    result = new_result(args.stage, app)
    env = dict(os.environ, MEASURE_APP_DIR=str(app), MEASURE_STAGE=str(args.stage))
    for key in ("SUPPLIER_API_URL", "SUPPLIER_CLIENT_ID", "SUPPLIER_CLIENT_SECRET"):
        env.pop(key, None)
    started = time.time()
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
    marks = "stage1" if args.stage == 1 else "stage1 or stage2"
    run_hidden(args.python, HERE / "hidden", marks, env, args.timeout_min, result)
    finalize(result)
    result["overbuild"] = count_overbuild(app)
    result["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage {args.stage}: {result['passed']}/{result['total']} passed, {result['scoring_status']} {result['unscored_reasons']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
