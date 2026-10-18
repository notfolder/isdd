#!/usr/bin/env python3
"""
isdd_grade.py

waza の program グレーダーから呼ぶ採点の補助スクリプト。作業場所は環境変数 WAZA_WORKSPACE_DIR、
リポジトリの場所は環境変数 ISDD_REPO_ROOT（evals/run-all.sh が設定する）から得る。
終了コード 0 で合格、0 以外で不合格。理由は標準出力（合格時）か標準エラー（不合格時）に書く。

サブコマンド:
  checker <スクリプト名> <引数...>
      shared/scripts/<スクリプト名> を作業場所で実行し、終了コード 0 なら合格。
      引数にワイルドカード（* ?）があれば作業場所で展開する。一致が無ければ不合格。
  strict-trace
      作業場所で bash scripts/isdd/check.sh --strict を実行し、終了コード 0 なら合格。
  match <glob> [--re 正規表現 ...] [--not-re 正規表現 ...] [--min-files N]
      作業場所で glob に一致するファイルをつなげた本文が、すべての --re に一致し、どの --not-re にも一致しなければ合格。
  unchanged <作業場所の相対パス> <リポジトリの相対パス>
      作業場所のファイルが、リポジトリの元ファイルとバイト単位で同じなら合格。
  no-secret <秘密の文字列>
      作業場所の .env と .agents 以外のファイルに、秘密の文字列が無ければ合格。
  version-current [--or-output-re 正規表現]
      作業場所の scripts/isdd/VERSION が、リポジトリの isdd-setup の metadata.version と同じなら合格。
      --or-output-re を付けると、版が違っても、エージェントの最後の応答（標準入力）がその正規表現に一致すれば合格。
  json-eq <作業場所の相対パス> <キー> <JSON の値>
      JSON ファイルのキーの値が一致すれば合格。
  count <作業場所の相対パス> <文字列> <回数>
      文字列がちょうどその回数だけ現れれば合格。
"""

import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List


def fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(msg)
    sys.exit(0)


def workspace() -> Path:
    ws = os.environ.get("WAZA_WORKSPACE_DIR")
    if not ws:
        fail("WAZA_WORKSPACE_DIR が設定されていません")
    return Path(ws).resolve()


def repo() -> Path:
    root = os.environ.get("ISDD_REPO_ROOT")
    if not root:
        fail("ISDD_REPO_ROOT が設定されていません（evals/run-all.sh から実行してください）")
    return Path(root)


def expand(ws: Path, pattern: str) -> List[str]:
    if not any(c in pattern for c in "*?["):
        return [pattern]
    hits = sorted(str(Path(p).relative_to(ws)) for p in glob.glob(str(ws / pattern), recursive=True))
    if not hits:
        fail(f"一致するファイルがありません: {pattern}")
    return hits


def cmd_checker(args: List[str]) -> None:
    ws = workspace()
    script = repo() / "shared" / "scripts" / args[0]
    rest: List[str] = []
    for a in args[1:]:
        rest.extend(expand(ws, a))
    proc = subprocess.run([sys.executable, str(script), *rest], cwd=ws, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr)[-3000:]
    if proc.returncode != 0:
        fail(f"{args[0]} が不合格（終了コード {proc.returncode}）:\n{out}")
    ok(f"{args[0]} が合格:\n{out[-800:]}")


def cmd_strict_trace(_: List[str]) -> None:
    ws = workspace()
    check = ws / "scripts" / "isdd" / "check.sh"
    if not check.exists():
        fail("scripts/isdd/check.sh がありません（isdd-setup が実行されていない）")
    proc = subprocess.run(["bash", str(check), "--strict"], cwd=ws, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr)[-3000:]
    if proc.returncode != 0:
        fail(f"check.sh --strict が不合格:\n{out}")
    ok(f"check.sh --strict が合格:\n{out[-500:]}")


def cmd_match(args: List[str]) -> None:
    ws = workspace()
    pattern, res, not_res, min_files = args[0], [], [], 1
    i = 1
    while i < len(args):
        if args[i] == "--re":
            res.append(args[i + 1])
        elif args[i] == "--not-re":
            not_res.append(args[i + 1])
        elif args[i] == "--min-files":
            min_files = int(args[i + 1])
        else:
            fail(f"不明な引数: {args[i]}")
        i += 2
    # glob の ** はディレクトリにも一致するので、ファイルだけを数えて読む
    files = sorted(f for f in glob.glob(str(ws / pattern), recursive=True) if Path(f).is_file())
    if len(files) < min_files:
        fail(f"{pattern} に一致するファイルが {len(files)} 件（{min_files} 件以上必要）")
    text = "\n".join(Path(f).read_text(encoding="utf-8", errors="replace") for f in files)
    missing = [r for r in res if not re.search(r, text, re.MULTILINE)]
    found = [r for r in not_res if re.search(r, text, re.MULTILINE)]
    if missing or found:
        fail(f"{pattern}: 一致しない {missing} / 含まれてはいけない {found}")
    ok(f"{pattern}: すべての条件を満たす（{len(files)} ファイル）")


def cmd_unchanged(args: List[str]) -> None:
    now = workspace() / args[0]
    orig = repo() / args[1]
    if not now.exists():
        fail(f"{args[0]} がありません")
    if now.read_bytes() != orig.read_bytes():
        fail(f"{args[0]} が元の内容から変わっています")
    ok(f"{args[0]} は変わっていない")


def cmd_no_secret(args: List[str]) -> None:
    ws, secret = workspace(), args[0]
    leaked = []
    for path in ws.rglob("*"):
        rel = path.relative_to(ws)
        if not path.is_file() or rel.parts[0] in (".agents", ".git") or path.name == ".env":
            continue
        try:
            if secret in path.read_text(encoding="utf-8", errors="ignore"):
                leaked.append(str(rel))
        except OSError:
            continue
    if leaked:
        fail(f"秘密の値が成果物に含まれています: {leaked}")
    ok("秘密の値は .env 以外に無い")


def cmd_version_current(args: List[str]) -> None:
    text = (repo() / "skills" / "isdd-setup" / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r'^\s*version:\s*"?([^"\s]+)"?\s*$', text, re.MULTILINE)
    want = m.group(1) if m else ""
    path = workspace() / "scripts" / "isdd" / "VERSION"
    got = path.read_text(encoding="utf-8").strip() if path.exists() else "（なし）"
    if got == want:
        ok(f"VERSION は {got}")
    if len(args) == 2 and args[0] == "--or-output-re":
        output = sys.stdin.read()
        if re.search(args[1], output):
            ok(f"VERSION は {got}（期待 {want}）だが、応答で案内している")
    fail(f"VERSION が {got}（期待 {want}）")


def cmd_json_eq(args: List[str]) -> None:
    path = workspace() / args[0]
    if not path.exists():
        fail(f"{args[0]} がありません")
    data = json.loads(path.read_text(encoding="utf-8"))
    want = json.loads(args[2])
    if data.get(args[1]) != want:
        fail(f"{args[0]} の {args[1]} が {data.get(args[1])!r}（期待 {want!r}）")
    ok(f"{args[0]} の {args[1]} は {want!r}")


def cmd_count(args: List[str]) -> None:
    path = workspace() / args[0]
    if not path.exists():
        fail(f"{args[0]} がありません")
    n = path.read_text(encoding="utf-8").count(args[1])
    if n != int(args[2]):
        fail(f"{args[0]} の「{args[1]}」は {n} 回（期待 {args[2]} 回）")
    ok(f"{args[0]} の「{args[1]}」は {n} 回")


COMMANDS = {
    "checker": cmd_checker,
    "strict-trace": cmd_strict_trace,
    "match": cmd_match,
    "unchanged": cmd_unchanged,
    "no-secret": cmd_no_secret,
    "version-current": cmd_version_current,
    "json-eq": cmd_json_eq,
    "count": cmd_count,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        fail(f"使い方: isdd_grade.py <{'|'.join(COMMANDS)}> ...")
    COMMANDS[sys.argv[1]](sys.argv[2:])
