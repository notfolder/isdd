#!/usr/bin/env python3
"""文書の価値の評価 1: 仕様の問い合わせ。材料（コードだけ、メモ、要件定義書・設計書）だけを読んで、質問に答えさせる。

  python3 measure/docval/qa.py answer --cond <code|notes_only|code_notes|docs_only|code_docs> --model <モデル> --run N
  python3 measure/docval/qa.py judge  --cond ... --model ... --run N   （Opus 5.5 の 3 人の多数決）
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from agentrun import run_claude_retry  # noqa: E402

MATERIAL = Path.home() / "isdd-measure-work" / "docval" / "material"
WORK = Path.home() / "isdd-measure-work" / "docval" / "work"
OUT = HERE.parent / "results" / "docval"
QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))

ANSWER_PROMPT = """あなたは、この備品の貸出管理システムを前任者から引き継いだ担当者です。前任者には連絡が取れません。
作業ディレクトリにある資料（この中にあるものがすべてです）だけを読んで、下の質問に答えてください。

決まり:
- 資料に書いてあること、資料から確かに読み取れることだけを答える。推測で埋めない。資料から分からないことは「資料からは分からない」と答える。
- コードがあっても実行しない。ファイルは変更しない（答えのファイルを 1 つ作るだけ）。インターネットは使わない。
- 答えは 1〜3 文で、具体的に（数字や条件は省かない）。
- 作業ディレクトリ直下の answers.json に、{"質問の id": "答え", ...} の形で全部の答えを書く。書き終えたら「完了」とだけ答える。

質問:
"""

JUDGE_PROMPT = """あなたは採点者です。業務システムの仕様についての質問に対する「答え」を、「正解」と照らして採点してください。

採点の基準（固定）:
- 2 点: 正解の要点をすべて含み、正解と食い違う内容が無い。言い回しの違いは問わない。
- 1 点: 正解の要点の一部だけを含む（例: 数字は合うが条件が欠ける、結論は合うが理由が欠ける）。食い違いは無い。
- 0 点: 「資料からは分からない」などの未回答、正解の要点を含まない、または正解と食い違う内容を含む。
- 正解に無い補足が付いていても、正解と食い違わなければ減点しない。
- 呼び名の「担当者」と「管理者」は同じ役割として扱う。

出力は JSON だけ: {"質問の id": 点, ...}（全部の質問を入れる。前置きや説明は書かない）。

"""


def answer(args):
    label = f"qa-{args.cond}-{args.model_short}-r{args.run}"
    out = OUT / f"{label}.json"
    if out.exists():
        print(label, "済み")
        return 0
    work = WORK / label
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(MATERIAL / args.cond, work, symlinks=False)
    prompt = ANSWER_PROMPT + "\n".join(f"- {q['id']}: {q['q']}" for q in QUESTIONS)
    started = time.time()
    data = run_claude_retry(work, prompt, args.model, "", 40)
    answers = {}
    try:
        answers = json.loads((work / "answers.json").read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(label, "answers.json を読めない:", e)
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, "cond": args.cond, "model": args.model, "run": args.run, "answers": answers,
                               "wall_sec": round(time.time() - started, 1), "usage": data.get("usage"), "cost_usd": data.get("total_cost_usd"),
                               "tool_uses": data.get("tool_uses"), "tool_names": data.get("tool_names"), "error": data.get("error")}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, "答え", len(answers), "件", round(time.time() - started), "秒")
    return 0


def judge(args):
    label = f"qa-{args.cond}-{args.model_short}-r{args.run}"
    path = OUT / f"{label}.json"
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("scores"):
        print(label, "採点済み")
        return 0
    body = "\n".join(f"### {q['id']}\n質問: {q['q']}\n正解: {q['a']}\n答え: {rec['answers'].get(q['id'], '（答えなし）')}\n" for q in QUESTIONS)
    votes = []
    jdir = WORK / "judge"
    jdir.mkdir(parents=True, exist_ok=True)
    for k in range(3):
        data = run_claude_retry(jdir, JUDGE_PROMPT + body, "claude-opus-5-5", "", 15)
        text = (data.get("texts") or [""])[-1]
        try:
            votes.append(json.loads(text[text.index("{"): text.rindex("}") + 1]))
        except Exception:  # noqa: BLE001
            votes.append({})
    scores = {}
    for q in QUESTIONS:
        vs = sorted(int(v.get(q["id"], 0)) for v in votes)
        scores[q["id"]] = vs[1]  # 3 人の中央の値（多数決）
    rec["scores"], rec["judge_votes"] = scores, votes
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, "合計", sum(scores.values()), "/", 2 * len(QUESTIONS))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["answer", "judge"])
    p.add_argument("--cond", required=True)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--run", type=int, default=1)
    a = p.parse_args()
    a.model_short = a.model.split("-")[1]
    sys.exit({"answer": answer, "judge": judge}[a.cmd](a))
