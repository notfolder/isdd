#!/usr/bin/env python3
"""
isdd_setup.py

isdd の対応表チェックをプロジェクトに組み込むセットアップスクリプト（isdd-setup スキルが実行する）。

行うこと:
  1. isdd-common のチェッカースクリプトを scripts/isdd/ に複製する（git 管理対象。再実行で上書き更新）
  2. scripts/isdd/check.sh を生成する（対応表チェックの唯一の入口。エージェントのフックも pre-commit もこれを呼ぶ）
  3. scripts/isdd/pre-commit を生成し、.git/hooks/pre-commit に組み込む（.git が無い場合は組み込みを省略して報告する）
  4. AGENTS.md と CLAUDE.md に isdd のトレーサビリティ規則を追記する（マーカーで囲み、再実行時は置き換える）
  5. scripts/isdd/completeness.json（実装完了チェックのプロファイル）を生成する。
     実行形態・認証の有無・外部連携の有無を記録し、implementation_completeness_checker.py が
     docker compose や「初期ユーザー」を要求するかどうかの判断に使う

行わないこと:
  - エージェント固有のフック設定の生成（エージェント自身が自分の環境向けに作る。作れない場合は作らない）

使用方法:
  python3 .agents/skills/isdd-common/scripts/isdd_setup.py --src src [--src another_dir]
      [--runtime container|cli|server|desktop|library|unspecified] [--auth|--no-auth] [--external|--no-external]
      [--e2e-dir e2e] [--design docs/detail_design.md] [--map docs/trace_map.md] [--skills-dir .agents/skills]

  --runtime、--auth、--external は詳細設計書の第 1 章（実行形態）、第 6 章（認証の有無）、第 4 章（外部連携の有無）から読み取って渡す。

終了コード:
  0: 完了（省略した項目があっても報告済みなら 0）
  1: 必須のスクリプトが見つからないなど、セットアップを続行できない
"""

import argparse
import json
import shutil
import stat
import sys
from pathlib import Path

RUNTIMES = ("container", "cli", "server", "desktop", "library", "unspecified")

CHECKER_FILES = (
    "trace_map_checker.py",
    "rq_ds_link_checker.py",
    "rq_integrity_checker.py",
    "implementation_completeness_checker.py",
)
MARK_BEGIN = "<!-- isdd-setup:begin -->"
MARK_END = "<!-- isdd-setup:end -->"
HOOK_MARK = "# isdd-setup pre-commit"


def rules_block(check_cmd: str, map_path: str, design_path: str) -> str:
    """AGENTS.md / CLAUDE.md に追記する規則ブロックを返す"""
    return f"""{MARK_BEGIN}
## isdd トレーサビリティ規則（isdd-setup が管理する。手で編集しない）

- 仕様とコードの対応は `{map_path}`（対応表）で管理する。コードに要件 ID や設計 ID を書かない。
- クラス・公開関数・ソースファイルを追加、改名、削除したら、同じ作業の中で `{map_path}` の行を更新する。
- コードを変更した作業の終わりに `{check_cmd}` を実行する。エラーが出たら直してから作業を終える。警告は報告に含める。
- 設計要素を増やす必要があれば、コードを書く前に `{design_path}` を更新する。設計 ID の採番は設計スキルの責務で、実装中に ID を作らない。
{MARK_END}
"""


def upsert_block(path: Path, block: str) -> str:
    """マーカー付きブロックをファイルに追記または置換する。戻り値は実施内容の説明"""
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if MARK_BEGIN in text and MARK_END in text:
            start = text.index(MARK_BEGIN)
            end = text.index(MARK_END) + len(MARK_END)
            new_text = text[:start] + block.rstrip("\n") + text[end:]
            path.write_text(new_text, encoding="utf-8")
            return f"{path}: 既存の規則ブロックを置き換えた"
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        path.write_text(text + sep + block, encoding="utf-8")
        return f"{path}: 規則ブロックを末尾に追記した"
    path.write_text(f"# {path.stem}\n\n" + block, encoding="utf-8")
    return f"{path}: 新規作成して規則ブロックを書いた"


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def main() -> int:
    parser = argparse.ArgumentParser(description="isdd 対応表チェックのセットアップ")
    parser.add_argument("--src", action="append", required=True, help="ソースディレクトリ（複数指定可）")
    parser.add_argument("--design", default="docs/detail_design.md")
    parser.add_argument("--map", default="docs/trace_map.md")
    parser.add_argument("--skills-dir", default=".agents/skills")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--runtime", choices=RUNTIMES, default="unspecified",
                        help="実行形態（詳細設計書の第 1 章から読み取る）。container のときだけ docker compose を要求する")
    parser.add_argument("--auth", dest="auth", action="store_true", default=False,
                        help="認証がある（README に「初期ユーザー」を要求する）")
    parser.add_argument("--no-auth", dest="auth", action="store_false", help="認証が無い")
    parser.add_argument("--external", dest="external", action="store_true", default=False,
                        help="外部連携がある（E2E を mock モードで回す前提）")
    parser.add_argument("--no-external", dest="external", action="store_false", help="外部連携が無い")
    parser.add_argument("--e2e-dir", default="e2e", help="E2E テストの置き場所")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    scripts_src = root / args.skills_dir / "isdd-common" / "scripts"
    # このスクリプト自身の隣にチェッカーがあれば、そちらを優先する（スキルの配置先に依存しない）
    here = Path(__file__).resolve().parent
    if (here / "trace_map_checker.py").exists():
        scripts_src = here
    if not (scripts_src / "trace_map_checker.py").exists():
        print(f"エラー: チェッカースクリプトが見つかりません: {scripts_src}", file=sys.stderr)
        return 1

    report = []
    dest = root / "scripts" / "isdd"
    dest.mkdir(parents=True, exist_ok=True)

    # 1. チェッカーの複製
    for name in CHECKER_FILES:
        src = scripts_src / name
        if src.exists():
            shutil.copyfile(src, dest / name)
            report.append(f"複製: {dest / name}")
        else:
            report.append(f"省略: {name} は配布元に無い")

    # 2. check.sh の生成
    src_dirs = " ".join(f'"{s}"' for s in args.src)
    check_sh = dest / "check.sh"
    check_sh.write_text(
        "#!/usr/bin/env bash\n"
        "# isdd 対応表チェックの入口（isdd-setup が生成。再実行で上書き）\n"
        "# 使い方: bash scripts/isdd/check.sh [--strict]\n"
        "#   --strict を付けると警告も失敗扱いにする（実装スキルの完了条件用）\n"
        "set -u\n"
        'cd "$(dirname "$0")/../.."\n'
        f'exec python3 scripts/isdd/trace_map_checker.py "{args.design}" "{args.map}" {src_dirs} "$@"\n',
        encoding="utf-8",
    )
    make_executable(check_sh)
    report.append(f"生成: {check_sh}")

    # 3. pre-commit の生成と組み込み
    pre_commit = dest / "pre-commit"
    pre_commit.write_text(
        "#!/usr/bin/env bash\n"
        f"{HOOK_MARK}\n"
        "# 対応表の壊れた参照（エラー）だけでコミットを止める。未登録（警告）は表示だけ。\n"
        "set -u\n"
        'cd "$(git rev-parse --show-toplevel)"\n'
        "bash scripts/isdd/check.sh\n"
        "status=$?\n"
        "if [ $status -ne 0 ]; then\n"
        '  echo "isdd: 対応表にエラーがあります。docs/trace_map.md を直してからコミットしてください。" >&2\n'
        "  exit $status\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    make_executable(pre_commit)
    report.append(f"生成: {pre_commit}")

    git_dir = root / ".git"
    hooks_dir = git_dir / "hooks"
    if git_dir.is_dir():
        hooks_dir.mkdir(parents=True, exist_ok=True)
        hook_path = hooks_dir / "pre-commit"
        wrapper = f"#!/usr/bin/env bash\n{HOOK_MARK}\nexec bash scripts/isdd/pre-commit\n"
        if hook_path.exists() and HOOK_MARK not in hook_path.read_text(encoding="utf-8", errors="replace"):
            report.append(f"省略: {hook_path} は isdd 以外のフックが既にある。手で `bash scripts/isdd/pre-commit` の呼び出しを足すこと")
        else:
            hook_path.write_text(wrapper, encoding="utf-8")
            make_executable(hook_path)
            report.append(f"組み込み: {hook_path}")
    else:
        report.append("省略: .git が無いため pre-commit は組み込んでいない（git init 後に再実行する）")

    # 4. AGENTS.md / CLAUDE.md への規則追記
    block = rules_block("bash scripts/isdd/check.sh", args.map, args.design)
    for name in ("AGENTS.md", "CLAUDE.md"):
        report.append(upsert_block(root / name, block))

    # 5. 実装完了チェックのプロファイル
    profile = {
        "runtime": args.runtime,
        "auth": bool(args.auth),
        "external": bool(args.external),
        "e2e_dir": args.e2e_dir,
    }
    profile_path = dest / "completeness.json"
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report.append(
        f"生成: {profile_path}（実行形態 {args.runtime} / 認証 {'あり' if args.auth else 'なし'} / "
        f"外部連携 {'あり' if args.external else 'なし'} / E2E {args.e2e_dir}）"
    )
    if args.runtime == "unspecified":
        report.append("注意: --runtime が未指定のため docker compose は要求しない。詳細設計書の第 1 章に実行形態があれば --runtime を付けて再実行する")

    print("isdd-setup 完了")
    print("-" * 50)
    for line in report:
        print(f"- {line}")
    print("-" * 50)
    print("次にすること:")
    print("  1. `bash scripts/isdd/check.sh` を一度実行して、チェッカーが動くことを確かめる")
    print("  2. エージェントの実行環境に「応答終了時に `bash scripts/isdd/check.sh` を実行する」フックを")
    print("     設定できる場合だけ設定する。応答終了時のイベントやフック機能が無ければ設定せず、その旨を報告する")
    print("  3. `python3 scripts/isdd/implementation_completeness_checker.py .` の冒頭に出る実行形態・認証・外部連携が")
    print("     詳細設計書と合っているか確かめる。違えば --runtime / --auth / --external を付けて再実行する")
    return 0


if __name__ == "__main__":
    sys.exit(main())
