#!/usr/bin/env python3
"""
RQ-DS Link Checker Script

目的:
  要件定義書 (requirements.md) と詳細設計書 (detail_design.md) の
  要件ID (RQ-*) と設計ID (DS-*) の対応関係をチェックし、
  欠落・不整合を検出します。
  （1 つの DS-* が複数の RQ-* に対応することは isdd では正常な設計表現なので、重複は検出しません）

使用方法:
  python3 rq_ds_link_checker.py <requirements.md> <detail_design.md> [--base <docs/requirements.md>]

変更フロー:
  変更要件定義書と変更設計書を渡すときは、--base に正本の要件定義書を渡す。
  変更設計書が既存の要件（変更要件定義書に無い RQ-*）を参照していても、正本にあれば未定義参照にしない。
  対応欠落の判定は、渡した変更要件定義書の要件だけで行う。

対応の根拠:
  設計書の「要件と設計の対応表」を含む見出しの節にある表の行で、DS-* と RQ-* が同じ行にあることだけを対応の根拠にする
  （isdd v2.1 以降。各章の表や設計 ID の名前からは対応を読まない）。設計書のほかの章に現れる DS-* が
  この節に無い場合も問題として報告する。

除外要件:
  設計書の「除外要件」を含む見出しの節に書かれた RQ-* は、ユーザーの承認を得て設計から外した要件として扱い、
  DS-* への対応を求めない（件数だけ表示する）。

未定義の参照:
  設計書が参照する RQ-* が要件定義書に無い場合（要件を消したのに設計に残っている、ID の書き間違いなど）を問題として報告する。

出力:
  - 対応欠落一覧: RQ-* にマッピングされていない DS-*、その逆
  - 未定義参照一覧: 要件定義書に無いのに設計書が参照している RQ-*
  - 不整合一覧: マッピング構造の矛盾
  - 検証サマリ: 総数、欠落数、不整合数

終了コード:
  0: 問題なし
  1: 1 件以上の問題あり、またはファイルを読めなかった
"""

import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Optional

# ハイフン区切りの複合IDにマッチする正規表現
# 例: RQ-FT-LOGIN, RQ-NF-PASSWORD-HASH-STORAGE
RQ_PATTERN = re.compile(r'\bRQ(?:-[A-Z0-9][A-Z0-9_]*)+')
DS_PATTERN = re.compile(r'\bDS(?:-[A-Z0-9][A-Z0-9_]*)+')

# ヘッダー列ラベルを除外（例: RQ-ID, DS-ID, RQ-BZ-ID, RQ-BK-ID）
HEADER_LABEL_PATTERN = re.compile(r'^(?:RQ|DS)(?:-[A-Z0-9]+)+-ID$')

# 業務コンテキストIDのプレフィックス（DS-*へのマッピング不要）
# RQ-BZ: 業務、RQ-BK: 業務課題、RQ-EF: 見込み経営効果。いずれも設計要素で実現するものではない
CONTEXT_PREFIXES = ('RQ-BK-', 'RQ-BZ-', 'RQ-EF-')

# 設計書の「要件と設計の対応表」節と「除外要件」節の見出し
HEADING_PATTERN = re.compile(r'^\s{0,3}#{1,6}\s+(.*)$')
MAPPING_HEADING = '要件と設計の対応表'
EXCLUSION_HEADING = '除外要件'


def _split_deleted_lines(content: str):
    """(有効な行, [削除] の行) に分ける。

    [追加] を含む文書を変更文書とみなし、[削除] だけを含む行を削除済みとして外す。[追加] と [削除] が同じ行にある行は
    判定できないので有効な行として残す（isdd-build の対応表チェッカーと同じ扱い）。
    [追加] が無い文書は正本なので、「[削除]」の文字があっても内容として読み、行を外さない。
    """
    lines = content.splitlines()
    if not any('[追加]' in line for line in lines):
        return lines, []
    active = [line for line in lines if '[削除]' not in line or '[追加]' in line]
    deleted = [line for line in lines if '[削除]' in line and '[追加]' not in line]
    return active, deleted


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

    def __init__(self, rq_file: Path, ds_file: Path, base_rq_file: Optional[Path] = None):
        self.rq_file = rq_file
        self.ds_file = ds_file
        self.base_rq_file = base_rq_file
        self.base_rq_ids: Set[str] = set()  # 正本の要件定義書の RQ-ID（変更フローで未定義参照の判定にだけ使う）
        self.rq_ids: Set[str] = set()
        self.deleted_rq_ids: Set[str] = set()  # [削除]行のRQ-ID（未定義参照の判定で、削除した要件への言及を許すため）
        self.excluded_rq_ids: Set[str] = set()  # 設計書の「除外要件」節にある RQ-ID（承認済みの除外）
        self.design_rq_refs: Set[str] = set()  # 設計書（[削除] 行を除く）に現れる RQ-ID
        self.ds_ids: Set[str] = set()
        self.rq_to_ds: Dict[str, Set[str]] = defaultdict(set)  # RQ → DS のマッピング
        self.ds_to_rq: Dict[str, Set[str]] = defaultdict(set)  # DS → RQ のマッピング
        self.issues: List[str] = []

    def extract_ids(self, text: str, pattern: re.Pattern) -> Set[str]:
        """テキストからIDを抽出（無効なIDを除外）"""
        return {m for m in pattern.findall(text) if _is_valid_id(m)}

    def parse_requirements(self) -> bool:
        """要件定義書を読み込み、RQ-* ID を抽出。[削除]タグを含む行は変更設計書の削除要件として除外する"""
        try:
            with open(self.rq_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 変更要件定義書（[追加] を含む文書）では [削除] 行を削除済み要件としてマッピング対象から除外する。
            # 正本には区分を書かないので、正本の行に「[削除]」の文字があっても内容として読む
            active_lines, deleted_lines = _split_deleted_lines(content)
            self.rq_ids = self.extract_ids('\n'.join(active_lines), RQ_PATTERN)
            # [削除]行のRQ-IDは、設計書が削除した要件に触れても未定義参照にしないために別途保持する
            self.deleted_rq_ids = self.extract_ids('\n'.join(deleted_lines), RQ_PATTERN)
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
        """詳細設計書を読み込み、DS-* ID と RQ-* への参照を抽出。[削除]タグを含む行は変更設計書の削除エントリとして除外する"""
        try:
            with open(self.ds_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 変更設計書（[追加] を含む文書）では [削除] 行を削除済みエントリとして ID 抽出・マッピング対象から除外する
            active_lines, _ = _split_deleted_lines(content)
            active_content = '\n'.join(active_lines)

            # DS-* ID を抽出（[削除]行を除外済みのテキストから）
            self.ds_ids = self.extract_ids(active_content, DS_PATTERN)
            self.design_rq_refs = self.extract_ids(active_content, RQ_PATTERN)
            if not self.ds_ids:
                self.issues.append("警告: detail_design.md から DS-* ID が検出されませんでした")

            # 見出しで節を区切り、「要件と設計の対応表」節の行と「除外要件」節の RQ-* を集める
            mapping_lines: List[str] = []
            found_mapping = False
            in_mapping = in_exclusion = False
            mapping_level = exclusion_level = 0
            for line in active_lines:
                heading = HEADING_PATTERN.match(line)
                if heading:
                    level = len(line.strip()) - len(line.strip().lstrip('#'))
                    title = heading.group(1)
                    if in_exclusion and level <= exclusion_level:
                        in_exclusion = False
                    if in_mapping and level <= mapping_level:
                        in_mapping = False
                    if EXCLUSION_HEADING in title:
                        in_exclusion, exclusion_level = True, level
                    elif MAPPING_HEADING in title:
                        in_mapping, mapping_level, found_mapping = True, level, True
                    continue
                if in_exclusion:
                    self.excluded_rq_ids |= {m for m in RQ_PATTERN.findall(line) if _is_valid_id(m)}
                elif in_mapping:
                    mapping_lines.append(line)

            if not found_mapping:
                self.issues.append(
                    f"⚠ 対応表の章が無い: 設計書に「{MAPPING_HEADING}」を含む見出しの節がありません"
                    "（要件との対応はこの節の表だけに書く）"
                )

            # 対応表の節の表の行ごとに DS-* と RQ-* の共起を検出（[削除]行はスキップ済み）
            mapped_ds: Set[str] = set()
            for line in mapping_lines:
                ds_in_line = {m for m in DS_PATTERN.findall(line) if _is_valid_id(m)}
                rq_in_line = {m for m in RQ_PATTERN.findall(line) if _is_valid_id(m)}
                mapped_ds |= ds_in_line
                if ds_in_line and rq_in_line:
                    for ds_id in ds_in_line:
                        for rq_id in rq_in_line:
                            self.rq_to_ds[rq_id].add(ds_id)
                            self.ds_to_rq[ds_id].add(rq_id)

            # ほかの章に現れるのに対応表の節に無い DS-*
            if found_mapping:
                missing = self.ds_ids - mapped_ds
                if missing:
                    self.issues.append(
                        f"⚠ 対応表の章に無い: 以下の DS-* は設計書にありますが、「{MAPPING_HEADING}」の表にありません:\n"
                        f"  {', '.join(sorted(missing))}"
                    )

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

        # DS-* にマッピングされていない RQ-*（コンテキストIDは除外）
        mappable_rq = {rq for rq in self.rq_ids if not _is_context_id(rq)}
        unmapped_rq = mappable_rq - set(self.rq_to_ds.keys()) - self.excluded_rq_ids
        if unmapped_rq:
            self.issues.append(
                f"⚠ 対応欠落: 以下の RQ-* には対応する DS-* がマッピングされていません:\n"
                f"  {', '.join(sorted(unmapped_rq))}"
            )

    def check_undefined_refs(self):
        """設計書が参照しているのに要件定義書に無い RQ-* を検出する"""
        undefined = self.design_rq_refs - self.rq_ids - self.deleted_rq_ids - self.base_rq_ids
        if undefined:
            self.issues.append(
                f"⚠ 未定義参照: 以下の RQ-* は設計書が参照していますが、要件定義書にありません:\n"
                f"  {', '.join(sorted(undefined))}"
            )

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
        if self.base_rq_file is not None:
            try:
                base = self.base_rq_file.read_text(encoding='utf-8')
            except FileNotFoundError:
                self.issues.append(f"エラー: {self.base_rq_file} が見つかりません")
                return False
            self.base_rq_ids = self.extract_ids(base, RQ_PATTERN)
            print(f"正本: {self.base_rq_file} の RQ-* {len(self.base_rq_ids)} 件を既存の要件として参照する")

        mappable_rq = sum(1 for rq in self.rq_ids if not _is_context_id(rq))
        print(f"検出: RQ-* ID 数: {len(self.rq_ids)} (コンテキストID除外後: {mappable_rq})")
        print(f"検出: DS-* ID 数: {len(self.ds_ids)}")
        if self.excluded_rq_ids:
            print(f"除外: 設計書の「除外要件」節にある RQ-* {len(self.excluded_rq_ids)} 件は対応を求めない: "
                  f"{', '.join(sorted(self.excluded_rq_ids))}")
        print(f"マッピング: RQ-DS 対応数: {sum(len(v) for v in self.rq_to_ds.values())}\n")

        self.check_coverage()
        self.check_undefined_refs()
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
    usage = "使用方法: python3 rq_ds_link_checker.py <requirements.md> <detail_design.md> [--base <docs/requirements.md>]"
    args = sys.argv[1:]
    base_rq_file = None
    if "--base" in args:
        i = args.index("--base")
        if i + 1 >= len(args):
            print(usage)
            sys.exit(1)
        base_rq_file = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) < 2:
        print(usage)
        sys.exit(1)

    rq_file = Path(args[0])
    ds_file = Path(args[1])

    checker = RQDSChecker(rq_file, ds_file, base_rq_file)
    if not checker.run():
        for issue in checker.issues:
            print(issue)
        print("チェックに失敗しました")
        sys.exit(1)
    checker.report()
    # 問題があれば終了コード 1 を返し、フックや CI で機械判定できるようにする
    if checker.issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
