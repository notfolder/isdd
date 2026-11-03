#!/usr/bin/env python3
"""計測 1 の実行器。1 群 1 回を段 1〜3 まで通す。段ごとに新しい claude -p（会話は引き継がない）。

使用方法:
  python3 measure/run.py --arm isdd|control --run 1 --model claude-haiku-5-5 --work <作業の親ディレクトリ> [--stages 1,2,3] [--max-rounds 12]

作業ディレクトリ: <work>/<arm>-r<run>（リポジトリの外に置く。リポジトリの CLAUDE.md を読ませないため）
isdd 群: リポジトリの skills/ を .claude/skills/ に入れ、answers.md を ANSWERS.md として置く。
各段: stages/stageN.md を REQUEST.md に置き、contract.md を置く。claude -p を起こし、STAGE_DONE ができるまで
同じセッションを --resume で最大 max-rounds 回続ける（質問や承認待ちで止まったときの続きの指示）。
エージェントの権限は、作業ディレクトリの中で使うツールだけを --allowedTools で明示して許す（無人で回すため）。
段が終わるたびに score.py で採点し、results/<arm>-r<run>/stageN.json と stageN.log（応答の記録）を書く。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ALLOWED_TOOLS = ["Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "LS", "Skill", "Agent", "TodoWrite", "NotebookEdit"]

FIRST_PROMPT_ISDD = """REQUEST.md の依頼を、isdd-spec と isdd-build のスキル（.claude/skills/ にある）を使って、要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください。
ユーザーは不在です。質問や承認が要るときは、ユーザーに聞かずに ANSWERS.md の回答に従って自分で答え、承認はすべて与えられたものとして進めてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id、文言）。必ず守ってください。
{change_note}
完了条件（isdd-build の実装後レビューまで）を満たしたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_CONTROL = """REQUEST.md の依頼を最後まで実装してください。
ユーザーは不在です。不明な点は依頼の文章と contract.md から最も単純な案で決めて進め、質問で止まらないでください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id、文言）。必ず守ってください。
{change_note}
実装が動くことを確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

CHANGE_NOTE = "これは既存のアプリへの変更要求です。前の段までの文書とコードがこのディレクトリにあります。既存の機能を壊さないでください。"
FOLLOW_UP = "続けてください。質問には ANSWERS.md の回答で自分で答え、承認はすべて与えます。残りを最後まで進め、完了したら STAGE_DONE を作ってください。"
FOLLOW_UP_CONTROL = "続けてください。不明な点は最も単純な案で決めて進め、残りを最後まで実装し、完了したら STAGE_DONE を作ってください。"


def run_claude(workdir: Path, prompt: str, model: str, session: str, timeout_min: int) -> dict:
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--permission-mode", "acceptEdits", "--allowedTools", *ALLOWED_TOOLS]
    if session:
        cmd += ["--resume", session]
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout_min * 60)
        out = proc.stdout
    except subprocess.TimeoutExpired as e:
        return {"error": f"timeout {timeout_min} min", "raw": (e.stdout or b"").decode(errors="replace")[-2000:], "wall_sec": time.time() - started}
    data = {}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        idx = out.rfind("\n{")
        if idx >= 0:
            try:
                data = json.loads(out[idx + 1:])
            except json.JSONDecodeError:
                pass
    if not data:
        data = {"error": "no json", "raw": (out + proc.stderr)[-3000:], "returncode": proc.returncode}
    data["wall_sec"] = round(time.time() - started, 1)
    return data


def sum_usage(rounds: list) -> dict:
    total = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    cost = 0.0
    turns = 0
    for r in rounds:
        u = r.get("usage") or {}
        for k in total:
            total[k] += int(u.get(k, 0) or 0)
        cost += float(r.get("total_cost_usd", 0) or 0)
        turns += int(r.get("num_turns", 0) or 0)
    total["total_tokens"] = sum(total.values())
    return {"usage": total, "cost_usd": round(cost, 4), "turns": turns, "rounds": len(rounds)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["isdd", "control"], required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--model", default="claude-haiku-5-5")
    parser.add_argument("--work", required=True)
    parser.add_argument("--stages", default="1,2,3")
    parser.add_argument("--max-rounds", type=int, default=12)
    parser.add_argument("--timeout-min", type=int, default=45, help="claude -p 1 回の上限")
    parser.add_argument("--label", default=None, help="結果ディレクトリの名前（既定 <arm>-r<run>）")
    parser.add_argument("--path-prefix", default=None, help="PATH の先頭に足すディレクトリ（python3 を 3.12 にするなど）")
    args = parser.parse_args()

    if args.path_prefix:
        os.environ["PATH"] = args.path_prefix + os.pathsep + os.environ.get("PATH", "")

    label = args.label or f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / label
    results_dir = HERE / "results" / label
    results_dir.mkdir(parents=True, exist_ok=True)
    stages = [int(s) for s in args.stages.split(",")]

    if 1 in stages:
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=False)
        if args.arm == "isdd":
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True)
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir():
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))
            shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    shutil.copyfile(HERE / "contract.md", workdir / "contract.md")

    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "run": args.run, "model": args.model, "stages": {}}

    for stage in stages:
        shutil.copyfile(HERE / "stages" / f"stage{stage}.md", workdir / "REQUEST.md")
        done_flag = workdir / "STAGE_DONE"
        if done_flag.exists():
            done_flag.unlink()
        template = FIRST_PROMPT_ISDD if args.arm == "isdd" else FIRST_PROMPT_CONTROL
        prompt = template.format(change_note=CHANGE_NOTE if stage > 1 else "")
        follow = FOLLOW_UP if args.arm == "isdd" else FOLLOW_UP_CONTROL
        rounds = []
        session = ""
        log = open(results_dir / f"stage{stage}.log", "w", encoding="utf-8")
        log.write(f"# {label} stage {stage} model {args.model} start {datetime.now().isoformat()}\n")
        stage_started = time.time()
        for i in range(args.max_rounds):
            data = run_claude(workdir, prompt if i == 0 else follow, args.model, session, args.timeout_min)
            rounds.append(data)
            session = data.get("session_id", session)
            log.write(f"\n## round {i + 1} ({data.get('wall_sec')} s, turns={data.get('num_turns')}, error={data.get('error')})\n\n")
            log.write(str(data.get("result", data.get("raw", "")))[:20000] + "\n")
            log.flush()
            if done_flag.exists():
                break
            if data.get("error") and "timeout" in str(data.get("error")):
                break
            if not session:
                break
        wall = round(time.time() - stage_started, 1)
        log.close()
        stage_info = {"done": done_flag.exists(), "wall_sec": wall, **sum_usage(rounds)}
        out_json = results_dir / f"stage{stage}.json"
        subprocess.run([sys.executable, str(HERE / "score.py"), "--app", str(workdir), "--stage", str(stage), "--out", str(out_json)], check=False)
        if out_json.exists():
            score = json.loads(out_json.read_text(encoding="utf-8"))
            stage_info["passed"] = score["passed"]
            stage_info["total"] = score["total"]
            stage_info["tests"] = score["tests"]
            stage_info["overbuild"] = score.get("overbuild")
            stage_info["score_error"] = score.get("error")
            prev = summary["stages"].get(str(stage - 1))
            if prev and prev.get("tests"):
                stage_info["regressions"] = sorted(t for t, v in prev["tests"].items() if v == "pass" and score["tests"].get(t) not in (None, "pass"))
        summary["stages"][str(stage)] = stage_info
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{label}] stage {stage}: done={stage_info['done']} passed={stage_info.get('passed')}/{stage_info.get('total')} "
              f"turns={stage_info['turns']} tokens={stage_info['usage']['total_tokens']} wall={wall}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
