#!/usr/bin/env python3
"""
evals.json から eval_metadata.json を生成するスクリプト。

テスト実行前の最初のステップとして実行する。
aggregate_benchmark.py が各 eval ディレクトリに配置された
eval_metadata.json を読むため、このスクリプトで事前生成する。

Usage:
    python3 skills/gen_eval_metadata.py
    python3 skills/gen_eval_metadata.py --skill isdd-requirements
    python3 skills/gen_eval_metadata.py --iteration 2
"""

import argparse
import json
from pathlib import Path


def generate_for_skill(skill_dir: Path, iteration: int) -> None:
    evals_path = skill_dir / "evals" / "evals.json"
    if not evals_path.exists():
        return

    data = json.loads(evals_path.read_text())
    skill_name = data["skill_name"]
    workspace = skill_dir.parent / f"{skill_name}-workspace"
    iter_dir = workspace / f"iteration-{iteration}"

    for e in data["evals"]:
        eval_id = e["id"]
        eval_dir = iter_dir / f"eval-{eval_id}"
        eval_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "eval_id": eval_id,
            "eval_name": e.get("eval_name", f"eval-{eval_id}"),
            "prompt": e["prompt"],
            "assertions": e.get("expectations", []),
        }

        out_path = eval_dir / "eval_metadata.json"
        out_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
        print(f"  Generated: {out_path.relative_to(skill_dir.parent.parent)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate eval_metadata.json from evals.json")
    parser.add_argument("--skill", help="対象スキル名（省略時は全スキル）")
    parser.add_argument("--iteration", type=int, default=1, help="イテレーション番号（デフォルト: 1）")
    args = parser.parse_args()

    skills_dir = Path(__file__).parent
    if args.skill:
        targets = [skills_dir / args.skill]
    else:
        targets = sorted(d for d in skills_dir.iterdir() if d.is_dir() and (d / "evals" / "evals.json").exists())

    for skill_dir in targets:
        print(f"{skill_dir.name}:")
        generate_for_skill(skill_dir, args.iteration)


if __name__ == "__main__":
    main()
