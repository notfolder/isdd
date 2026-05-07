#!/usr/bin/env python3
"""
RQ Integrity Checker Script

目的:
  要件定義書 (requirements.md) の内部整合性をチェックします。
  - IDフォーマット検証
  - RQ-BK 双方向マッピング検証
  - 必須カテゴリ存在確認

使用方法:
  python3 rq_integrity_checker.py <requirements.md>

出力:
  - フォーマット違反一覧: 不正なRQ-* IDフォーマット
  - BKマッピング欠落一覧: 対応するRQ-BK-*がない要件
  - 孤立BK一覧: 対応要件が1件もないRQ-BK-*
  - 検証サマリ: 総数、違反数、欠落数
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple

# RQ-* IDにマッチする正規表現
RQ_PATTERN = re.compile(r'\bRQ(?:-[A-Z0-9][A-Z0-9_]*)+')

# ヘッダー列ラベルを除外（例: RQ-ID, RQ-BK-ID）
HEADER_LABEL_PATTERN = re.compile(r'^(?:RQ)(?:-[A-Z0-9]+)+-ID$')

# 有効なカテゴリ
VALID_CATEGORIES = {'BZ', 'BK', 'FT', 'UI', 'EX', 'DT', 'NF', 'TS', 'OP'}

# 必須カテゴリ（最低1件必要）
REQUIRED_CATEGORIES = {'BK', 'BZ'}

# BKマッピング不要なコンテキストID
CONTEXT_PREFIXES = ('RQ-BK-', 'RQ-BZ-')


def _is_valid_id(id_str: str) -> bool:
    """ヘッダーラベル・短すぎるIDを除外する"""
    if HEADER_LABEL_PATTERN.match(id_str):
        return False
    parts = id_str.split('-')
    # RQ-BK-NAME のように最低3パーツ必要
    return len(parts) >= 3


def _get_category(id_str: str) -> str:
    """RQ-{カテゴリ}-... からカテゴリを取得"""
    parts = id_str.split('-')
    return parts[1] if len(parts) >= 2 else ''


def _is_context_id(id_str: str) -> bool:
    """BKマッピング不要のコンテキストIDか判定"""
    return any(id_str.startswith(p) for p in CONTEXT_PREFIXES)


class RQIntegrityChecker:
    """要件定義書の内部整合性チェッカー"""

    def __init__(self, rq_file: Path):
        self.rq_file = rq_file
        self.all_ids: List[str] = []            # ドキュメント中の全RQ-* ID（重複含む）
        self.unique_ids: Set[str] = set()
        self.ids_by_category: Dict[str, Set[str]] = defaultdict(set)
        self.bk_to_reqs: Dict[str, Set[str]] = defaultdict(set)  # BK → 非BK要件
        self.req_to_bks: Dict[str, Set[str]] = defaultdict(set)  # 非BK要件 → BK
        self.issues: List[str] = []
        self.content_lines: List[str] = []

    def _extract_ids_from_text(self, text: str) -> List[str]:
        """テキストからRQ-* IDを抽出（無効ID除外）"""
        return [m for m in RQ_PATTERN.findall(text) if _is_valid_id(m)]

    def parse(self) -> bool:
        """要件定義書を読み込み解析する"""
        try:
            with open(self.rq_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.issues.append(f"エラー: {self.rq_file} が見つかりません")
            return False
        except Exception as e:
            self.issues.append(f"エラー: ファイル読み込み失敗: {e}")
            return False

        self.content_lines = content.splitlines()
        self.all_ids = self._extract_ids_from_text(content)

        if not self.all_ids:
            self.issues.append("警告: requirements.md から RQ-* ID が検出されませんでした")
            return False

        # カテゴリ別に分類
        for id_str in self.all_ids:
            cat = _get_category(id_str)
            self.ids_by_category[cat].add(id_str)

        self.unique_ids = set(self.all_ids)

        # 行ごとにBK ↔ 非BK要件の共起を検出してマッピング構築
        self._build_bk_mapping()

        return True

    def _build_bk_mapping(self):
        """
        ドキュメントの各行でRQ-BK-*と非BK要件の共起を検出する。

        対応表の典型パターン（例）:
          | RQ-BK-VERIFY-OUTPUT | RQ-FT-PRINT-HELLO, RQ-NF-ERROR-PROPAGATION |
        この行から RQ-BK-VERIFY-OUTPUT → {RQ-FT-PRINT-HELLO, RQ-NF-ERROR-PROPAGATION} を構築。
        """
        for line in self.content_lines:
            ids_in_line = self._extract_ids_from_text(line)
            if not ids_in_line:
                continue

            bk_ids = {i for i in ids_in_line if i.startswith('RQ-BK-')}
            non_bk_ids = {i for i in ids_in_line if not _is_context_id(i)}

            if bk_ids and non_bk_ids:
                for bk in bk_ids:
                    for req in non_bk_ids:
                        self.bk_to_reqs[bk].add(req)
                        self.req_to_bks[req].add(bk)

    def check_format(self):
        """IDフォーマットと有効カテゴリを検証する"""
        invalid = []
        for id_str in self.unique_ids:
            cat = _get_category(id_str)
            if cat not in VALID_CATEGORIES:
                invalid.append(id_str)

        if invalid:
            self.issues.append(
                f"✗ フォーマット違反: 不正なカテゴリのRQ-* IDが {len(invalid)} 件:\n"
                + "".join(f"  - {i}\n" for i in sorted(invalid))
            )

    def check_required_categories(self):
        """必須カテゴリ（RQ-BK, RQ-BZ）が存在するか確認する"""
        for cat in REQUIRED_CATEGORIES:
            if not self.ids_by_category.get(cat):
                self.issues.append(
                    f"✗ 必須カテゴリ欠落: RQ-{cat}-* が1件も見つかりません"
                )

    def check_bk_mapping(self):
        """RQ-BK 双方向マッピングを検証する"""
        all_non_bk = {
            i for i in self.unique_ids if not _is_context_id(i)
        }
        all_bk = self.ids_by_category.get('BK', set())

        # 非BK要件にBK参照がないもの
        unmapped_reqs = all_non_bk - set(self.req_to_bks.keys())
        if unmapped_reqs:
            self.issues.append(
                f"✗ BKマッピング欠落: 以下の要件に対応するRQ-BK-*がありません ({len(unmapped_reqs)} 件):\n"
                + "".join(f"  - {i}\n" for i in sorted(unmapped_reqs))
            )

        # BKに対応する非BK要件がないもの（孤立BK）
        isolated_bks = all_bk - set(self.bk_to_reqs.keys())
        if isolated_bks:
            self.issues.append(
                f"✗ 孤立BK: 以下のRQ-BK-*に対応要件がありません ({len(isolated_bks)} 件):\n"
                + "".join(f"  - {i}\n" for i in sorted(isolated_bks))
            )


    def run(self) -> bool:
        """全チェックを実行する"""
        print("RQ Integrity Checker\n" + "=" * 50)

        if not self.parse():
            return False

        total = len(self.unique_ids)
        by_cat = {cat: len(ids) for cat, ids in self.ids_by_category.items()}
        print(f"検出: RQ-* ID 総数: {total}")
        for cat in sorted(VALID_CATEGORIES):
            count = by_cat.get(cat, 0)
            if count:
                print(f"  - RQ-{cat}-*: {count}件")
        print()

        self.check_format()
        self.check_required_categories()
        self.check_bk_mapping()

        return True

    def report(self) -> int:
        """チェック結果をレポートし、問題件数を返す"""
        print("結果レポート")
        print("-" * 50)

        if not self.issues:
            all_bk = self.ids_by_category.get('BK', set())
            all_non_bk = {i for i in self.unique_ids if not _is_context_id(i)}
            print("✓ 全てのチェックに合格しました")
            print(f"  - RQ-* 総数: {len(self.unique_ids)}")
            print(f"  - RQ-BK-*: {len(all_bk)}件")
            print(f"  - 非BK/BZ要件: {len(all_non_bk)}件")
            print(f"  - BKマッピング欠落: 0件")
            print(f"  - 孤立BK: 0件")
            print(f"  - フォーマット違反: 0件")
            return 0
        else:
            print(f"✗ {len(self.issues)} 件の問題が検出されました:\n")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
            return len(self.issues)


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 rq_integrity_checker.py <requirements.md>")
        sys.exit(1)

    rq_file = Path(sys.argv[1])
    checker = RQIntegrityChecker(rq_file)

    if not checker.run():
        print("\nチェックに失敗しました")
        sys.exit(1)

    issue_count = checker.report()
    if issue_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
