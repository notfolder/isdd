#!/usr/bin/env python3
"""
RQ Integrity Checker Script

目的:
  要件定義書 (requirements.md) の内部整合性をチェックします。
  - IDフォーマット検証
  - RQ-BK 双方向マッピング検証
  - 必須カテゴリ存在確認（RQ-BK、RQ-BZ）
  - 受け入れテストの網羅（RQ-FT・RQ-UI・RQ-EX が、第 7 章のいずれかのシナリオ（RQ-TS）の
    「検証する要件ID」列に 1 回以上現れること。この列の ID は RQ-BK との対応に数えない）

変更要件定義書（change_requirements.md）の扱い:
  [追加] または [削除] の区分を含む文書は変更要件定義書とみなす。変更要件定義書は
  変更のない章を「変更なし。既存要件定義書を参照」と書くため、RQ-BZ が現れないことがある。
  そのため必須カテゴリ存在確認は RQ-BK だけに緩め、その旨を出力に書く。
  受け入れテストの網羅は、[追加] の行で定義した RQ-FT・RQ-UI・RQ-EX にだけ求める（既存の要件は正本で確かめる）。
  [削除] の行のシナリオは網羅に数えない。

使用方法:
  python3 rq_integrity_checker.py <requirements.md | change_requirements.md>

出力:
  - フォーマット違反一覧: 不正なRQ-* IDフォーマット
  - BKマッピング欠落一覧: 対応するRQ-BK-*がない要件
  - 孤立BK一覧: 対応要件が1件もないRQ-BK-*
  - 受け入れテスト欠落一覧: どのシナリオの「検証する要件ID」にも現れないRQ-FT・RQ-UI・RQ-EX
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
VALID_CATEGORIES = {'BZ', 'BK', 'EF', 'FT', 'UI', 'EX', 'DT', 'NF', 'TS', 'OP'}

# 必須カテゴリ（最低1件必要）
REQUIRED_CATEGORIES = {'BK', 'BZ'}

# BKマッピング不要なコンテキストID
CONTEXT_PREFIXES = ('RQ-BK-', 'RQ-BZ-')

# 受け入れテスト（第 7 章の RQ-TS）での検証を求めるカテゴリ
TESTED_CATEGORIES = {'FT', 'UI', 'EX'}

# 第 7 章の表の「検証する要件ID」列の見出し
VERIFY_COLUMN_PATTERN = re.compile(r'検証する要件\s*ID')


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
        self.is_change_doc: bool = False  # [追加] / [削除] の区分を含む変更要件定義書か
        self.ts_verifies: Dict[str, Set[str]] = defaultdict(set)  # RQ-TS → 検証する要件ID
        self.line_verify_ids: Dict[int, Set[str]] = {}  # 行番号 → その行の「検証する要件ID」列の ID
        self.has_verify_column: bool = False
        self.ids_outside_verify: Set[str] = set()  # 「検証する要件ID」列の外に現れる ID

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

        # 第 7 章の表の「検証する要件ID」列を読む（BK 対応の構築より先）
        self._parse_verify_column()

        # 行ごとにBK ↔ 非BK要件の共起を検出してマッピング構築
        self._build_bk_mapping()

        return True

    @staticmethod
    def _split_cells(line: str) -> List[str]:
        """Markdown の表の行をセルに分ける（先頭と末尾の | を除く）"""
        body = line.strip()
        if body.startswith('|'):
            body = body[1:]
        if body.endswith('|'):
            body = body[:-1]
        return [c.strip() for c in body.split('|')]

    def _parse_verify_column(self):
        """
        「検証する要件ID」列を持つ表（第 7 章のテスト用利用シナリオ）を列名で読み分ける。
        各行の RQ-TS（行の最初の ID）→ その列の ID を ts_verifies に、行番号 → その列の ID を
        line_verify_ids に記録する。この列の ID は RQ-BK との対応に数えない。
        [削除] の行のシナリオは網羅に数えない（変更要件定義書）。
        """
        verify_col = None
        for idx, line in enumerate(self.content_lines):
            stripped = line.strip()
            if not stripped.startswith('|'):
                verify_col = None
                continue
            cells = self._split_cells(stripped)
            if verify_col is None:
                for i, cell in enumerate(cells):
                    if VERIFY_COLUMN_PATTERN.search(cell):
                        verify_col = i
                        self.has_verify_column = True
                        break
                continue
            if all(set(c) <= set('-: ') for c in cells):
                continue  # 区切り行
            if verify_col >= len(cells):
                continue
            verify_ids = set(self._extract_ids_from_text(cells[verify_col]))
            self.line_verify_ids[idx] = verify_ids
            if '[削除]' in line:
                continue
            own = self._extract_ids_from_text(cells[0]) if cells else []
            if own and own[0].startswith('RQ-TS-'):
                self.ts_verifies[own[0]] |= verify_ids

    def _build_bk_mapping(self):
        """
        ドキュメントの各行でRQ-BK-*と非BK要件の共起を検出する。

        対応表の典型パターン（例）:
          | RQ-BK-VERIFY-OUTPUT | RQ-FT-PRINT-HELLO, RQ-NF-ERROR-PROPAGATION |
        この行から RQ-BK-VERIFY-OUTPUT → {RQ-FT-PRINT-HELLO, RQ-NF-ERROR-PROPAGATION} を構築。
        """
        for idx, line in enumerate(self.content_lines):
            ids_in_line = self._extract_ids_from_text(line)
            if not ids_in_line:
                continue

            excluded = self.line_verify_ids.get(idx, set())
            self.ids_outside_verify.update(i for i in ids_in_line if i not in excluded)
            bk_ids = {i for i in ids_in_line if i.startswith('RQ-BK-')}
            non_bk_ids = {i for i in ids_in_line if not _is_context_id(i) and i not in excluded}

            if bk_ids and non_bk_ids:
                for bk in bk_ids:
                    for req in non_bk_ids:
                        self.bk_to_reqs[bk].add(req)
                        self.req_to_bks[req].add(bk)

    def check_decided_items_section(self):
        """「1-2. 依頼に無く自分で決めた項目」の節があるか（requirements-chapters.md の規則。無い決め事は「無し」と書く）"""
        pattern = re.compile(r'^\s*#{2,4}\s+.*依頼に無く.*決めた項目')
        if not any(pattern.match(line) for line in self.content_lines):
            self.issues.append(
                "✗ 節の欠落: 「1-2. 依頼に無く自分で決めた項目」の節がありません"
                "（エージェントが決めたことを表で書く。無ければ「無し」と書く。requirements-chapters.md）"
            )

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
        """必須カテゴリ（RQ-BK, RQ-BZ）が存在するか確認する。変更要件定義書では RQ-BK だけを必須にする"""
        required = {'BK'} if self.is_change_doc else REQUIRED_CATEGORIES
        for cat in required:
            if not self.ids_by_category.get(cat):
                self.issues.append(
                    f"✗ 必須カテゴリ欠落: RQ-{cat}-* が1件も見つかりません"
                )

    def _verify_only_ids(self) -> Set[str]:
        """「検証する要件ID」列にだけ現れる ID（定義ではなく参照）"""
        in_verify = set()
        for ids in self.line_verify_ids.values():
            in_verify |= ids
        return in_verify - self.ids_outside_verify

    def check_undefined_verify_refs(self):
        """正本で「検証する要件ID」にだけ現れる要件は未定義の参照。変更要件定義書では既存要件の参照なので問題にしない"""
        if self.is_change_doc:
            return
        undefined = self._verify_only_ids()
        if undefined:
            self.issues.append(
                f"✗ 未定義参照: 以下の要件 ID は「検証する要件ID」にだけ現れ、定義する行がありません ({len(undefined)} 件):\n"
                + "".join(f"  - {i}\n" for i in sorted(undefined))
            )

    def check_bk_mapping(self):
        """RQ-BK 双方向マッピングを検証する（「検証する要件ID」列にだけ現れる参照は対象外）"""
        verify_only = self._verify_only_ids()
        all_non_bk = {
            i for i in self.unique_ids if not _is_context_id(i) and i not in verify_only
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


    def _tested_targets(self) -> Set[str]:
        """受け入れテストでの検証を求める要件。変更要件定義書では [追加] の行で定義した要件だけ"""
        if not self.is_change_doc:
            return {i for i in self.unique_ids if _get_category(i) in TESTED_CATEGORIES}
        targets = set()
        for line in self.content_lines:
            if '[追加]' not in line or '[削除]' in line:
                continue
            stripped = line.strip()
            if not stripped.startswith('|'):
                continue
            cells = self._split_cells(stripped)
            own = self._extract_ids_from_text(cells[0]) if cells else []
            if own and _get_category(own[0]) in TESTED_CATEGORIES:
                targets.add(own[0])
        return targets

    def check_scenario_coverage(self):
        """RQ-FT・RQ-UI・RQ-EX が、いずれかの RQ-TS の「検証する要件ID」に現れるか確認する"""
        targets = self._tested_targets()
        if not targets:
            return
        covered = set()
        for ids in self.ts_verifies.values():
            covered |= ids
        missing = targets - covered
        if not missing:
            return
        hint = ("第 7 章の表に「検証する要件ID」列が見つかりません。各シナリオ（RQ-TS）の行に、確かめる要件 ID を書く列を足してください\n"
                if not self.has_verify_column else "")
        self.issues.append(
            f"✗ 受け入れテスト欠落: 以下の要件は、どのテスト用利用シナリオ（RQ-TS）の「検証する要件ID」にも現れません ({len(missing)} 件):\n"
            + hint
            + "".join(f"  - {i}\n" for i in sorted(missing))
        )

    def run(self) -> bool:
        """全チェックを実行する"""
        print("RQ Integrity Checker\n" + "=" * 50)

        if not self.parse():
            return False

        total = len(self.unique_ids)
        by_cat = {cat: len(ids) for cat, ids in self.ids_by_category.items()}
        self.is_change_doc = any('[追加]' in line or '[削除]' in line for line in self.content_lines)
        if self.is_change_doc:
            print("文書種別: 変更要件定義書（[追加] / [削除] を検出）。RQ-BZ の存在確認は省く")
        print(f"検出: RQ-* ID 総数: {total}")
        for cat in sorted(VALID_CATEGORIES):
            count = by_cat.get(cat, 0)
            if count:
                print(f"  - RQ-{cat}-*: {count}件")
        print()

        self.check_format()
        self.check_decided_items_section()
        self.check_required_categories()
        self.check_bk_mapping()
        self.check_undefined_verify_refs()
        self.check_scenario_coverage()

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
            print(f"  - 受け入れテスト欠落: 0件（シナリオ {len(self.ts_verifies)} 本）")
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
        for issue in checker.issues:
            print(issue)
        print("\nチェックに失敗しました")
        sys.exit(1)

    issue_count = checker.report()
    if issue_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
