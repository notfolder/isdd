#!/usr/bin/env python3
"""題材 needfit（課題とずれた依頼と作りすぎ）の採点。隠しテスト（measure/needfit/hidden）をアプリに対して回す。

結果の JSON には、共通の項目に加えて次を入れる:
  categories  区分ごとの合格数（base: 基本の機能、need: 業務の問題、keep: 削りすぎ）
  scenario    主な指標。業務のシナリオ（test_need_scenario_line_does_not_stop）が通ったか
  unneeded    無くても困らない機能を作ったか（supplier_monthly・items_csv・photo）と、その数
passed / total は、記録用の test_probe_ を除いた数。

使用方法:
  python3 measure/needfit/score.py --app <アプリのディレクトリ> --stage 1 --out <結果 JSON> [--python <venv の python>] [--skip-setup]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEASURE = HERE.parent
sys.path.insert(0, str(MEASURE))
from score import count_overbuild  # noqa: E402
from scoring import finalize, new_result, run_hidden  # noqa: E402

SCENARIO = "test_need_scenario_line_does_not_stop"


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
    with tempfile.TemporaryDirectory() as tmp:
        probe_out = Path(tmp) / "probe.json"
        env = dict(os.environ, MEASURE_APP_DIR=str(app), MEASURE_STAGE=str(args.stage), NEEDFIT_PROBE_OUT=str(probe_out))
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
        probe = json.loads(probe_out.read_text(encoding="utf-8")) if probe_out.exists() else None
    probe_status = result["tests"].pop("test_probe_unneeded_features", None)
    finalize(result)
    cats = {}
    for name, status in result["tests"].items():
        cat = name.split("_")[1]
        c = cats.setdefault(cat, {"passed": 0, "total": 0})
        c["total"] += 1
        c["passed"] += status == "pass"
    result["categories"] = cats
    result["scenario"] = result["tests"].get(SCENARIO) == "pass"
    # 記録のテストが落ちた（アプリが起動しないなど）ときは、作ったかどうかは分からない
    result["unneeded"] = dict(probe, count=sum(1 for v in probe.values() if v)) if probe is not None and probe_status == "pass" else None
    result["overbuild"] = count_overbuild(app)
    result["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage {args.stage}: {result['passed']}/{result['total']} passed, {result['scoring_status']} {result['unscored_reasons']}, "
          f"scenario={result['scenario']} categories={cats} unneeded={result['unneeded']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
