"""
implementation_completeness_checker.py

実装完了チェッカー。プロジェクトの実行形態に応じて、次の項目を機械的に確認する。
  1. docker-compose.yml が存在するか（実行形態がコンテナの場合だけ）
  2. E2E ディレクトリ配下にテストファイルが1件以上存在するか（常に）
  3. README.md に「起動方法」があるか（常に）。「初期ユーザー」があるか（認証がある場合だけ）
  4. docs/trace_map.md（設計IDとコードの対応表）が存在し、1行以上の対応があるか（常に）

どの項目を要求するかは、isdd-setup が生成する scripts/isdd/completeness.json（プロファイル）で決まる。
プロファイルが無い場合は「実行形態は未指定」として扱い、docker-compose と初期ユーザーは要求しない。

プロファイルの書式（JSON）:
  {
    "runtime": "container" | "cli" | "server" | "desktop" | "library" | "unspecified",
    "auth": true | false,
    "external": true | false,
    "e2e_dir": "e2e"
  }

使用方法:
  python3 implementation_completeness_checker.py [プロジェクトルート] [--profile scripts/isdd/completeness.json]

引数:
  プロジェクトルート: チェック対象のルートディレクトリ（省略時はカレントディレクトリ）
  --profile: プロファイルのパス（省略時はルート直下の scripts/isdd/completeness.json を探す）

終了コード:
  0: 全チェック通過
  1: 1件以上の不足あり
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

DEFAULT_PROFILE_PATH = Path("scripts") / "isdd" / "completeness.json"
DEFAULT_PROFILE = {
    "runtime": "unspecified",
    "auth": False,
    "external": False,
    "e2e_dir": "e2e",
}
# E2E テストファイルとみなす名前のパターン（言語を固定しない）
E2E_TEST_PATTERNS = [
    "*.spec.*", "*.test.*", "test_*.py", "*_test.py", "*_test.go",
    "*Test.java", "*Tests.cs", "*Test.cs", "*_spec.rb", "*_test.rb",
    "*Test.php", "*Test.kt", "*Tests.swift", "*.feature",
]


def _make_result(name: str, passed: bool, message: str) -> dict:
    """
    チェック結果を表す辞書を生成する。

    Args:
        name (str): チェック項目名
        passed (bool): チェックが通過したか
        message (str): 詳細メッセージ
    Returns:
        dict: チェック結果辞書
    """
    return {"name": name, "passed": passed, "message": message}


def _display_path(path: Path, root: Path) -> str:
    """ルートからの相対パスで表示する。ルート外なら絶対パスのまま返す。"""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def load_profile(root: Path, profile_arg: Optional[str]) -> tuple[dict, str]:
    """
    プロファイルを読み込む。無ければ既定値を返す。

    Args:
        root (Path): プロジェクトルート
        profile_arg (Optional[str]): --profile で指定されたパス
    Returns:
        tuple[dict, str]: プロファイル辞書と、どこから読んだかの説明
    """
    path = Path(profile_arg) if profile_arg else root / DEFAULT_PROFILE_PATH
    if not path.is_absolute():
        path = root / path
    profile = dict(DEFAULT_PROFILE)
    if not path.exists():
        return profile, f"プロファイル無し（{_display_path(path, root)}）。実行形態は未指定として扱う"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return profile, f"プロファイルを読めなかったため既定値を使う: {exc}"
    for key in DEFAULT_PROFILE:
        if key in loaded:
            profile[key] = loaded[key]
    return profile, f"プロファイル: {_display_path(path, root)}"


def check_docker_compose(root: Path, profile: dict) -> dict:
    """
    実行形態がコンテナのとき、docker-compose.yml または compose.yaml の存在を確認する。

    Args:
        root (Path): プロジェクトルートのパス
        profile (dict): プロファイル
    Returns:
        dict: チェック結果
    """
    name = "docker compose 定義の存在確認"
    if profile.get("runtime") != "container":
        return _make_result(
            name, True,
            f"対象外: 実行形態が {profile.get('runtime')} のため docker compose は要求しない",
        )
    candidates = [
        root / "docker-compose.yml",
        root / "docker-compose.yaml",
        root / "compose.yml",
        root / "compose.yaml",
    ]
    found = [p for p in candidates if p.exists()]
    if found:
        return _make_result(name, True, f"存在確認OK: {found[0].name}")
    return _make_result(
        name, False,
        "docker-compose.yml / compose.yaml が見つかりません。"
        " 実行形態がコンテナの設計に合わせて作成してください。",
    )


def check_e2e_tests(root: Path, profile: dict) -> dict:
    """
    E2E ディレクトリ配下にテストファイルが1件以上存在するかを確認する。

    Args:
        root (Path): プロジェクトルートのパス
        profile (dict): プロファイル
    Returns:
        dict: チェック結果
    """
    e2e_name = str(profile.get("e2e_dir") or "e2e")
    e2e_dir = root / e2e_name
    name = "E2E テストファイルの存在確認"
    if not e2e_dir.exists():
        return _make_result(
            name, False,
            f"{e2e_name}/ ディレクトリが存在しません。E2E テストを実装してください。",
        )
    test_files: set[Path] = set()
    for pattern in E2E_TEST_PATTERNS:
        test_files.update(e2e_dir.rglob(pattern))
    files = sorted(test_files)
    if files:
        return _make_result(
            name, True,
            f"テストファイル {len(files)} 件確認OK: "
            + ", ".join(str(f.relative_to(root)) for f in files[:5])
            + ("..." if len(files) > 5 else ""),
        )
    return _make_result(
        name, False,
        f"{e2e_name}/ ディレクトリは存在しますがテストファイルが0件です。"
        " E2E テストを実装・配置してください。",
    )


def check_readme(root: Path, profile: dict) -> dict:
    """
    README.md に「起動方法」があるか、認証がある場合は「初期ユーザー」もあるかを確認する。

    Args:
        root (Path): プロジェクトルートのパス
        profile (dict): プロファイル
    Returns:
        dict: チェック結果
    """
    name = "README.md の起動方法・初期ユーザー記載確認"
    readme_path = root / "README.md"
    required = ["起動方法"]
    if profile.get("auth"):
        required.append("初期ユーザー")
    if not readme_path.exists():
        return _make_result(
            name, False,
            "README.md が存在しません。" + "・".join(f"「{r}」" for r in required) + " を記載した README.md を作成してください。",
        )
    content = readme_path.read_text(encoding="utf-8")
    missing = [f"「{r}」セクション" for r in required if r not in content]
    if not missing:
        note = "" if profile.get("auth") else "（認証が無いため「初期ユーザー」は要求しない）"
        return _make_result(name, True, "README.md に " + "・".join(f"「{r}」" for r in required) + f" の記載を確認OK{note}")
    return _make_result(name, False, f"README.md に不足があります: {', '.join(missing)}。追記してください。")


def check_trace_map(root: Path) -> dict:
    """
    docs/trace_map.md が存在し、DS-ID の行が1件以上あるかを確認する。

    Args:
        root (Path): プロジェクトルートのパス
    Returns:
        dict: チェック結果
    """
    name = "docs/trace_map.md の存在確認"
    map_path = root / "docs" / "trace_map.md"
    if not map_path.exists():
        return _make_result(
            name, False,
            "docs/trace_map.md が見つかりません。設計IDとクラス・公開関数の対応表を作成してください。",
        )
    content = map_path.read_text(encoding="utf-8")
    rows = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if "DS-MD-" in stripped or ("DS-" in stripped and "::" in stripped):
            rows.append(stripped)
    if rows:
        return _make_result(name, True, f"対応表の行 {len(rows)} 件確認OK")
    return _make_result(
        name, False,
        "docs/trace_map.md は存在しますが対応の行が0件です。設計IDと修飾名の行を追加してください。",
    )


def run_checks(root: Path, profile: dict) -> list[dict]:
    """
    全チェックを実行して結果リストを返す。

    Args:
        root (Path): プロジェクトルートのパス
        profile (dict): プロファイル
    Returns:
        list[dict]: 各チェックの結果リスト
    """
    return [
        check_docker_compose(root, profile),
        check_e2e_tests(root, profile),
        check_readme(root, profile),
        check_trace_map(root),
    ]


def print_report(results: list[dict], profile: dict, profile_note: str) -> int:
    """
    チェック結果をコンソールに出力し、終了コードを返す。

    Args:
        results (list[dict]): チェック結果リスト
        profile (dict): プロファイル
        profile_note (str): プロファイルの出どころ
    Returns:
        int: 全通過なら0、1件以上不足なら1
    """
    print("=" * 60)
    print("実装完了チェック結果")
    print("=" * 60)
    print(f"{profile_note}")
    print(f"実行形態: {profile.get('runtime')} / 認証: {'あり' if profile.get('auth') else 'なし'}"
          f" / 外部連携: {'あり' if profile.get('external') else 'なし'} / E2E ディレクトリ: {profile.get('e2e_dir')}")
    print("-" * 60)

    failed_count = 0
    for result in results:
        status = "OK  " if result["passed"] else "FAIL"
        print(f"[{status}] {result['name']}")
        print(f"       {result['message']}")
        if not result["passed"]:
            failed_count += 1

    print("=" * 60)
    passed_count = len(results) - failed_count
    print(f"結果: {passed_count} / {len(results)} 項目通過")
    if failed_count == 0:
        print("全チェック通過。実装完了条件を満たしています。")
    else:
        print(f"{failed_count} 件の不足があります。完了前に必ず対処してください。")
    print("=" * 60)
    return 0 if failed_count == 0 else 1


def main() -> None:
    """
    エントリーポイント。引数からプロジェクトルートとプロファイルを受け取りチェックを実行する。
    """
    args = sys.argv[1:]
    profile_arg = None
    if "--profile" in args:
        idx = args.index("--profile")
        if idx + 1 >= len(args):
            print("エラー: --profile にはパスが必要です", file=sys.stderr)
            sys.exit(2)
        profile_arg = args[idx + 1]
        del args[idx:idx + 2]
    root = Path(args[0]).resolve() if args else Path.cwd()
    if not root.is_dir():
        print(f"エラー: ディレクトリが存在しません: {root}", file=sys.stderr)
        sys.exit(1)

    profile, note = load_profile(root, profile_arg)
    print(f"チェック対象ルート: {root}")
    results = run_checks(root, profile)
    sys.exit(print_report(results, profile, note))


if __name__ == "__main__":
    main()
