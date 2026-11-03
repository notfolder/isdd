#!/usr/bin/env python3
"""results/*/summary.json から比較表（Markdown）を出す。"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    rows = []
    for summary in sorted((HERE / "results").glob("*/summary.json")):
        d = json.loads(summary.read_text(encoding="utf-8"))
        label = summary.parent.name
        for st, info in sorted(d["stages"].items()):
            rows.append((label, int(st), info))
    print("| 群・回 | 段 | 通過 | 退行 | 作りすぎの目安（公開関数 / 行） | トークン | ツール呼び出し | 所要（秒） |")
    print("|---|---|---|---|---|---|---|---|")
    for label, st, info in rows:
        ob = info.get("overbuild") or {}
        reg = info.get("regressions")
        print(f"| {label} | {st} | {info.get('passed')}/{info.get('total')} | {len(reg) if reg is not None else '―'} | "
              f"{ob.get('public_functions')} / {ob.get('lines')} | {info.get('agent_tokens', '―')} | {info.get('tool_uses', '―')} | {info.get('agent_duration_sec', info.get('wall_sec'))} |")
    print()
    print("## 最終段の落ちたテスト")
    for label, st, info in rows:
        if st == 3:
            fails = sorted(k.replace('[chromium]', '') for k, v in (info.get('tests') or {}).items() if v != 'pass')
            print(f"- {label}: {', '.join(fails) or '無し'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
