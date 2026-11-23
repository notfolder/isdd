#!/usr/bin/env python3
"""文書評価のやり直し（2026-11-23）の材料を作る。同じコード・同じ付属テスト・同じ README で、
要件定義書あり・なし × 設計書あり・なしの 4 条件と、古い文書の 2 条件を作る。

  python3 measure/docval/build4.py            材料を ~/isdd-measure-work/docval/material/ の下に作り、manifest4.json を書く
  python3 measure/docval/build4.py --check    作ってある材料が manifest4.json と同じかを確かめる

出発点: isdd が依頼 10 回を通して作った成果物（measure/results/longrun-isdd-opus-r2/snapshot-stage10。git の管理外）。
どの条件からも外すもの: 対応表（docs/trace_map.md）、.history、AGENTS.md、CLAUDE.md、scripts/isdd、.claude、採点用の残り物。
条件（<R> は README の版。d4 は元の README、d4m は起動方法とテストの節だけに減らした README）:
  <R>_none   文書なし
  <R>_req    docs/requirements.md だけ
  <R>_des    docs/detail_design.md だけ
  <R>_both   両方
  <R>_lack   両方。ただし文書は依頼 5 の時点のもの（あとの 5 つの依頼で増えた仕様が欠けている。longrun-isdd-opus-r1 の snapshot-stage5）
  <R>_contra 両方。ただし文書の 4 つの決まりを、今のコードと逆に書き換えたもの（CONTRA）
  <R>bug_none・req・des・both  コードに 6 つの不具合（mutations.md、bug4.patch）を入れたもの。文書・README・テストは正しいまま
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
SRC = RESULTS / "longrun-isdd-opus-r2" / "snapshot-stage10"
OLD_DOCS = RESULTS / "longrun-isdd-opus-r1" / "snapshot-stage5" / "docs"
MATERIAL = Path.home() / "isdd-measure-work" / "docval" / "material"
MANIFEST = HERE / "manifest4.json"
DROP = shutil.ignore_patterns(".history", "AGENTS.md", "CLAUDE.md", "scripts", ".claude", ".venv", "__pycache__", ".pytest_cache", ".git",
                              "REQUEST.md", "STAGE_DONE", "contract.md", "docs", "results", "data")
KEEP_README_SECTIONS = ("起動方法", "テスト")

# 文書を今のコードと逆に書き換える 4 つの決まり（コード・README・テストは変えない）
CONTRA = [
    ("X1 同時に借りられる上限: 2 件 → 3 件", [(r"2 件(?!目)", "3 件")]),
    ("X2 延長で延びる日数: 7 日 → 14 日（延長後の期限は貸出日 + 28 日）", [(r"(?<![0-9])21 日", "28 日"), (r"(?<![0-9])7 日", "14 日")]),
    ("X3 貸出日にできる範囲: 30 日前まで → 10 日前まで", [(r"(?<![0-9])31 日前", "11 日前"), (r"(?<![0-9])30 日前", "10 日前")]),
    ("X4 履歴を見られる人: 管理者だけ → 社員も自分が借りた分は見られる", [
        ("総務の決まり（履歴は管理者だけ。社員には自分の分も見せない）", "総務の決まり（履歴は管理者が全部を見られ、社員は自分が借りた分だけを見られる）"),
        ("履歴の画面を開けるのは、その時点で役割が管理者の利用者だけ。社員には自分が借りた分も見せない（総務の決まり）", "履歴の画面は、管理者はすべての履歴を、社員は自分が借りた分だけを見られる（総務の決まり）"),
        ("不可（貸出状況へ移り `.error`。自分が借りた分も見せない）", "可（自分が借りた分だけ）"),
    ]),
]


def minimal_readme(text: str) -> str:
    """README を、先頭の説明と、起動方法・テストの節だけにする。"""
    parts = re.split(r"(?m)^(?=## )", text)
    keep = [parts[0]] + [p for p in parts[1:] if p.splitlines()[0][3:].strip() in KEEP_README_SECTIONS]
    return "".join(keep).rstrip() + "\n"


def contra(text: str, counts: dict) -> str:
    for name, pairs in CONTRA:
        for pat, new in pairs:
            if pat.startswith(("総務", "履歴", "不可")):
                n = text.count(pat)
                text = text.replace(pat, new)
            else:
                text, n = re.subn(pat, new, text)
            counts[name] = counts.get(name, 0) + n
    return text


def build() -> dict:
    notes = {}
    for readme in ("d4", "d4m"):
        for bug in ("", "bug"):
            for cond in ("none", "req", "des", "both") + (("lack", "contra") if not bug else ()):
                dest = MATERIAL / f"{readme}{bug}_{cond}"
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(SRC, dest, ignore=DROP)
                if readme == "d4m":
                    (dest / "README.md").write_text(minimal_readme((SRC / "README.md").read_text(encoding="utf-8")), encoding="utf-8")
                if bug:
                    subprocess.run(["patch", "-p1", "-s", "-d", str(dest), "-i", str(HERE / "bug4.patch")], check=True)
                docs_from = OLD_DOCS if cond == "lack" else SRC / "docs"
                names = {"none": [], "req": ["requirements.md"], "des": ["detail_design.md"]}.get(cond, ["requirements.md", "detail_design.md"])
                for name in names:
                    (dest / "docs").mkdir(exist_ok=True)
                    text = (docs_from / name).read_text(encoding="utf-8")
                    if cond == "contra":
                        counts = {}
                        text = contra(text, counts)
                        notes[f"{readme}_contra/{name}"] = counts
                    (dest / "docs" / name).write_text(text, encoding="utf-8")
    return notes


def manifest() -> dict:
    out = {}
    for d in sorted(MATERIAL.glob("d4*_*")):
        out[d.name] = {str(f.relative_to(d)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(d.rglob("*")) if f.is_file() and "__pycache__" not in f.parts}
    return out


if __name__ == "__main__":
    if "--check" in sys.argv:
        want = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
        got = manifest()
        bad = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
        print("一致" if not bad else f"食い違い: {bad}")
        sys.exit(1 if bad else 0)
    notes = build()
    files = manifest()
    MANIFEST.write_text(json.dumps({"source": str(SRC.relative_to(HERE.parent)), "old_docs": str(OLD_DOCS.relative_to(HERE.parent)),
                                    "contra": [c[0] for c in CONTRA], "contra_replacements": notes, "files": files}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for name, fs in files.items():
        print(name, len(fs), "ファイル")
    print(json.dumps(notes, ensure_ascii=False, indent=1))
