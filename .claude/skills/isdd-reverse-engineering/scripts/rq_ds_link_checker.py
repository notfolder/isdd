#!/usr/bin/env python3
"""
RQ-DS Link Checker Script

目的:
  要件定義書 (requirements.md) と詳細設計書 (detail_design.md) の
  要件ID (RQ-*) と設計ID (DS-*) の対応関係をチェックし、
  欠落・重複・不整合を検出します。

使用方法:
  python3 rq_ds_link_checker.py <requirements.md> <detail_design.md>

出力:
  - 対応欠落一覧: RQ-* にマッピングされていない DS-*、その逆
  - 重複一覧: 複数の RQ-* にマッピングされている DS-*
  - 不整合一覧: マッピング構造の矛盾
  - 検証サマリ: 総数、欠落数、重複数、不整合数
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List

# ハイフン区切りの複合IDにマッチする正規表現
# 例: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH-STORAGE
RQ_PATTERN = re.compile(r'\bRQ(?:-[A-Z0-9][A-Z0-9_]*)+')
DS_PATTERN = re.compile(r'\bDS(?:-[A-Z0-9][A-Z0-9_]*)+')

# ヘッダー列ラベルを除外（例: RQ-ID, DS-ID, RQ-BZ-ID, RQ-BK-ID）
HEADER_LABEL_PATTERN = re.compile(r'^(?:RQ|DS)(?:-[A-Z0-9]+)+-ID$')

# 業務コンテキストIDのプレフィックス（DS-*へのマッピング不要）
CONTEXT_PREFIXES = ('RQ-BK-', 'RQ-BZ-')


def _is_valid_id(id_str: str) -> bool:
    """ヘッダーラベル・短すぎるID・業務コンテキストIDを除外する"""
    # テーブルヘッダー列ラベル除外
    if HEADER_LABEL_PATTERN.match(id_str):
        return False
    # パーツ数が2以下（例: RQ-BK）は不完全なIDとして除外
    parts = id_str.split('-')
    if len(parts) < 3:
        return False
    return True


def _is_context_id(rq_id: str) -> bool:
    """業務課題・事業目的などのコンテキストIDかどうか判定（DS-*マッピング不要）"""
    return any(rq_id.startswith(p) for p in CONTEXT_PREFIXES)


class RQDSChecker:
    """RQ-* と DS-* の対応関係チェッカー"""

    def __init__(self, rq_file: Path, ds_file: Path):
        self.rq_file = rq_file
        self.ds_file = ds_file
        self.rq_ids: Set[str] = set()
        self.ds_ids: Set[str] = set()
        self.rq_to_ds: Dict[str, Set[str]] = defaultdict(set)  # RQ → DS のマッピング
        self.ds_to_rq: Dict[str, Set[str]] = defaultdict(set)  # DS → RQ のマッピング
        self.issues: List[str] = []

    def extract_ids(self, text: str, pattern: re.Pattern) -> Set[str]:
        """テキストからIDを抽出（無効なIDを除外）"""
        return {m for m in pattern.findall(text) if _is_valid_id(m)}

    def parse_requirements(self) -> bool:
        """要件定義書を読み込み、RQ-* ID を抽出"""
        try:
            with open(self.rq_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.rq_ids = self.extract_ids(content, RQ_PATTERN)
            if not self.rq_ids:
                self.issues.append("警告: requirements.md から RQ-* ID が検出されませんでした")
                return False
            return True
        except FileNotFoundError:
            self.issues.append(f"エラー: {self.rq_file} が見つかりません")
            return False
        except Exception as e:
            self.issues.append(f"エラー: requirements.md の読み込みに失敗しました: {e}")
            return False

    def parse_design(self) -> bool:
        """詳細設計書を読み込み、DS-* ID と RQ-* への参照を抽出"""
        try:
            with open(self.ds_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # DS-* ID を抽出
            self.ds_ids = self.extract_ids(content, DS_PATTERN)
            if not self.ds_ids:
                self.issues.append("警告: detail_design.md から DS-* ID が検出されませんでした")

            # マークダウンテーブルの行ごとに DS-* と RQ-* の共起を検出
            for line in content.splitlines():
                ds_in_line = {m for m in DS_PATTERN.findall(line) if _is_valid_id(m)}
                rq_in_line = {m for m in RQ_PATTERN.findall(line) if _is_valid_id(m)}
                if ds_in_line and rq_in_line:
                    for ds_id in ds_in_line:
                        for rq_id in rq_in_line:
                            self.rq_to_ds[rq_id].add(ds_id)
                            self.ds_to_rq[ds_id].add(rq_id)

            # フォールバック: 旧フォーマット "DS-XXX: RQ-YYY, RQ-ZZZ" の検出
            for ds_id in self.ds_ids:
                if ds_id in self.ds_to_rq:
                    continue  # 既にテーブル行から検出済み
                escaped = re.escape(ds_id)
                pattern = rf'\b{escaped}\b[:\s\-\(\)]*({RQ_PATTERN.pattern}(?:\s*,\s*{RQ_PATTERN.pattern})*)'
                matches = re.findall(pattern, content)
                if matches:
                    rqs = [m for m in RQ_PATTERN.findall(matches[0]) if _is_valid_id(m)]
                    for rq in rqs:
                        self.rq_to_ds[rq].add(ds_id)
                        self.ds_to_rq[ds_id].add(rq)

            return True
        except FileNotFoundError:
            self.issues.append(f"エラー: {self.ds_file} が見つかりません")
            return False
        except Exception as e:
            self.issues.append(f"エラー: detail_design.md の読み込みに失敗しました: {e}")
            return False

    def _infer_mappings_from_naming(self):
        """
        DS-* ID のサフィックスからRQ-* ID を推定してマッピングに追加する。

        isddの命名規則: DS-{type}-{component}-{RQ-suffix}
        例: DS-CL-EQUIPMENT-SERVICE-FT-MANAGE-EQUIPMENT → RQ-FT-MANAGE-EQUIPMENT
        """
        # RQ-* サフィックス → RQ-ID のマップを構築
        # サフィックス = RQ プレフィックスを除いた部分（例: FT-MANAGE-EQUIPMENT）
        rq_suffixes: Dict[str, str] = {}
        for rq_id in self.rq_ids:
            if _is_context_id(rq_id):
                continue
            parts = rq_id.split('-')
            suffix = '-'.join(parts[1:])  # 'RQ' プレフィックスを除去
            # 短すぎるサフィックス（1パーツ）は曖昧なためスキップ
            if len(parts) >= 3:
                rq_suffixes[suffix] = rq_id

        for ds_id in self.ds_ids:
            if ds_id in self.ds_to_rq:
                continue  # 既にマッピング済み
            parts = ds_id.split('-')
            # DS-* ID の各サフィックス候補を試す（長い順に試して最初にマッチしたものを採用）
            for i in range(1, len(parts) - 1):  # 最低2パーツ以上のサフィックスを試す
                suffix = '-'.join(parts[i:])
                if suffix in rq_suffixes:
                    rq_id = rq_suffixes[suffix]
                    self.rq_to_ds[rq_id].add(ds_id)
                    self.ds_to_rq[ds_id].add(rq_id)
                    break

    def check_coverage(self):
        """RQ-* と DS-* の対応欠落をチェック"""
        # RQ-* にマッピングされていない DS-*
        unmapped_ds = self.ds_ids - set(self.ds_to_rq.keys())
        if unmapped_ds:
            self.issues.append(
                f"⚠ 対応欠落: 以下の DS-* には対応する RQ-* がマッピングされていません:\n"
                f"  {', '.join(sorted(unmapped_ds))}"
            )

        # DS-* にマッピングされていない RQ-*（コンテキストIDは除外）
        mappable_rq = {rq for rq in self.rq_ids if not _is_context_id(rq)}
        unmapped_rq = mappable_rq - set(self.rq_to_ds.keys())
        if unmapped_rq:
            self.issues.append(
                f"⚠ 対応欠落: 以下の RQ-* には対応する DS-* がマッピングされていません:\n"
                f"  {', '.join(sorted(unmapped_rq))}"
            )

    def check_duplicates(self):
        """複数の RQ-* にマッピングされている DS-* をチェック（重複判定）"""
        duplicates = {ds: rqs for ds, rqs in self.ds_to_rq.items() if len(rqs) > 1}
        if duplicates:
            issue_str = "⚠ 重複: 以下の DS-* は複数の RQ-* に対応しています:\n"
            for ds, rqs in sorted(duplicates.items()):
                issue_str += f"  {ds} → {', '.join(sorted(rqs))}\n"
            self.issues.append(issue_str.rstrip())

    def check_consistency(self):
        """マッピング構造の整合性をチェック"""
        for rq, ds_set in self.rq_to_ds.items():
            for ds in ds_set:
                if rq not in self.ds_to_rq.get(ds, set()):
                    self.issues.append(
                        f"⚠ 不整合: {rq} → {ds} のマッピングが片方向です"
                    )

    def run(self) -> bool:
        """チェック全体を実行"""
        print("RQ-DS Link Checker\n" + "=" * 50)

        if not self.parse_requirements():
            return False
        if not self.parse_design():
            return False

        # 命名規則からマッピングを推定
        self._infer_mappings_from_naming()

        mappable_rq = sum(1 for rq in self.rq_ids if not _is_context_id(rq))
        print(f"検出: RQ-* ID 数: {len(self.rq_ids)} (コンテキストID除外後: {mappable_rq})")
        print(f"検出: DS-* ID 数: {len(self.ds_ids)}")
        print(f"マッピング: RQ-DS 対応数: {sum(len(v) for v in self.rq_to_ds.values())}\n")

        self.check_coverage()
        self.check_duplicates()
        self.check_consistency()

        return True

    def report(self):
        """チェック結果をレポート出力"""
        print("\n結果レポート")
        print("-" * 50)

        if not self.issues:
            print("✓ 全てのチェックに合格しました")
            print(f"  - RQ-* 総数: {len(self.rq_ids)}")
            print(f"  - DS-* 総数: {len(self.ds_ids)}")
            print(f"  - 欠落: 0件")
            print(f"  - 重複: 0件")
            print(f"  - 不整合: 0件")
        else:
            print(f"✗ {len(self.issues)} 件の問題が検出されました:\n")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}\n")

        print("\n対応マッピング (有効なもの)")
        print("-" * 50)
        if self.rq_to_ds:
            for rq in sorted(self.rq_to_ds.keys()):
                ds_list = ', '.join(sorted(self.rq_to_ds[rq]))
                print(f"  {rq} → {ds_list}")
        else:
            print("  (対応がありません)")


def main():
    """メイン処理"""
    if len(sys.argv) < 3:
        print("使用方法: python3 rq_ds_link_checker.py <requirements.md> <detail_design.md>")
        sys.exit(1)

    rq_file = Path(sys.argv[1])
    ds_file = Path(sys.argv[2])

    checker = RQDSChecker(rq_file, ds_file)
    if checker.run():
        checker.report()
    else:
        print("チェックに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
