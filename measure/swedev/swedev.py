#!/usr/bin/env python3
"""計測 2（SWE-Dev easy）の準備・採点。1 パッケージを 1 つの作業ディレクトリとし、課題を段として順に積む。

  python3 measure/swedev/swedev.py prepare  --pkg <pkg> --arm isdd|control --stage N --work <作業の親>
      段 1: Docker イメージの /app/<pkg> を <work>/<pkg>-<arm>/ に取り出して git init（isdd 群は .claude/skills/ と ANSWERS.md も）。
      毎段: 課題の対象関数（GT と file_code の差）を作業ディレクトリの今のファイルから AST で消し、課題のテストファイルを消し、REQUEST.md（PRD）を置く。
  python3 measure/swedev/swedev.py baseline --pkg <pkg>
      各課題の隠しテストを無改変のイメージで回し、GT の合格数を results/baseline-<pkg>.json に記録する。
  python3 measure/swedev/swedev.py evaluate --pkg <pkg> --arm isdd|control --stage N --work <作業の親> [--wall-sec --tokens --tool-uses]
      作業ディレクトリの src_dir をコンテナにマウントし、段 1〜N の課題のテストを回す（前の段の課題は退行の検出）。
      results/<pkg>-<arm>/stageN.json と summary.json に書く。snapshot も取る。
  python3 measure/swedev/swedev.py report
"""

import argparse
import ast
import base64
import json
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
IMAGE = "dorothyduuu/swe-dev:{pkg}-image"
DOCKER = ["docker", "run", "--rm", "-i", "--platform", "linux/amd64"]

REQUEST_HEADER = """# Request (change to the existing code in this directory)

The functions and methods listed in the PRD below have been removed from the existing code base in this directory
(their docstrings and signatures are given in the PRD). Implement them so that they work with the rest of the code base.
Keep the existing behavior of everything else. The hidden acceptance tests are the project's own unit tests for this feature,
run with `python -m pytest` inside the package's test directory.

"""


def task(name: str) -> dict:
    return json.loads((HERE / "tasks" / f"{name}.json").read_text(encoding="utf-8"))


def qualified_defs(src: str) -> dict:
    """{修飾名: (開始行, 終了行)}。トップレベル関数・クラス、クラス直下のメソッド。開始行はデコレータを含む。"""
    out = {}
    tree = ast.parse(src)
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([d.lineno for d in n.decorator_list] + [n.lineno])
            out[n.name] = (start, n.end_lineno)
        elif isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = min([d.lineno for d in m.decorator_list] + [m.lineno])
                    out[f"{n.name}.{m.name}"] = (start, m.end_lineno)
    return out


def removed_defs(t: dict) -> dict:
    """課題で消された定義 {ファイル: [修飾名]}（GT と file_code の差）。"""
    out = {}
    for path, code in t["file_code"].items():
        gt = set(qualified_defs(t["GT_file_code"][path]))
        now = set(qualified_defs(code))
        out[path] = sorted(gt - now)
    return out


def remove_from_file(path: Path, names: list) -> dict:
    """ファイルから修飾名の定義を消す（本体ごと）。クラスの中身が空になれば pass を入れる。"""
    src = path.read_text(encoding="utf-8")
    defs = qualified_defs(src)
    lines = src.splitlines(keepends=True)
    missing = [n for n in names if n not in defs]
    ranges = sorted([defs[n] for n in names if n in defs], reverse=True)
    for start, end in ranges:
        del lines[start - 1:end]
    new_src = "".join(lines)
    # 空になったクラスを補う
    try:
        tree = ast.parse(new_src)
    except SyntaxError:
        fixed = []
        for i, line in enumerate(lines):
            fixed.append(line)
            if line.lstrip().startswith("class ") and line.rstrip().endswith(":"):
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                indent = len(line) - len(line.lstrip())
                if not nxt.strip() or (len(nxt) - len(nxt.lstrip())) <= indent:
                    fixed.append(" " * (indent + 4) + "pass\n")
        new_src = "".join(fixed)
        ast.parse(new_src)
    path.write_text(new_src, encoding="utf-8")
    return {"removed": [n for n in names if n in defs], "missing": missing}


def workdir_of(args) -> Path:
    return Path(args.work).resolve() / f"{args.pkg}-{args.arm}"


def results_dir_of(args) -> Path:
    d = HERE / "results" / f"{args.pkg}-{args.arm}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def prepare(args) -> int:
    names = PLAN["packages"][args.pkg]
    t = task(names[args.stage - 1])
    workdir = workdir_of(args)
    if args.stage == 1:
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.parent.mkdir(parents=True, exist_ok=True)
        cid = subprocess.run(["docker", "create", "--platform", "linux/amd64", IMAGE.format(pkg=args.pkg)], capture_output=True, text=True, check=True).stdout.strip()
        try:
            subprocess.run(["docker", "cp", f"{cid}:{t['dir_path']}", str(workdir)], check=True, capture_output=True)
        finally:
            subprocess.run(["docker", "rm", cid], capture_output=True)
        shutil.rmtree(workdir / ".git", ignore_errors=True)
        # 正解のソースと隠しテストの複製（build/lib、egg-info、modified_testcases、バイトコード）を消す
        for junk in ("build", "dist", ".tox", ".eggs", "modified_testcases", ".pytest_cache"):
            shutil.rmtree(workdir / junk, ignore_errors=True)
        for junk in list(workdir.rglob("*.egg-info")) + list(workdir.rglob("__pycache__")):
            shutil.rmtree(junk, ignore_errors=True)
        for junk in list(workdir.rglob("*.pyc")):
            junk.unlink()
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=False)
        if args.arm == "isdd":
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True)
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))
    if args.arm == "isdd":
        shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    log = {"task": names[args.stage - 1], "files": {}}
    for path, defs in removed_defs(t).items():
        p = workdir / path
        if not defs:
            continue
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(t["file_code"][path], encoding="utf-8")
            log["files"][path] = {"written_file_code": True}
            continue
        log["files"][path] = remove_from_file(p, defs)
    test_path = workdir / t["test_file"]
    if test_path.exists():
        test_path.unlink()
        log["test_removed"] = t["test_file"]
    (workdir / "REQUEST.md").write_text(REQUEST_HEADER + t["PRD"].rstrip() + "\n", encoding="utf-8")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    (results_dir_of(args) / f"prepare-stage{args.stage}.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(workdir)
    print(json.dumps(log, ensure_ascii=False))
    return 0


def run_tests(pkg: str, tasks: list, mount, timeout: int = 900) -> dict:
    """コンテナで課題のテストを回し、{課題名: {テスト名: pass|fail}} を返す。"""
    t0 = tasks[0]
    script = ["set +e"]
    for t in tasks:
        tf = f"{t['dir_path']}/{t['test_file']}"
        script.append(f"mkdir -p \"$(dirname '{tf}')\"")
        script.append(f"printf '%s' '{base64.b64encode(t['test_code'].encode()).decode()}' | base64 -d > '{tf}'")
    script.append(f"cd '{t0['dir_path']}'")
    for i, t in enumerate(tasks):
        script.append(f"python -m pytest -v -p no:cacheprovider --junitxml=/tmp/junit{i}.xml '{t['test_file']}' > /tmp/out{i}.txt 2>&1")
    for i, _ in enumerate(tasks):
        script.append(f"echo '=====JUNIT {i}====='; cat /tmp/junit{i}.xml 2>/dev/null; echo; echo '=====TAIL {i}====='; tail -5 /tmp/out{i}.txt")
    cmd = list(DOCKER)
    if mount is not None:
        src = (mount / t0["src_dir"]).resolve()
        cmd += ["-v", f"{src}:{t0['dir_path']}/{t0['src_dir'].rstrip('/')}"]
    cmd.append(IMAGE.format(pkg=pkg))
    cmd += ["sh", "-s"]
    proc = subprocess.run(cmd, input="\n".join(script) + "\n", capture_output=True, text=True, timeout=timeout)
    out = proc.stdout
    result = {}
    for i, t in enumerate(tasks):
        marker = f"=====JUNIT {i}====="
        tail_marker = f"=====TAIL {i}====="
        seg = out.split(marker, 1)[1].split(tail_marker, 1) if marker in out else ["", ""]
        xml, tail = seg[0].strip(), (seg[1].split("=====JUNIT", 1)[0].strip() if len(seg) > 1 else "")
        tests = {}
        if xml.startswith("<"):
            try:
                root = ET.fromstring(xml)
                for tc in root.iter("testcase"):
                    status = "pass"
                    for child in tc:
                        if child.tag in ("failure", "error"):
                            status = "fail"
                            break
                        if child.tag == "skipped":
                            status = "skip"
                    tests[f"{tc.get('classname')}::{tc.get('name')}"] = status
            except ET.ParseError:
                pass
        result[t["sample_name"]] = {"tests": tests, "tail": tail[-600:]}
    if not result or proc.returncode not in (0, 1) and not any(r["tests"] for r in result.values()):
        result["_error"] = (out + proc.stderr)[-2000:]
    return result


def baseline(args) -> int:
    names = PLAN["packages"][args.pkg]
    tasks = [task(n) for n in names]
    res = run_tests(args.pkg, tasks, None)
    out = {n: {"passed": sum(1 for v in r["tests"].values() if v == "pass"), "total": len(r["tests"]), "tests": r["tests"], "tail": r["tail"]}
           for n, r in zip(names, [res[t["sample_name"]] for t in tasks])}
    (HERE / "results" / f"baseline-{args.pkg}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for n, r in out.items():
        print(f"{n}: GT {r['passed']}/{r['total']}")
    return 0


def evaluate(args) -> int:
    names = PLAN["packages"][args.pkg][: args.stage]
    tasks = [task(n) for n in names]
    workdir = workdir_of(args)
    results_dir = results_dir_of(args)
    snap = results_dir / f"snapshot-stage{args.stage}"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(workdir, snap, ignore=shutil.ignore_patterns(".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache", "*.egg-info", "build"))
    base_path = HERE / "results" / f"baseline-{args.pkg}.json"
    base = json.loads(base_path.read_text(encoding="utf-8")) if base_path.exists() else {}
    started = time.time()
    res = run_tests(args.pkg, tasks, workdir)
    per_task = {}
    for n, t in zip(names, tasks):
        r = res.get(t["sample_name"], {"tests": {}, "tail": ""})
        gt = base.get(n, {})
        gt_pass = {k for k, v in gt.get("tests", {}).items() if v == "pass"}
        passed = sum(1 for k, v in r["tests"].items() if v == "pass" and (not gt_pass or k in gt_pass))
        per_task[n] = {"passed": passed, "gt_passed": len(gt_pass) or None, "total": len(r["tests"]), "tests": r["tests"], "tail": r["tail"],
                       "rate": round(passed / len(gt_pass), 4) if gt_pass else None}
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"pkg": args.pkg, "arm": args.arm, "stages": {}}
    info = {"task": names[-1], "done": (workdir / "STAGE_DONE").exists(), "wall_sec": args.wall_sec, "agent_tokens": args.tokens, "tool_uses": args.tool_uses,
            "note": args.note, "current": per_task[names[-1]], "previous": {n: per_task[n] for n in names[:-1]}, "eval_sec": round(time.time() - started, 1),
            "error": res.get("_error")}
    prev = summary["stages"].get(str(args.stage - 1))
    regressions = []
    if prev:
        prev_tests = dict(prev.get("current", {}).get("tests", {}))
        for n, p in prev.get("previous", {}).items():
            prev_tests.update({f"{n}|{k}": v for k, v in p.get("tests", {}).items()})
        prev_tests = {(k if "|" in k else f"{prev['task']}|{k}"): v for k, v in prev_tests.items()}
        now_tests = {f"{n}|{k}": v for n in names[:-1] for k, v in per_task[n]["tests"].items()}
        regressions = sorted(k for k, v in prev_tests.items() if v == "pass" and now_tests.get(k) not in (None, "pass"))
    info["regressions"] = regressions
    info["overbuild"] = count_overbuild(workdir / tasks[0]["src_dir"])
    summary["stages"][str(args.stage)] = info
    (results_dir / f"stage{args.stage}.json").write_text(json.dumps(per_task, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    cur = per_task[names[-1]]
    print(f"[{args.pkg}-{args.arm}] stage {args.stage} {names[-1]}: {cur['passed']}/{cur['gt_passed']} regressions={regressions} error={bool(res.get('_error'))}")
    return 0


def count_overbuild(src: Path) -> dict:
    public = lines = files = 0
    for p in src.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        files += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        lines += text.count("\n") + 1
        try:
            public += sum(1 for n in qualified_defs(text) if not n.split(".")[-1].startswith("_"))
        except SyntaxError:
            pass
    return {"source_files": files, "lines": lines, "public_functions": public}


def report(args) -> int:
    print("| パッケージ・群 | 段 | 課題 | 通過（/GT） | 退行 | トークン | ツール | 所要（秒） | 公開関数 / 行 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for summary in sorted((HERE / "results").glob("*/summary.json")):
        d = json.loads(summary.read_text(encoding="utf-8"))
        for st, info in sorted(d["stages"].items(), key=lambda kv: int(kv[0])):
            c = info["current"]
            ob = info.get("overbuild") or {}
            print(f"| {d['pkg']}-{d['arm']} | {st} | {info['task'].split('-test_')[-1] if '-test_' in info['task'] else info['task']} | {c['passed']}/{c['gt_passed']} | "
                  f"{len(info.get('regressions') or [])} | {info.get('agent_tokens')} | {info.get('tool_uses')} | {info.get('wall_sec')} | {ob.get('public_functions')} / {ob.get('lines')} |")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "baseline", "evaluate", "report"):
        p = sub.add_parser(name)
        if name != "report":
            p.add_argument("--pkg", required=True, choices=list(PLAN["packages"]))
        if name in ("prepare", "evaluate"):
            p.add_argument("--arm", choices=["isdd", "control"], required=True)
            p.add_argument("--stage", type=int, required=True)
            p.add_argument("--work", required=True)
        if name == "evaluate":
            p.add_argument("--wall-sec", type=float, default=None)
            p.add_argument("--tokens", type=int, default=None)
            p.add_argument("--tool-uses", type=int, default=None)
            p.add_argument("--note", default="")
    args = parser.parse_args()
    return {"prepare": prepare, "baseline": baseline, "evaluate": evaluate, "report": report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
