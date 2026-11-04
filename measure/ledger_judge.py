#!/usr/bin/env python3
"""計測 5 の判定。隠し台帳と、要件定義書（isdd 群）または最終報告（対照群）、依頼者役とのやり取りの記録を Opus に突き合わせさせる。

  python3 measure/ledger_judge.py --ledger measure/ledger/stage1.md --workdir <作業ディレクトリ> --log <stageN.log> --out <結果 JSON>

出力: {"items": {"L1": {"asked": true/false, "in_requirements": "一致|食い違い|無し", "note": ...}, ...},
       "asked": n, "matched": n, "mismatched": n, "missing": n, "extra_decisions": n}
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from agentrun import run_claude_retry  # noqa: E402

PROMPT = """あなたは要件定義の採点者です。次の 3 つを読んで、台帳の項目ごとに判定し、JSON だけを出力してください。

[隠し台帳]（依頼者が本当は望んでいたこと。依頼文には書かれていない）
{ledger}

[開発者と依頼者のやり取りの記録]（開発者の応答と、依頼者役の答え）
{log}

[開発者が書いた要件定義書]（無ければ「（無し）」）
{req}

判定:
- asked: 開発者がその項目について依頼者に質問したか（記録に質問があれば true）。
- in_requirements: 要件定義書にその項目が「一致」して書かれているか、「食い違い」（別の内容で決めている）か、「無し」（書かれていない）か。要件定義書が無ければ、やり取りの記録の最終報告で判断する。
- extra_decisions: 台帳にも依頼文にも無いことを開発者が決めた項目の数（要件定義書の「依頼に無く自分で決めた項目」の表や報告から数える）。

出力は次の JSON だけ:
{{"items": {{"L1": {{"asked": true, "in_requirements": "一致", "note": "..."}}, ...}}, "extra_decisions": 0}}
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-opus-5-5")
    a = ap.parse_args()
    ledger = Path(a.ledger).read_text(encoding="utf-8")
    log = Path(a.log).read_text(encoding="utf-8")[-40000:]
    req_path = Path(a.workdir) / "docs" / "requirements.md"
    req = req_path.read_text(encoding="utf-8")[:40000] if req_path.exists() else "（無し）"
    prompt = PROMPT.format(ledger=ledger, log=log, req=req)
    data = run_claude_retry(Path(a.workdir).parent, prompt, a.model, "", 20)
    text = str(data.get("result") or "")
    start, end = text.find("{"), text.rfind("}")
    result = {}
    if start >= 0 and end > start:
        try:
            result = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            result = {"error": "json parse", "raw": text[-2000:]}
    items = result.get("items", {})
    summary = {"asked": sum(1 for v in items.values() if v.get("asked")),
               "matched": sum(1 for v in items.values() if v.get("in_requirements") == "一致"),
               "mismatched": sum(1 for v in items.values() if v.get("in_requirements") == "食い違い"),
               "missing": sum(1 for v in items.values() if v.get("in_requirements") == "無し"),
               "extra_decisions": result.get("extra_decisions"), "n_items": len(items)}
    result["summary"] = summary
    result["judge_tokens"] = sum((data.get("usage") or {}).values()) if data.get("usage") else None
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
