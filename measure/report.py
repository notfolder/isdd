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
    print("| 群・回 | 段 | 妥当 | 通過 | 退行 | 作りすぎの目安（公開関数 / 行） | 新規トークン（入力＋出力＋キャッシュ作成） | 総トークン（キャッシュ読み込み込み） | ツール呼び出し | 所要（秒） |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for label, st, info in rows:
        ob = info.get("overbuild") or {}
        reg = info.get("regressions")
        snap = summary.parent / f"snapshot-stage{st}"
        if label.startswith("isdd"):
            valid = any(sk.startswith("isdd") for sk in info.get("skills_called", [])) or all((snap / f).exists() for f in ("docs/requirements.md", "docs/detail_design.md", "docs/trace_map.md"))
        else:
            valid = not info.get("isdd_skills_visible") and not info.get("skills_called")
        u = info.get("usage") or {}
        fresh = (u.get("input_tokens", 0) + u.get("output_tokens", 0) + u.get("cache_creation_input_tokens", 0)) if u else info.get("agent_tokens", "―")
        total = u.get("total_tokens", "―") if u else "―"
        print(f"| {label} | {st} | {'○' if valid else '×'} | {info.get('passed')}/{info.get('total')} | {len(reg) if reg is not None else '―'} | "
              f"{ob.get('public_functions')} / {ob.get('lines')} | {fresh} | {total} | {info.get('tool_uses', '―')} | {info.get('agent_duration_sec', info.get('wall_sec'))} |")
    print()
    print("## 最終段の落ちたテスト")
    for label, st, info in rows:
        if st == 3:
            fails = sorted(k.replace('[chromium]', '') for k, v in (info.get('tests') or {}).items() if v != 'pass')
            print(f"- {label}: {', '.join(fails) or '無し'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
