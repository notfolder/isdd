#!/usr/bin/env python3
"""文書の価値の評価 2（不具合か仕様かの判定）と評価 3（依頼者のレビュー）。

  python3 measure/docval/t23.py triage --cond <code_bug|code_notes_bug|code_docs_bug> --model <モデル> --run N
  python3 measure/docval/t23.py review --cond <code_bug|notes_err|req_err> --model <モデル> --run N
評価 2 は答えの鍵と突き合わせて自動で採点する。評価 3 は Opus 5.5 の 3 人の多数決で、挙げられた指摘を仕込んだ 6 つの誤りに対応づける。
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
from scoring import collect_votes, parse_json_object, valid_found_vote  # noqa: E402

MATERIAL = Path.home() / "isdd-measure-work" / "docval" / "material"
WORK = Path.home() / "isdd-measure-work" / "docval" / "work"
OUT = HERE.parent / "results" / "docval"

REPORTS = [
    ("R1", "bug", "社員が、同時に 3 件の備品を借りられました。"),
    ("R2", "spec", "貸出の登録の画面で、借りる社員の一覧に、管理者の名前が出てきません。"),
    ("R3", "bug", "社員でログインしたら、貸出と返却の履歴の画面が見られました。"),
    ("R4", "spec", "社員が「借りる」を押したのに、貸出中にならず「申請中」のままです。"),
    ("R5", "bug", "期限の延長をしたら、返却の期限が 14 日延びました。"),
    ("R6", "spec", "一度延長した備品を、もう一度延長しようとしたら、できませんでした。"),
    ("R7", "bug", "備品を借りたままの社員に退職の処理をしたら、そのまま通りました。"),
    ("R8", "spec", "退職の処理をした社員が、アカウントの一覧に「無効」と出たまま残っています。"),
    ("R9", "bug", "CSV を出力したら、借りている社員の名前が入っていました。"),
    ("R10", "spec", "31 日前の日付で貸出を登録しようとしたら、受け付けられませんでした。"),
    ("R11", "bug", "貸出日からちょうど 14 日目の備品が、「期限超過」と表示されています。"),
    ("R12", "spec", "管理番号を「pc-001」で登録したのに、一覧には「PC-001」と出ています。"),
]

TRIAGE_PROMPT = """あなたは、この備品の貸出管理システムの保守を引き継いだ担当者です。前任者にも、依頼した総務の担当者にも、今は連絡が取れません。
利用者から、下の 12 件の「動き」の報告が届きました。どれも実際にこのシステムで起きています（再現を確かめてあります）。
作業ディレクトリにある資料（この中にあるものがすべてです）だけを読んで、それぞれの動きが「仕様どおり」（依頼者が意図した動き）か「不具合」（依頼者の意図と違う動き）かを判定してください。

決まり:
- 資料から根拠が取れるものだけを「仕様どおり」「不具合」と判定する。根拠が取れなければ「判断できない」とする。
- コードがあっても実行しない。ファイルは変更しない（答えのファイルを 1 つ作るだけ）。インターネットは使わない。
- 作業ディレクトリ直下の triage.json に、{"R1": {"verdict": "仕様どおり" か "不具合" か "判断できない", "basis": "根拠にした資料の場所と内容を 1 文で"}, ...} の形で 12 件すべてを書く。書き終えたら「完了」とだけ答える。

報告:
"""

INTENT = """- アカウント: 社員が自分で登録する。最初の 1 人は自動で管理者、2 人目からは社員。管理者は社員を管理者にしたり戻したりできる。管理者が 1 人も居なくなる操作はできない。
- 備品: 管理者が登録・修正・削除する。管理番号は大文字と小文字を区別せず、大文字にそろえる。貸出中の備品は削除できない。分類は「PC」「周辺機器」「その他」。
- 貸出: 管理者が、空いている備品を社員に貸す。1 人が同時に借りられるのは 2 件まで。管理者は借りられない。貸出日は今日から 30 日前まで。
- 返却: 管理者と、借りている本人ができる。
- 期限: 返却の期限は貸出日から 14 日。貸出日から 15 日以上たって返っていなければ「期限超過」（14 日目までは「貸出中」）。期限超過の備品を持つ社員には貸さない。
- 延長: 1 回の貸出につき 1 回だけ、7 日延ばせる。期限超過の備品は延長できない。操作できるのは管理者。
- 履歴: 貸出と返却の履歴を残す。見られるのは管理者だけ。社員は自分の分も見られない。
- 社員が借りる: 社員が画面から「借りる」を押すと申請になり、管理者が承認して初めて貸出になる。
- 退職: 退職の処理をした社員のアカウントは消さずに「無効」で残す。備品を借りたままの社員は退職の処理ができない。
- CSV: 管理者が一覧を CSV で出せる。借りている社員は社員番号だけを出し、名前は出さない。
- 誰でも（ログインしなくても）貸出状況の一覧を見られる。"""

REVIEW_PROMPT = """あなたは、備品の貸出管理システムを開発会社に依頼した総務の担当者です。あなたが依頼した内容の要点は次のとおりです。

""" + INTENT + """

開発会社から成果物が届きました。作業ディレクトリにあるものがすべてです。
成果物の中身を確かめて、あなたが依頼した内容と違っている所を、すべて挙げてください。

決まり:
- 依頼した内容と食い違っている所だけを挙げる。依頼に無い細かい点（文言、画面の見た目、技術の選び方）は挙げない。
- コードがあっても実行しない。ファイルは変更しない（答えのファイルを 1 つ作るだけ）。インターネットは使わない。
- 作業ディレクトリ直下の issues.json に、[{"what": "何が、依頼とどう違うか（1 文）", "where": "成果物のどこに書いてあるか"}, ...] の形で書く。違いが無ければ空の配列。書き終えたら「完了」とだけ答える。
"""

MUTATIONS = {"M1": "1 人が同時に借りられる数が 3 件になっている（依頼は 2 件）", "M2": "社員も履歴を見られる（依頼は管理者だけ）",
             "M3": "延長が 14 日延びる（依頼は 7 日）", "M4": "借りたままの社員に退職の処理ができる（依頼はできない）",
             "M5": "CSV に借りている社員の名前が出る（依頼は社員番号だけ）", "M6": "貸出日から 14 日以上で期限超過になる（依頼は 15 日以上）"}

REVIEW_JUDGE = """あなたは採点者です。依頼者が成果物を確かめて挙げた「指摘」の一覧を、成果物に仕込まれていた 6 つの誤りと対応づけてください。

仕込まれていた誤り:
""" + "\n".join(f"- {k}: {v}" for k, v in MUTATIONS.items()) + """

基準（固定）:
- 指摘が、誤りの内容（何がどう違うか）を正しく言い当てていれば、その誤りを「見つけた」とする。数字や向きが違う指摘は見つけたことにしない。
- どの誤りにも当たらない指摘は「ほかの指摘」として数える。
出力は JSON だけ: {"found": ["M1", ...], "other": ほかの指摘の数}（前置きや説明は書かない）。

指摘の一覧:
"""


def run_reader(label, cond, prompt, model, outfile):
    work = WORK / label
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(MATERIAL / cond, work, symlinks=False)
    started = time.time()
    data = run_claude_retry(work, prompt, model, "", 40)
    result = None
    try:
        result = json.loads((work / outfile).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(label, outfile, "を読めない:", e)
    return result, {"wall_sec": round(time.time() - started, 1), "usage": data.get("usage"), "cost_usd": data.get("total_cost_usd"),
                    "tool_uses": data.get("tool_uses"), "error": data.get("error")}


def triage(args):
    label = f"triage-{args.cond}-{args.model_short}-r{args.run}"
    out = OUT / f"{label}.json"
    if out.exists():
        print(label, "済み")
        return 0
    prompt = TRIAGE_PROMPT + "\n".join(f"- {rid}: {text}" for rid, _, text in REPORTS)
    result, meta = run_reader(label, args.cond, prompt, args.model, "triage.json")
    unreadable = not isinstance(result, dict)  # 判定のファイルを作れなかった回。「判断できない」と区別して残す
    result = result if isinstance(result, dict) else {}
    score = {"bug_caught": 0, "spec_right": 0, "wrong": 0, "undecided": 0}
    detail = {}
    for rid, kind, _ in REPORTS:
        verdict = str((result.get(rid) or {}).get("verdict", ""))
        got = "bug" if "不具合" in verdict else ("spec" if "仕様" in verdict else "undecided")
        detail[rid] = got
        if got == "undecided":
            score["undecided"] += 1
        elif got == kind:
            score["bug_caught" if kind == "bug" else "spec_right"] += 1
        else:
            score["wrong"] += 1
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, "cond": args.cond, "model": args.model, "run": args.run, "answers": result, "detail": detail, "score": score, "result_unreadable": unreadable, **meta},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, score, meta["wall_sec"], "秒")
    return 0


def review(args):
    label = f"review-{args.cond}-{args.model_short}-r{args.run}"
    out = OUT / f"{label}.json"
    if out.exists():
        print(label, "済み")
        return 0
    issues, meta = run_reader(label, args.cond, REVIEW_PROMPT, args.model, "issues.json")
    issues_unreadable = not isinstance(issues, list)  # 指摘のファイルを作れなかった回。「指摘なし」と区別して残す
    issues = issues if isinstance(issues, list) else []
    body = "\n".join(f"{i + 1}. {x.get('what', '')}（{x.get('where', '')}）" for i, x in enumerate(issues) if isinstance(x, dict)) or "（指摘なし）"
    jdir = WORK / "judge"
    jdir.mkdir(parents=True, exist_ok=True)

    def ask():
        data = run_claude_retry(jdir, REVIEW_JUDGE + body, "claude-opus-5-5", "", 15)
        return parse_json_object((data.get("texts") or [""])[-1])

    # 形の壊れた応答を「1 件も見つけていない」として数えず、捨てて聞き直す。3 件そろわなければ結果を書かない
    votes, rejected = collect_votes(ask, lambda v: valid_found_vote(v, MUTATIONS))
    if votes is None:
        print(label, f"未採点: 形の正しい採点が 3 件そろわなかった（捨てた応答 {len(rejected)} 件）。review をやり直す")
        return 1
    found = sorted(m for m in MUTATIONS if sum(m in (v.get("found") or []) for v in votes) >= 2)
    other = sorted(int(v.get("other", 0) or 0) for v in votes)[1]
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"label": label, "cond": args.cond, "model": args.model, "run": args.run, "issues": issues, "found": found, "other": other,
                               "judge_votes": votes, "judge_rejected": rejected, "issues_unreadable": issues_unreadable, **meta}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(label, "見つけた", found, "ほか", other, meta["wall_sec"], "秒")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["triage", "review"])
    p.add_argument("--cond", required=True)
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--run", type=int, default=1)
    a = p.parse_args()
    a.model_short = a.model.split("-")[1]
    sys.exit({"triage": triage, "review": review}[a.cmd](a))
