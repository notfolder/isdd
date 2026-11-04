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
sys.path.insert(0, str(HERE.parent))
from agentrun import ISDD_SKILLS, ask_responder, run_claude, run_claude_retry  # noqa: E402
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
        if args.arm.startswith("isdd"):
            dest = workdir / ".claude" / "skills"
            dest.mkdir(parents=True)
            for skill in (REPO / "skills").iterdir():
                if skill.is_dir() and not skill.name.endswith("-workspace"):
                    shutil.copytree(skill, dest / skill.name, ignore=shutil.ignore_patterns("evals"))
    if args.arm.startswith("isdd") and not getattr(args, "no_answers", False):
        shutil.copyfile(HERE / "answers.md", workdir / "ANSWERS.md")
    shutil.copyfile(HERE / "contract.md", workdir / "contract.md")
    (workdir / "REQUEST.md").write_text("# Request\n\n" + stage["request"].rstrip() + "\n\nFollow `contract.md` (start-up, PORT, DATA_DIR, language).\n", encoding="utf-8")
    flag = workdir / "STAGE_DONE"
    if flag.exists():
        flag.unlink()
    print(workdir)
    return 0


FIRST_ISDD = """REQUEST.md の依頼を、isdd-spec と isdd-build のスキル（.claude/skills/ にある）を使って、要件定義 → 設計 → 実装 → 実装後レビューまで最後まで進めてください。
他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。質問や承認が要るときは、ユーザーに聞かずに ANSWERS.md の回答に従って自分で答え、承認はすべて与えられたものとして進めてください。
契約は contract.md にあります（setup.sh と run.sh、PORT、DATA_DIR、初期データ、画面の言語は英語）。必ず守ってください。採点は人がブラウザで操作して行うので、依頼の機能がすべて画面から使えること、ナビゲーションが分かりやすいこと、指定の色が使われていることが重要です。
{change_note}
完了条件（isdd-build の実装後レビューまで）を満たし、`bash setup.sh` → `PORT=任意 bash run.sh` で起動して主要な画面が開けることを確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。自分が起動したサーバーは PID で止めてください。"""
FIRST_CONTROL = """REQUEST.md の依頼を最後まで実装してください。Skill ツールは使わないでください。
他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。不明な点は依頼の文章と contract.md から最も単純な案で決めて進め、質問で止まらないでください。
契約は contract.md にあります（setup.sh と run.sh、PORT、DATA_DIR、初期データ、画面の言語は英語）。必ず守ってください。採点は人がブラウザで操作して行うので、依頼の機能がすべて画面から使えること、ナビゲーションが分かりやすいこと、指定の色が使われていることが重要です。
{change_note}
実装が動くこと（`bash setup.sh` → `PORT=任意 bash run.sh` で起動し、主要な画面が開けること）を確かめたら、作業ディレクトリ直下に STAGE_DONE というファイルを作り、完了の要約を書いてください。途中で止まるときは作らないでください。自分が起動したサーバーは PID で止めてください。"""
FIRST_ISDD_Q = FIRST_ISDD.replace("他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。質問や承認が要るときは、ユーザーに聞かずに ANSWERS.md の回答に従って自分で答え、承認はすべて与えられたものとして進めてください。",
    "他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことや承認が要ることは、応答の中で依頼者に質問してください（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最小案で決め、要件定義書の「依頼に無く自分で決めた項目」に書いてください。")
FIRST_CONTROL_Q = FIRST_CONTROL.replace("他のプロセスを `pkill`・`killall`・`kill -9 -1` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。ユーザーは不在です。不明な点は依頼の文章と contract.md から最も単純な案で決めて進め、質問で止まらないでください。",
    "他のプロセスを `pkill`・`killall` などで止めないでください（同じマシンで別の作業が動いています）。自分が起動したサーバーは、その PID だけを止めてください。依頼者は応答を読んで答えます。分からないことは、応答の中で依頼者に質問してよいです（質問は番号を付けてまとめる。依頼者の答えが次の依頼として届きます）。依頼者が「任せる」と答えたことは最も単純な案で決めてください。")
CHANGE_NOTE = "これは既存の Web サイトへの変更要求です。前の段までの文書とコードがこのディレクトリにあります。変更した点以外の既存の機能を壊さないでください。"
FOLLOW_ISDD = "続けてください。質問には ANSWERS.md の回答で自分で答え、承認はすべて与えます。残りを最後まで進め、完了したら STAGE_DONE を作ってください。"
FOLLOW_CONTROL = "続けてください。不明な点は最も単純な案で決めて進め、残りを最後まで実装し、完了したら STAGE_DONE を作ってください。"


def run_stage(args) -> int:
    """段を無人実行する（prepare 済みの作業ディレクトリで claude -p を回し、STAGE_DONE まで追い打ち）。終わったら finish 相当の記録と snapshot。"""
    workdir = workdir_of(args)
    results_dir = results_dir_of(args)
    ledger_text = Path(args.responder).read_text(encoding="utf-8") if args.responder else None
    if args.responder:
        prompt = (FIRST_ISDD_Q if args.arm.startswith("isdd") else FIRST_CONTROL_Q).format(change_note=CHANGE_NOTE if args.stage > 1 else "")
    else:
        prompt = (FIRST_ISDD if args.arm.startswith("isdd") else FIRST_CONTROL).format(change_note=CHANGE_NOTE if args.stage > 1 else "")
    follow = FOLLOW_ISDD if args.arm.startswith("isdd") else FOLLOW_CONTROL
    done_flag = workdir / "STAGE_DONE"
    rounds, session, questions = [], "", 0
    started = time.time()
    log = open(results_dir / f"stage{args.stage}.log", "w", encoding="utf-8")
    for i in range(args.max_rounds):
        if i > 0 and args.responder:
            last = (rounds[-1].get("texts") or [rounds[-1].get("result") or ""])[-1]
            follow = ask_responder(ledger_text, last, args.responder_model, workdir)
            if any(k in last for k in ("?", "？", "教えてください", "どちら")):
                questions += 1
            log.write(f"\n### 依頼者役の答え {i}\n\n{follow[:4000]}\n")
        data = run_claude_retry(workdir, prompt if i == 0 else follow, args.model, session, args.timeout_min)
        rounds.append(data)
        session = data.get("session_id", session)
        log.write(f"\n## round {i + 1} ({data.get('wall_sec')} s, turns={data.get('num_turns')}, tools={data.get('tool_uses')}, skills={data.get('skills_called')}, visible={data.get('skills_visible')}, error={data.get('error')})\n\n")
        log.write(str(data.get("result", data.get("raw", "")))[:20000] + "\n")
        log.flush()
        print(f"[{args.site}-{args.arm}] stage {args.stage}: round {i + 1} {data.get('wall_sec')}s tools={data.get('tool_uses')} skills={data.get('skills_called')} done={done_flag.exists()}", flush=True)
        if done_flag.exists() or (data.get("error") and "timeout" in str(data.get("error"))) or not session:
            break
    log.close()
    wall = round(time.time() - started, 1)
    snap = results_dir / f"snapshot-stage{args.stage}"
    if snap.exists():
        shutil.rmtree(snap)
    shutil.copytree(workdir, snap, ignore=IGNORE)
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    for r in rounds:
        for k in usage:
            usage[k] += int((r.get("usage") or {}).get(k, 0) or 0)
    skills_called = [sk for r in rounds for sk in r.get("skills_called", [])]
    visible = sorted({sk for r in rounds for sk in (r.get("skills_visible") or [])})
    isdd_used = any(sk in ISDD_SKILLS for sk in skills_called)
    artifacts = all((workdir / f).exists() for f in ("docs/requirements.md", "docs/detail_design.md", "docs/trace_map.md", "scripts/isdd"))
    valid = (isdd_used or artifacts) if args.arm.startswith("isdd") else (not visible and not isdd_used)
    p, s = _summary(results_dir, args)
    s["runner"] = "claude -p"
    s["stages"][str(args.stage)] = {"done": done_flag.exists(), "wall_sec": wall, "agent_tokens": sum(usage.values()), "usage": usage,
                                    "tool_uses": sum(r.get("tool_uses", 0) for r in rounds), "rounds": len(rounds), "skills_called": skills_called,
                                    "isdd_skills_visible": visible, "valid": valid, "responder": bool(args.responder), "questions_rounds": questions, "note": args.note}
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{args.site}-{args.arm}] stage {args.stage}: done={done_flag.exists()} valid={valid} tokens={sum(usage.values())} wall={wall}s rounds={len(rounds)}", flush=True)
    return 0


def grade(args) -> int:
    """serve 済みのサイトを、Opus の採点者 N 人（claude -p）に採点させ、stageN-verdicts-{k}.json を書かせる。"""
    results_dir = results_dir_of(args)
    server = json.loads((results_dir / f"stage{args.stage}-server.json").read_text(encoding="utf-8"))
    template = (HERE / "grader-prompt.md").read_text(encoding="utf-8")
    body = template.split("---\n", 1)[1].rsplit("\n---", 1)[0]
    grader_root = Path("/tmp/webgen/grader-v2")
    for k in range(1, args.votes + 1):
        gdir = grader_root / f"{args.site}-{args.arm}-s{args.stage}-{k}"
        gdir.mkdir(parents=True, exist_ok=True)
        vp = results_dir / f"stage{args.stage}-verdicts-{k}.json"
        prompt = (body.replace("{base_url}", server["base_url"]).replace("{cases_path}", str(results_dir / f"stage{args.stage}-cases.json"))
                  .replace("{grader_dir}", str(gdir)).replace("{verdicts_path}", str(vp)))
        data = run_claude_retry(gdir, prompt, args.grader_model, "", 30)
        print(f"[{args.site}-{args.arm}] stage {args.stage}: grader {k} {data.get('wall_sec')}s tools={data.get('tool_uses')} written={vp.exists()} error={data.get('error')}", flush=True)
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
    ballots = []
    for k in range(1, max(args.votes, 1) + 1):
        vk = results_dir / f"stage{args.stage}-verdicts-{k}.json"
        if vk.exists():
            ballots.append(json.loads(vk.read_text(encoding="utf-8")))
    if ballots:
        # 採点者の多数決（3 者ばらばらなら PARTIAL）。stageN-verdicts-{k}.json を読む
        verdicts = {}
        for c in PLAN["sites"][args.site]["stages"][args.stage - 1]["cases"]:
            votes = [str((b.get(c["id"]) or {}).get("verdict", "NO")).upper() for b in ballots]
            if not votes:
                continue
            best = max(set(votes), key=votes.count)
            if votes.count(best) == 1 and len(votes) >= 3:
                best = "PARTIAL"
            verdicts[c["id"]] = {"verdict": best, "reason": " / ".join(f"{v}: {(b.get(c['id']) or {}).get('reason', '')[:120]}" for v, b in zip(votes, ballots)), "votes": votes}
        vp = results_dir / f"stage{args.stage}-verdicts.json"
        vp.write_text(json.dumps(verdicts, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        vp = results_dir / f"stage{args.stage}-verdicts.json"
        verdicts = json.loads(vp.read_text(encoding="utf-8")) if vp.exists() else {}
    cases = PLAN["sites"][args.site]["stages"][args.stage - 1]["cases"]
    points = {"YES": 1.0, "PARTIAL": 0.5, "NO": 0.0}
    per = {}
    for c in cases:
        v = verdicts.get(c["id"]) or {}
        verdict = str(v.get("verdict", "NO")).upper()
        per[c["id"]] = {"verdict": verdict if verdict in points else "NO", "reason": v.get("reason", ""), "category": c["category"], "change": bool(c.get("change"))}
    total = sum(points[x["verdict"]] for x in per.values())
    p, s = _summary(results_dir, args)
    info = s["stages"].setdefault(str(args.stage), {})
    prev = s["stages"].get(str(args.stage - 1), {}).get("cases", {})
    regressions = sorted(k for k, v in prev.items() if v["verdict"] == "YES" and k in per and per[k]["verdict"] != "YES")
    server = results_dir / f"stage{args.stage}-server.json"
    started = json.loads(server.read_text(encoding="utf-8")).get("started") if server.exists() else None
    if ballots:
        info["grader"] = {"model": getattr(args, "grader_model", None), "votes": len(ballots)}
    change_cases = [k for k, v in per.items() if v["change"]]
    info["change_missed"] = sorted(k for k in change_cases if per[k]["verdict"] != "YES")
    info["change_total"] = len(change_cases)
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
    print("| 課題・群 | 段 | 点 / ケース | YES / PARTIAL / NO | 変更の取りこぼし | 退行 | 起動 | トークン | ツール | 所要（秒） | 公開関数 / 行 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for summary in sorted((HERE / "results").glob("*/summary.json")):
        d = json.loads(summary.read_text(encoding="utf-8"))
        for st, info in sorted(d["stages"].items(), key=lambda kv: int(kv[0])):
            cs = info.get("cases", {})
            cnt = {k: sum(1 for v in cs.values() if v["verdict"] == k) for k in ("YES", "PARTIAL", "NO")}
            ob = info.get("overbuild") or {}
            print(f"| {d['site']}-{d['arm']} | {st} | {info.get('score')} / {info.get('n_cases')} | {cnt['YES']} / {cnt['PARTIAL']} / {cnt['NO']} | {len(info.get('change_missed') or [])} / {info.get('change_total', 0)} | {len(info.get('regressions') or [])} | "
                  f"{info.get('started')} | {info.get('agent_tokens')} | {info.get('tool_uses')} | {info.get('wall_sec')} | {ob.get('public_functions')} / {ob.get('lines')} |")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "run", "finish", "serve", "stop", "grade", "score", "report"):
        p = sub.add_parser(name)
        if name != "report":
            p.add_argument("--site", required=True, choices=list(PLAN["sites"]))
            p.add_argument("--arm", required=True, help="isdd / control、または isdd-r1 のように回数を付けた名前")
            p.add_argument("--stage", type=int, required=True)
        if name in ("prepare", "finish", "serve", "run"):
            p.add_argument("--work", required=True)
        if name == "prepare":
            p.add_argument("--no-answers", action="store_true", help="固定回答を置かない（計測 5 の依頼者役モード）")
        if name == "run":
            p.add_argument("--model", default="claude-haiku-5-5")
            p.add_argument("--max-rounds", type=int, default=12)
            p.add_argument("--timeout-min", type=int, default=45)
            p.add_argument("--responder", default=None, help="依頼者役の隠し台帳（計測 5）")
            p.add_argument("--responder-model", default="claude-sonnet-5-5")
            p.add_argument("--note", default="")
        if name == "grade":
            p.add_argument("--votes", type=int, default=3)
            p.add_argument("--grader-model", default="claude-opus-5-5")
        if name == "score":
            p.add_argument("--votes", type=int, default=1, help="採点者の数（stageN-verdicts-{k}.json の多数決）")
            p.add_argument("--grader-model", default=None, help="記録用。summary.json に書く")
        if name == "finish":
            p.add_argument("--wall-sec", type=float, required=True)
            p.add_argument("--tokens", type=int, default=None)
            p.add_argument("--tool-uses", type=int, default=None)
            p.add_argument("--note", default="")
    args = parser.parse_args()
    return {"prepare": prepare, "run": run_stage, "finish": finish, "serve": serve, "stop": stop, "grade": grade, "score": score, "report": report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
