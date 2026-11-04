#!/usr/bin/env python3
"""計測 3（FeatureBench fast、mlflow の課題 4 件を段として積む）の準備・採点。

  python3 measure/featurebench/fb.py prepare  --arm isdd|control --stage N --work <作業の親>
      段 1: イメージの /testbed を <work>/<arm>/ に取り出し（.git と build/ は消す）、git init。isdd 群は .claude/skills/ と ANSWERS.md。
      毎段: 課題のマスク patch（機能のコードを消す）と test_patch（F2P のテストを消す）を当て、REQUEST.md（problem_statement）を置く。
      コンテナ fb-<arm>（作業ディレクトリを /testbed にマウント）を起動し、エージェントは docker exec でテストを回す。
  python3 measure/featurebench/fb.py baseline
      無改変のイメージで各課題の F2P テストを回し、GT の合格数を results/baseline.json に記録する。
  python3 measure/featurebench/fb.py evaluate --arm ... --stage N --work ... [--wall-sec --tokens --tool-uses --note]
      段 1〜N の test_patch を逆適用して F2P テストを戻し、F2P（段ごと）と当段の P2P を回し、元に戻す。results/<arm>/stageN.json と summary.json に書く。
  python3 measure/featurebench/fb.py report
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
IMAGE = PLAN["image"]

REQUEST_HEADER = """# Request (change to the existing code base in this directory)

This directory is the `mlflow` repository (the same tree that the task below calls `/testbed/`). A running Docker container
named `{container}` has this directory mounted at `/testbed` with all dependencies installed; run tests with
`docker exec {container} bash -lc 'cd /testbed && /opt/miniconda3/envs/testbed/bin/python -m pytest <path>'`. Edit the files here (on the host); the container sees them.

"""


def task(name: str) -> dict:
    return json.loads((HERE / "tasks" / f"{name}.json").read_text(encoding="utf-8"))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def git_apply(workdir: Path, diff: str, reverse: bool = False) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".diff", delete=False) as f:
        f.write(diff if diff.endswith("\n") else diff + "\n")
        path = f.name
    cmd = ["git", "apply", "--whitespace=fix"] + (["-R"] if reverse else []) + [path]
    proc = run(cmd, cwd=workdir)
    Path(path).unlink()
    if proc.returncode != 0:
        return proc.stderr[-800:]
    return ""


def workdir_of(args) -> Path:
    return Path(args.work).resolve() / args.arm


def results_dir_of(args) -> Path:
    d = HERE / "results" / args.arm
    d.mkdir(parents=True, exist_ok=True)
    return d


def container_name(arm: str) -> str:
    return f"fb-{arm}"


def prepare(args) -> int:
    names = PLAN["tasks"]
    t = task(names[args.stage - 1])
    workdir = workdir_of(args)
    cname = container_name(args.arm)
    log = {"task": names[args.stage - 1]}
    if args.stage == 1:
        run(["docker", "rm", "-f", cname])
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.parent.mkdir(parents=True, exist_ok=True)
        cid = run(["docker", "create", "--platform", "linux/amd64", IMAGE], check=True).stdout.strip()
        try:
            subprocess.run(["docker", "cp", f"{cid}:/testbed", str(workdir)], check=True, capture_output=True)
        finally:
            run(["docker", "rm", cid])
        for junk in (".git", "build", "dist", ".pytest_cache"):
            shutil.rmtree(workdir / junk, ignore_errors=True)
        for junk in list(workdir.rglob("__pycache__")):
            shutil.rmtree(junk, ignore_errors=True)
        run(["git", "init", "-q"], cwd=workdir)
        if args.arm == "isdd":
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True, exist_ok=True)
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"), dirs_exist_ok=True)
        proc = run(["docker", "run", "-d", "--name", cname, "--platform", "linux/amd64", "-v", f"{workdir}:/testbed", IMAGE, "tail", "-f", "/dev/null"])
        log["container"] = proc.stdout.strip()[:12] or proc.stderr[-300:]
    if args.arm == "isdd":
        shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    log["mask"] = git_apply(workdir, t["patch"]) or "ok"
    # F2P のテストはマスク patch が触っていることがあるので、test_patch ではなくファイルを消す（評価時に test_patch を逆適用して元の内容を戻す）
    for f in t["FAIL_TO_PASS"]:
        if (workdir / f).exists():
            (workdir / f).unlink()
    log["test_removed"] = t["FAIL_TO_PASS"]
    (workdir / "REQUEST.md").write_text(REQUEST_HEADER.format(container=cname) + t["problem_statement"].rstrip() + "\n", encoding="utf-8")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    (results_dir_of(args) / f"prepare-stage{args.stage}.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(workdir)
    print(json.dumps(log, ensure_ascii=False))
    return 0


def run_pytest(mount: Path, files: list, timeout: int = 1800, per_file: int = 900) -> dict:
    """一時コンテナで各テストファイルを回し {ファイル: {テスト: pass|fail|skip}} を返す。"""
    script = ["set +e", "cd /testbed"]
    for i, f in enumerate(files):
        script.append(f"timeout {per_file} /opt/miniconda3/envs/testbed/bin/python -m pytest -p no:cacheprovider -o addopts='' --junitxml=/tmp/j{i}.xml -q '{f}' > /tmp/o{i}.txt 2>&1")
    for i, f in enumerate(files):
        script.append(f"echo '=====JUNIT {i}====='; cat /tmp/j{i}.xml 2>/dev/null; echo; echo '=====TAIL {i}====='; tail -3 /tmp/o{i}.txt")
    cmd = ["docker", "run", "--rm", "-i", "--platform", "linux/amd64", "-v", f"{mount}:/testbed", IMAGE, "bash", "-s"]
    proc = subprocess.run(cmd, input="\n".join(script) + "\n", capture_output=True, text=True, timeout=timeout)
    out = proc.stdout
    result = {}
    for i, f in enumerate(files):
        seg = out.split(f"=====JUNIT {i}=====", 1)[1] if f"=====JUNIT {i}=====" in out else ""
        xml = seg.split(f"=====TAIL {i}=====", 1)[0].strip()
        tail = seg.split(f"=====TAIL {i}=====", 1)[1].split("=====JUNIT", 1)[0].strip() if f"=====TAIL {i}=====" in seg else ""
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
        result[f] = {"tests": tests, "tail": tail[-400:]}
    if not any(r["tests"] for r in result.values()):
        result["_error"] = (out + proc.stderr)[-1500:]
    return result


def baseline(args) -> int:
    with tempfile.TemporaryDirectory(dir="/Volumes/SSD/isdd-measure") as tmp:
        cid = run(["docker", "create", "--platform", "linux/amd64", IMAGE]).stdout.strip()
        subprocess.run(["docker", "cp", f"{cid}:/testbed", f"{tmp}/testbed"], check=True, capture_output=True)
        run(["docker", "rm", cid])
        files = []
        for n in PLAN["tasks"]:
            t = task(n)
            files += t["FAIL_TO_PASS"]
        res = run_pytest(Path(tmp) / "testbed", files)
    out = {}
    for n in PLAN["tasks"]:
        t = task(n)
        out[n] = {f: {"passed": sum(1 for v in res.get(f, {}).get("tests", {}).values() if v == "pass"), "total": len(res.get(f, {}).get("tests", {})), "tests": res.get(f, {}).get("tests", {}), "tail": res.get(f, {}).get("tail", "")} for f in t["FAIL_TO_PASS"]}
    out["_error"] = res.get("_error")
    (HERE / "results" / "baseline.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for n, r in out.items():
        if n != "_error":
            print(n, {f: f"{v['passed']}/{v['total']}" for f, v in r.items()})
    if out["_error"]:
        print("error:", out["_error"][-500:])
    return 0


def evaluate(args) -> int:
    names = PLAN["tasks"][: args.stage]
    tasks = [task(n) for n in names]
    workdir = workdir_of(args)
    results_dir = results_dir_of(args)
    base = json.loads((HERE / "results" / "baseline.json").read_text(encoding="utf-8")) if (HERE / "results" / "baseline.json").exists() else {}
    # 当段の課題の変更ファイルを記録として残す
    snap = results_dir / f"snapshot-stage{args.stage}"
    snap.mkdir(parents=True, exist_ok=True)
    for line in tasks[-1]["patch"].splitlines():
        if line.startswith("diff --git"):
            rel = line.split(" b/")[-1]
            src = workdir / rel
            if src.exists():
                (snap / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, snap / rel)
    for extra in ("docs", ".history", "STAGE_DONE"):
        if (workdir / extra).exists():
            if (workdir / extra).is_dir():
                shutil.copytree(workdir / extra, snap / extra, dirs_exist_ok=True)
            else:
                shutil.copyfile(workdir / extra, snap / extra)
    # F2P テストを戻す（段 1〜N）
    restore_errors = [git_apply(workdir, t["test_patch"], reverse=True) for t in tasks]
    started = time.time()
    f2p_files = [f for t in tasks for f in t["FAIL_TO_PASS"]]
    # P2P（壊してはいけない既存テスト）は 1 ファイル数十分かかるので、--p2p のとき（最終段）だけ、段 1〜N の全課題の P2P を回す
    p2p_files = sorted({f for t in tasks for f in t["PASS_TO_PASS"]}) if args.p2p else []
    try:
        res = run_pytest(workdir, f2p_files + p2p_files, timeout=7200, per_file=1800 if args.p2p else 900)
    finally:
        # テストをまた消す
        for t in tasks:
            for f in t["FAIL_TO_PASS"]:
                if (workdir / f).exists():
                    (workdir / f).unlink()
    per_task = {}
    for n, t in zip(names, tasks):
        files = {}
        for f in t["FAIL_TO_PASS"]:
            r = res.get(f, {"tests": {}, "tail": ""})
            gt = set(k for k, v in base.get(n, {}).get(f, {}).get("tests", {}).items() if v == "pass")
            passed = sum(1 for k, v in r["tests"].items() if v == "pass" and (not gt or k in gt))
            files[f] = {"passed": passed, "gt_passed": len(gt) or None, "total": len(r["tests"]), "tests": r["tests"], "tail": r["tail"]}
        per_task[n] = files
    p2p = {f: {"passed": sum(1 for v in res.get(f, {}).get("tests", {}).values() if v == "pass"), "skipped": sum(1 for v in res.get(f, {}).get("tests", {}).values() if v == "skip"),
               "total": len(res.get(f, {}).get("tests", {})), "tail": res.get(f, {}).get("tail", "")} for f in p2p_files}
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "repo": PLAN["repo"], "stages": {}}
    cur = per_task[names[-1]]
    cur_passed = sum(v["passed"] for v in cur.values()); cur_gt = sum((v["gt_passed"] or 0) for v in cur.values())
    prev_info = summary["stages"].get(str(args.stage - 1))
    regressions = []
    if prev_info:
        prev_tests = {}
        for n, files in prev_info.get("f2p", {}).items():
            for f, v in files.items():
                for k, st in v.get("tests", {}).items():
                    prev_tests[f"{n}|{f}|{k}"] = st
        now_tests = {f"{n}|{f}|{k}": st for n in names[:-1] for f, v in per_task[n].items() for k, st in v["tests"].items()}
        regressions = sorted(k for k, v in prev_tests.items() if v == "pass" and now_tests.get(k) not in (None, "pass"))
    info = {"task": names[-1], "done": (workdir / "STAGE_DONE").exists(), "wall_sec": args.wall_sec, "agent_tokens": args.tokens, "tool_uses": args.tool_uses, "note": args.note,
            "f2p_passed": cur_passed, "f2p_gt": cur_gt, "f2p_rate": round(cur_passed / cur_gt, 4) if cur_gt else None,
            "p2p": p2p, "p2p_all_pass": (all(v["total"] > 0 and v["passed"] + v["skipped"] == v["total"] for v in p2p.values()) if p2p else None),
            "f2p": per_task, "regressions": regressions, "restore_errors": [e for e in restore_errors if e], "eval_sec": round(time.time() - started, 1), "error": res.get("_error")}
    summary["stages"][str(args.stage)] = info
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (results_dir / f"stage{args.stage}.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{args.arm}] stage {args.stage} {names[-1]}: F2P {cur_passed}/{cur_gt} P2P all pass={info['p2p_all_pass']} regressions={regressions} error={bool(res.get('_error'))}")
    return 0


def report(args) -> int:
    print("| 群 | 段 | 課題 | F2P 通過 / GT | P2P 全合格 | 退行 | トークン | ツール | 所要（秒） |")
    print("|---|---|---|---|---|---|---|---|---|")
    for summary in sorted((HERE / "results").glob("*/summary.json")):
        d = json.loads(summary.read_text(encoding="utf-8"))
        for st, info in sorted(d["stages"].items(), key=lambda kv: int(kv[0])):
            print(f"| {d['arm']} | {st} | {info['task'].split('.')[2]} | {info['f2p_passed']}/{info['f2p_gt']} | {info['p2p_all_pass']} | {len(info.get('regressions') or [])} | {info.get('agent_tokens')} | {info.get('tool_uses')} | {info.get('wall_sec')} |")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "baseline", "evaluate", "report"):
        p = sub.add_parser(name)
        if name in ("prepare", "evaluate"):
            p.add_argument("--arm", choices=["isdd", "control"], required=True)
            p.add_argument("--stage", type=int, required=True)
            p.add_argument("--work", required=True)
        if name == "evaluate":
            p.add_argument("--wall-sec", type=float, default=None)
            p.add_argument("--tokens", type=int, default=None)
            p.add_argument("--tool-uses", type=int, default=None)
            p.add_argument("--note", default="")
            p.add_argument("--p2p", action="store_true", help="P2P テストも回す（最終段）")
    args = parser.parse_args()
    return {"prepare": prepare, "baseline": baseline, "evaluate": evaluate, "report": report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
