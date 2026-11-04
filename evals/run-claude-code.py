#!/usr/bin/env python3
"""
run-claude-code.py — waza の場面定義（evals/<スキル>/tasks/*.yaml）を、waza を使わずに
Claude Code のヘッドレス実行（claude -p）で回す。Anthropic API キーではなく Claude Code の
ログイン（定額契約）で動かしたいときに使う。

evals/run-all.sh claude と同じ場面・同じ fixture・同じ採点基準を使うが、実行基盤が
Copilot CLI ではなく Claude Code なので、結果は参考値として扱う（waza の記録とは別に保存する）。

使い方:
  python3 evals/run-claude-code.py <スキル名>... [--task <場面名か ID のグロブ>]... [--model claude-haiku-5-5]
                                   [--attempts 2] [--out evals/artifacts-claude-code]
                                   [--permission-mode acceptEdits] [--allowed-tools 'Bash Edit Write ...']

  例: python3 evals/run-claude-code.py isdd-build --task 'Hello World 未マッピング*'

依存: PyYAML（pip install pyyaml）、claude コマンド（ログイン済み）。

権限: 作業場所は一時ディレクトリで、エージェントはそこでファイルを作りコマンドを実行する。
  既定は --permission-mode acceptEdits と --allowed-tools（Bash Edit Write Read Glob Grep Skill）で、
  許可されていないツール呼び出しは失敗として扱われる（対話的な確認は無い）。
  claude へ渡す追加の引数は --claude-args で足せる（例: --claude-args '--max-turns 200'）。

場面ごとの手順:
  1. 作業場所（一時ディレクトリ）に fixture を複製し、skills/ を .claude/skills/ に置く
  2. claude -p で最初の依頼を送り、follow_up_prompts を --resume で順に送る
  3. graders を採点する
     - file:    must_exist / content_patterns（must_match・must_not_match）
     - program: command と args を作業場所で実行（WAZA_WORKSPACE_DIR・ISDD_REPO_ROOT を渡す）。終了コード 0 で合格。
                標準入力にエージェントの最後の応答を渡す（isdd_grade.py version-current --or-output-re 用）
     - prompt:  同じセッションを --resume --fork-session で開き、採点の問いを送って pass/fail を JSON で受け取る
                （waza の continue_session: true と同じく会話とツール呼び出しの履歴を見て判定する）
  4. 1 回目で落ちたら同じモデルで 1 回だけ再試行する（昇格はしない）

結果は <out>/<スキル名>/<場面 ID>/attempt-N/ に result.json（判定）と transcript.json（応答）を置く。
作業場所は消さない（result.json の workspace に場所を書く）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
EVALS = REPO / "evals"
DEFAULT_MODEL = "claude-haiku-5-5"
DEFAULT_TOOLS = "Bash Edit Write Read Glob Grep Skill"
JUDGE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {"pass": {"type": "boolean"}, "reason": {"type": "string"}},
        "required": ["pass", "reason"],
    },
    ensure_ascii=False,
)
JUDGE_TAIL = (
    "\n\n（採点の答え方）set_waza_grade_pass / set_waza_grade_fail というツールはこの環境にはありません。"
    "代わりに、条件を満たすなら pass を true、満たさないなら false にして、根拠を reason に書いた JSON だけを答えてください。"
    "ファイルを書き換えたりコマンドを実行したりしないでください。"
)

AGENT_ARGS: list[str] = []  # main() で組み立てる（権限の指定）


def log(msg: str) -> None:
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_claude(workspace: Path, prompt: str, model: str, timeout: int, resume: str | None = None,
               fork: bool = False, extra: list[str] | None = None) -> dict:
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--setting-sources", "project"]
    if resume:
        cmd += ["--resume", resume]
        if fork:
            cmd += ["--fork-session"]
    cmd += extra if extra is not None else AGENT_ARGS
    # 依頼は標準入力で渡す（--allowedTools など可変長の引数に飲み込まれないようにする）
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # 入れ子の起動を許す
    try:
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=timeout, env=env,
                              input=prompt)
    except subprocess.TimeoutExpired as exc:
        return {"is_error": True, "result": f"timeout after {timeout}s", "stderr": (exc.stderr or "")[-2000:]}
    out = proc.stdout.strip()
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        data = {"is_error": True, "result": out[-4000:], "stderr": proc.stderr[-2000:], "exit": proc.returncode}
    if proc.returncode != 0 and not data.get("is_error"):
        data["is_error"] = True
        data["stderr"] = proc.stderr[-2000:]
    return data


def grade_file(cfg: dict, workspace: Path) -> tuple[bool, str]:
    reasons = []
    ok = True
    for rel in cfg.get("must_exist", []) or []:
        if not (workspace / rel).exists():
            ok = False
            reasons.append(f"無い: {rel}")
    for pat in cfg.get("content_patterns", []) or []:
        path = workspace / pat["path"]
        if not path.exists():
            ok = False
            reasons.append(f"無い: {pat['path']}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for rx in pat.get("must_match", []) or []:
            if not re.search(rx, text, re.MULTILINE):
                ok = False
                reasons.append(f"{pat['path']} に無い: {rx}")
        for rx in pat.get("must_not_match", []) or []:
            if re.search(rx, text, re.MULTILINE):
                ok = False
                reasons.append(f"{pat['path']} にある: {rx}")
    return ok, "; ".join(reasons) if reasons else "ok"


def grade_program(cfg: dict, workspace: Path, last_response: str) -> tuple[bool, str]:
    env = dict(os.environ)
    env["WAZA_WORKSPACE_DIR"] = str(workspace)
    env["ISDD_REPO_ROOT"] = str(REPO)
    cmd = [cfg["command"]] + list(cfg.get("args", []) or [])
    try:
        proc = subprocess.run(cmd, cwd=workspace, capture_output=True, text=True, timeout=600,
                              env=env, input=last_response)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    detail = (proc.stdout.strip() + "\n" + proc.stderr.strip()).strip()
    return proc.returncode == 0, detail[-1500:] or f"exit={proc.returncode}"


def grade_prompt(cfg: dict, workspace: Path, session_id: str, model: str) -> tuple[bool, str]:
    prompt = cfg["prompt"].rstrip() + JUDGE_TAIL
    data = run_claude(workspace, prompt, model, timeout=600, resume=session_id, fork=True,
                      extra=["--permission-mode", "plan", "--json-schema", JUDGE_SCHEMA])
    verdict = data.get("structured_output")
    if not isinstance(verdict, dict):
        m = re.search(r"\{.*\}", str(data.get("result", "")), re.DOTALL)
        try:
            verdict = json.loads(m.group(0)) if m else None
        except json.JSONDecodeError:
            verdict = None
    if not isinstance(verdict, dict) or "pass" not in verdict:
        return False, f"判定が読めない: {str(data.get('result', ''))[:500]}"
    return bool(verdict["pass"]), str(verdict.get("reason", ""))[:1500]


def prepare_workspace(eval_dir: Path, task: dict, skill_name: str) -> Path:
    workspace = Path(tempfile.mkdtemp(prefix=f"cc-{skill_name}-"))
    fixture = (task.get("inputs", {}).get("context", {}) or {}).get("fixture")
    src = eval_dir / fixture if fixture else eval_dir / "fixtures"
    if src.is_dir():
        shutil.copytree(src, workspace, dirs_exist_ok=True)
    dest = workspace / ".claude" / "skills"
    dest.mkdir(parents=True, exist_ok=True)
    for skill in (REPO / "skills").iterdir():
        if skill.is_dir() and not skill.name.endswith("-workspace"):
            # evals/ は場面定義（秘密の文字列の fixture を含む）なので配らない（run-all.sh の files-check と同じ扱い）
            shutil.copytree(skill, dest / skill.name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("evals", "__pycache__", "*.pyc", ".DS_Store"))
    return workspace


def run_task(eval_dir: Path, skill_name: str, task: dict, model: str, attempt_dir: Path,
             default_timeout: int) -> dict:
    inputs = task.get("inputs", {})
    timeout = int(task.get("timeout_seconds", default_timeout))
    workspace = prepare_workspace(eval_dir, task, skill_name)
    attempt_dir.mkdir(parents=True, exist_ok=True)
    log(f"作業場所: {workspace}")
    transcript = []
    session_id = None
    prompts = [inputs["prompt"]] + list(inputs.get("follow_up_prompts", []) or [])
    started = dt.datetime.now()
    for i, p in enumerate(prompts):
        log(f"依頼 {i + 1}/{len(prompts)} を送る")
        data = run_claude(workspace, p, model, timeout, resume=session_id)
        session_id = data.get("session_id", session_id)
        transcript.append({"prompt": p, "response": data.get("result"), "is_error": data.get("is_error"),
                           "num_turns": data.get("num_turns"), "duration_ms": data.get("duration_ms"),
                           "stderr": data.get("stderr")})
        (attempt_dir / "transcript.json").write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
        if data.get("is_error"):
            log(f"  エラー: {str(data.get('result'))[:300]}")
            break
        log(f"  応答 {len(str(data.get('result') or ''))} 文字、{data.get('num_turns')} ターン、{(data.get('duration_ms') or 0) // 1000} 秒")
    last_response = str(transcript[-1].get("response") or "")
    grades = []
    for g in task.get("graders", []) or []:
        gtype = g.get("type")
        cfg = g.get("config", {}) or {}
        if gtype == "file":
            ok, detail = grade_file(cfg, workspace)
        elif gtype == "program":
            ok, detail = grade_program(cfg, workspace, last_response)
        elif gtype == "prompt":
            if session_id:
                ok, detail = grade_prompt(cfg, workspace, session_id, model)
            else:
                ok, detail = False, "セッションが無い"
        else:
            ok, detail = False, f"未対応の grader: {gtype}"
        log(f"  採点 {g.get('name')}: {'PASS' if ok else 'FAIL'}  {detail.splitlines()[0][:120] if detail else ''}")
        grades.append({"name": g.get("name"), "type": gtype, "pass": ok, "detail": detail})
    result = {
        "task_id": task.get("id"), "name": task.get("name"), "model": model, "workspace": str(workspace),
        "session_id": session_id, "started": started.isoformat(timespec="seconds"),
        "finished": dt.datetime.now().isoformat(timespec="seconds"),
        "pass": all(g["pass"] for g in grades) and bool(grades) and not transcript[-1].get("is_error"),
        "grades": grades,
    }
    (attempt_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_tasks(eval_dir: Path) -> tuple[dict, list[tuple[Path, dict]]]:
    eval_file = eval_dir / "eval.copilot.yaml"
    spec = yaml.safe_load(eval_file.read_text(encoding="utf-8"))
    tasks = []
    for pattern in spec.get("tasks", []) or []:
        for path in sorted(eval_dir.glob(pattern)):
            tasks.append((path, yaml.safe_load(path.read_text(encoding="utf-8"))))
    return spec, tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skills", nargs="+")
    ap.add_argument("--task", action="append", default=[], help="場面名か ID のグロブ（複数可）")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--attempts", type=int, default=2)
    ap.add_argument("--out", default=str(EVALS / "artifacts-claude-code"))
    ap.add_argument("--permission-mode", default="acceptEdits")
    ap.add_argument("--allowed-tools", default=DEFAULT_TOOLS, help="空文字で指定しない")
    ap.add_argument("--claude-args", default="", help="claude へ渡す追加の引数（1 つの文字列）")
    args = ap.parse_args()

    AGENT_ARGS.extend(["--permission-mode", args.permission_mode])
    if args.allowed_tools.strip():
        AGENT_ARGS.extend(["--allowedTools", ",".join(args.allowed_tools.split())])
    AGENT_ARGS.extend(shlex.split(args.claude_args))

    check = subprocess.run([sys.executable, str(REPO / "tools" / "build_skills.py"), "--check"])
    if check.returncode != 0:
        print("skills/ の複製が shared/ と一致しません。python3 tools/build_skills.py を実行してください", file=sys.stderr)
        return 1

    rows = []
    failures = 0
    for skill_name in args.skills:
        eval_dir = EVALS / skill_name
        spec, tasks = load_tasks(eval_dir)
        default_timeout = int((spec.get("config", {}) or {}).get("timeout_seconds", 900))
        for path, task in tasks:
            if args.task and not any(fnmatch.fnmatch(task.get("name", ""), g) or fnmatch.fnmatch(task.get("id", ""), g)
                                     for g in args.task):
                continue
            log(f"==> {skill_name}: {task.get('name')} ({path.name})")
            outcome: list[str] = []
            for attempt in range(1, args.attempts + 1):
                attempt_dir = Path(args.out) / skill_name / str(task.get("id")) / f"attempt-{attempt}"
                log(f"attempt {attempt}: {args.model}")
                result = run_task(eval_dir, skill_name, task, args.model, attempt_dir, default_timeout)
                outcome.append("PASS" if result["pass"] else "FAIL")
                if result["pass"]:
                    break
            if outcome[-1] != "PASS":
                failures += 1
            rows.append((skill_name, task.get("name"), outcome))
    print("\n結果（実行基盤: Claude Code ヘッドレス、モデル: %s）" % args.model)
    print("| スキル | 場面 | 1 回目 | 再試行 |")
    print("|---|---|---|---|")
    for skill_name, name, outcome in rows:
        print(f"| {skill_name} | {name} | {outcome[0]} | {outcome[1] if len(outcome) > 1 else '-'} |")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
