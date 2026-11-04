#!/usr/bin/env python3
"""計測 1 の採点。アプリ（契約の run.sh を持つディレクトリ）に対して、その段までの隠しテストを回し、結果を JSON に書く。

使用方法:
  python3 measure/score.py --app <アプリのディレクトリ> --stage <1|2|3> --out <結果 JSON> [--python <venv の python>] [--skip-setup]

書くもの: {"stage", "tests": {"test名": "pass|fail|skip"}, "passed", "total", "overbuild": {...}, "duration_sec"}
作りすぎの目安（契約に依存しない数え方）: ソースの公開関数・クラスの数（Python は ast）、HTML テンプレートの数、総行数。
"""

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXCLUDE_DIRS = {".venv", "venv", "node_modules", ".git", "__pycache__", "e2e", "tests", "test", ".claude", "docs",
                ".history", "scripts", "results", "data", "migrations"}
CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".php"}


def count_overbuild(app: Path) -> dict:
    public = classes = files = lines = templates = 0
    for root, dirs, names in os.walk(app):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for n in names:
            p = Path(root) / n
            if p.suffix in (".html", ".htm", ".jinja", ".j2"):
                templates += 1
            if p.suffix not in CODE_EXT or n.startswith("test_") or n.endswith("_test.py"):
                continue
            files += 1
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines += text.count("\n") + 1
            if p.suffix == ".py":
                try:
                    tree = ast.parse(text)
                except SyntaxError:
                    continue
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                        public += 1
                    elif isinstance(node, ast.ClassDef):
                        classes += 1
                        for sub in node.body:
                            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and not sub.name.startswith("_"):
                                public += 1
    return {"source_files": files, "lines": lines, "public_functions": public, "classes": classes, "templates": templates}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True)
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--python", default=str(HERE / ".venv" / "bin" / "python"))
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
    marks = " or ".join(f"stage{i}" for i in range(1, args.stage + 1))
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "junit.xml"
        cmd = [args.python, "-m", "pytest", str(HERE / "hidden"), "-m", marks, "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"]
        try:
            proc = subprocess.run(cmd, cwd=HERE / "hidden", env=env, capture_output=True, text=True, timeout=args.timeout_min * 60)
            result["pytest_tail"] = (proc.stdout + proc.stderr)[-4000:]
        except subprocess.TimeoutExpired as e:
            result["error"] = (result["error"] or "") + f"\npytest timeout ({args.timeout_min} min)"
            result["pytest_tail"] = ((e.stdout or b"").decode(errors="replace") + (e.stderr or b"").decode(errors="replace"))[-4000:]
        if xml.exists():
            root = ET.parse(str(xml)).getroot()
            for tc in root.iter("testcase"):
                status = "pass"
                for child in tc:
                    if child.tag in ("failure", "error"):
                        status = "fail"
                        break
                    if child.tag == "skipped":
                        status = "skip"
                result["tests"][tc.get("name")] = status
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
