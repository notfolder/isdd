#!/usr/bin/env python3
"""計測 1 の実行器。1 群 1 回を段 1〜3 まで通す。段ごとに新しい claude -p（会話は引き継がない）。

使用方法:
  python3 measure/run.py --arm isdd|control --run 1 --model claude-haiku-5-5 --work <作業の親ディレクトリ> [--stages 1,2,3] [--max-rounds 12]

作業ディレクトリ: <work>/<arm>-r<run>（リポジトリの外に置く。リポジトリの CLAUDE.md を読ませないため）
isdd 群: リポジトリの skills/ を .claude/skills/ に入れ、段ごとの answers/stageN.md を ANSWERS.md として置く。
各段: stages/stageN.md を REQUEST.md に、contracts/stage1..N.md をつないだものを contract.md に置く（段 N の契約は段 1〜N の累積）。
claude -p を起こし（依頼は標準入力、--permission-mode acceptEdits、--allowedTools で作業に使うツールを列挙、
--setting-sources project でユーザーグローバルの設定とスキルを読ませない）、STAGE_DONE ができるまで同じセッションを
--resume で最大 max-rounds 回続ける（質問や承認待ちで止まったときの続きの指示）。
段が終わるたびに作業ディレクトリの snapshot を results/<arm>-r<run>/snapshot-stageN に取り、次の段をすぐ始める。
採点（score.py、Playwright）は snapshot に対して別スレッドで行い、複数の実行器が同時に採点しないよう
results/.score.lock で直列にする（性能のテストが互いの負荷で落ちないため）。
すべての段が終わったら results/<arm>-r<run>/summary.json に、段ごとの合格・退行・作りすぎ・トークン・往復数・所要時間を書く。
"""

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from agentrun import ISDD_SKILLS, RESPONDER_PROMPT, ask_responder, run_claude, run_claude_retry  # noqa: E402
SNAPSHOT_IGNORE = shutil.ignore_patterns(".venv", "venv", "node_modules", "__pycache__", ".git", "data", ".pytest_cache", "results")

FIRST_PROMPT_ISDD = """REQUEST.md の依頼を、isdd-spec と isdd-build のスキル（.claude/skills/ にある）を使って、要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください。
他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。質問や承認が要るときは、ユーザーに聞かずに ANSWERS.md の回答に従って自分で答え、承認はすべて与えられたものとして進めてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id、文言）。必ず守ってください。
{change_note}
完了条件（isdd-build の実装後レビューまで）を満たしたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_CONTROL = """REQUEST.md の依頼を最後まで実装してください。Skill ツールは使わないでください。
他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。不明な点は依頼の文章と contract.md から最も単純な案で決めて進め、質問で止まらないでください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id、文言）。必ず守ってください。
{change_note}
実装が動くことを確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_ISDD_Q = """REQUEST.md の依頼を、isdd-spec と isdd-build のスキル（.claude/skills/ にある）を使って、要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください。
他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことや承認が要ることは、応答の中で依頼者に質問してください（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最小案で決め、要件定義書の「依頼に無く自分で決めた項目」に書いてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id とクラス名）。必ず守ってください。
完了条件（isdd-build の実装後レビューまで）を満たしたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_CONTROL_Q = """REQUEST.md の依頼を最後まで実装してください。Skill ツールは使わないでください。
他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことは、応答の中で依頼者に質問してよいです（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最も単純な案で決めてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id とクラス名）。必ず守ってください。
実装が動くことを確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

CHANGE_NOTE = "これは既存のアプリへの変更要求です。前の段までの文書とコードがこのディレクトリにあります。既存の機能を壊さないでください。"
FOLLOW_UP = "続けてください。質問には ANSWERS.md の回答で自分で答え、承認はすべて与えます。残りを最後まで進め、完了したら STAGE_DONE を作ってください。"
FOLLOW_UP_CONTROL = "続けてください。不明な点は最も単純な案で決めて進め、残りを最後まで実装し、完了したら STAGE_DONE を作ってください。"


def log(label: str, msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{label}] {msg}", flush=True)


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


def write_contract(workdir: Path, stage: int) -> None:
    (workdir / "contract.md").write_text((HERE / "contracts" / f"stage{stage}.md").read_text(encoding="utf-8"), encoding="utf-8")


def score_snapshot(label: str, stage: int, snap: Path, out_json: Path, lock_path: Path) -> None:
    with open(lock_path, "w") as lock:
        log(label, f"stage {stage}: 採点の順番待ち")
        fcntl.flock(lock, fcntl.LOCK_EX)
        log(label, f"stage {stage}: 採点を開始")
        started = time.time()
        subprocess.run([sys.executable, str(HERE / "score.py"), "--app", str(snap), "--stage", str(stage), "--out", str(out_json)],
                       check=False, capture_output=True)
        log(label, f"stage {stage}: 採点を終了（{round(time.time() - started)} 秒）")
        fcntl.flock(lock, fcntl.LOCK_UN)


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
    parser.add_argument("--responder", default=None, help="依頼者役の隠し台帳（計測 5）。指定すると固定回答の代わりに、台帳を持つ依頼者役のモデルが質問に答える")
    parser.add_argument("--responder-model", default="claude-sonnet-5-5")
    parser.add_argument("--contract", default=None, help="契約ファイルの名前（既定 contracts/stage<N>.md。計測 5 は stage1-min.md）")
    args = parser.parse_args()

    if args.path_prefix:
        os.environ["PATH"] = args.path_prefix + os.pathsep + os.environ.get("PATH", "")

    label = args.label or f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / label
    results_dir = HERE / "results" / label
    results_dir.mkdir(parents=True, exist_ok=True)
    lock_path = HERE / "results" / ".score.lock"
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
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))

    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "run": args.run, "model": args.model, "stages": {}}
    if all(str(st) in summary["stages"] and summary["stages"][str(st)].get("passed") is not None for st in stages):
        log(label, "採点済みのため何もしない")
        return 0
    summary["runner"] = "claude -p"
    scorers = []

    for stage in stages:
        shutil.copyfile(HERE / "stages" / f"stage{stage}.md", workdir / "REQUEST.md")
        if args.contract:
            (workdir / "contract.md").write_text((HERE / "contracts" / args.contract).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_contract(workdir, stage)
        if args.arm == "isdd" and not args.responder:
            shutil.copyfile(HERE / "answers" / f"stage{stage}.md", workdir / "ANSWERS.md")
        done_flag = workdir / "STAGE_DONE"
        if done_flag.exists():
            done_flag.unlink()
        if args.responder:
            prompt = FIRST_PROMPT_ISDD_Q if args.arm == "isdd" else FIRST_PROMPT_CONTROL_Q
            ledger_text = (HERE / args.responder).read_text(encoding="utf-8") if not Path(args.responder).is_absolute() else Path(args.responder).read_text(encoding="utf-8")
        else:
            template = FIRST_PROMPT_ISDD if args.arm == "isdd" else FIRST_PROMPT_CONTROL
            prompt = template.format(change_note=CHANGE_NOTE if stage > 1 else "")
        follow = FOLLOW_UP if args.arm == "isdd" else FOLLOW_UP_CONTROL
        questions_asked = 0
        rounds = []
        session = ""
        log_file = open(results_dir / f"stage{stage}.log", "w", encoding="utf-8")
        log_file.write(f"# {label} stage {stage} model {args.model} start {datetime.now().isoformat()}\n")
        stage_started = time.time()
        log(label, f"stage {stage}: 開始")
        for i in range(args.max_rounds):
            if i > 0 and args.responder:
                last = (rounds[-1].get("texts") or [rounds[-1].get("result") or ""])[-1]
                answer = ask_responder(ledger_text, last, args.responder_model, workdir)
                if "?" in last or "？" in last or "教えてください" in last or "どちら" in last:
                    questions_asked += 1
                log_file.write(f"\n### 依頼者役の答え {i}\n\n{answer[:4000]}\n")
                follow = answer
            data = run_claude_retry(workdir, prompt if i == 0 else follow, args.model, session, args.timeout_min)
            rounds.append(data)
            session = data.get("session_id", session)
            log_file.write(f"\n## round {i + 1} ({data.get('wall_sec')} s, turns={data.get('num_turns')}, error={data.get('error')}, is_error={data.get('is_error')})\n\n")
            log_file.write(str(data.get("result", data.get("raw", "")))[:20000] + "\n")
            log_file.flush()
            log(label, f"stage {stage}: round {i + 1} 終了（{data.get('wall_sec')} 秒、turns={data.get('num_turns')}、tools={data.get('tool_uses')}、skills={data.get('skills_called')}、done={done_flag.exists()}）")
            log_file.write(f"skills_visible={data.get('skills_visible')} tool_names={data.get('tool_names')}\n")
            if done_flag.exists():
                break
            if data.get("error") and "timeout" in str(data.get("error")):
                break
            if not session:
                break
        wall = round(time.time() - stage_started, 1)
        log_file.close()
        snap = results_dir / f"snapshot-stage{stage}"
        if snap.exists():
            shutil.rmtree(snap)
        shutil.copytree(workdir, snap, ignore=SNAPSHOT_IGNORE)
        skills_called = [sk for r in rounds for sk in r.get("skills_called", [])]
        visible = sorted({sk for r in rounds for sk in (r.get("skills_visible") or [])})
        tool_names = {}
        for r in rounds:
            for k, v in (r.get("tool_names") or {}).items():
                tool_names[k] = tool_names.get(k, 0) + v
        isdd_used = any(sk in ISDD_SKILLS for sk in skills_called)
        artifacts = all((workdir / f).exists() for f in ("docs/requirements.md", "docs/detail_design.md", "docs/trace_map.md", "scripts/isdd"))
        valid = ((isdd_used or artifacts) if args.arm == "isdd" else not visible and not isdd_used)
        stage_info = {"done": done_flag.exists(), "wall_sec": wall, "started": datetime.fromtimestamp(stage_started).isoformat(timespec="seconds"),
                      "responder": bool(args.responder), "questions_rounds": questions_asked,
                      "tool_uses": sum(tool_names.values()), "tool_names": tool_names, "skills_called": skills_called, "isdd_skills_visible": visible,
                      "valid": valid, "isdd_artifacts": artifacts, "validity_note": ("isdd の成果物もスキル呼び出しも無し" if args.arm == "isdd" and not (isdd_used or artifacts) else
                                                       ("対照群に isdd のスキルが見えていた" if args.arm == "control" and (visible or isdd_used) else "")),
                      **sum_usage(rounds)}
        summary["stages"][str(stage)] = stage_info
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        t = threading.Thread(target=score_snapshot, args=(label, stage, snap, results_dir / f"stage{stage}.json", lock_path))
        t.start()
        scorers.append((stage, t))

    for stage, t in scorers:
        t.join()
    for stage in stages:
        out_json = results_dir / f"stage{stage}.json"
        info = summary["stages"][str(stage)]
        if out_json.exists():
            score = json.loads(out_json.read_text(encoding="utf-8"))
            info.update({"passed": score["passed"], "total": score["total"], "tests": score["tests"], "overbuild": score.get("overbuild"), "score_error": score.get("error")})
            prev = summary["stages"].get(str(stage - 1))
            if prev and prev.get("tests"):
                info["regressions"] = sorted(t for t, v in prev["tests"].items() if v == "pass" and score["tests"].get(t) not in (None, "pass"))
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        log(label, f"stage {stage}: done={info['done']} valid={info.get('valid')} passed={info.get('passed')}/{info.get('total')} regressions={info.get('regressions')} "
                   f"turns={info['turns']} tools={info.get('tool_uses')} skills={info.get('skills_called')} tokens={info['usage']['total_tokens']} wall={info['wall_sec']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
