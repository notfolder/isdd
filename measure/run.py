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

FIRST_PROMPT_AIDLC = """/aidlc {scope} REQUEST.md の依頼を、AI-DLC のワークフローで最後まで（要件 → 設計 → 実装 → テスト）進めてください。
他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は画面の選択肢を使えません。質問は ANSWERS.md に依頼者の回答があるので、それを依頼者の答えとして使い、ANSWERS.md に無いことは依頼の文章と contract.md から最も単純な案を依頼者の答えとしてください。回答方法を聞く場面では「Chat」を選んだものとします。承認が要るところでは止まって承認を求めてください（依頼者が次の発言で答えます）。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id、文言）。必ず守ってください。アプリのコードはこの作業ディレクトリの直下に置いてください。
{change_note}
ワークフローの最後の段階が承認されたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_ISDD_Q = """REQUEST.md の依頼を、isdd-spec と isdd-build のスキル（.claude/skills/ にある）を使って、要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください。
他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことや承認が要ることは、応答の中で依頼者に質問してください（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最小案で決め、要件定義書の「依頼に無く自分で決めた項目」に書いてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id とクラス名）。必ず守ってください。
完了条件（isdd-build の実装後レビューまで）を満たしたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_CONTROL_Q = """REQUEST.md の依頼を最後まで実装してください。Skill ツールは使わないでください。
他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことは、応答の中で依頼者に質問してよいです（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最も単純な案で決めてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id とクラス名）。必ず守ってください。
実装が動くことを確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"""

FIRST_PROMPT_AIDLC_Q = """/aidlc {scope} REQUEST.md の依頼を、AI-DLC のワークフローで進めてください。
他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は画面の選択肢を使えませんが、応答を読んで答えます。質問や承認が要るところでは、応答の中で依頼者に聞いてください（依頼者の答えが次の発言として届きます）。回答方法を聞く場面では「Chat」を選んだものとします。依頼者が「任せる」と答えたことは最も単純な案で決めてください。
採点の契約は contract.md にあります（起動方法、URL、画面の要素の id とクラス名）。必ず守ってください。アプリのコードはこの作業ディレクトリの直下に置いてください。
{until}"""
ISDD_UNTIL_END = "完了条件（isdd-build の実装後レビューまで）を満たしたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"
ISDD_UNTIL_REQ = "今回は要件定義まで（isdd-spec で docs/requirements.md を書き、依頼者がその要件定義を承認するまで）で止めます。承認されたら、設計には進まず、作業ディレクトリ直下に STAGE_DONE というファイルを作り、決めた要件の要約を書いてください。承認の前には作らないでください。"
AIDLC_UNTIL_END = "ワークフローの最後の段階が承認されたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。"
AIDLC_UNTIL_REQ = "今回は要件定義まで（Requirements Analysis の段階が依頼者に承認されるまで）で止めます。その承認が記録されたら、次の段階には進まず、作業ディレクトリ直下に STAGE_DONE というファイルを作り、決めた要件の要約を書いてください。承認の前には作らないでください。"

AIDLC_ANSWERS_HEAD = """# 質問への依頼者の回答

質問にはこのファイルの回答を依頼者の答えとして使う。ここに無いことは、依頼の文章と契約から最も単純な案を依頼者の答えとする。承認はこのファイルでは与えない（依頼者が発言で答える）。

"""
ASK_MAY = "分からないことは、応答の中で依頼者に質問してよいです"
ASK_FIRST = "依頼に書かれていないことや決まっていないことは、作り始める前に、応答の中で依頼者に質問してください"
KEEP_NOTES = "依頼者と決めたこと、依頼文で伝えられた方針と、その理由は、作業ディレクトリ直下の DECISIONS.md に書き足してください。作業の最初に必ず DECISIONS.md を読んでください（無ければ作る）。テストも書き、毎回すべて通してください。"
KEEP_NOTES_CODE = "調べて分かったコードの構造（どの機能がどこにあり、きまりがどこにどう書かれているか）と、依頼者と決めたこと、その理由は、作業ディレクトリ直下の NOTES.md に書き足してください。作業の最初に必ず NOTES.md を読んでください（無ければ作る）。テストも直し、毎回すべて通してください。"
SEED_NOTE_ISDD = "このディレクトリには既存のコードがあります。isdd の文書（docs/requirements.md・docs/detail_design.md・docs/trace_map.md）が無ければ、isdd-reverse-engineering のスキルで、今回の変更に必要な範囲の文書を起こしてから、変更を進めてください。"
TASK = HERE  # --task で題材のフォルダ（stages/、contracts/、answers/、score.py）に切り替える

CHANGE_NOTE = "これは既存のアプリへの変更要求です。前の段までの文書とコードがこのディレクトリにあります。既存の機能を壊さないでください。"
CONTINUE_ISDD = "要件定義は承認済みです。予定を変えて、ここで止めずに続きの設計 → 実装 → 実装後レビューまで最後まで進めてください。これまでと同じく、分からないことや承認が要ることは応答の中で依頼者に質問してください（依頼者の答えが次の依頼として届きます）。前に作った STAGE_DONE は消してあります。\n" + ISDD_UNTIL_END
CONTINUE_AIDLC = "Requirements Analysis は承認済みです。予定を変えて、ここで止めずにワークフローの残りの段階を最後まで進めてください。これまでと同じく、質問や承認が要るところでは応答の中で依頼者に聞いてください（依頼者の答えが次の発言として届きます）。前に作った STAGE_DONE は消してあります。\n" + AIDLC_UNTIL_END
FOLLOW_UP = "続けてください。質問には ANSWERS.md の回答で自分で答え、承認はすべて与えます。残りを最後まで進め、完了したら STAGE_DONE を作ってください。"
FOLLOW_UP_AIDLC = "承認します。続けてください。質問への私の答えは ANSWERS.md のとおりです（無いことは最も単純な案でよい）。ワークフローの最後の段階が承認されたら STAGE_DONE を作ってください。"
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
    (workdir / "contract.md").write_text((TASK / "contracts" / f"stage{stage}.md").read_text(encoding="utf-8"), encoding="utf-8")


def score_snapshot(label: str, stage: int, snap: Path, out_json: Path, lock_path: Path) -> None:
    with open(lock_path, "w") as lock:
        log(label, f"stage {stage}: 採点の順番待ち")
        fcntl.flock(lock, fcntl.LOCK_EX)
        log(label, f"stage {stage}: 採点を開始")
        started = time.time()
        subprocess.run([sys.executable, str(TASK / "score.py"), "--app", str(snap), "--stage", str(stage), "--out", str(out_json)],
                       check=False, capture_output=True)
        log(label, f"stage {stage}: 採点を終了（{round(time.time() - started)} 秒）")
        fcntl.flock(lock, fcntl.LOCK_UN)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["isdd", "control", "aidlc"], required=True)
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
    parser.add_argument("--task", default=None, help="題材のフォルダ名（measure/ の下。既定はお題 1。例: scicalc）")
    parser.add_argument("--scope", default="classic", help="AI-DLC 群の進め方（classic、express など）")
    parser.add_argument("--until-requirements", action="store_true", help="isdd 群・AI-DLC 群（依頼者役あり）を要件定義の承認で止める。隠しテストの採点はしない")
    parser.add_argument("--continue-session", default=None, help="要件定義で止めた回の続きを回す。その回のセッション ID。作業フォルダは消さず、最初の指示を「続きを最後まで」に替える")
    parser.add_argument("--workdir-label", default=None, help="作業フォルダの名前（既定は --label と同じ）。続きを別の結果フォルダに記録するときに使う")
    parser.add_argument("--ask-first", action="store_true", help="対照群（依頼者役あり）の指示を「質問してよい」から「作る前に質問する」の一文に替える（一文つきの対照群）")
    parser.add_argument("--keep-notes", action="store_true", help="対照群（依頼者役あり）に、決めたことを DECISIONS.md に残して毎回読むことと、テストを書いて毎回通すことの 2 文を足す（数文つきの対照群。--ask-first と併せて使う）")
    parser.add_argument("--seed", default=None, help="最初の依頼の前に作業フォルダへ写す既存のアプリのフォルダ（題材 bigapp）。指定すると、どの依頼も既存のアプリへの変更として扱う")
    parser.add_argument("--contract", default=None, help="契約ファイルの名前（既定 contracts/stage<N>.md。計測 5 は stage1-min.md）")
    args = parser.parse_args()

    if args.path_prefix:
        os.environ["PATH"] = args.path_prefix + os.pathsep + os.environ.get("PATH", "")

    global TASK
    if args.task:
        TASK = HERE / args.task
    label = args.label or (f"{args.task}-" if args.task else "") + f"{args.arm}-r{args.run}"
    workdir = Path(args.work).resolve() / (args.workdir_label or label)
    results_dir = HERE / "results" / label
    results_dir.mkdir(parents=True, exist_ok=True)
    lock_path = HERE / "results" / ".score.lock"
    stages = [int(s) for s in args.stages.split(",")]

    if 1 in stages and not args.continue_session:
        if workdir.exists():
            shutil.rmtree(workdir)
        workdir.mkdir(parents=True)
        if args.seed:
            shutil.copytree(args.seed, workdir, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", "data"))
        subprocess.run(["git", "init", "-q"], cwd=workdir, check=False)
        if args.arm == "isdd":
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True, exist_ok=True)  # 文書つきの出発点（--seed）には、すでにスキルが入っていることがある
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"), dirs_exist_ok=True)
        if args.arm == "aidlc":
            # AI-DLC（awslabs/aidlc-workflows）を Claude Code 用に設定する。aidlc コマンドは事前に入れておく
            done = subprocess.run(["aidlc", "config", "--harness", "claude", "--yes"], cwd=workdir, capture_output=True, text=True)
            log(label, "aidlc config: " + (done.stdout + done.stderr).strip()[-200:])
            if done.returncode != 0:
                return 1

    summary_path = results_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"arm": args.arm, "run": args.run, "model": args.model, "stages": {}}
    if all(str(st) in summary["stages"] and summary["stages"][str(st)].get("passed") is not None for st in stages):
        log(label, "採点済みのため何もしない")
        return 0
    summary["runner"] = "claude -p"
    if args.ask_first:
        summary["ask_first"] = True
    if args.keep_notes:
        summary["keep_notes"] = True
    if args.continue_session:
        summary["continued_from"] = {"workdir_label": args.workdir_label, "session": args.continue_session}
    if args.arm == "aidlc":
        summary["aidlc"] = {"scope": args.scope, "version": subprocess.run(["aidlc", "--version"], capture_output=True, text=True).stdout.strip()}
    scorers = []

    for stage in stages:
        shutil.copyfile(TASK / "stages" / f"stage{stage}.md", workdir / "REQUEST.md")
        if args.contract:
            (workdir / "contract.md").write_text((TASK / "contracts" / args.contract).read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_contract(workdir, stage)
        if args.arm in ("isdd", "aidlc") and not args.responder:
            answers = (TASK / "answers" / f"stage{stage}.md").read_text(encoding="utf-8")
            if args.arm == "aidlc":
                # 固定回答の前書きは isdd 群向け（承認はすべて与えられたものとする）なので、項目だけを残して前書きを差し替える
                answers = AIDLC_ANSWERS_HEAD + "\n".join(line for line in answers.splitlines() if line.startswith("- ")) + "\n"
            (workdir / "ANSWERS.md").write_text(answers, encoding="utf-8")
        done_flag = workdir / "STAGE_DONE"
        if done_flag.exists():
            done_flag.unlink()
        if args.responder:
            if args.arm == "aidlc":
                prompt = FIRST_PROMPT_AIDLC_Q.format(scope=args.scope, until=AIDLC_UNTIL_REQ if args.until_requirements else AIDLC_UNTIL_END)
            else:
                prompt = FIRST_PROMPT_ISDD_Q if args.arm == "isdd" else FIRST_PROMPT_CONTROL_Q
                if args.arm == "control" and args.ask_first:
                    assert ASK_MAY in prompt
                    prompt = prompt.replace(ASK_MAY, ASK_FIRST)
                if args.arm == "control" and args.keep_notes:
                    notes = KEEP_NOTES_CODE if args.seed else KEEP_NOTES
                    prompt = prompt.replace("\n採点の契約は", "\n" + notes + "\n採点の契約は", 1)
                    assert notes in prompt
                if args.arm == "isdd" and args.seed:
                    prompt = prompt.replace("\n採点の契約は", "\n" + SEED_NOTE_ISDD + "\n採点の契約は", 1)
                    assert SEED_NOTE_ISDD in prompt
                if (stage > 1 or args.seed) and not args.until_requirements:
                    prompt = prompt.replace("\n採点の契約は", "\n" + CHANGE_NOTE + "\n採点の契約は", 1)
                    assert CHANGE_NOTE in prompt
                if args.arm == "isdd" and args.until_requirements:
                    assert ISDD_UNTIL_END in prompt
                    prompt = prompt.replace("要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください", "進めてください").replace(ISDD_UNTIL_END, ISDD_UNTIL_REQ)
            if args.continue_session:
                prompt = CONTINUE_AIDLC if args.arm == "aidlc" else CONTINUE_ISDD
            ledger_text = Path(args.responder).read_text(encoding="utf-8")
        else:
            template = {"isdd": FIRST_PROMPT_ISDD, "aidlc": FIRST_PROMPT_AIDLC}.get(args.arm, FIRST_PROMPT_CONTROL)
            prompt = template.format(change_note=CHANGE_NOTE if stage > 1 else "", scope=args.scope)
        follow = {"isdd": FOLLOW_UP, "aidlc": FOLLOW_UP_AIDLC}.get(args.arm, FOLLOW_UP_CONTROL)
        questions_asked = 0
        rounds = []
        session = args.continue_session or ""
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
        aidlc_info = {}
        if args.arm == "aidlc":
            # AI-DLC の記録（段階の状態と承認の数）。isdd のスキルが見えていないことと合わせて有効とする
            records = sorted((workdir / "aidlc" / "spaces").glob("*/intents/*/aidlc-state.md"))
            audit = "".join(f.read_text(encoding="utf-8", errors="replace") for r in records for f in sorted((r.parent / "audit").glob("*.md")))
            aidlc_info = {"aidlc_records": [r.parent.name for r in records], "aidlc_gates_approved": audit.count("GATE_APPROVED"),
                          "aidlc_human_turns": audit.count("HUMAN_TURN"), "aidlc_workflow_completed": "WORKFLOW_COMPLETED" in audit}
            valid = bool(records) and not visible and not isdd_used
        stage_info = {"done": done_flag.exists(), "wall_sec": wall, "started": datetime.fromtimestamp(stage_started).isoformat(timespec="seconds"),
                      "responder": bool(args.responder), "questions_rounds": questions_asked,
                      "tool_uses": sum(tool_names.values()), "tool_names": tool_names, "skills_called": skills_called, "isdd_skills_visible": visible,
                      "valid": valid, **aidlc_info, "isdd_artifacts": artifacts, "validity_note": ("isdd の成果物もスキル呼び出しも無し" if args.arm == "isdd" and not (isdd_used or artifacts) else
                                                       ("対照群に isdd のスキルが見えていた" if args.arm == "control" and (visible or isdd_used) else "")),
                      **sum_usage(rounds)}
        summary["stages"][str(stage)] = stage_info
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        if not args.until_requirements:
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
