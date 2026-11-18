#!/usr/bin/env python3
"""題材 ripple の準備。お題 1 の段 3 まで終わった回（measure/results/<元の名前>/snapshot-stage3）を作業ディレクトリに戻し、
段 4〜6 を続きとして回せるようにする。

使用方法:
  python3 measure/ripple/prepare.py --from control-r1 --work <作業の親ディレクトリ>
  python3 measure/run.py --task ripple --arm control --run 1 --stages 4,5,6 --label ripple-control-r1 --work <作業の親ディレクトリ> ...

作るもの: <work>/ripple-<元の名前>（snapshot-stage3 の複製、git init 済み）と、measure/results/ripple-<元の名前>/summary.json
（元の回の段 3 の結果を写す。段 4 の退行を数えるため）。
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="source", required=True, help="元の回の名前（例: control-r1、isdd-r2、aidlc-r1）")
    parser.add_argument("--work", required=True)
    parser.add_argument("--refresh-isdd-skills", action="store_true", help="isdd 群の .claude/skills を、今のリポジトリの skills/ に入れ替える")
    args = parser.parse_args()
    snap = RESULTS / args.source / "snapshot-stage3"
    old = json.loads((RESULTS / args.source / "summary.json").read_text(encoding="utf-8"))
    if not snap.is_dir() or "3" not in old["stages"]:
        print(f"{args.source}: 段 3 の snapshot か結果が無い", file=sys.stderr)
        return 1
    label = f"ripple-{args.source}"
    workdir = Path(args.work).resolve() / label
    if workdir.exists():
        shutil.rmtree(workdir)
    shutil.copytree(snap, workdir, symlinks=True, ignore=shutil.ignore_patterns(".venv", "__pycache__", "STAGE_DONE"))
    subprocess.run(["git", "init", "-q"], cwd=workdir, check=False)
    skills_version = None
    if args.refresh_isdd_skills:
        dest = workdir / ".claude" / "skills"
        if not dest.is_dir():
            print(f"{args.source}: .claude/skills が無い（isdd 群ではない）", file=sys.stderr)
            return 1
        shutil.rmtree(dest)
        dest.mkdir()
        for skill in (HERE.parent.parent / "skills").iterdir():
            if skill.is_dir() and not skill.name.endswith("-workspace"):
                shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))
        for line in (dest / "isdd-spec" / "SKILL.md").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version:"):
                skills_version = line.split(":", 1)[1].strip().strip('"')
                break
    out = RESULTS / label
    out.mkdir(parents=True, exist_ok=True)
    summary = {"arm": old["arm"], "run": old["run"], "model": old.get("model"), "continued_from": args.source, "isdd_skills_refreshed_to": skills_version,
               "stages": {"3": old["stages"]["3"]}}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{label}: {workdir} を用意した（元の段 3: {old['stages']['3'].get('passed')}/{old['stages']['3'].get('total')}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
