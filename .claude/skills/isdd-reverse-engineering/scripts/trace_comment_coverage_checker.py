#!/usr/bin/env python3
"""
Trace Comment Coverage Checker Script

目的:
  ソースコードのトレーサブルコメント（RQ-* および DS-* への参照）の
  付与状況をチェックし、未付与要素とカバレッジを検出します。

使用方法:
  python3 trace_comment_coverage_checker.py <source_dir> [<rq_ds_mapping.json>]

出力:
  - 未付与要素一覧: トレーサブルコメントが付与されていない関数/クラス/モジュール
  - 記載不足項目一覧: 必須項目（RQ-*, DS-*）が記載されていないコメント
  - カバレッジ率: トレーサブルコメント付与率（%）
"""

import re
import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List, Tuple, Optional


class TraceCommentChecker:
    """トレーサブルコメント付与状況チェッカー"""

    # サポート言語の拡張子と関数/クラス定義パターン
    LANG_PATTERNS = {
        '.py': {
            'extensions': ['.py'],
            'function': r'^\s*(?:async\s+)?def\s+(\w+)\s*\(',
            'class': r'^\s*class\s+(\w+)(?:\(|:)',
            'module': r'""".*?"""',
            'comment': r'(?:"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|#.*?)(?:\n|$)',
        },
        '.ts': {
            'extensions': ['.ts', '.tsx'],
            'function': r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',
            'class': r'(?:export\s+)?class\s+(\w+)\s*(?:\{|extends)',
            'module': r'/\*\*[\s\S]*?\*/',
            'comment': r'(?:\/\*\*[\s\S]*?\*\/|\/\/.*?)(?:\n|$)',
        },
        '.java': {
            'extensions': ['.java'],
            'function': r'(?:public|private|protected)?\s+(?:static\s+)?(?:async\s+)?(?:\w+\s+)*(\w+)\s*\(',
            'class': r'(?:public|private)?\s*class\s+(\w+)\s*(?:\{|extends)',
            'module': r'/\*\*[\s\S]*?\*/',
            'comment': r'(?:\/\*\*[\s\S]*?\*\/|\/\/.*?)(?:\n|$)',
        },
        '.go': {
            'extensions': ['.go'],
            'function': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(',
            'class': r'type\s+(\w+)\s+struct',
            'module': r'/\*[\s\S]*?\*/',
            'comment': r'(?:\/\*[\s\S]*?\*\/|\/\/.*?)(?:\n|$)',
        },
    }

    def __init__(self, source_dir: Path, rq_ds_mapping: Optional[Dict] = None):
        self.source_dir = source_dir
        self.rq_ds_mapping = rq_ds_mapping or {}
        self.elements: List[Dict] = []  # 抽出された全要素
        self.without_trace: List[Dict] = []  # トレースなし
        self.incomplete_trace: List[Dict] = []  # RQ or DS が不足
        self.valid_trace: List[Dict] = []  # 有効なトレース

    def detect_language(self, file_path: Path) -> Optional[str]:
        """ファイルの拡張子から言語を判定"""
        suffix = file_path.suffix.lower()
        for lang, patterns in self.LANG_PATTERNS.items():
            if suffix in patterns['extensions']:
                return lang
        return None

    def extract_elements(self, file_path: Path, content: str, language: str) -> List[Dict]:
        """ソースコードから関数/クラス/モジュールを抽出"""
        patterns = self.LANG_PATTERNS[language]
        elements = []

        # モジュールレベルのコメントをチェック
        module_comment = ""
        for match in re.finditer(patterns['module'], content):
            module_comment = match.group(0)
            break

        # 関数を抽出
        for match in re.finditer(patterns['function'], content, re.MULTILINE):
            func_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            # 関数直前のコメント（docstring or comment）を抽出
            lines_before = content[:match.start()].split('\n')
            func_comment = ""
            for line in reversed(lines_before[-10:]):  # 最大10行上を検索
                if line.strip().startswith(('"""', "'''", '/*', '//', '#')):
                    func_comment += line + "\n"
                elif line.strip():
                    break
            
            elements.append({
                'type': 'function',
                'name': func_name,
                'file': str(file_path.relative_to(self.source_dir)),
                'line': line_num,
                'comment': func_comment,
            })

        # クラスを抽出
        for match in re.finditer(patterns['class'], content, re.MULTILINE):
            class_name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            
            lines_before = content[:match.start()].split('\n')
            class_comment = ""
            for line in reversed(lines_before[-10:]):
                if line.strip().startswith(('"""', "'''", '/*', '//', '#')):
                    class_comment += line + "\n"
                elif line.strip():
                    break
            
            elements.append({
                'type': 'class',
                'name': class_name,
                'file': str(file_path.relative_to(self.source_dir)),
                'line': line_num,
                'comment': class_comment,
            })

        return elements

    def check_trace_comments(self):
        """全ソースファイルをスキャンしてトレーサブルコメントをチェック"""
        if not self.source_dir.exists():
            print(f"エラー: {self.source_dir} が見つかりません")
            return False

        for file_path in self.source_dir.rglob('*'):
            if file_path.is_dir():
                continue

            language = self.detect_language(file_path)
            if not language:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                elements = self.extract_elements(file_path, content, language)
                self.elements.extend(elements)

                # 各要素のトレーサブルコメントをチェック
                for elem in elements:
                    has_rq = 'RQ-' in elem['comment']
                    has_ds = 'DS-' in elem['comment']
                    has_comment = bool(elem['comment'].strip())

                    if not has_comment:
                        self.without_trace.append(elem)
                    elif not (has_rq and has_ds):
                        self.incomplete_trace.append({
                            **elem,
                            'missing': ('RQ' if not has_rq else '') + ('DS' if not has_ds else ''),
                        })
                    else:
                        self.valid_trace.append(elem)

            except UnicodeDecodeError:
                # バイナリファイルをスキップ
                continue
            except Exception as e:
                print(f"警告: {file_path} の処理中にエラー: {e}")
                continue

        return True

    def run(self) -> bool:
        """チェック全体を実行"""
        print("Trace Comment Coverage Checker\n" + "=" * 50)
        return self.check_trace_comments()

    def report(self):
        """チェック結果をレポート出力"""
        total = len(self.elements)
        with_trace = len(self.valid_trace)
        coverage = (with_trace / total * 100) if total > 0 else 0

        print("\n結果レポート")
        print("-" * 50)
        print(f"スキャン対象: {self.source_dir}")
        print(f"検出: 関数/クラス/モジュール総数: {total}")
        print(f"有効なトレース: {with_trace} ({coverage:.1f}%)")
        print(f"未付与: {len(self.without_trace)}")
        print(f"不足: {len(self.incomplete_trace)}\n")

        if self.without_trace:
            print("✗ トレーサブルコメント未付与の要素")
            print("-" * 50)
            for elem in sorted(self.without_trace, key=lambda x: (x['file'], x['line']))[:20]:
                print(f"  {elem['file']}:{elem['line']} - {elem['type']} '{elem['name']}'")
            if len(self.without_trace) > 20:
                print(f"  ... 他 {len(self.without_trace) - 20} 件")
            print()

        if self.incomplete_trace:
            print("⚠ 記載不足（RQ-* または DS-* が不足）の要素")
            print("-" * 50)
            for elem in sorted(self.incomplete_trace, key=lambda x: (x['file'], x['line']))[:20]:
                print(f"  {elem['file']}:{elem['line']} - {elem['type']} '{elem['name']}' (不足: {elem['missing']})")
            if len(self.incomplete_trace) > 20:
                print(f"  ... 他 {len(self.incomplete_trace) - 20} 件")
            print()

        print("カバレッジサマリ")
        print("-" * 50)
        print(f"総数: {total} 要素")
        print(f"有効: {with_trace} 要素 ({coverage:.1f}%)")
        print(f"未付与: {len(self.without_trace)} 要素 ({len(self.without_trace)/total*100 if total > 0 else 0:.1f}%)")
        print(f"不足: {len(self.incomplete_trace)} 要素 ({len(self.incomplete_trace)/total*100 if total > 0 else 0:.1f}%)")


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python3 trace_comment_coverage_checker.py <source_dir> [<rq_ds_mapping.json>]")
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    rq_ds_mapping = {}

    if len(sys.argv) >= 3:
        mapping_file = Path(sys.argv[2])
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                rq_ds_mapping = json.load(f)
        except Exception as e:
            print(f"警告: RQ-DS マッピングの読み込みに失敗しました: {e}")

    checker = TraceCommentChecker(source_dir, rq_ds_mapping)
    if checker.run():
        checker.report()
    else:
        print("チェックに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
