#!/usr/bin/env python3
"""計測 1 の段の準備と記録（実行は Agent ツールなど外で行うときに使う）。

  python3 measure/stage.py prepare --arm isdd|control --run N --stage S --work <作業の親>
      → 作業ディレクトリ <work>/<arm>-r<run> を用意し（段 1 は作り直し）、REQUEST.md・contract.md（contracts/stage1..N.md の累積。isdd 群は .claude/skills/ と answers/stageN.md を ANSWERS.md として）を置き、STAGE_DONE を消す。
  python3 measure/stage.py finish --arm isdd|control --run N --stage S --work <作業の親> --wall-sec <秒> [--tokens N --tool-uses N --note <文>]
      → 作業ディレクトリの snapshot を results/<arm>-r<run>/snapshot-stageS に取り、summary.json に所要時間・トークン・STAGE_DONE の有無を書く。すぐ次の段を始めてよい。
  python3 measure/stage.py score --arm isdd|control --run N --stage S --work <作業の親>
      → snapshot を score.py で採点し（results/.score.lock で他の採点と直列）、summary.json に合格数・退行・作りすぎを書く。背景で回してよい。
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def prepare(args) -> int:
    label = f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / label
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
        shutil.copyfile(HERE / "answers" / f"stage{args.stage}.md", workdir / "ANSWERS.md")
    parts = [(HERE / "contracts" / f"stage{i}.md").read_text(encoding="utf-8").rstrip() for i in range(1, args.stage + 1)]
    (workdir / "contract.md").write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    shutil.copyfile(HERE / "stages" / f"stage{args.stage}.md", workdir / "REQUEST.md")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    print(workdir)
    return 0


def _summary(results_dir: Path, args) -> tuple:
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "run": args.run, "model": args.model, "runner": "Agent tool", "stages": {}}
    return summary_path, summary


def finish(args) -> int:
    """作業ディレクトリの snapshot を取り、段の所要時間・トークン・ツール呼び出し数を summary.json に書く（採点はしない）。"""
    label = f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / label
    results_dir = HERE / "results" / label
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path, summary = _summary(results_dir, args)
    snap = results_dir / f"snapshot-stage{args.stage}"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(workdir, snap, ignore=shutil.ignore_patterns(".venv", "venv", "node_modules", "__pycache__", ".git", "data", ".pytest_cache", "results"))
    info = {"done": (workdir / "STAGE_DONE").exists(), "wall_sec": args.wall_sec, "agent_tokens": args.tokens, "tool_uses": args.tool_uses, "note": args.note}
    summary["stages"][str(args.stage)] = info
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{label}] stage {args.stage}: snapshot 取得 done={info['done']} wall={args.wall_sec}s tokens={args.tokens}")
    return 0


def score(args) -> int:
    """snapshot を採点し、summary.json に合格・退行・作りすぎを書く。results/.score.lock で他の採点と直列にする。"""
    import fcntl
    label = f"{args.arm}-r{args.run}"
    results_dir = HERE / "results" / label
    snap = results_dir / f"snapshot-stage{args.stage}"
    out_json = results_dir / f"stage{args.stage}.json"
    with open(HERE / "results" / ".score.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        subprocess.run([sys.executable, str(HERE / "score.py"), "--app", str(snap), "--stage", str(args.stage), "--out", str(out_json)], check=False)
        fcntl.flock(lock, fcntl.LOCK_UN)
    summary_path, summary = _summary(results_dir, args)
    sc = json.loads(out_json.read_text(encoding="utf-8"))
    info = summary["stages"].setdefault(str(args.stage), {})
    info.update({"passed": sc["passed"], "total": sc["total"], "tests": sc["tests"], "overbuild": sc.get("overbuild"), "score_error": sc.get("error")})
    prev = summary["stages"].get(str(args.stage - 1))
    if prev and prev.get("tests"):
        info["regressions"] = sorted(t for t, v in prev["tests"].items() if v == "pass" and sc["tests"].get(t) not in (None, "pass"))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{label}] stage {args.stage}: passed={info.get('passed')}/{info.get('total')} regressions={info.get('regressions')} error={sc.get('error')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "finish", "score"):
        p = sub.add_parser(name)
        p.add_argument("--arm", choices=["isdd", "control"], required=True)
        p.add_argument("--run", type=int, required=True)
        p.add_argument("--stage", type=int, required=True)
        p.add_argument("--work", required=True)
        p.add_argument("--model", default="claude-haiku-5-5")
        if name == "finish":
            p.add_argument("--wall-sec", type=float, required=True)
            p.add_argument("--tokens", type=int, default=None)
            p.add_argument("--tool-uses", type=int, default=None)
            p.add_argument("--note", default="")
    args = parser.parse_args()
    return {"prepare": prepare, "finish": finish, "score": score}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
