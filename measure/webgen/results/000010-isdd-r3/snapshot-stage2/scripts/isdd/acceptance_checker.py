#!/usr/bin/env python3
"""
Acceptance Checker Script（受け入れ判定）

目的:
  「要件が実装されたか」を E2E テストの結果で判定する。対応表は「テストがあるか」までしか見ないので、
  JUnit XML の結果を読んで、設計書 8-2 の DS-TS ごとに合格・不合格・未実行・要再実行を判定し、
  要件（RQ-FT・RQ-UI・RQ-EX と、検証対象の RQ-NF）ごとの実装済み判定の表を Markdown で出す。

使用方法:
  python3 acceptance_checker.py <requirements.md> <detail_design.md> <trace_map.md>
      --junit <パスかグロブ> [--junit ...] [--strict] [--active-change <ポインタファイル>]
      [--tests <テストディレクトリ>] [--src <ソースディレクトリ>]...

読むもの:
  - 要件定義書 第 7 章: 「検証する要件ID」列（RQ-TS → 検証する RQ-*）
  - 詳細設計書 第 11 章: DS-TS → RQ-TS（または RQ-NF へ直接）。11-1 の除外要件は対象外
  - 対応表: DS-TS の行の修飾名（e2e/test_x.py::test_y、または e2e/test_x.py）
  - JUnit XML: testcase の classname・name・結果。testsuite の timestamp
  - --active-change があれば、そのディレクトリの change_requirements.md と change_detail_design.md の
    [追加] の行を重ねる（[削除] の行は読まない）

照合:
  - pytest: classname "e2e.test_x" / "e2e.test_x.TestFoo" → ファイル e2e/test_x.py。name の "[...]" は除く
  - go test: name の "/サブテスト" は除く。classname はパッケージなのでファイルは不明（名前だけで結ぶ）
  - JUnit（Java）: classname の末尾のクラス名とメソッド名で "OrderTest.testCancel" の形に結ぶ
  - jest 系: name がテストの説明文で関数名が無いので、ファイル単位の行（file 属性）でだけ結ぶ
  - テストファイルだけを指す行は、そのファイルの testcase 全部が通れば合格

判定:
  DS-TS: 合格 / 不合格（failure か error が 1 件以上）/ 未実行（結べる testcase が無い、または skipped だけ）/
         要再実行（XML の timestamp が --src・--tests の最新の更新時刻より古い）
  要件:  実装済み（関係する DS-TS が全部合格）/ 不合格（1 件以上不合格）/ 未検証（DS-TS が無い、または実行されていない）

終了コード:
  既定では 0（警告だけ）。--strict では、不合格・未実行・要再実行の DS-TS か、未検証・不合格の要件が
  1 件でもあれば 1。
"""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

RQ_PATTERN = re.compile(r'\bRQ(?:-[A-Z0-9][A-Z0-9_]*)+')
DS_PATTERN = re.compile(r'\bDS(?:-[A-Z0-9][A-Z0-9_]*)+')
HEADER_LABEL_PATTERN = re.compile(r'^(?:RQ|DS)(?:-[A-Z0-9]+)*-ID$')
VERIFY_COLUMN_PATTERN = re.compile(r'検証する要件\s*ID')
MAPPING_HEADING = '要件と設計の対応表'
EXCLUSION_HEADING = '除外要件'
TESTED_CATEGORIES = ('RQ-FT-', 'RQ-UI-', 'RQ-EX-')
QUALIFIED_RE = re.compile(r'`?([^`|]+?)`?\s*$')


def _ids(pattern, text: str) -> List[str]:
    return [m for m in pattern.findall(text) if not HEADER_LABEL_PATTERN.match(m) and len(m.split('-')) >= 3]


def _split_cells(line: str) -> List[str]:
    body = line.strip()
    if body.startswith('|'):
        body = body[1:]
    if body.endswith('|'):
        body = body[:-1]
    return [c.strip() for c in body.split('|')]


def _is_separator(cells: List[str]) -> bool:
    return all(set(c) <= set('-: ') for c in cells)


def _active_lines(path: Path) -> List[str]:
    """文書の行。[削除] を含む行は読まない（変更文書）。正本には区分が無いので全行"""
    lines = path.read_text(encoding='utf-8').splitlines()
    is_change = any('[追加]' in l or '[削除]' in l for l in lines)
    if not is_change:
        return lines
    return [l for l in lines if '[削除]' not in l]


class Requirements:
    """要件定義書 第 7 章の「検証する要件ID」列"""

    def __init__(self):
        self.ts_verifies: Dict[str, Set[str]] = defaultdict(set)  # RQ-TS → RQ-*
        self.tested: Set[str] = set()  # RQ-FT・RQ-UI・RQ-EX の全 ID
        self.has_verify_column = False

    def read(self, path: Path):
        if not path.exists():
            return
        lines = _active_lines(path)
        verify_col: Optional[int] = None
        for line in lines:
            for i in _ids(RQ_PATTERN, line):
                if i.startswith(TESTED_CATEGORIES):
                    self.tested.add(i)
            stripped = line.strip()
            if not stripped.startswith('|'):
                verify_col = None
                continue
            cells = _split_cells(stripped)
            if verify_col is None:
                for i, cell in enumerate(cells):
                    if VERIFY_COLUMN_PATTERN.search(cell):
                        verify_col = i
                        self.has_verify_column = True
                        break
                continue
            if _is_separator(cells) or verify_col >= len(cells):
                continue
            own = _ids(RQ_PATTERN, cells[0])
            if own and own[0].startswith('RQ-TS-'):
                self.ts_verifies[own[0]] |= set(_ids(RQ_PATTERN, cells[verify_col]))


class Design:
    """詳細設計書 第 11 章（DS-TS → RQ）と 11-1（除外要件）"""

    def __init__(self):
        self.ts_to_rq: Dict[str, Set[str]] = defaultdict(set)  # DS-TS → RQ-TS / RQ-NF など
        self.excluded: Set[str] = set()
        self.all_ds_ts: Set[str] = set()

    def read(self, path: Path):
        if not path.exists():
            return
        lines = _active_lines(path)
        in_mapping = False
        in_exclusion = False
        for line in lines:
            heading = re.match(r'^\s*#+\s*(.+)$', line)
            if heading:
                title = heading.group(1)
                in_exclusion = EXCLUSION_HEADING in title
                in_mapping = (MAPPING_HEADING in title) and not in_exclusion
                continue
            ds_ids = [d for d in _ids(DS_PATTERN, line) if d.startswith('DS-TS-')]
            self.all_ds_ts.update(ds_ids)
            if in_exclusion:
                self.excluded.update(_ids(RQ_PATTERN, line))
            elif in_mapping and ds_ids:
                rqs = set(_ids(RQ_PATTERN, line))
                for d in ds_ids:
                    self.ts_to_rq[d] |= rqs


class TraceMap:
    """対応表の DS-TS 行"""

    def __init__(self):
        self.ts_rows: Dict[str, List[str]] = defaultdict(list)  # DS-TS → 修飾名

    def read(self, path: Path):
        if not path.exists():
            return
        for line in path.read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped.startswith('|'):
                continue
            cells = _split_cells(stripped)
            if len(cells) < 2 or _is_separator(cells):
                continue
            ds = _ids(DS_PATTERN, cells[0])
            if not ds or not ds[0].startswith('DS-TS-'):
                continue
            qualified = cells[1].strip('`').strip()
            if qualified:
                self.ts_rows[ds[0]].append(qualified)


class TestCase:
    __slots__ = ('classname', 'name', 'file', 'status', 'base_name', 'class_simple', 'module_path')

    def __init__(self, classname: str, name: str, file_attr: str, status: str):
        self.classname = classname
        self.name = name
        self.file = file_attr.replace('\\', '/') if file_attr else ''
        self.status = status  # pass / fail / skip
        # pytest "[param]"、go "/subtest" を除いた名前
        base = re.split(r'[\[/]', name, maxsplit=1)[0].strip()
        self.base_name = base
        # pytest の classname "e2e.test_x.TestFoo" / Java "com.example.OrderTest"
        # go test の classname はパッケージのパス（"example.com/app/e2e"）なのでファイルもクラスも不明
        if '/' in classname:
            parts = []
        else:
            parts = classname.split('.') if classname else []
        self.class_simple = parts[-1] if parts else ''
        self.module_path = '/'.join(parts)  # "e2e/test_x/TestFoo" → ファイル候補の前方一致に使う

    def matches_file(self, rel_file: str) -> bool:
        """testcase がそのテストファイルのものか（ファイルが分かる形式のときだけ真）"""
        rel = rel_file.replace('\\', '/')
        if self.file:
            return self.file == rel or self.file.endswith('/' + rel) or rel.endswith('/' + self.file)
        if not self.module_path:
            return False
        stem = re.sub(r'\.[A-Za-z0-9]+$', '', rel)  # "e2e/test_x.py" → "e2e/test_x"
        # classname "e2e.test_x.TestFoo"（pytest）や "test_x.TestFoo"（unittest discover -s e2e）の
        # 先頭から何個かをつないだものが、ファイルのパス（拡張子なし）に一致するか末尾一致すれば同じファイル
        parts = self.module_path.split('/')
        for n in range(len(parts), 0, -1):
            prefix = '/'.join(parts[:n])
            if stem == prefix or stem.endswith('/' + prefix):
                return True
        return False

    def file_known(self) -> bool:
        return bool(self.file) or bool(self.module_path)


def read_junit(paths: List[Path]) -> Tuple[List[TestCase], Optional[datetime]]:
    cases: List[TestCase] = []
    newest: Optional[datetime] = None
    for path in paths:
        try:
            tree = ET.parse(str(path))
        except ET.ParseError as e:
            print(f"警告: JUnit XML を読めません: {path}: {e}")
            continue
        root = tree.getroot()
        suites = [root] if root.tag == 'testsuite' else list(root.iter('testsuite'))
        stamp = None
        for suite in suites:
            ts = suite.get('timestamp')
            if ts:
                stamp = _parse_timestamp(ts) or stamp
        if stamp is None:
            stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if newest is None or stamp > newest:
            newest = stamp
        for tc in root.iter('testcase'):
            status = 'pass'
            for child in tc:
                tag = child.tag.split('}')[-1]
                if tag in ('failure', 'error'):
                    status = 'fail'
                    break
                if tag == 'skipped':
                    status = 'skip'
            cases.append(TestCase(tc.get('classname', '') or '', tc.get('name', '') or '', tc.get('file', '') or '', status))
    return cases, newest


def _parse_timestamp(text: str) -> Optional[datetime]:
    text = text.strip()
    if text.endswith('Z'):
        text = text[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.astimezone()  # ローカル時刻とみなす
    return dt


def newest_mtime(dirs: List[Path]) -> Optional[datetime]:
    newest = None
    for d in dirs:
        if not d.exists():
            continue
        if d.is_file():
            try:
                m = datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc)
                if newest is None or m > newest:
                    newest = m
            except OSError:
                pass
            continue
        for root, subdirs, files in os.walk(d):
            subdirs[:] = [s for s in subdirs if s not in ('results', '__pycache__', 'node_modules', '.git')]
            for f in files:
                p = Path(root) / f
                try:
                    m = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                except OSError:
                    continue
                if newest is None or m > newest:
                    newest = m
    return newest


def match_cases(qualified: str, cases: List[TestCase]) -> List[TestCase]:
    """対応表の修飾名に結べる testcase"""
    if '::' not in qualified:
        return [c for c in cases if c.matches_file(qualified)]
    rel, tail = qualified.split('::', 1)
    if '.' in tail:
        cls, name = tail.split('.', 1)
    else:
        cls, name = '', tail
    out = []
    for c in cases:
        if c.base_name != name:
            continue
        if cls and c.class_simple and c.class_simple != cls:
            continue
        if c.file_known() and not c.matches_file(rel) and not (cls and c.class_simple == cls):
            continue
        out.append(c)
    return out


def main() -> int:
    args = sys.argv[1:]
    positional: List[str] = []
    junit_patterns: List[str] = []
    src_dirs: List[str] = []
    test_dirs: List[str] = []
    strict = False
    active_change: Optional[str] = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--strict':
            strict = True
        elif a in ('--junit', '--src', '--tests', '--active-change'):
            if i + 1 >= len(args):
                print(f"エラー: {a} に値がありません")
                return 2
            v = args[i + 1]
            i += 1
            if a == '--junit':
                junit_patterns.append(v)
            elif a == '--src':
                src_dirs.append(v)
            elif a == '--tests':
                test_dirs.append(v)
            else:
                active_change = v
        elif a.startswith('--junit='):
            junit_patterns.append(a.split('=', 1)[1])
        else:
            positional.append(a)
        i += 1
    if len(positional) != 3:
        print(__doc__)
        return 2
    req_path, design_path, map_path = (Path(p) for p in positional)

    print("Acceptance Checker（受け入れ判定）\n" + "=" * 50)
    warnings: List[str] = []
    for p in (req_path, design_path, map_path):
        if not p.exists():
            warnings.append(f"ファイルが見つかりません: {p}")
    req = Requirements()
    req.read(req_path)
    design = Design()
    design.read(design_path)
    tmap = TraceMap()
    tmap.read(map_path)

    # 進行中の変更を重ねる
    if active_change and Path(active_change).exists():
        first = Path(active_change).read_text(encoding='utf-8').splitlines()
        change_dir = Path(first[0].strip()) if first and first[0].strip() else None
        if change_dir:
            creq = change_dir / 'change_requirements.md'
            cdes = change_dir / 'change_detail_design.md'
            if creq.exists():
                req.read(creq)
            if cdes.exists():
                design.read(cdes)
            print(f"進行中の変更: {change_dir}（変更要件定義書・変更設計書の [追加] の行を重ねて判定）")

    if test_dirs and not any(Path(d).exists() for d in test_dirs):
        print(f"テストディレクトリ（{', '.join(test_dirs)}）が無いので受け入れ判定を省く（E2E の有無は implementation_completeness_checker.py が確かめる）")
        return 0

    xml_paths: List[Path] = []
    for pat in junit_patterns:
        xml_paths.extend(Path(p) for p in sorted(glob.glob(pat, recursive=True)))
    cases, newest_result = read_junit(xml_paths)
    print(f"結果ファイル: {len(xml_paths)} 件、testcase: {len(cases)} 件")

    stale = False
    code_newest = newest_mtime([Path(d) for d in src_dirs + test_dirs])
    # timestamp を秒で丸める実行系があるので、2 秒の猶予を置く
    if newest_result and code_newest and (code_newest - newest_result).total_seconds() > 2:
        stale = True

    if req.tested and not req.has_verify_column:
        warnings.append("要件定義書 第 7 章の表に「検証する要件ID」列が無い（要件ごとの判定ができない）")

    # DS-TS ごとの判定
    ts_result: Dict[str, str] = {}
    ts_tests: Dict[str, List[str]] = defaultdict(list)
    for ds in sorted(design.all_ds_ts):
        rows = tmap.ts_rows.get(ds, [])
        if not rows:
            ts_result[ds] = '未実行'
            continue
        matched: List[TestCase] = []
        for q in rows:
            found = match_cases(q, cases)
            matched.extend(found)
            ts_tests[ds].append(q)
        if not matched or all(c.status == 'skip' for c in matched):
            ts_result[ds] = '未実行'
        elif any(c.status == 'fail' for c in matched):
            ts_result[ds] = '不合格'
        elif stale:
            ts_result[ds] = '要再実行'
        else:
            ts_result[ds] = '合格'

    print("\nDS-TS ごとの判定")
    print("-" * 50)
    counts = defaultdict(int)
    for ds, r in ts_result.items():
        counts[r] += 1
        print(f"  {ds}: {r}" + (f"（{', '.join(ts_tests[ds])}）" if ts_tests[ds] else "（対応表に行が無い）"))
    if not ts_result:
        print("  8-2 の DS-TS が無い")
    if not xml_paths and (ts_result or req.tested):
        warnings.append("JUnit XML が 1 つも無い（8-4 の実行コマンドで E2E を回して e2e/results/ に結果を出す）")
    if stale:
        warnings.append("結果ファイルがコードより古い（E2E を回し直す）")

    # 要件ごとの判定（RQ-TS → DS-TS、RQ-NF → DS-TS 直接）
    rq_to_ts: Dict[str, Set[str]] = defaultdict(set)  # RQ-* → RQ-TS
    for ts, rqs in req.ts_verifies.items():
        for r in rqs:
            rq_to_ts[r].add(ts)
    rqts_to_ds: Dict[str, Set[str]] = defaultdict(set)  # RQ-TS / RQ-NF → DS-TS
    for ds, rqs in design.ts_to_rq.items():
        for r in rqs:
            rqts_to_ds[r].add(ds)
    targets = set(req.tested) | {r for r in rq_to_ts if r.startswith('RQ-NF-')} \
        | {r for r in rqts_to_ds if r.startswith('RQ-NF-')}
    targets -= design.excluded

    rows_out: List[Tuple[str, str, str, str, str]] = []
    rq_result: Dict[str, str] = {}
    for rq in sorted(targets):
        ts_list = sorted(rq_to_ts.get(rq, set()))
        ds_list: Set[str] = set()
        for ts in ts_list:
            ds_list |= rqts_to_ds.get(ts, set())
        ds_list |= rqts_to_ds.get(rq, set())  # RQ-NF → DS-TS 直接
        results = [ts_result.get(d, '未実行') for d in sorted(ds_list)]
        if not results or all(r == '未実行' for r in results):
            verdict = '未検証'
        elif any(r == '不合格' for r in results):
            verdict = '不合格'
        elif all(r == '合格' for r in results):
            verdict = '実装済み'
        else:
            verdict = '未検証'  # 一部が未実行・要再実行
        rq_result[rq] = verdict
        tests = []
        for d in sorted(ds_list):
            tests.extend(ts_tests.get(d, []))
        rows_out.append((rq, ', '.join(f'`{t}`' for t in ts_list) or '―',
                         ', '.join(f'`{d}`' for d in sorted(ds_list)) or '―',
                         ', '.join(f'`{t}`' for t in tests) or '―', verdict))

    print("\n### 要件ごとの実装済み判定\n")
    print("| RQ-ID | RQ-TS | DS-TS | テスト | 結果 |")
    print("|---|---|---|---|---|")
    if rows_out:
        for rq, ts, ds, tests, verdict in rows_out:
            print(f"| `{rq}` | {ts} | {ds} | {tests} | {verdict} |")
    else:
        print("| 該当なし | ― | ― | ― | ― |")

    rq_counts = defaultdict(int)
    for v in rq_result.values():
        rq_counts[v] += 1

    print("\n結果レポート")
    print("-" * 50)
    print(f"  DS-TS: 合格 {counts['合格']} / 不合格 {counts['不合格']} / 未実行 {counts['未実行']} / 要再実行 {counts['要再実行']}（全 {len(ts_result)}）")
    print(f"  要件: 実装済み {rq_counts['実装済み']} / 不合格 {rq_counts['不合格']} / 未検証 {rq_counts['未検証']}（全 {len(rq_result)}）")
    for w in warnings:
        print(f"  警告: {w}")

    bad_ts = counts['不合格'] + counts['未実行'] + counts['要再実行']
    bad_rq = rq_counts['不合格'] + rq_counts['未検証']
    if bad_ts == 0 and bad_rq == 0 and not warnings:
        print("✓ 受け入れ判定に合格しました")
        return 0
    if strict:
        print("✗ 受け入れ判定に失敗しました（--strict）")
        return 1
    print("△ 受け入れ判定に未完了があります（--strict では失敗扱い）")
    return 0


if __name__ == '__main__':
    sys.exit(main())
