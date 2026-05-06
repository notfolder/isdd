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
from typing import Set, Dict, List, Tuple


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

    # RQ-* / DS-* の完全IDパターン（ハイフン区切りのセグメントを複数許容）
    RQ_PATTERN = r'\bRQ(?:-[A-Z0-9][A-Z0-9_]*)+'
    DS_PATTERN = r'\bDS(?:-[A-Z0-9][A-Z0-9_]*)+'

    # マークダウン表のヘッダーラベルとして使われる疑似ID（誤検出除外）
    HEADER_ID_SUFFIX = re.compile(r'-ID$')

    def extract_ids(self, text: str, pattern: str) -> Set[str]:
        """テキストからID（RQ-* または DS-*）を抽出。表ヘッダーラベルは除外する"""
        matches = re.findall(pattern, text)
        return {m for m in matches if not self.HEADER_ID_SUFFIX.search(m)}

    def parse_requirements(self) -> bool:
        """要件定義書を読み込み、RQ-* ID を抽出"""
        try:
            with open(self.rq_file, 'r', encoding='utf-8') as f:
                content = f.read()
            self.rq_ids = self.extract_ids(content, self.RQ_PATTERN)
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
            self.ds_ids = self.extract_ids(content, self.DS_PATTERN)
            if not self.ds_ids:
                self.issues.append("警告: detail_design.md から DS-* ID が検出されませんでした")

            # マークダウンテーブルの同一行に DS-* と RQ-* が共存する場合を対応関係とみなす
            for line in content.split('\n'):
                if '|' not in line:
                    continue
                ds_in_line = re.findall(self.DS_PATTERN, line)
                rq_in_line = re.findall(self.RQ_PATTERN, line)
                for ds in ds_in_line:
                    for rq in rq_in_line:
                        self.rq_to_ds[rq].add(ds)
                        self.ds_to_rq[ds].add(rq)

            # フォールバック: "DS-XXX ... RQ-YYY" 形式の非テーブル記述も抽出
            for ds_id in self.ds_ids:
                if ds_id in self.ds_to_rq:
                    continue  # テーブル行で既に検出済み
                pattern = (
                    rf'\b{re.escape(ds_id)}\b'
                    rf'[:\s\-\(\)]*'
                    rf'((?:{self.RQ_PATTERN})(?:\s*[,、]\s*(?:{self.RQ_PATTERN}))*)'
                )
                matches = re.findall(pattern, content)
                if matches:
                    rqs = re.findall(self.RQ_PATTERN, matches[0])
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

    def check_coverage(self):
        """RQ-* と DS-* の対応欠落をチェック"""
        # RQ-* にマッピングされていない DS-*
        unmapped_ds = self.ds_ids - set(self.ds_to_rq.keys())
        if unmapped_ds:
            self.issues.append(
                f"⚠ 対応欠落: 以下の DS-* には対応する RQ-* がマッピングされていません:\n"
                f"  {', '.join(sorted(unmapped_ds))}"
            )

        # DS-* にマッピングされていない RQ-*
        unmapped_rq = self.rq_ids - set(self.rq_to_ds.keys())
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

        print(f"検出: RQ-* ID 数: {len(self.rq_ids)}")
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
