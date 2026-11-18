#!/usr/bin/env python3
"""題材 ripple（お題 1 の続き、段 4〜6）の採点。段 1〜3 の隠しテスト（measure/hidden）と段 4〜6 の隠しテスト
（measure/ripple/hidden）を、アプリに対して回し、お題 1 の score.py と同じ形の JSON に書く。

使用方法:
  python3 measure/ripple/score.py --app <アプリのディレクトリ> --stage <4|5|6> --out <結果 JSON> [--python <venv の python>] [--skip-setup]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEASURE = HERE.parent
sys.path.insert(0, str(MEASURE))
from score import count_overbuild  # noqa: E402


def run_pytest(python: str, hidden: Path, marks: str, env: dict, timeout_min: int, result: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "junit.xml"
        cmd = [python, "-m", "pytest", str(hidden), "-m", marks, "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"]
        try:
            proc = subprocess.run(cmd, cwd=hidden, env=env, capture_output=True, text=True, timeout=timeout_min * 60)
            result["pytest_tail"] = result.get("pytest_tail", "") + (proc.stdout + proc.stderr)[-4000:]
        except subprocess.TimeoutExpired:
            result["error"] = (result["error"] or "") + f"\npytest timeout ({timeout_min} min): {hidden.parent.name}/{hidden.name}"
        if xml.exists():
            for tc in ET.parse(str(xml)).getroot().iter("testcase"):
                status = "pass"
                for child in tc:
                    if child.tag in ("failure", "error"):
                        status = "fail"
                        break
                    if child.tag == "skipped":
                        status = "skip"
                result["tests"][tc.get("name")] = status


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
    result = {"stage": args.stage, "app": str(app), "tests": {}, "passed": 0, "total": 0, "setup_ok": None, "error": None}
    env = dict(os.environ, MEASURE_APP_DIR=str(app), MEASURE_STAGE=str(args.stage))
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
    run_pytest(args.python, MEASURE / "hidden", " or ".join(f"stage{i}" for i in range(1, min(args.stage, 3) + 1)), env, args.timeout_min, result)
    if args.stage >= 4:
        run_pytest(args.python, HERE / "hidden", " or ".join(f"stage{i}" for i in range(4, args.stage + 1)), env, args.timeout_min, result)
    result["total"] = len(result["tests"])
    result["passed"] = sum(1 for v in result["tests"].values() if v == "pass")
    result["overbuild"] = count_overbuild(app)
    result["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage {args.stage}: {result['passed']}/{result['total']} passed, overbuild={result['overbuild']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
