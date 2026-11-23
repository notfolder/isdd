#!/usr/bin/env python3
"""文書評価のやり直し（2026-11-23）で使う claude -p の起動。agentrun.run_claude と同じ読み取りに、
利用者の共通ルール（ホームと ~/.claude の CLAUDE.md）を読ませない設定を足したもの。

作業フォルダがホームの下にあると、--setting-sources project でも、親フォルダのホームにある CLAUDE.md と
~/.claude/CLAUDE.md が読み手に読み込まれる。そこで作業フォルダをホームの外（/Users/Shared の下）に置き、
--settings の claudeMdExcludes でも外す。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agentrun import ALLOWED_TOOLS, seconds_until_reset  # noqa: E402

WORK_ROOT = Path("/Users/Shared/isdd-measure-work/docval4")
SETTINGS = json.dumps({"claudeMdExcludes": [str(Path.home() / ".claude" / "CLAUDE.md"), str(Path.home() / "CLAUDE.md")]})


def run_claude(workdir: Path, prompt: str, model: str, timeout_min: int) -> dict:
    cmd = ["claude", "-p", "--model", model, "--output-format", "stream-json", "--verbose", "--setting-sources", "project",
           "--settings", SETTINGS, "--permission-mode", "acceptEdits", "--allowedTools", ",".join(ALLOWED_TOOLS)]
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout_min * 60, env=env, input=prompt)
    except subprocess.TimeoutExpired as e:
        return {"error": f"timeout {timeout_min} min", "raw": ((e.stdout or b"").decode(errors="replace"))[-2000:], "wall_sec": round(time.time() - started, 1)}
    data = {"tool_uses": 0, "tool_names": {}, "texts": [], "cwd": str(workdir)}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use":
                    data["tool_uses"] += 1
                    data["tool_names"][c.get("name", "?")] = data["tool_names"].get(c.get("name", "?"), 0) + 1
                elif c.get("type") == "text":
                    data["texts"].append(c["text"])
        elif t == "result":
            data["usage"] = ev.get("usage")
            data["total_cost_usd"] = ev.get("total_cost_usd")
            data["result"] = ev.get("result")
            data["is_error"] = ev.get("is_error")
    if "usage" not in data:
        data["error"] = "no result event"
        data["raw"] = (proc.stdout + proc.stderr)[-3000:]
    text = str(data.get("result") or "") + str(data.get("raw") or "")
    if (data.get("is_error") or "hit your" in text or "rate_limit" in text) and "limit" in text:
        data["error"] = "rate_limit"
        data["reset_text"] = text[:300]
    data["wall_sec"] = round(time.time() - started, 1)
    return data


def run_claude_retry(workdir: Path, prompt: str, model: str, session: str, timeout_min: int) -> dict:
    """agentrun.run_claude_retry と同じ呼び方。上限で止まったら回復まで待ってやり直す。session は使わない。"""
    while True:
        data = run_claude(workdir, prompt, model, timeout_min)
        if data.get("error") == "rate_limit":
            wait = seconds_until_reset(data.get("reset_text", ""))
            print(f"利用上限に到達。{wait // 60} 分待って再開する", flush=True)
            time.sleep(wait)
            continue
        return data


if __name__ == "__main__":
    # 読み手の作業フォルダで、読み込まれている CLAUDE.md を聞く（やり直しの前の確認）
    d = WORK_ROOT / "probe"
    d.mkdir(parents=True, exist_ok=True)
    out = run_claude(d, "あなたの文脈に読み込まれている CLAUDE.md（利用者やプロジェクトの指示ファイル）のパスを、すべて列挙してください。1 つも無ければ「無し」とだけ答えてください。ツールは使わないでください。", "claude-haiku-5-5", 5)
    print(out.get("result"), out.get("error"))
