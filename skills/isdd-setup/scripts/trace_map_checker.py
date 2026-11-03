#!/usr/bin/env python3
"""
Trace Map Checker Script

目的:
  対応表（docs/trace_map.md）を介して、詳細設計書の設計ID（DS-*）と
  ソースコードのクラス・公開関数・モジュールの対応を検証する。
  コード側には ID を書かない方式（isdd v2.0.0 以降）の整合チェッカー。

使用方法:
  python3 trace_map_checker.py <detail_design.md> <trace_map.md> <source_dir> [<source_dir> ...] [--strict]
      [--active-change <ポインタファイル>] [--tests <テストディレクトリ>]... [--granularity function|class]

テストディレクトリ（--tests。既定の運用では e2e）:
  配下のファイルはすべてテストとみなす。ソースディレクトリの中のテストファイル（test_*.py など）も同じ扱い。
  テストファイルは DS-TS の行でだけ対応表に載せられる（DS-TS → e2e/test_order.py::test_cancel_order）。
  テストディレクトリが存在するときは、詳細設計書 8-2（E2E テストのシナリオ）の DS-TS が対応表に無ければ警告する。
  テストディレクトリが無いときは警告しない（E2E の有無は implementation_completeness_checker.py が確かめる）。

粒度（--granularity。既定は function）:
  function: コードのファイル・クラス・公開関数・メソッドのすべてが対応表に要る。
  class:    ファイルとクラスが要る。公開関数は、そのファイル（トップレベル関数）かクラス（メソッド）が
            対応表にあれば未登録と扱わない。設計書に DS-FN があれば、粒度にかかわらず対応表に要る。

進行中の変更（変更フロー）:
  --active-change に渡したファイル（既定の運用では docs/active_change）があれば、その 1 行目を
  変更のディレクトリ（.history/[YYYYMMDD]-[タスク名]）とみなし、そこにある change_detail_design.md を
  正本の詳細設計書に重ねて判定する。有効な設計 ID は「正本 ＋ 変更設計書の ID − 変更設計書の [削除] 行の ID」。
  正本への反映は実装後に isdd-build の実装後レビューが行い、反映が終わるとポインタファイルを消す。
  ポインタファイルが無ければ、正本だけで判定する。

対応表の形式（Markdown の表。列名は「DS-ID」「修飾名」「備考」）:
  | DS-ID | 修飾名 | 備考 |
  |---|---|---|
  | `DS-MD-HELLO-MODULE` | `src/hello.py` | モジュール |
  | `DS-CL-HELLO-WORLD-PRINTER` | `src/hello.py::HelloWorldPrinter` | クラス |
  | `DS-FN-GET-HELLO-MESSAGE` | `src/hello.py::HelloWorldPrinter.get_hello_message` | メソッド |

修飾名の文法:
  <ファイルパス>                      … モジュール（ファイル）単位
  <ファイルパス>::<名前>              … トップレベルのクラスまたは関数
  <ファイルパス>::<クラス名>.<名前>   … メソッド
  ファイルパスはプロジェクトルート（カレントディレクトリ）からの相対パス。

判定:
  エラー（終了コード 1）
    - 対応表の DS-ID が詳細設計書に存在しない
    - 対応表の修飾名がコードに存在しない（改名・削除の見落とし）
    - DS-MD の行にファイル以外の修飾名、DS-MD 以外の行にファイルだけの修飾名が書かれている
    - テストファイルを DS-TS 以外の行が指している。DS-TS の行がテスト以外を指している
  警告（既定では終了コード 0。--strict 指定時は終了コード 1）
    - コードにあるクラス・公開関数・ファイルが対応表に未登録（公開関数は --granularity class なら緩める）
    - 詳細設計書の DS-MD / DS-CL / DS-FN が対応表に未登録（未実装の可能性）
    - 詳細設計書の表で DS-MD と同じ行に並ぶ設計 ID（第 7 章「実現する設計 ID」。DS-IF・DS-BT・DS-EV・DS-SC など）が
      対応表に未登録（未実装の可能性）。設計書が「このファイルで実現する」と宣言した要素を拾う
    - 詳細設計書 8-2 の DS-TS が対応表に未登録（テストが無い可能性。テストディレクトリがあるときだけ）
    - 進行中の変更設計書で [削除] にした設計 ID が対応表に残っている（コードと対応表の行の消し忘れ）

公開要素の定義:
  アンダースコア始まりの名前（_private、__dunder__）は対象外。
  テストファイル（test_*.py、*_test.py、*.spec.ts、*.test.ts、conftest.py）は対象外。
  node_modules、.venv、venv、__pycache__、dist、build、.git 配下は対象外。

言語の扱い:
  記号（クラス・関数・メソッド）まで確認できる言語: Python（ast）、TypeScript / JavaScript、Java、Go（正規表現で近似）
  ファイルの存在だけ確認する言語: それ以外の一般的なソース拡張子（C#、Ruby、PHP、Kotlin、Swift、Rust、C/C++ など）。
    これらのファイルを指す「::名前」付きの修飾名は、ファイルが存在すれば「確認対象外」として数え、エラーにも警告にもしない。
    対応表に未登録のファイルは、どの言語でも警告にする。
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

DS_PATTERN = re.compile(r'\bDS(?:-[A-Z0-9][A-Z0-9_]*)+')
HEADER_LABEL_PATTERN = re.compile(r'^(?:RQ|DS)(?:-[A-Z0-9]+)+-ID$')

SKIP_DIRS = {'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', '.git', '.history', '.agents', '.claude'}
TEST_FILE_PATTERNS = (
    re.compile(r'^test_.*\.py$'),
    re.compile(r'.*_test\.py$'),
    re.compile(r'^conftest\.py$'),
    re.compile(r'.*\.spec\.[jt]sx?$'),
    re.compile(r'.*\.test\.[jt]sx?$'),
    re.compile(r'.*_test\.go$'),
    re.compile(r'.*Test\.java$'),
    re.compile(r'.*Tests?\.cs$'),
    re.compile(r'.*_spec\.rb$'),
    re.compile(r'.*_test\.rb$'),
    re.compile(r'.*Test\.php$'),
    re.compile(r'.*Test\.kt$'),
    re.compile(r'.*Tests\.swift$'),
)

# 記号（クラス・関数・メソッド）まで抽出できる言語
SYMBOL_LANGS = {'.py', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.java', '.go'}
# ファイルの存在だけ確認する言語（記号の抽出はしない）
FILE_ONLY_LANGS = {
    '.cs', '.rb', '.php', '.kt', '.kts', '.swift', '.rs', '.c', '.h', '.cpp', '.hpp', '.cc', '.hh',
    '.scala', '.dart', '.vue', '.svelte', '.sh', '.bash', '.pl', '.pm', '.lua', '.ex', '.exs', '.erl',
    '.hs', '.ml', '.fs', '.clj', '.cljs', '.m', '.mm', '.r', '.jl', '.groovy', '.ps1', '.vb', '.sql',
}
TS_LIKE_LANGS = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}

# Python 以外は正規表現で近似抽出する（クラス所属は判定しない）
REGEX_LANGS = {
    '.ts': {
        'function': re.compile(
            # function 宣言、または const/let/var に代入されたアロー関数・function 式
            r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)\s*[(<]'
            r'|^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=\n]+)?=\s*(?:async\s*)?(?:\([^)\n]*\)|\w+)\s*(?::[^=\n]+)?=>'
            r'|^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=\n]+)?=\s*(?:async\s+)?function\b',
            re.MULTILINE,
        ),
        'class': re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)', re.MULTILINE),
        'method': re.compile(r'^\s+(?:public|private|protected|static|async|\s)*\s*(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|, ]+)?\s*\{', re.MULTILINE),
    },
    '.tsx': None,  # .ts と同じ（.js .jsx .mjs .cjs も同じ）
    '.java': {
        'function': re.compile(r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?[\w<>\[\], ]+\s+(\w+)\s*\([^)]*\)\s*(?:throws[\w, ]+)?\s*\{', re.MULTILINE),
        'class': re.compile(r'^\s*(?:public|private|protected)?\s*(?:abstract\s+|final\s+)?(?:class|interface|enum|record)\s+(\w+)', re.MULTILINE),
        'method': None,
    },
    '.go': {
        'function': re.compile(r'^func\s+(\w+)\s*\(', re.MULTILINE),
        'class': re.compile(r'^type\s+(\w+)\s+(?:struct|interface)\b', re.MULTILINE),
        'method': re.compile(r'^func\s+\(\s*\w+\s+\*?(\w+)\s*\)\s+(\w+)\s*\(', re.MULTILINE),
    },
}
JAVA_KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'return', 'new', 'else', 'try', 'synchronized'}


def _is_valid_ds(id_str: str) -> bool:
    if HEADER_LABEL_PATTERN.match(id_str):
        return False
    return len(id_str.split('-')) >= 3


def _is_public(name: str) -> bool:
    return not name.startswith('_')


def _is_test_file(path: Path) -> bool:
    return any(p.match(path.name) for p in TEST_FILE_PATTERNS)


class CodeSymbols:
    """ソースコードから抽出した要素（ファイル・クラス・関数・メソッド）"""

    def __init__(self):
        self.files: Set[str] = set()
        # 記号を抽出できなかった言語のファイル（存在確認だけに使う）
        self.file_only: Set[str] = set()
        # 修飾名 → 種別（'class' | 'function' | 'method'）
        self.symbols: Dict[str, str] = {}
        # テストファイルとその記号（DS-TS の行だけが指せる）
        self.test_files: Set[str] = set()
        self.test_symbols: Dict[str, str] = {}

    def add(self, qualified: str, kind: str):
        self.symbols[qualified] = kind


def extract_python(rel: str, content: str, out: CodeSymbols) -> None:
    """Python ファイルを ast で解析し、公開クラス・関数・メソッドを登録する"""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_public(node.name):
                out.add(f"{rel}::{node.name}", 'function')
        elif isinstance(node, ast.ClassDef):
            if not _is_public(node.name):
                continue
            out.add(f"{rel}::{node.name}", 'class')
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public(sub.name):
                    out.add(f"{rel}::{node.name}.{sub.name}", 'method')


def extract_regex(rel: str, content: str, lang: str, out: CodeSymbols) -> None:
    """Python 以外のファイルを正規表現で近似解析する"""
    patterns = REGEX_LANGS['.ts'] if lang in TS_LIKE_LANGS else REGEX_LANGS[lang]
    classes: List[str] = []
    for m in patterns['class'].finditer(content):
        name = m.group(1)
        if _is_public(name):
            classes.append(name)
            out.add(f"{rel}::{name}", 'class')
    for m in patterns['function'].finditer(content):
        # 選択肢のある正規表現では、マッチしたグループだけが名前を持つ
        name = next((g for g in m.groups() if g), None)
        if not name or name in JAVA_KEYWORDS or not _is_public(name):
            continue
        out.add(f"{rel}::{name}", 'function')
    if patterns.get('method') is not None:
        for m in patterns['method'].finditer(content):
            if lang == '.go':
                cls, name = m.group(1), m.group(2)
                if _is_public(name):
                    out.add(f"{rel}::{cls}.{name}", 'method')
            else:
                name = m.group(1)
                if name in JAVA_KEYWORDS or name in ('constructor',) or not _is_public(name):
                    continue
                # クラス所属は判定できないため、全クラスとの組み合わせを許容する
                for cls in classes:
                    out.add(f"{rel}::{cls}.{name}", 'method')
    if lang == '.java':
        # Java のメソッドは function パターンで拾われるため、クラス所属の組み合わせも許容する
        for q, kind in list(out.symbols.items()):
            if q.startswith(rel + '::') and kind == 'function':
                name = q.split('::', 1)[1]
                for cls in classes:
                    out.add(f"{rel}::{cls}.{name}", 'method')


def _walk_sources(root: Path, dirs: List[Path]):
    """ディレクトリ配下の対応言語のファイルを (相対パス, 拡張子, 中身) で返す"""
    for base in dirs:
        base = (root / base).resolve() if not base.is_absolute() else base
        if not base.exists():
            continue
        for path in sorted(base.rglob('*')):
            if path.is_dir():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            lang = path.suffix.lower()
            if lang not in SYMBOL_LANGS and lang not in FILE_ONLY_LANGS:
                continue
            try:
                content = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            try:
                rel = path.resolve().relative_to(root).as_posix()
            except ValueError:
                rel = path.as_posix()
            if path.name == '__init__.py' and not content.strip():
                continue
            yield path, rel, lang, content


def _extract(rel: str, lang: str, content: str, out: CodeSymbols) -> None:
    out.files.add(rel)
    if lang not in SYMBOL_LANGS:
        out.file_only.add(rel)
    elif lang == '.py':
        extract_python(rel, content, out)
    else:
        extract_regex(rel, content, lang, out)


def collect_code(root: Path, source_dirs: List[Path], test_dirs: Optional[List[Path]] = None) -> CodeSymbols:
    out = CodeSymbols()
    tests = CodeSymbols()
    for path, rel, lang, content in _walk_sources(root, source_dirs):
        _extract(rel, lang, content, tests if _is_test_file(path) else out)
    for _, rel, lang, content in _walk_sources(root, test_dirs or []):
        _extract(rel, lang, content, tests)
    out.test_files = tests.files
    out.test_symbols = tests.symbols
    return out


class DesignIds:
    """詳細設計書（または変更設計書の有効行）から読み取った設計 ID"""

    def __init__(self):
        self.ids: Set[str] = set()
        # DS-MD と同じ表の行に並ぶ設計 ID（第 7 章の「実現する設計 ID」）。そのファイルで実現する要素
        self.code_realized: Set[str] = set()
        # 8-2「E2E テストのシナリオ」の節にある DS-TS
        self.e2e_scenarios: Set[str] = set()

    def merge(self, other: 'DesignIds') -> None:
        self.ids |= other.ids
        self.code_realized |= other.code_realized
        self.e2e_scenarios |= other.e2e_scenarios

    def remove(self, ids: Set[str]) -> None:
        self.ids -= ids
        self.code_realized -= ids
        self.e2e_scenarios -= ids


E2E_SECTION_PATTERN = re.compile(r'E2E.*シナリオ')
HEADING_PATTERN = re.compile(r'^\s{0,3}#{1,6}\s+(.*)$')


def scan_design_lines(lines: List[str]) -> DesignIds:
    """設計書の行（[削除] 行を除いたもの）から設計 ID を集める"""
    out = DesignIds()
    in_e2e = False
    for line in lines:
        ids = [m for m in DS_PATTERN.findall(line) if _is_valid_ds(m)]
        heading = HEADING_PATTERN.match(line)
        if heading:
            in_e2e = bool(E2E_SECTION_PATTERN.search(heading.group(1)))
        out.ids.update(ids)
        if in_e2e:
            out.e2e_scenarios.update(i for i in ids if i.startswith('DS-TS-'))
        if line.lstrip().startswith('|') and any(i.startswith('DS-MD-') for i in ids):
            out.code_realized.update(i for i in ids if not i.startswith(('DS-MD-', 'DS-TS-')))
    return out


def parse_design(design_path: Path) -> DesignIds:
    """詳細設計書から有効な設計 ID を抽出する（[削除] 行は除外）"""
    lines = [ln for ln in design_path.read_text(encoding='utf-8').splitlines() if '[削除]' not in ln]
    return scan_design_lines(lines)


def parse_change_design(change_path: Path) -> Tuple[DesignIds, Set[str]]:
    """変更設計書から (追加・参照する設計 ID, [削除] 行の DS-ID) を抽出する"""
    active: List[str] = []
    deleted: Set[str] = set()
    for line in change_path.read_text(encoding='utf-8').splitlines():
        if '[削除]' in line:
            deleted |= {m for m in DS_PATTERN.findall(line) if _is_valid_ds(m)}
        else:
            active.append(line)
    return scan_design_lines(active), deleted


def resolve_active_change(pointer: Optional[Path]) -> Optional[Path]:
    """ポインタファイルの 1 行目（変更のディレクトリ）から change_detail_design.md のパスを返す。ポインタが無ければ None"""
    if pointer is None or not pointer.exists():
        return None
    lines = [ln.strip() for ln in pointer.read_text(encoding='utf-8').splitlines() if ln.strip()]
    if not lines:
        return None
    return Path(lines[0].rstrip('/')) / 'change_detail_design.md'


def parse_trace_map(map_path: Path) -> Tuple[List[Tuple[str, str, int]], List[str]]:
    """対応表を読み、(DS-ID, 修飾名, 行番号) の一覧と書式エラーを返す"""
    rows: List[Tuple[str, str, int]] = []
    format_errors: List[str] = []
    content = map_path.read_text(encoding='utf-8')
    ds_col: Optional[int] = None
    name_col: Optional[int] = None
    in_table = False
    for lineno, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if not stripped.startswith('|'):
            if in_table:
                # 対応表の表が終わった。以降の表（凡例など）は読まない
                break
            continue
        if ds_col is not None:
            in_table = True
        cells = [c.strip() for c in stripped.strip('|').split('|')]
        if all(re.fullmatch(r':?-{3,}:?', c) for c in cells if c):
            continue
        if ds_col is None:
            lowered = [c.lower() for c in cells]
            if 'ds-id' in lowered and '修飾名' in cells:
                ds_col = lowered.index('ds-id')
                name_col = cells.index('修飾名')
            continue
        if len(cells) <= max(ds_col, name_col):
            format_errors.append(f"{lineno} 行目: 列数が不足しています")
            continue
        ds_id = cells[ds_col].strip('`').strip()
        qualified = cells[name_col].strip('`').strip()
        if not ds_id or not qualified:
            format_errors.append(f"{lineno} 行目: DS-ID または修飾名が空です")
            continue
        if not DS_PATTERN.fullmatch(ds_id):
            format_errors.append(f"{lineno} 行目: DS-ID の書式が不正です: {ds_id}")
            continue
        rows.append((ds_id, qualified, lineno))
    if ds_col is None:
        format_errors.append("対応表に「DS-ID」「修飾名」の列を持つ表が見つかりません")
    return rows, format_errors


class TraceMapChecker:
    def __init__(self, design: Path, trace_map: Path, source_dirs: List[Path], root: Path,
                 active_change: Optional[Path] = None, test_dirs: Optional[List[Path]] = None,
                 granularity: str = 'function'):
        self.design = design
        self.active_change = active_change
        self.trace_map = trace_map
        self.source_dirs = source_dirs
        self.test_dirs = test_dirs or []
        self.granularity = granularity
        self.root = root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        # 言語未対応のため記号の実在を確認できなかった行（エラーでも警告でもない）
        self.unverified: List[str] = []

    def run(self) -> None:
        for p, label in ((self.design, '詳細設計書'), (self.trace_map, '対応表')):
            if not p.exists():
                self.errors.append(f"{label}が見つかりません: {p}")
        if self.errors:
            return

        design = parse_design(self.design)
        deleted_ids: Set[str] = set()
        if self.active_change is not None:
            if not self.active_change.exists():
                self.errors.append(f"進行中の変更の変更設計書が見つかりません: {self.active_change}"
                                   "（ポインタファイルの 1 行目に変更のディレクトリを書く。変更が終わっていればポインタファイルを消す）")
                return
            added, deleted_ids = parse_change_design(self.active_change)
            design.merge(added)
            design.remove(deleted_ids)
        design_ids = design.ids
        rows, format_errors = parse_trace_map(self.trace_map)
        self.errors.extend(format_errors)
        code = collect_code(self.root, self.source_dirs, self.test_dirs)

        mapped_ids: Set[str] = set()
        mapped_names: Set[str] = set()
        for ds_id, qualified, lineno in rows:
            mapped_ids.add(ds_id)
            mapped_names.add(qualified)
            if ds_id in deleted_ids:
                self.warnings.append(f"対応表 {lineno} 行目: 進行中の変更で削除する設計 ID が残っています"
                                     f"（コードと対応表の行を消す）: {ds_id}")
            elif ds_id not in design_ids:
                self.errors.append(f"対応表 {lineno} 行目: DS-ID が詳細設計書に存在しません: {ds_id}")
            is_file_level = '::' not in qualified
            file_part = qualified.split('::', 1)[0]
            if ds_id.startswith('DS-TS-'):
                # テストの行。テストファイルかその関数を指す
                if qualified in code.test_files or qualified in code.test_symbols:
                    continue
                if file_part in code.test_files:
                    self.errors.append(f"対応表 {lineno} 行目: テストに存在しない修飾名です（改名・削除の見落とし）: {qualified}")
                else:
                    self.errors.append(f"対応表 {lineno} 行目: DS-TS の行はテストファイル（または e2e 配下のテスト関数）を指してください: {qualified}")
                continue
            if file_part in code.test_files:
                self.errors.append(f"対応表 {lineno} 行目: テストファイルは DS-TS の行にだけ書けます: {qualified}")
                continue
            if ds_id.startswith('DS-MD-') and not is_file_level:
                self.errors.append(f"対応表 {lineno} 行目: DS-MD の修飾名はファイルパスだけにしてください: {qualified}")
            if not ds_id.startswith('DS-MD-') and is_file_level:
                self.errors.append(f"対応表 {lineno} 行目: DS-MD 以外の修飾名には「::名前」が必要です: {qualified}")
            if is_file_level:
                if qualified not in code.files:
                    self.errors.append(f"対応表 {lineno} 行目: ファイルが見つかりません: {qualified}")
            elif qualified not in code.symbols:
                if file_part in code.file_only:
                    # 記号を抽出できない言語。ファイルがあれば確認対象外として数える（DS-MD の行は別に要る）
                    self.unverified.append(f"対応表 {lineno} 行目: 言語未対応のため記号の実在は未確認（ファイルは存在）: {qualified}")
                elif file_part not in code.files:
                    self.errors.append(f"対応表 {lineno} 行目: ファイルが見つかりません: {qualified}")
                else:
                    self.errors.append(f"対応表 {lineno} 行目: コードに存在しない修飾名です（改名・削除の見落とし）: {qualified}")

        for rel in sorted(code.files):
            if rel not in mapped_names:
                self.warnings.append(f"対応表に未登録のファイル: {rel}（DS-MD の行を追加するか、設計書に設計要素を追加する）")
        for qualified, kind in sorted(code.symbols.items()):
            if qualified in mapped_names:
                continue
            rel, tail = qualified.split('::', 1)
            # Python 以外で近似生成した Class.method の組み合わせは、同名の function が登録済みなら未登録扱いにしない
            if kind == 'method' and '.' in tail:
                plain = f"{rel}::{tail.split('.', 1)[1]}"
                if plain in mapped_names:
                    continue
                if not rel.endswith('.py') and not rel.endswith('.go'):
                    # TS/Java は全クラスとの組み合わせを生成しているため警告対象にしない
                    continue
            if self.granularity == 'class' and kind != 'class':
                # クラス粒度: メソッドはクラスが、トップレベル関数はファイルが登録済みなら未登録と扱わない
                owner = f"{rel}::{tail.split('.', 1)[0]}" if kind == 'method' and '.' in tail else rel
                if owner in mapped_names:
                    continue
            kind_label = {'class': 'クラス', 'function': '関数', 'method': 'メソッド'}[kind]
            self.warnings.append(f"対応表に未登録の{kind_label}: {qualified}")

        for ds_id in sorted(design_ids):
            if ds_id.startswith(('DS-MD-', 'DS-CL-', 'DS-FN-')) and ds_id not in mapped_ids:
                self.warnings.append(f"詳細設計書の設計要素が対応表に未登録（未実装の可能性）: {ds_id}")
        for ds_id in sorted(design.code_realized):
            if not ds_id.startswith(('DS-MD-', 'DS-CL-', 'DS-FN-')) and ds_id not in mapped_ids:
                self.warnings.append(f"詳細設計書でファイルに置くとした設計要素（第 7 章の「実現する設計 ID」）が対応表に未登録"
                                     f"（未実装の可能性）: {ds_id}")
        tests_present = any((self.root / d).exists() for d in self.test_dirs)
        if tests_present:
            for ds_id in sorted(design.e2e_scenarios):
                if ds_id not in mapped_ids:
                    self.warnings.append(f"詳細設計書 8-2 の E2E シナリオが対応表に未登録（テストが無い可能性）: {ds_id}")

        self.summary = {
            'deleted_ids': len(deleted_ids),
            'design_ids': len(design_ids),
            'rows': len(rows),
            'files': len(code.files),
            'file_only': len(code.file_only),
            'symbols': len(code.symbols),
            'test_files': len(code.test_files),
        }

    def report(self, strict: bool) -> int:
        print("Trace Map Checker\n" + "=" * 50)
        print(f"詳細設計書: {self.design}")
        if self.active_change is not None:
            deleted = self.summary['deleted_ids'] if hasattr(self, 'summary') else 0
            print(f"進行中の変更: {self.active_change}（正本に重ねて判定。削除する設計 ID {deleted} 件）")
        print(f"対応表: {self.trace_map}")
        print(f"ソース: {', '.join(str(s) for s in self.source_dirs)}")
        if self.test_dirs:
            print(f"テスト: {', '.join(str(t) for t in self.test_dirs)}（粒度: {self.granularity}）")
        else:
            print(f"粒度: {self.granularity}")
        if hasattr(self, 'summary'):
            s = self.summary
            print(f"検出: 設計ID {s['design_ids']} 件 / 対応表 {s['rows']} 行 / ファイル {s['files']} 件"
                  f"（うち記号未対応の言語 {s['file_only']} 件）/ クラス・関数 {s['symbols']} 件 / テストファイル {s['test_files']} 件")
        print("\n結果レポート\n" + "-" * 50)
        if self.errors:
            print(f"✗ エラー {len(self.errors)} 件（直してからコミットすること）")
            for e in self.errors:
                print(f"  - {e}")
        if self.warnings:
            print(f"⚠ 警告 {len(self.warnings)} 件（isdd-build の完了条件では 0 件にすること）")
            for w in self.warnings:
                print(f"  - {w}")
        if self.unverified:
            print(f"ℹ 確認対象外 {len(self.unverified)} 件（記号を抽出できない言語。ファイルの存在だけ確認した）")
            for u in self.unverified:
                print(f"  - {u}")
        print("\n検証サマリ\n" + "-" * 50)
        print(f"エラー: {len(self.errors)} 件")
        print(f"警告: {len(self.warnings)} 件")
        if not self.errors and not self.warnings:
            print("✓ 対応表チェックに合格しました")
            return 0
        if not self.errors:
            print("✓ エラーなし（警告あり）")
            return 1 if strict else 0
        print("✗ 対応表チェックに失敗しました")
        return 1


USAGE = ("使用方法: python3 trace_map_checker.py <detail_design.md> <trace_map.md> <source_dir> [<source_dir> ...]"
         " [--strict] [--active-change <ポインタファイル>] [--tests <テストディレクトリ>]... [--granularity function|class]")
GRANULARITIES = ('function', 'class')


def main() -> None:
    args: List[str] = []
    strict = False
    pointer: Optional[Path] = None
    test_dirs: List[Path] = []
    granularity = 'function'
    argv = sys.argv[1:]
    i = 0

    def value_of(name: str) -> str:
        nonlocal i
        a = argv[i]
        if a.startswith(name + '='):
            return a.split('=', 1)[1]
        if i + 1 >= len(argv):
            print(USAGE)
            sys.exit(2)
        i += 1
        return argv[i]

    while i < len(argv):
        a = argv[i]
        if a == '--strict':
            strict = True
        elif a == '--active-change' or a.startswith('--active-change='):
            pointer = Path(value_of('--active-change'))
        elif a == '--tests' or a.startswith('--tests='):
            test_dirs.append(Path(value_of('--tests')))
        elif a == '--granularity' or a.startswith('--granularity='):
            granularity = value_of('--granularity')
            if granularity not in GRANULARITIES:
                print(f"--granularity は {' / '.join(GRANULARITIES)} のどれかにしてください: {granularity}")
                sys.exit(2)
        elif not a.startswith('--'):
            args.append(a)
        i += 1
    if len(args) < 3:
        print(USAGE)
        sys.exit(2)
    root = Path.cwd().resolve()
    checker = TraceMapChecker(Path(args[0]), Path(args[1]), [Path(a) for a in args[2:]], root,
                              resolve_active_change(pointer), test_dirs, granularity)
    checker.run()
    sys.exit(checker.report(strict))


if __name__ == '__main__':
    main()
