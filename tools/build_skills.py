#!/usr/bin/env python3
"""
build_skills.py

shared/ 配下の共通ファイル（references と scripts）を、shared/manifest.json の一覧どおりに
各スキルの references/ と scripts/ へ複製する。

複製した結果は git に含める。gh skill publish はリポジトリの内容をそのまま公開し、
install.sh も skills/ をそのまま展開するため、複製をコミットしておけば両者の中身が一致する。

skills/<スキル>/references/ と skills/<スキル>/scripts/ はこのスクリプトだけが書き込む。
手で編集した場合は --check が差分として検出する。

使用方法:
  python3 tools/build_skills.py           # 複製を作り直す
  python3 tools/build_skills.py --check   # 複製が正本と一致するかだけを確かめる（変更しない）

終了コード:
  0: 一致している（--check）、または複製を作り直した
  1: 不一致がある（--check）、または manifest・正本に誤りがある
"""

import argparse
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared"
SKILLS = ROOT / "skills"
KINDS = ("references", "scripts")
VERSION_RE = re.compile(r'^\s*version:\s*"?([^"\s]+)"?\s*$', re.MULTILINE)


def load_manifest() -> Dict[str, Dict[str, List[str]]]:
    """manifest.json を読み、スキル名から種類ごとのファイル一覧への対応を返す"""
    data = json.loads((SHARED / "manifest.json").read_text(encoding="utf-8"))
    return data["skills"]


def validate(manifest: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """manifest と正本の矛盾を調べ、エラーの説明の一覧を返す"""
    errors = []
    skill_dirs = sorted(d.name for d in SKILLS.iterdir() if (d / "SKILL.md").exists())
    for name in skill_dirs:
        if name not in manifest:
            errors.append(f"manifest に無いスキル: skills/{name}")
    used = {kind: set() for kind in KINDS}
    for name, kinds in manifest.items():
        if name not in skill_dirs:
            errors.append(f"manifest のスキルが skills/ に無い: {name}")
        for kind in KINDS:
            for fname in kinds.get(kind, []):
                used[kind].add(fname)
                if not (SHARED / kind / fname).is_file():
                    errors.append(f"正本が無い: shared/{kind}/{fname}（{name} が参照）")
    for kind in KINDS:
        for path in sorted((SHARED / kind).iterdir()):
            if path.is_file() and path.name not in used[kind]:
                errors.append(f"どのスキルにも複製されない正本: shared/{kind}/{path.name}")
    versions = {}
    for name in skill_dirs:
        match = VERSION_RE.search((SKILLS / name / "SKILL.md").read_text(encoding="utf-8"))
        versions[name] = match.group(1) if match else "（なし）"
    if len(set(versions.values())) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in versions.items())
        errors.append(f"metadata.version が揃っていない: {detail}")
    return errors


def diff_skill(name: str, kinds: Dict[str, List[str]]) -> List[str]:
    """1 スキル分の複製と正本の差分の説明を返す"""
    diffs = []
    for kind in KINDS:
        expected = set(kinds.get(kind, []))
        dest = SKILLS / name / kind
        actual = {p.name for p in dest.iterdir() if p.is_file()} if dest.is_dir() else set()
        for fname in sorted(expected - actual):
            diffs.append(f"未複製: skills/{name}/{kind}/{fname}")
        for fname in sorted(actual - expected):
            diffs.append(f"余分: skills/{name}/{kind}/{fname}")
        for fname in sorted(expected & actual):
            if not filecmp.cmp(SHARED / kind / fname, dest / fname, shallow=False):
                diffs.append(f"正本と違う: skills/{name}/{kind}/{fname}")
    return diffs


def build_skill(name: str, kinds: Dict[str, List[str]]) -> None:
    """1 スキル分の references/ と scripts/ を正本から作り直す"""
    for kind in KINDS:
        dest = SKILLS / name / kind
        files = kinds.get(kind, [])
        if dest.exists():
            shutil.rmtree(dest)
        if not files:
            continue
        dest.mkdir(parents=True)
        for fname in files:
            shutil.copy2(SHARED / kind / fname, dest / fname)


def main() -> int:
    parser = argparse.ArgumentParser(description="共通ファイルを各スキルへ複製する")
    parser.add_argument("--check", action="store_true", help="複製が正本と一致するかだけを確かめる")
    args = parser.parse_args()

    manifest = load_manifest()
    errors = validate(manifest)
    if errors:
        for line in errors:
            print(f"エラー: {line}", file=sys.stderr)
        return 1

    if args.check:
        diffs = [d for name, kinds in manifest.items() for d in diff_skill(name, kinds)]
        if diffs:
            for line in diffs:
                print(f"不一致: {line}", file=sys.stderr)
            print("python3 tools/build_skills.py を実行して複製を作り直してください。", file=sys.stderr)
            return 1
        print(f"一致: {len(manifest)} スキルの複製が shared/ と一致しています。")
        return 0

    for name, kinds in manifest.items():
        build_skill(name, kinds)
    print(f"複製: {len(manifest)} スキルの references/ と scripts/ を shared/ から作り直しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
