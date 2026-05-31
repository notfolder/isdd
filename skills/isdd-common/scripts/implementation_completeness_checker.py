"""
implementation_completeness_checker.py

実装完了チェッカー。以下の3項目を機械的に確認する。
  1. docker-compose.yml が存在するか
  2. e2e/ 配下にテストファイルが1件以上存在するか
  3. README.md に「起動方法」「初期ユーザー」のセクションが存在するか

使用方法:
  python3 implementation_completeness_checker.py [プロジェクトルート]

引数:
  プロジェクトルート: チェック対象のルートディレクトリ（省略時はカレントディレクトリ）

終了コード:
  0: 全チェック通過
  1: 1件以上の不足あり
"""

import sys
import os
from pathlib import Path


# チェック結果を格納するデータクラス相当の辞書型
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


def check_docker_compose(root: Path) -> dict:
    """
    docker-compose.yml または docker-compose.yaml の存在を確認する。

    Args:
        root (Path): プロジェクトルートのパス
    Returns:
        dict: チェック結果
    """
    # どちらの拡張子も許容する
    candidates = [
        root / "docker-compose.yml",
        root / "docker-compose.yaml",
    ]
    found = [p for p in candidates if p.exists()]
    if found:
        return _make_result(
            "docker-compose.yml の存在確認",
            True,
            f"存在確認OK: {found[0].name}",
        )
    return _make_result(
        "docker-compose.yml の存在確認",
        False,
        "docker-compose.yml / docker-compose.yaml が見つかりません。"
        " docker compose を前提とした運用設計に合わせて作成してください。",
    )


def check_e2e_tests(root: Path) -> dict:
    """
    e2e/ ディレクトリ配下にテストファイルが1件以上存在するかを確認する。
    テストファイルの対象は *.spec.ts / *.test.ts / test_*.py / *_test.py とする。

    Args:
        root (Path): プロジェクトルートのパス
    Returns:
        dict: チェック結果
    """
    e2e_dir = root / "e2e"
    if not e2e_dir.exists():
        return _make_result(
            "e2e テストファイルの存在確認",
            False,
            "e2e/ ディレクトリが存在しません。E2Eテストを実装してください。",
        )

    # テストファイルのパターン（再帰的に検索）
    patterns = ["*.spec.ts", "*.test.ts", "test_*.py", "*_test.py"]
    test_files: list[Path] = []
    for pattern in patterns:
        test_files.extend(e2e_dir.rglob(pattern))

    if test_files:
        return _make_result(
            "e2e テストファイルの存在確認",
            True,
            f"テストファイル {len(test_files)} 件確認OK: "
            + ", ".join(str(f.relative_to(root)) for f in test_files[:5])
            + ("..." if len(test_files) > 5 else ""),
        )
    return _make_result(
        "e2e テストファイルの存在確認",
        False,
        "e2e/ ディレクトリは存在しますがテストファイルが0件です。"
        " E2Eテストを実装・配置してください。",
    )


def check_readme(root: Path) -> dict:
    """
    README.md に「起動方法」と「初期ユーザー」の両方が含まれるかを確認する。

    Args:
        root (Path): プロジェクトルートのパス
    Returns:
        dict: チェック結果
    """
    readme_path = root / "README.md"
    if not readme_path.exists():
        return _make_result(
            "README.md の起動方法・初期ユーザー記載確認",
            False,
            "README.md が存在しません。起動方法と初期ユーザー情報を記載した README.md を作成してください。",
        )

    content = readme_path.read_text(encoding="utf-8")

    # 「起動方法」と「初期ユーザー」の両方が含まれるかチェック
    missing: list[str] = []
    if "起動方法" not in content:
        missing.append("「起動方法」セクション")
    if "初期ユーザー" not in content:
        missing.append("「初期ユーザー」セクション")

    if not missing:
        return _make_result(
            "README.md の起動方法・初期ユーザー記載確認",
            True,
            "README.md に「起動方法」「初期ユーザー」の記載を確認OK",
        )
    return _make_result(
        "README.md の起動方法・初期ユーザー記載確認",
        False,
        f"README.md に不足があります: {', '.join(missing)}。追記してください。",
    )


def run_checks(root: Path) -> list[dict]:
    """
    全チェックを実行して結果リストを返す。

    Args:
        root (Path): プロジェクトルートのパス
    Returns:
        list[dict]: 各チェックの結果リスト
    """
    return [
        check_docker_compose(root),
        check_e2e_tests(root),
        check_readme(root),
    ]


def print_report(results: list[dict]) -> int:
    """
    チェック結果をコンソールに出力し、終了コードを返す。

    Args:
        results (list[dict]): チェック結果リスト
    Returns:
        int: 全通過なら0、1件以上不足なら1
    """
    print("=" * 60)
    print("実装完了チェック結果")
    print("=" * 60)

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
    エントリーポイント。引数からプロジェクトルートを受け取りチェックを実行する。
    """
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path.cwd()

    if not root.is_dir():
        print(f"エラー: ディレクトリが存在しません: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"チェック対象ルート: {root}")
    results = run_checks(root)
    exit_code = print_report(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
