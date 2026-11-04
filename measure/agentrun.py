#!/usr/bin/env python3
"""計測で共通に使う、claude -p の無人実行（逐次出力の読み取り）と依頼者役。run.py と webgen.py が import する。"""

import json
import os
import subprocess
import time
from pathlib import Path

ALLOWED_TOOLS = ["Bash", "Read", "Write", "Edit", "MultiEdit", "Glob", "Grep", "LS", "Skill", "Agent", "TodoWrite", "NotebookEdit"]

RESPONDER_PROMPT = """あなたはシステムの依頼者です。IT には詳しくありません。開発者（エージェント）からの次の応答を読み、質問や承認の依頼に答えてください。

答え方の規則:
- 手元の「隠し台帳」にある項目は、台帳の答えをそのまま伝える。台帳に無い項目は「分からない。任せる」と答える。
- 聞かれていないことは言わない。台帳の内容を先回りして教えない。
- 承認を求められたら「承認する」と答える。推奨案が示されていれば推奨に従う。
- 質問が無く、報告や進捗だけなら「続けてください」とだけ答える。
- 出力は依頼者の返事の文章だけ（前置きや説明は書かない。番号付きの質問には番号で答える）。

隠し台帳:
{ledger}

開発者の応答:
{response}"""


ISDD_SKILLS = {"isdd-spec", "isdd-build", "isdd-reverse-engineering", "isdd-setup"}


def run_claude(workdir: Path, prompt: str, model: str, session: str, timeout_min: int) -> dict:
    """claude -p を逐次出力（stream-json）で起こし、応答・トークン・ツール呼び出し・見えていたスキルを返す。"""
    cmd = ["claude", "-p", "--model", model, "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
           "--permission-mode", "acceptEdits", "--allowedTools", ",".join(ALLOWED_TOOLS)]
    if session:
        cmd += ["--resume", session]
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # 入れ子の起動を許す
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout_min * 60, env=env, input=prompt)
    except subprocess.TimeoutExpired as e:
        return {"error": f"timeout {timeout_min} min", "raw": ((e.stdout or b"").decode(errors="replace"))[-2000:], "wall_sec": round(time.time() - started, 1)}
    data = {"tool_uses": 0, "tool_names": {}, "skills_called": [], "skills_visible": None, "texts": []}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            data["session_id"] = ev.get("session_id")
            data["skills_visible"] = sorted(c for c in (ev.get("slash_commands") or []) if c.startswith("isdd"))
        elif t == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    name = c.get("name", "?")
                    data["tool_uses"] += 1
                    data["tool_names"][name] = data["tool_names"].get(name, 0) + 1
                    if name == "Skill":
                        skill = str((c.get("input") or {}).get("skill", ""))
                        data["skills_called"].append(skill)
                elif c.get("type") == "text":
                    data["texts"].append(c["text"])
        elif t == "result":
            data["usage"] = ev.get("usage")
            data["total_cost_usd"] = ev.get("total_cost_usd")
            data["num_turns"] = ev.get("num_turns")
            data["result"] = ev.get("result")
            data["session_id"] = ev.get("session_id", data.get("session_id"))
            data["is_error"] = ev.get("is_error")
    if "usage" not in data:
        data["error"] = "no result event"
        data["raw"] = (proc.stdout + proc.stderr)[-3000:]
        data["returncode"] = proc.returncode
    text = str(data.get("result") or "") + str(data.get("raw") or "")
    if data.get("is_error") or "hit your" in text or "rate_limit" in text:
        if "limit" in text:
            data["error"] = "rate_limit"
            data["reset_text"] = text[:300]
    data["wall_sec"] = round(time.time() - started, 1)
    return data


def seconds_until_reset(text: str) -> int:
    """「resets 3pm (Asia/Tokyo)」のような文から、回復までの秒数を出す（分からなければ 30 分）"""
    import re
    from datetime import datetime, timedelta
    m = re.search(r"resets?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", text, re.I)
    if not m:
        return 1800
    hour = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "pm" else 0)
    minute = int(m.group(2) or 0)
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return int((target - now).total_seconds()) + 120


def run_claude_retry(workdir: Path, prompt: str, model: str, session: str, timeout_min: int, log=print) -> dict:
    """上限で止まったら回復まで待ってやり直す。"""
    while True:
        data = run_claude(workdir, prompt, model, session, timeout_min)
        if data.get("error") == "rate_limit":
            wait = seconds_until_reset(data.get("reset_text", ""))
            log(f"利用上限に到達。{wait // 60} 分待って再開する（{data.get('reset_text', '')[:80]}）")
            time.sleep(wait)
            continue
        return data


def ask_responder(ledger: str, response: str, model: str, workdir: Path) -> str:
    """依頼者役のモデルに、エージェントの応答への返事を作らせる（台帳の範囲だけ）"""
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--setting-sources", "project", "--permission-mode", "plan", "--allowedTools", ""]
    try:
        proc = subprocess.run(cmd, cwd=workdir.parent, capture_output=True, text=True, timeout=300, env=env,
                              input=RESPONDER_PROMPT.format(ledger=ledger, response=response[-12000:]))
        data = json.loads(proc.stdout.strip() or "{}")
        text = (data.get("result") or "").strip()
    except Exception as e:  # noqa: BLE001
        text = ""
    return text or "続けてください。分からないことは任せます。"


