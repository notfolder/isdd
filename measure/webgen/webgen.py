#!/usr/bin/env python3
"""計測 4（WebGen-Bench の 3 課題、新規 → 変更 × 2）の準備・起動・採点。

  python3 measure/webgen/webgen.py prepare --site 000010 --arm isdd|control --stage N --work <作業の親>
  python3 measure/webgen/webgen.py finish  --site ... --arm ... --stage N --work ... --wall-sec S [--tokens N --tool-uses N --note ..]
      → snapshot と記録。
  python3 measure/webgen/webgen.py serve   --site ... --arm ... --stage N --work ...
      → snapshot で setup.sh を実行し、run.sh を背景で起動（空の DATA_DIR）。URL と採点ケースの JSON（results/<site>-<arm>/stageN-cases.json）を出す。
        採点はこの後 Agent ツール（Haiku ＋ Playwright）で行い、verdicts を results/<site>-<arm>/stageN-verdicts.json に書かせる。
  python3 measure/webgen/webgen.py score   --site ... --arm ... --stage N
      → verdicts を読み、サーバーを止め、summary.json に点数（YES=1, PARTIAL=0.5, NO=0）と退行を書く。
  python3 measure/webgen/webgen.py report
"""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
IGNORE = shutil.ignore_patterns(".venv", "venv", "node_modules", "__pycache__", ".git", "data", ".pytest_cache", "results", "dist", ".next")


def workdir_of(args) -> Path:
    return Path(args.work).resolve() / f"{args.site}-{args.arm}"


def results_dir_of(args) -> Path:
    d = HERE / "results" / f"{args.site}-{args.arm}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def prepare(args) -> int:
    workdir = workdir_of(args)
    stage = PLAN["sites"][args.site]["stages"][args.stage - 1]
    if args.stage == 1:
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=False)
        if args.arm == "isdd":
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True)
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))
    if args.arm == "isdd":
        shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    shutil.copyfile(HERE / "contract.md", workdir / "contract.md")
    (workdir / "REQUEST.md").write_text("# Request\n\n" + stage["request"].rstrip() + "\n\nFollow `contract.md` (start-up, PORT, DATA_DIR, language).\n", encoding="utf-8")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    print(workdir)
    return 0


def _summary(results_dir: Path, args):
    p = results_dir / "summary.json"
    s = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"site": args.site, "arm": args.arm, "stages": {}}
    return p, s


def finish(args) -> int:
    workdir = workdir_of(args)
    results_dir = results_dir_of(args)
    snap = results_dir / f"snapshot-stage{args.stage}"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(workdir, snap, ignore=IGNORE)
    p, s = _summary(results_dir, args)
    s["stages"][str(args.stage)] = {"done": (workdir / "STAGE_DONE").exists(), "wall_sec": args.wall_sec, "agent_tokens": args.tokens, "tool_uses": args.tool_uses, "note": args.note}
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{args.site}-{args.arm}] stage {args.stage}: snapshot done={s['stages'][str(args.stage)]['done']}")
    return 0


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def serve(args) -> int:
    results_dir = results_dir_of(args)
    snap = results_dir / f"snapshot-stage{args.stage}"
    app = snap
    env = dict(os.environ)
    env["PATH"] = "/tmp/isdd-measure/bin:" + env["PATH"]
    env.pop("PYTHONPATH", None)
    env.pop("VIRTUAL_ENV", None)
    setup_log = results_dir / f"stage{args.stage}-setup.log"
    if (app / "setup.sh").exists():
        with open(setup_log, "w") as f:
            proc = subprocess.run(["bash", "setup.sh"], cwd=app, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=1200)
        if proc.returncode != 0:
            print(f"setup.sh failed (see {setup_log})")
    port = _free_port()
    data_dir = results_dir / f"stage{args.stage}-data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir()
    env.update({"PORT": str(port), "DATA_DIR": str(data_dir)})
    log = open(results_dir / f"stage{args.stage}-app.log", "w")
    proc = subprocess.Popen(["bash", "run.sh"], cwd=app, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base_url = f"http://127.0.0.1:{port}"
    ok = False
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base_url + "/", timeout=2)
            ok = True
            break
        except Exception:
            if proc.poll() is not None:
                break
            time.sleep(0.5)
    (results_dir / f"stage{args.stage}-server.json").write_text(json.dumps({"pid": proc.pid, "port": port, "base_url": base_url, "started": ok}), encoding="utf-8")
    cases = PLAN["sites"][args.site]["stages"][args.stage - 1]["cases"]
    cases_path = results_dir / f"stage{args.stage}-cases.json"
    cases_path.write_text(json.dumps({"base_url": base_url, "cases": cases}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"base_url": base_url, "started": ok, "cases": str(cases_path), "verdicts": str(results_dir / f"stage{args.stage}-verdicts.json"), "n_cases": len(cases)}))
    return 0 if ok else 1


def stop(args) -> int:
    results_dir = results_dir_of(args)
    sp = results_dir / f"stage{args.stage}-server.json"
    if sp.exists():
        info = json.loads(sp.read_text(encoding="utf-8"))
        try:
            os.killpg(info["pid"], signal.SIGTERM)
        except Exception:
            pass
    return 0


def score(args) -> int:
    results_dir = results_dir_of(args)
    stop(args)
    vp = results_dir / f"stage{args.stage}-verdicts.json"
    verdicts = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else {}
    cases = PLAN["sites"][args.site]["stages"][args.stage - 1]["cases"]
    points = {"YES": 1.0, "PARTIAL": 0.5, "NO": 0.0}
    per = {}
    for c in cases:
        v = verdicts.get(c["id"]) or {}
        verdict = str(v.get("verdict", "NO")).upper()
        per[c["id"]] = {"verdict": verdict if verdict in points else "NO", "reason": v.get("reason", ""), "category": c["category"]}
    total = sum(points[x["verdict"]] for x in per.values())
    p, s = _summary(results_dir, args)
    info = s["stages"].setdefault(str(args.stage), {})
    prev = s["stages"].get(str(args.stage - 1), {}).get("cases", {})
    regressions = sorted(k for k, v in prev.items() if v["verdict"] == "YES" and k in per and per[k]["verdict"] != "YES")
    server = results_dir / f"stage{args.stage}-server.json"
    started = json.loads(server.read_text(encoding="utf-8")).get("started") if server.exists() else None
    info.update({"cases": per, "score": total, "n_cases": len(cases), "accuracy": round(total / len(cases), 3), "regressions": regressions, "started": started,
                 "overbuild": count_overbuild(results_dir / f"snapshot-stage{args.stage}")})
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{args.site}-{args.arm}] stage {args.stage}: {total}/{len(cases)} started={started} regressions={regressions}")
    return 0


def count_overbuild(app: Path) -> dict:
    import ast
    exclude = {".venv", "venv", "node_modules", ".git", "__pycache__", "e2e", "tests", "test", ".claude", "docs", ".history", "scripts", "results", "data", "static", "dist"}
    files = lines = public = 0
    for root, dirs, names in os.walk(app):
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".")]
        for n in names:
            p = Path(root) / n
            if p.suffix not in {".py", ".js", ".ts", ".tsx", ".jsx"} or n.startswith("test_"):
                continue
            files += 1
            text = p.read_text(encoding="utf-8", errors="replace")
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
                        public += sum(1 for sub in node.body if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and not sub.name.startswith("_"))
    return {"source_files": files, "lines": lines, "public_functions": public}


def report(args) -> int:
    print("| 課題・群 | 段 | 点 / ケース | YES / PARTIAL / NO | 退行 | 起動 | トークン | ツール | 所要（秒） | 公開関数 / 行 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for summary in sorted((HERE / "results").glob("*/summary.json")):
        d = json.loads(summary.read_text(encoding="utf-8"))
        for st, info in sorted(d["stages"].items(), key=lambda kv: int(kv[0])):
            cs = info.get("cases", {})
            cnt = {k: sum(1 for v in cs.values() if v["verdict"] == k) for k in ("YES", "PARTIAL", "NO")}
            ob = info.get("overbuild") or {}
            print(f"| {d['site']}-{d['arm']} | {st} | {info.get('score')} / {info.get('n_cases')} | {cnt['YES']} / {cnt['PARTIAL']} / {cnt['NO']} | {len(info.get('regressions') or [])} | "
                  f"{info.get('started')} | {info.get('agent_tokens')} | {info.get('tool_uses')} | {info.get('wall_sec')} | {ob.get('public_functions')} / {ob.get('lines')} |")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "finish", "serve", "stop", "score", "report"):
        p = sub.add_parser(name)
        if name != "report":
            p.add_argument("--site", required=True, choices=list(PLAN["sites"]))
            p.add_argument("--arm", choices=["isdd", "control"], required=True)
            p.add_argument("--stage", type=int, required=True)
        if name in ("prepare", "finish", "serve"):
            p.add_argument("--work", required=True)
        if name == "finish":
            p.add_argument("--wall-sec", type=float, required=True)
            p.add_argument("--tokens", type=int, default=None)
            p.add_argument("--tool-uses", type=int, default=None)
            p.add_argument("--note", default="")
    args = parser.parse_args()
    return {"prepare": prepare, "finish": finish, "serve": serve, "stop": stop, "score": score, "report": report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
