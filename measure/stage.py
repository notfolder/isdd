#!/usr/bin/env python3
"""計測 1 の段の準備と記録（実行は Agent ツールなど外で行うときに使う）。

  python3 measure/stage.py prepare --arm isdd|control --run N --stage S --work <作業の親>
      → 作業ディレクトリ <work>/<arm>-r<run> を用意し（段 1 は作り直し）、REQUEST.md・contract.md（isdd 群は .claude/skills/ と ANSWERS.md も）を置き、STAGE_DONE を消す。
  python3 measure/stage.py finish --arm isdd|control --run N --stage S --work <作業の親> --wall-sec <秒> [--note <文>]
      → score.py で採点し、results/<arm>-r<run>/summary.json に段の結果（合格数、退行、作りすぎ、所要時間、STAGE_DONE の有無）を書く。
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
            shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    shutil.copyfile(HERE / "contract.md", workdir / "contract.md")
    shutil.copyfile(HERE / "stages" / f"stage{args.stage}.md", workdir / "REQUEST.md")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    print(workdir)
    return 0


def finish(args) -> int:
    label = f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / label
    results_dir = HERE / "results" / label
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "run": args.run, "model": args.model, "stages": {}}
    snap = results_dir / f"snapshot-stage{args.stage}"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(workdir, snap, ignore=shutil.ignore_patterns(".venv", "venv", "node_modules", "__pycache__", ".git", "data", ".pytest_cache", "results"))
    out_json = results_dir / f"stage{args.stage}.json"
    subprocess.run([sys.executable, str(HERE / "score.py"), "--app", str(workdir), "--stage", str(args.stage), "--out", str(out_json)], check=False)
    info = {"done": (workdir / "STAGE_DONE").exists(), "wall_sec": args.wall_sec, "note": args.note}
    if out_json.exists():
        score = json.loads(out_json.read_text(encoding="utf-8"))
        info.update({"passed": score["passed"], "total": score["total"], "tests": score["tests"], "overbuild": score.get("overbuild"), "score_error": score.get("error")})
        prev = summary["stages"].get(str(args.stage - 1))
        if prev and prev.get("tests"):
            info["regressions"] = sorted(t for t, v in prev["tests"].items() if v == "pass" and score["tests"].get(t) not in (None, "pass"))
    summary["stages"][str(args.stage)] = info
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{label}] stage {args.stage}: done={info['done']} passed={info.get('passed')}/{info.get('total')} regressions={info.get('regressions')} wall={args.wall_sec}s")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "finish"):
        p = sub.add_parser(name)
        p.add_argument("--arm", choices=["isdd", "control"], required=True)
        p.add_argument("--run", type=int, required=True)
        p.add_argument("--stage", type=int, required=True)
        p.add_argument("--work", required=True)
        p.add_argument("--model", default="claude-haiku-5-5")
        if name == "finish":
            p.add_argument("--wall-sec", type=float, required=True)
            p.add_argument("--note", default="")
    args = parser.parse_args()
    return prepare(args) if args.cmd == "prepare" else finish(args)


if __name__ == "__main__":
    sys.exit(main())
