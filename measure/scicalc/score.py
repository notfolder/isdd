#!/usr/bin/env python3
"""sci-calc の採点。AI-DLC v1 の評価器の契約テスト（vendor/contracttest、hidden/openapi.yaml の x-test-cases 88 件）を、
アプリ（pyproject.toml を持つディレクトリ）に対して回し、お題 1 の score.py と同じ形の JSON に書く。

使用方法:
  python3 measure/scicalc/score.py --app <アプリのディレクトリ> --stage 1 --out <結果 JSON>

契約テストは Python 3.13 と pyyaml・httpx が要るので、uv で一時の環境を作って回す（アプリ側の環境は contracttest が uv で作る）。
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from score import count_overbuild  # noqa: E402

INNER = """
import json, os, sys
os.environ.pop("VIRTUAL_ENV", None)  # uv run の一時環境ではなく、アプリの .venv に依存を入れさせる
from dataclasses import asdict
from pathlib import Path
from contracttest.spec import load_spec
from contracttest.runner import run_contract_tests
spec = load_spec(Path(sys.argv[2]))
try:
    res = asdict(run_contract_tests(spec, workspace=Path(sys.argv[1]), use_sandbox=False))
except Exception as e:  # 環境を作れない・起動できないときは全件を不合格として数える
    res = {"total": len(spec.test_cases), "cases": [], "server_error": repr(e)[:1500]}
print("RESULT_JSON " + json.dumps(res, default=str))
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--stage", type=int, default=1)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    app = Path(args.app).resolve()
    started = time.time()
    out = {"stage": args.stage, "tests": {}, "passed": 0, "total": 0, "overbuild": count_overbuild(app)}
    try:
        proc = subprocess.run(["uv", "run", "--no-project", "--python", "3.13", "--with", "pyyaml", "--with", "httpx", "python", "-c", INNER,
                               str(app), str(HERE / "hidden" / "openapi.yaml")],
                              cwd=HERE / "vendor", capture_output=True, text=True, timeout=900)
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT_JSON ")), None)
        if line is None:
            out["error"] = (proc.stdout + proc.stderr)[-2000:]
        else:
            res = json.loads(line[len("RESULT_JSON "):])
            out["total"] = res["total"]
            for i, case in enumerate(res["cases"]):
                name = f"{i + 1:03d} {case['method']} {case['path']} {case['name']}"
                out["tests"][name] = "skip" if case["skipped"] else ("pass" if case["passed"] else "fail")
            out["passed"] = sum(1 for v in out["tests"].values() if v == "pass")
            if res.get("server_error"):
                out["error"] = "server: " + str(res["server_error"])[:1500]
    except subprocess.TimeoutExpired:
        out["error"] = "timeout"
    out["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"passed {out['passed']}/{out['total']} error={out.get('error')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
