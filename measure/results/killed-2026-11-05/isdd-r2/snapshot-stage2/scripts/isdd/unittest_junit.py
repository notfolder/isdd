#!/usr/bin/env python3
"""
unittest を実行して JUnit XML を書く（標準ライブラリだけ）。pytest が無い Python プロジェクトの E2E 用。

使用方法:
  python3 scripts/isdd/unittest_junit.py -s e2e -o e2e/results/e2e.xml [-p "test*.py"] [-t <トップレベル>]

  -s: テストを探すディレクトリ（既定 e2e）。-p: ファイル名のパターン（既定 test*.py）。
  -t: インポートの基準ディレクトリ（既定は -s と同じ。pytest と同じ "e2e.test_x" の classname にしたいときは "." を渡す）。
  -o: 出力先の JUnit XML（既定 <テストディレクトリ>/results/e2e.xml）。親ディレクトリは作る。

testcase の classname はモジュール名とクラス名（例: "e2e.test_order.OrderTest"）、name はテストメソッド名。
終了コードは、全件通過なら 0、失敗・エラーがあれば 1（acceptance_checker.py は XML を読むので終了コードに依存しない）。
"""

import argparse
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr


class JUnitResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []  # (classname, name, status, message, elapsed)
        self._start = {}

    def startTest(self, test):
        self._start[test] = time.time()
        super().startTest(test)

    def _record(self, test, status, message=""):
        elapsed = time.time() - self._start.get(test, time.time())
        classname = f"{test.__class__.__module__}.{test.__class__.__name__}"
        name = getattr(test, "_testMethodName", str(test))
        self.cases.append((classname, name, status, message, elapsed))

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "failure", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._record(test, "pass")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._record(test, "failure", "unexpected success")


def write_xml(path: Path, cases, elapsed: float, timestamp: str) -> None:
    failures = sum(1 for c in cases if c[2] == "failure")
    errors = sum(1 for c in cases if c[2] == "error")
    skipped = sum(1 for c in cases if c[2] == "skipped")
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             f'<testsuites><testsuite name="unittest" tests="{len(cases)}" failures="{failures}" errors="{errors}" '
             f'skipped="{skipped}" time="{elapsed:.3f}" timestamp={quoteattr(timestamp)}>']
    for classname, name, status, message, sec in cases:
        head = f'<testcase classname={quoteattr(classname)} name={quoteattr(name)} time="{sec:.3f}"'
        if status == "pass":
            lines.append(head + "/>")
        else:
            lines.append(head + f"><{status} message={quoteattr(message.splitlines()[0] if message else status)}>{escape(message)}</{status}></testcase>")
    lines.append("</testsuite></testsuites>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="unittest を実行して JUnit XML を書く")
    parser.add_argument("-s", "--start-dir", default="e2e")
    parser.add_argument("-p", "--pattern", default="test*.py")
    parser.add_argument("-t", "--top-level-dir", default=None)
    parser.add_argument("-o", "--output", default=None)
    args = parser.parse_args()
    out = Path(args.output) if args.output else Path(args.start_dir) / "results" / "e2e.xml"
    suite = unittest.defaultTestLoader.discover(args.start_dir, pattern=args.pattern, top_level_dir=args.top_level_dir)
    timestamp = datetime.now().isoformat()
    started = time.time()
    runner = unittest.TextTestRunner(resultclass=JUnitResult, verbosity=1)
    result = runner.run(suite)
    write_xml(out, result.cases, time.time() - started, timestamp)
    print(f"JUnit XML: {out}（{len(result.cases)} 件）")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
