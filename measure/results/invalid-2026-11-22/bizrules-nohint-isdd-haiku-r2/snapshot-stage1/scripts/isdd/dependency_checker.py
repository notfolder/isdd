#!/usr/bin/env python3
"""
Dependency Checker Script

目的:
  詳細設計書の第 7 章「依存の規則」を書き写した scripts/isdd/dependencies.json に従って、
  ソースコードの import（依存の向き）が設計どおりかを確かめる。
  対応表（trace_map_checker.py）は「設計要素がコードにあるか」を見るが、設計の構造（層の越境、
  連携ライブラリを通さない外部呼び出し、ラッパーへの業務ロジックの混入）は見ない。その穴を埋める。

使用方法:
  python3 dependency_checker.py <dependencies.json> <source_dir> [<source_dir> ...]

規則ファイル（dependencies.json）の形:
  {
    "rules": [
      {"from": "src", "deny": ["external/crm/src", "requests"], "reason": "外部 API は連携ライブラリを通して呼ぶ"},
      {"from": "external/crm/src", "deny": ["src"], "reason": "連携ライブラリに業務ロジックを入れない"},
      {"from": "src/ui", "allow": ["src/service"], "reason": "画面層は業務層だけに依存する"}
    ]
  }
  - from:  規則を当てるディレクトリ（プロジェクトルートからの相対パス）。配下のファイルすべてに当てる
  - deny:  依存してはいけない先。プロジェクト内のディレクトリかファイル（/ を含む）、または外部モジュール名
           （python の requests、npm の axios、Go の github.com/... など。先頭の一致で判定する）
  - allow: 依存してよいプロジェクト内のディレクトリ。これを書くと、from 自身と allow 以外のプロジェクト内への
           依存はすべて違反になる。外部モジュールは allow の対象外（deny でだけ制限する）
  - reason: 違反の表示に添える理由（省略可）
  規則が空（"rules": []）なら何も確かめず、合格として終わる。

判定:
  違反があれば終了コード 1。規則が無い、または違反が無ければ 0。
  import を読める言語: Python（ast）、TypeScript / JavaScript、Java、Go（正規表現）。それ以外の言語は確認対象外として数える。
  プロジェクト内への依存は、import をファイルパスに解決して判定する（解決できない import は外部モジュールとみなす）。
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SKIP_DIRS = {'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', '.git', '.mypy_cache', '.pytest_cache'}
PY_EXTS = ('.py',)
TS_EXTS = ('.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts')
TS_INDEX_CANDIDATES = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '/index.ts', '/index.tsx', '/index.js', '/index.jsx']
TS_IMPORT_PATTERN = re.compile(
    r"""(?<![\w$.])(?:import|export)\s+(?:[^'"]*?\s+from\s+)?['"]([^'"]+)['"]"""
    r"""|require\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|import\(\s*['"]([^'"]+)['"]\s*\)""",
    re.MULTILINE,
)
JAVA_IMPORT_PATTERN = re.compile(r'^\s*import\s+(?:static\s+)?([\w.]+)(?:\.\*)?\s*;', re.MULTILINE)
GO_IMPORT_BLOCK = re.compile(r'^import\s*\((.*?)\)', re.MULTILINE | re.DOTALL)
GO_IMPORT_SINGLE = re.compile(r'^import\s+(?:\w+\s+)?"([^"]+)"', re.MULTILINE)
GO_IMPORT_IN_BLOCK = re.compile(r'(?:^|\s)(?:\w+\s+)?"([^"]+)"')
TEST_FILE_PATTERNS = [
    re.compile(r'^test_.*\.py$'), re.compile(r'.*_test\.py$'), re.compile(r'^conftest\.py$'),
    re.compile(r'.*\.spec\.[jt]sx?$'), re.compile(r'.*\.test\.[jt]sx?$'), re.compile(r'.*_test\.go$'),
    re.compile(r'.*Test\.java$'),
]


class Dependency:
    """1 つの import。project_path はプロジェクト内に解決できたときだけ入る"""

    def __init__(self, raw: str, lineno: int, project_path: Optional[str]):
        self.raw = raw
        self.lineno = lineno
        self.project_path = project_path

    @property
    def is_project(self) -> bool:
        return self.project_path is not None


def _is_test_file(path: Path) -> bool:
    return any(p.match(path.name) for p in TEST_FILE_PATTERNS)


def _norm(p: str) -> str:
    return p.strip().strip('/').replace('\\', '/')


def _under(path: str, prefix: str) -> bool:
    """path が prefix（ディレクトリまたはファイル）と同じか、その配下か"""
    path, prefix = _norm(path), _norm(prefix)
    return path == prefix or path.startswith(prefix + '/')


class Resolver:
    """import をプロジェクト内のファイルパスに解決する"""

    def __init__(self, root: Path, source_dirs: List[Path]):
        self.root = root
        self.roots: List[Path] = []
        for d in source_dirs:
            d = (root / d).resolve() if not d.is_absolute() else d
            if d.is_file():
                d = d.parent
            if d.exists() and d not in self.roots:
                self.roots.append(d)
                # src/ 直下をパッケージの根として import するプロジェクトのために、親も候補に入れる
                if d.parent not in self.roots and d.parent != root:
                    self.roots.append(d.parent)
        if root not in self.roots:
            self.roots.append(root)
        self.go_module = self._read_go_module()

    def _read_go_module(self) -> Optional[str]:
        gomod = self.root / 'go.mod'
        if not gomod.exists():
            return None
        m = re.search(r'^module\s+(\S+)', gomod.read_text(encoding='utf-8', errors='replace'), re.MULTILINE)
        return m.group(1) if m else None

    def _rel(self, path: Path) -> Optional[str]:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return None

    def _find(self, dotted: str, exts: Tuple[str, ...]) -> Optional[str]:
        """a.b.c を各ルートから a/b/c.<ext> または a/b/c/ として探す"""
        parts = dotted.split('.')
        for base in self.roots:
            cand_dir = base.joinpath(*parts)
            if cand_dir.is_dir():
                return self._rel(cand_dir)
            for ext in exts:
                cand = base.joinpath(*parts[:-1], parts[-1] + ext)
                if cand.is_file():
                    return self._rel(cand)
        return None

    def python(self, file: Path, node: ast.AST) -> List[Tuple[str, Optional[str]]]:
        out: List[Tuple[str, Optional[str]]] = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, self._find(alias.name, PY_EXTS)))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                base = file.parent
                for _ in range(node.level - 1):
                    base = base.parent
                mod = node.module or ''
                target = base.joinpath(*mod.split('.')) if mod else base
                resolved = None
                if target.is_dir():
                    resolved = self._rel(target)
                elif target.with_suffix('.py').is_file():
                    resolved = self._rel(target.with_suffix('.py'))
                raw = '.' * node.level + mod
                if resolved is None and target.is_dir() is False:
                    # from . import x の x がモジュールのこともある
                    for alias in node.names:
                        sub = target / (alias.name + '.py')
                        if sub.is_file():
                            out.append((raw + '.' + alias.name, self._rel(sub)))
                    if out:
                        return out
                out.append((raw, resolved))
            else:
                mod = node.module or ''
                resolved = self._find(mod, PY_EXTS) if mod else None
                if resolved is not None and (self.root / resolved).is_dir():
                    # from pkg import mod の mod がモジュールのこともある
                    for alias in node.names:
                        sub = self._find(mod + '.' + alias.name, PY_EXTS)
                        out.append((mod + '.' + alias.name, sub or resolved))
                else:
                    out.append((mod, resolved))
        return out

    def ts(self, file: Path, spec: str) -> Optional[str]:
        if not spec.startswith('.'):
            return None
        target = (file.parent / spec).resolve()
        if target.is_file():
            return self._rel(target)
        for suffix in TS_INDEX_CANDIDATES:
            cand = Path(str(target) + suffix)
            if cand.is_file():
                return self._rel(cand)
        if target.is_dir():
            return self._rel(target)
        return None

    def java(self, dotted: str) -> Optional[str]:
        return self._find(dotted, ('.java', '.kt'))

    def go(self, spec: str) -> Optional[str]:
        if self.go_module and (spec == self.go_module or spec.startswith(self.go_module + '/')):
            rel = spec[len(self.go_module):].strip('/')
            target = self.root / rel if rel else self.root
            if target.is_dir():
                return self._rel(target)
        return None


def extract_dependencies(file: Path, rel: str, content: str, resolver: Resolver) -> Optional[List[Dependency]]:
    """ファイルの import を返す。読めない言語なら None"""
    ext = file.suffix.lower()
    deps: List[Dependency] = []
    if ext in PY_EXTS:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return deps
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for raw, resolved in resolver.python(file, node):
                    deps.append(Dependency(raw, getattr(node, 'lineno', 0), resolved))
        return deps
    if ext in TS_EXTS:
        for m in TS_IMPORT_PATTERN.finditer(content):
            spec = next((g for g in m.groups() if g), None)
            if not spec:
                continue
            lineno = content.count('\n', 0, m.start()) + 1
            deps.append(Dependency(spec, lineno, resolver.ts(file, spec)))
        return deps
    if ext == '.java':
        for m in JAVA_IMPORT_PATTERN.finditer(content):
            lineno = content.count('\n', 0, m.start()) + 1
            deps.append(Dependency(m.group(1), lineno, resolver.java(m.group(1))))
        return deps
    if ext == '.go':
        specs: List[Tuple[str, int]] = []
        for m in GO_IMPORT_SINGLE.finditer(content):
            specs.append((m.group(1), content.count('\n', 0, m.start()) + 1))
        for block in GO_IMPORT_BLOCK.finditer(content):
            base_line = content.count('\n', 0, block.start()) + 1
            for m in GO_IMPORT_IN_BLOCK.finditer(block.group(1)):
                specs.append((m.group(1), base_line + block.group(1).count('\n', 0, m.start())))
        for spec, lineno in specs:
            deps.append(Dependency(spec, lineno, resolver.go(spec)))
        return deps
    return None


def _module_matches(raw: str, entry: str) -> bool:
    """外部モジュール名の一致（requests / requests.adapters / @scope/pkg / github.com/x/y/z）"""
    raw, entry = raw.strip(), entry.strip()
    return raw == entry or raw.startswith(entry + '.') or raw.startswith(entry + '/')


def check(root: Path, rules: List[dict], source_dirs: List[Path]) -> Tuple[List[str], int, int]:
    """(違反の一覧, 確かめたファイル数, 読めない言語のファイル数) を返す"""
    resolver = Resolver(root, source_dirs)
    violations: List[str] = []
    checked = 0
    unverified = 0
    seen: Set[Path] = set()
    for src in source_dirs:
        base = (root / src).resolve() if not src.is_absolute() else src
        if not base.exists():
            continue
        for path in ([base] if base.is_file() else sorted(base.rglob('*'))):
            if path.is_dir() or path in seen or any(part in SKIP_DIRS for part in path.parts) or _is_test_file(path):
                continue
            seen.add(path)
            try:
                rel = path.resolve().relative_to(root).as_posix()
            except ValueError:
                continue
            applicable = [r for r in rules if _under(rel, str(r.get('from', '')))]
            if not applicable:
                continue
            try:
                content = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            deps = extract_dependencies(path, rel, content, resolver)
            if deps is None:
                unverified += 1
                continue
            checked += 1
            for rule in applicable:
                src_dir = _norm(str(rule.get('from', '')))
                reason = rule.get('reason') or ''
                tag = f"（規則: {reason}）" if reason else ''
                denies = [str(d) for d in rule.get('deny', []) or []]
                allows = [str(a) for a in rule.get('allow', []) or []]
                for dep in deps:
                    for entry in denies:
                        hit = (dep.is_project and _under(dep.project_path or '', entry)) or \
                              (not dep.is_project and _module_matches(dep.raw, entry))
                        if hit:
                            target = dep.project_path if dep.is_project else dep.raw
                            violations.append(f"{rel}:{dep.lineno} → {target} は {src_dir} から依存してはいけない先です{tag}")
                            break
                    if allows and dep.is_project:
                        target = dep.project_path or ''
                        if _under(target, src_dir) or any(_under(target, a) for a in allows):
                            continue
                        violations.append(f"{rel}:{dep.lineno} → {target} は {src_dir} から依存してよい先"
                                          f"（{src_dir}, {', '.join(_norm(a) for a in allows)}）にありません{tag}")
    return violations, checked, unverified


def main() -> None:
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(argv) < 2:
        print("使用方法: python3 dependency_checker.py <dependencies.json> <source> [<source> ...]（source はディレクトリかファイル）")
        sys.exit(2)
    rules_path = Path(argv[0])
    source_dirs = [Path(a) for a in argv[1:]]
    root = Path.cwd().resolve()
    print("Dependency Checker\n" + "=" * 50)
    print(f"規則: {rules_path}")
    print(f"ソース: {', '.join(str(s) for s in source_dirs)}")
    if not rules_path.exists():
        print("規則ファイルが無いため、依存の検査は行わない（isdd-setup を実行すると雛形ができる）")
        sys.exit(0)
    try:
        data = json.loads(rules_path.read_text(encoding='utf-8'))
    except (ValueError, OSError) as e:
        print(f"✗ 規則ファイルを読めません: {e}")
        sys.exit(1)
    rules = data.get('rules') if isinstance(data, dict) else None
    if not isinstance(rules, list):
        print('✗ 規則ファイルに "rules" の配列がありません')
        sys.exit(1)
    if not rules:
        print("依存の規則は無い（詳細設計書 第 7 章に依存の規則があれば dependencies.json に書き写す）")
        print("✓ 依存チェックに合格しました（規則なし）")
        sys.exit(0)
    violations, checked, unverified = check(root, rules, source_dirs)
    print(f"規則 {len(rules)} 件 / 確かめたファイル {checked} 件 / import を読めない言語のファイル {unverified} 件")
    print("\n結果レポート\n" + "-" * 50)
    if violations:
        print(f"✗ 違反 {len(violations)} 件（設計書第 7 章の依存の規則に反する。コードを直すか、設計を見直して規則を更新する）")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)
    print("✓ 依存チェックに合格しました")
    sys.exit(0)


if __name__ == '__main__':
    main()
