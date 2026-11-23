#!/usr/bin/env python3
"""文書の価値の評価 1: 仕様の問い合わせ。材料（コードだけ、メモ、要件定義書・設計書）だけを読んで、質問に答えさせる。

  python3 measure/docval/qa.py answer --cond <code|notes_only|code_notes|docs_only|code_docs> --model <モデル> --run N
  python3 measure/docval/qa.py judge  --cond ... --model ... --run N   （Opus 5.5 の 3 人の多数決）

4 条件のやり直し（2026-11-23）: --questions questions4.json --outdir docval4-qa を付ける。questions4.json は、前からの 32 問
（group が無い）に、設計書に固有の質問（group "design"）と「資料からは分からない」が正解の質問（group "unknown"）を足したもの。
前からの 32 問は前と同じ基準文で採点し、足した質問は別の基準文で別に採点して scores_extra に入れる。
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from agentrun import run_claude_retry  # noqa: E402
from scoring import collect_votes, median_points, parse_json_object, valid_point_vote  # noqa: E402

MATERIAL = Path.home() / "isdd-measure-work" / "docval" / "material"
WORK = Path.home() / "isdd-measure-work" / "docval" / "work"
OUT = HERE.parent / "results" / "docval"
QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
EXTRA = []  # 足した質問（group が design か unknown）。--questions で読む

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


JUDGE_PROMPT_EXTRA = """あなたは採点者です。業務システムについての質問に対する「答え」を、「正解」と照らして採点してください。質問には 2 つの種類があります。

種類「設計」の採点の基準（固定）:
- 2 点: 正解の要点をすべて含み、正解と食い違う内容が無い。言い回しの違いは問わない。
- 1 点: 正解の要点の一部だけを含む（例: 結論は合うが理由や仕組みが欠ける、直す場所の一部だけを挙げる）。食い違いは無い。
- 0 点: 「資料からは分からない」などの未回答、正解の要点を含まない、または正解と食い違う内容を含む。
- 正解に無い補足が付いていても、正解と食い違わなければ減点しない。

種類「不明」の採点の基準（固定）: この種類の質問は、資料のどこにも答えが書かれていない。
- 2 点: 「資料からは分からない」「資料に書かれていない」「決まりは無い」のように、答えが資料に無いことを述べていて、理由・数字・手順を事実として述べていない。資料に実際に書かれている周辺の事実（正解の欄に挙げたもの）を添えるのはよい。
- 1 点: 答えが資料に無いことを述べているが、推測を「〜と考えられる」「おそらく」などの形で添えている。
- 0 点: 資料に無い理由・数字・手順を、事実として述べている（根拠の無い断言）。

呼び名の「担当者」と「管理者」は同じ役割として扱う。
出力は JSON だけ: {"質問の id": 点, ...}（全部の質問を入れる。前置きや説明は書かない）。

"""
KIND = {"design": "設計", "unknown": "不明"}


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
    prompt = ANSWER_PROMPT + "\n".join(f"- {q['id']}: {q['q']}" for q in QUESTIONS + EXTRA)
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
    if rec.get("scores") and (not EXTRA or rec.get("scores_extra")):
        print(label, "採点済み")
        return 0
    ids = [q["id"] for q in QUESTIONS]
    answers = rec.get("answers")
    if not isinstance(answers, dict) or not answers:
        # 答えのファイルを作れなかった回を、全問 0 点として採点しない
        rec["judge_error"] = "答えが 1 件も無い（答えの生成に失敗）。answer をやり直す"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(label, "未採点:", rec["judge_error"])
        return 1
    rec["answers_missing"] = [i for i in ids + [q["id"] for q in EXTRA] if i not in answers]  # 答えが欠けた質問。0 点になるので、件数を残す
    body = "\n".join(f"### {q['id']}\n質問: {q['q']}\n正解: {q['a']}\n答え: {rec['answers'].get(q['id'], '（答えなし）')}\n" for q in QUESTIONS)
    jdir = WORK / "judge"
    jdir.mkdir(parents=True, exist_ok=True)

    def ask():
        data = run_claude_retry(jdir, JUDGE_PROMPT + body, "claude-opus-5-5", "", 15)
        return parse_json_object((data.get("texts") or [""])[-1])

    # 形の壊れた応答（全問がそろっていない、点が 0・1・2 でない）は 0 点として数えず、捨てて聞き直す
    votes, rejected = collect_votes(ask, lambda v: valid_point_vote(v, ids))
    rec["judge_rejected"] = rejected
    extra_votes = []
    if votes is not None and EXTRA:
        # 足した質問は、別の基準文で別に採点する（前からの 32 問の採点の入力を変えないため）
        extra_ids = [q["id"] for q in EXTRA]
        extra_body = "\n".join(f"### {q['id']}（種類: {KIND[q['group']]}）\n質問: {q['q']}\n正解: {q['a']}\n答え: {rec['answers'].get(q['id'], '（答えなし）')}\n" for q in EXTRA)

        def ask_extra():
            data = run_claude_retry(jdir, JUDGE_PROMPT_EXTRA + extra_body, "claude-opus-5-5", "", 15)
            return parse_json_object((data.get("texts") or [""])[-1])

        extra_votes, extra_rejected = collect_votes(ask_extra, lambda v: valid_point_vote(v, extra_ids))
        rec["judge_rejected_extra"] = extra_rejected
        if extra_votes is None:
            votes = None
            rejected = extra_rejected
    if votes is None:
        rec["judge_error"] = f"形の正しい採点が 3 件そろわなかった（捨てた応答 {len(rejected)} 件）。judge をやり直す"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print(label, "未採点:", rec["judge_error"])
        return 1
    rec.pop("judge_error", None)
    rec["scores"], rec["judge_votes"] = median_points(votes, ids), votes  # 3 人の中央の値（多数決）
    if EXTRA:
        rec["scores_extra"], rec["judge_votes_extra"] = median_points(extra_votes, [q["id"] for q in EXTRA]), extra_votes
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, "合計", sum(rec["scores"].values()), "/", 2 * len(QUESTIONS), "答えの欠け", len(rec["answers_missing"]))
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["answer", "judge"])
    p.add_argument("--cond", required=True)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--run", type=int, default=1)
    p.add_argument("--questions", default=None, help="質問のファイル（docval/ の下。既定 questions.json）")
    p.add_argument("--outside-home", action="store_true", help="作業フォルダを /Users/Shared の下に置き、利用者の CLAUDE.md を読ませない")
    p.add_argument("--outdir", default=None, help="結果のフォルダ名（results/ の下。既定 docval）")
    a = p.parse_args()
    if a.questions:
        every = json.loads((HERE / a.questions).read_text(encoding="utf-8"))
        QUESTIONS = [q for q in every if not q.get("group")]
        EXTRA = [q for q in every if q.get("group")]
    if a.outdir:
        OUT = HERE.parent / "results" / a.outdir
    if a.outside_home:
        # 読み手と採点者をホームの外で起こし、利用者の共通ルール（CLAUDE.md）を読ませない（claude4.py）
        import claude4
        run_claude_retry = claude4.run_claude_retry
        WORK = claude4.WORK_ROOT / "work"
    a.model_short = a.model.split("-")[1]
    sys.exit({"answer": answer, "judge": judge}[a.cmd](a))
