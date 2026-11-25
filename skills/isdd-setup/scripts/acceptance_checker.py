#!/usr/bin/env python3
"""
Acceptance Checker Script（受け入れ判定）

目的:
  「要件が実装されたか」を E2E テストの結果で判定する。対応表は「テストがあるか」までしか見ないので、
  JUnit XML の結果を読んで、設計書 8-2 の DS-TS ごとに合格・不合格・未実行・要再実行を判定し、
  要件（RQ-FT・RQ-UI・RQ-EX・RQ-NF・RQ-DT・RQ-OP）ごとの実装済み判定の表を Markdown で出す。

使用方法:
  python3 acceptance_checker.py <requirements.md> <detail_design.md> <trace_map.md>
      --junit <パスかグロブ> [--junit ...] [--strict] [--active-change <ポインタファイル>]
      [--tests <テストディレクトリ>] [--src <ソースディレクトリ>]...

読むもの:
  - 要件定義書 第 7 章: 「検証する要件ID」列（RQ-TS → 検証する RQ-*）
  - 詳細設計書 第 11 章: DS-TS → RQ-TS（または RQ-NF・RQ-DT・RQ-OP へ直接）。11-1 の除外要件も判定の対象
    （設計をまとめても、要件を確かめる義務は残る）
  - 詳細設計書 8-5「テスト以外で確かめる要件」: RQ-NF・RQ-DT・RQ-OP の手動の確認（確認方法・確認結果・確認日）
  - 対応表: DS-TS の行の修飾名（e2e/test_x.py::test_y、または e2e/test_x.py）
  - JUnit XML: testcase の classname・name・結果。testsuite の timestamp
  - --active-change があれば、そのディレクトリの change_requirements.md と change_detail_design.md の
    [追加] の行を重ね、[削除] の行にだけ現れる ID（要件・RQ-TS・DS-TS）を正本から外す（変更で消す要件に
    テストを求めない。[削除] と [追加] の両方の行に現れる ID は対応の差し替えなので外さない）

照合:
  - pytest: classname "e2e.test_x" / "e2e.test_x.TestFoo" → ファイル e2e/test_x.py。name の "[...]" は除く
  - go test: name の "/サブテスト" は除く。classname はパッケージなのでファイルは不明（名前だけで結ぶ）
  - JUnit（Java）: classname の末尾のクラス名とメソッド名で "OrderTest.testCancel" の形に結ぶ
  - jest 系: name がテストの説明文で関数名が無いので、ファイル単位の行（file 属性）でだけ結ぶ
  - テストファイルだけを指す行は、そのファイルの testcase 全部が通れば合格

判定:
  対応表の DS-TS の行（テスト関数かテストファイル）ごとに判定してから、DS-TS にまとめる。
  行:    不合格（failure か error が 1 件以上）/ 未実行（結べる testcase が無い、または skipped が 1 件以上）/
         要再実行（その testcase を出した XML の timestamp が --src・--tests の最新の更新時刻より古い）/ 合格
  DS-TS: 1 行でも不合格なら不合格、次に 1 行でも未実行なら未実行、次に 1 行でも要再実行なら要再実行、全行が合格なら合格
  同じ testcase が複数の XML にあれば、timestamp が新しいほうだけを使う（古い結果に別の実行の結果を足しても、古い結果は古いまま）
  要件:  実装済み（関係する DS-TS が全部合格）/ 不合格（1 件以上不合格）/ 未検証（DS-TS が無い、または実行されていない）
         RQ-NF・RQ-DT・RQ-OP は、テストの経路が無ければ 8-5 の表で「確認済み（手動）」「未確認（手動）」、
         8-5 にも無ければ「検証方法なし」（表に出すが、--strict でも失敗にしない）

終了コード:
  既定では 0（警告だけ）。--strict では、不合格・未実行・要再実行の DS-TS か、未検証・不合格の要件が
  1 件でもあれば 1。「未確認（手動）」「検証方法なし」は表と件数に出すだけで、終了コードを変えない。
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
OPTIONAL_CATEGORIES = ('RQ-NF-', 'RQ-DT-', 'RQ-OP-')  # テストか手動の確認で確かめる。確かめ方が無くても失敗にはしない
MANUAL_HEADING = 'テスト以外で確かめる'
MANUAL_DONE = '確認済み'
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


def _cell(cells: List[str], cols: Dict[str, int], key: str) -> str:
    i = cols.get(key)
    return cells[i].strip() if i is not None and i < len(cells) else ''


def _active_lines(path: Path) -> List[str]:
    """文書の行。[削除] を含む行は読まない（変更文書）。正本には区分が無いので全行"""
    lines = path.read_text(encoding='utf-8').splitlines()
    is_change = any('[追加]' in l or '[削除]' in l for l in lines)
    if not is_change:
        return lines
    return [l for l in lines if '[削除]' not in l]


def _deleted_ids(path: Path, pattern) -> Set[str]:
    """変更文書で削除する ID（[削除] の行にだけ現れ、[追加] の行には現れない ID）。区分の無い正本では空"""
    lines = path.read_text(encoding='utf-8').splitlines()
    if not any('[追加]' in l or '[削除]' in l for l in lines):
        return set()
    deleted: Set[str] = set()
    added: Set[str] = set()
    for l in lines:
        if '[削除]' in l:
            deleted.update(_ids(pattern, l))
        if '[追加]' in l:
            added.update(_ids(pattern, l))
    return deleted - added


class Requirements:
    """要件定義書 第 7 章の「検証する要件ID」列"""

    def __init__(self):
        self.ts_verifies: Dict[str, Set[str]] = defaultdict(set)  # RQ-TS → RQ-*
        self.tested: Set[str] = set()  # RQ-FT・RQ-UI・RQ-EX の全 ID
        self.optional: Set[str] = set()  # RQ-NF・RQ-DT・RQ-OP の全 ID
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
                elif i.startswith(OPTIONAL_CATEGORIES):
                    self.optional.add(i)
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

    def drop(self, ids: Set[str]):
        """進行中の変更で削除する要件・RQ-TS を判定の対象から外す"""
        self.tested -= ids
        self.optional -= ids
        for ts in ids:
            self.ts_verifies.pop(ts, None)
        for ts in self.ts_verifies:
            self.ts_verifies[ts] -= ids


class Design:
    """詳細設計書 第 11 章（DS-TS → RQ）、11-1（除外要件）、8-5（テスト以外で確かめる要件）"""

    def __init__(self):
        self.ts_to_rq: Dict[str, Set[str]] = defaultdict(set)  # DS-TS → RQ-TS / RQ-NF など
        self.excluded: Set[str] = set()
        self.all_ds_ts: Set[str] = set()
        self.manual: Dict[str, Tuple[str, bool]] = {}  # RQ-* → (確認方法, 確認済みか)

    def read(self, path: Path):
        if not path.exists():
            return
        lines = _active_lines(path)
        in_mapping = False
        in_exclusion = False
        in_manual = False
        manual_cols: Optional[Dict[str, int]] = None
        for line in lines:
            heading = re.match(r'^\s*#+\s*(.+)$', line)
            if heading:
                title = heading.group(1)
                in_exclusion = EXCLUSION_HEADING in title
                in_mapping = (MAPPING_HEADING in title) and not in_exclusion
                in_manual = MANUAL_HEADING in title
                manual_cols = None
                continue
            if in_manual and line.strip().startswith('|'):
                cells = _split_cells(line)
                if manual_cols is None:
                    manual_cols = {key: i for i, c in enumerate(cells) for key in ('確認方法', '確認結果', '確認日') if key in c}
                elif not _is_separator(cells):
                    done = MANUAL_DONE in _cell(cells, manual_cols, '確認結果') and _cell(cells, manual_cols, '確認日') not in ('', '―', '-', '—')
                    for r in _ids(RQ_PATTERN, line):
                        self.manual[r] = (_cell(cells, manual_cols, '確認方法'), done)
            ds_ids = [d for d in _ids(DS_PATTERN, line) if d.startswith('DS-TS-')]
            self.all_ds_ts.update(ds_ids)
            if in_exclusion:
                self.excluded.update(_ids(RQ_PATTERN, line))
            elif in_mapping and ds_ids:
                rqs = set(_ids(RQ_PATTERN, line))
                for d in ds_ids:
                    self.ts_to_rq[d] |= rqs


    def drop(self, ds_ids: Set[str], rq_ids: Set[str]):
        """進行中の変更で削除する DS-TS と、削除する RQ（RQ-TS・RQ-NF）への対応を外す"""
        self.all_ds_ts -= ds_ids
        for ds in ds_ids:
            self.ts_to_rq.pop(ds, None)
        for ds in self.ts_to_rq:
            self.ts_to_rq[ds] -= rq_ids
        for r in rq_ids:
            self.manual.pop(r, None)


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
    __slots__ = ('classname', 'name', 'file', 'status', 'base_name', 'class_simple', 'module_path', 'stamp')

    def __init__(self, classname: str, name: str, file_attr: str, status: str, stamp: Optional[datetime] = None):
        self.stamp = stamp  # この testcase を出した XML の時刻
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


def read_junit(paths: List[Path]) -> List[TestCase]:
    """testcase を読む。同じ testcase（classname・name・file が同じ）が複数の XML にあれば、時刻の新しいほうだけを残す"""
    latest: Dict[Tuple[str, str, str], TestCase] = {}
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
        for tc in root.iter('testcase'):
            status = 'pass'
            for child in tc:
                tag = child.tag.split('}')[-1]
                if tag in ('failure', 'error'):
                    status = 'fail'
                    break
                if tag == 'skipped':
                    status = 'skip'
            case = TestCase(tc.get('classname', '') or '', tc.get('name', '') or '', tc.get('file', '') or '', status, stamp)
            key = (case.classname, case.name, case.file)
            old = latest.get(key)
            if old is None or old.stamp is None or stamp >= old.stamp:
                latest[key] = case
    return list(latest.values())


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
            deleted_rq: Set[str] = set()
            if creq.exists():
                req.read(creq)
                deleted_rq = _deleted_ids(creq, RQ_PATTERN)
                req.drop(deleted_rq)
            if cdes.exists():
                design.read(cdes)
                deleted_ds = {d for d in _deleted_ids(cdes, DS_PATTERN) if d.startswith('DS-TS-')}
                design.drop(deleted_ds, deleted_rq)
            if not creq.exists() and not cdes.exists() and (change_dir / 'bug_report.md').exists():
                print(f"進行中の変更: {change_dir}（不具合修正。変更する文書が無いので正本だけで判定）")
            else:
                print(f"進行中の変更: {change_dir}（変更要件定義書・変更設計書の [追加] の行を重ね、[削除] の ID を外して判定）")

    if test_dirs and not any(Path(d).exists() for d in test_dirs):
        print(f"テストディレクトリ（{', '.join(test_dirs)}）が無いので受け入れ判定を省く（E2E の有無は implementation_completeness_checker.py が確かめる）")
        return 0

    xml_paths: List[Path] = []
    for pat in junit_patterns:
        xml_paths.extend(Path(p) for p in sorted(glob.glob(pat, recursive=True)))
    cases = read_junit(xml_paths)
    print(f"結果ファイル: {len(xml_paths)} 件、testcase: {len(cases)} 件")

    stale = False
    code_newest = newest_mtime([Path(d) for d in src_dirs + test_dirs])

    def is_stale(c: TestCase) -> bool:
        # timestamp を秒で丸める実行系があるので、2 秒の猶予を置く
        return bool(c.stamp and code_newest and (code_newest - c.stamp).total_seconds() > 2)

    if req.tested and not req.has_verify_column:
        warnings.append("要件定義書 第 7 章の表に「検証する要件ID」列が無い（要件ごとの判定ができない）")

    # DS-TS ごとの判定
    ts_result: Dict[str, str] = {}
    ts_tests: Dict[str, List[str]] = defaultdict(list)
    skipped_rows: List[str] = []
    for ds in sorted(design.all_ds_ts):
        rows = tmap.ts_rows.get(ds, [])
        if not rows:
            ts_result[ds] = '未実行'
            continue
        # 行（テスト関数かテストファイル）ごとに判定してからまとめる。1 行の合格で、ほかの行の未実行を隠さない
        row_results: List[str] = []
        for q in rows:
            found = match_cases(q, cases)
            ts_tests[ds].append(q)
            if any(c.status == 'fail' for c in found):
                row_results.append('不合格')
            elif not found or any(c.status == 'skip' for c in found):
                row_results.append('未実行')
                if found:
                    skipped_rows.append(q)
            elif any(is_stale(c) for c in found):
                row_results.append('要再実行')
                stale = True
            else:
                row_results.append('合格')
        for verdict in ('不合格', '未実行', '要再実行', '合格'):
            if verdict in row_results:
                ts_result[ds] = verdict
                break

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
    if skipped_rows:
        warnings.append("skipped の testcase がある行は未実行として扱う（skip を外して実行する）: " + ', '.join(sorted(set(skipped_rows))))
    excluded_ts = sorted(r for r in design.excluded if r.startswith('RQ-TS-'))
    if excluded_ts:
        warnings.append("11-1 の除外要件にテスト用利用シナリオがある（シナリオは除外できない。吸収先の設計を確かめる DS-TS に結び直す）: " + ', '.join(excluded_ts))

    # 要件ごとの判定（RQ-TS → DS-TS、RQ-NF → DS-TS 直接）
    rq_to_ts: Dict[str, Set[str]] = defaultdict(set)  # RQ-* → RQ-TS
    for ts, rqs in req.ts_verifies.items():
        for r in rqs:
            rq_to_ts[r].add(ts)
    rqts_to_ds: Dict[str, Set[str]] = defaultdict(set)  # RQ-TS / RQ-NF → DS-TS
    for ds, rqs in design.ts_to_rq.items():
        for r in rqs:
            rqts_to_ds[r].add(ds)
    # 11-1 の除外要件も対象に残す（設計を吸収先にまとめても、要件を確かめる義務は残る）
    targets = set(req.tested) | set(req.optional) | {r for r in rq_to_ts if r.startswith(OPTIONAL_CATEGORIES)} \
        | {r for r in rqts_to_ds if r.startswith(OPTIONAL_CATEGORIES)} | {r for r in design.manual if r.startswith(OPTIONAL_CATEGORIES)}

    rows_out: List[Tuple[str, str, str, str, str]] = []
    rq_result: Dict[str, str] = {}
    for rq in sorted(targets):
        ts_list = sorted(rq_to_ts.get(rq, set()))
        ds_list: Set[str] = set()
        for ts in ts_list:
            ds_list |= rqts_to_ds.get(ts, set())
        ds_list |= rqts_to_ds.get(rq, set())  # RQ-NF・RQ-DT・RQ-OP → DS-TS 直接
        results = [ts_result.get(d, '未実行') for d in sorted(ds_list)]
        manual_note = ''
        if not ts_list and not ds_list and rq.startswith(OPTIONAL_CATEGORIES):
            # テストの経路が無い RQ-NF・RQ-DT・RQ-OP は、8-5 の手動の確認を見る。それも無ければ「検証方法なし」として表に残す
            if rq in design.manual:
                method, done = design.manual[rq]
                verdict = '確認済み（手動）' if done else '未確認（手動）'
                manual_note = f"手動: {method}" if method else '手動'
            else:
                verdict = '検証方法なし'
        elif not results or all(r == '未実行' for r in results):
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
                         ', '.join(f'`{t}`' for t in tests) or manual_note or '―', verdict))

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
    if rq_counts['確認済み（手動）'] or rq_counts['未確認（手動）'] or rq_counts['検証方法なし']:
        print(f"  テスト以外: 確認済み（手動） {rq_counts['確認済み（手動）']} / 未確認（手動） {rq_counts['未確認（手動）']} / 検証方法なし {rq_counts['検証方法なし']}"
              "（RQ-NF・RQ-DT・RQ-OP。終了コードは変えない。未確認と検証方法なしはユーザーに示す）")
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
