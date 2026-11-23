#!/usr/bin/env python3
"""計測 1 の採点。アプリ（契約の run.sh を持つディレクトリ）に対して、その段までの隠しテストを回し、結果を JSON に書く。

使用方法:
  python3 measure/score.py --app <アプリのディレクトリ> --stage <1|2|3> --out <結果 JSON> [--python <venv の python>] [--skip-setup]

書くもの: {"stage", "tests": {"test名": "pass|fail|skip"}, "passed", "total", "overbuild": {...}, "duration_sec"} と、
採点できたかの項目（scoring_status、unscored_reasons、expected_total、not_run。scoring.py の説明を参照）。
作りすぎの目安（契約に依存しない数え方）: ソースの公開関数・クラスの数（Python は ast）、HTML テンプレートの数、総行数。
"""

import argparse
import ast
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scoring import finalize, new_result, run_hidden  # noqa: E402
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
    result = new_result(args.stage, app)
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
    run_hidden(args.python, HERE / "hidden", " or ".join(f"stage{i}" for i in range(1, args.stage + 1)), env, args.timeout_min, result)
    finalize(result)
    result["overbuild"] = count_overbuild(app)
    result["duration_sec"] = round(time.time() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"stage {args.stage}: {result['passed']}/{result['total']} passed, {result['scoring_status']} {result['unscored_reasons']}, overbuild={result['overbuild']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
