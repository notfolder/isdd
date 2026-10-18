"""rq_integrity_checker.py の単体テスト"""

import unittest

from helpers import TempDirMixin, run_script, write

GOOD = """
| RQ-BZ-ID | 業務名 |
|---|---|
| `RQ-BZ-HELLO-CHECK` | 動作確認 |

| RQ-BK-ID | 業務課題 | 対象業務 |
|---|---|---|
| `RQ-BK-SHARED-CHECK-SCRIPT` | 共通の確認手段を用意する | `RQ-BZ-HELLO-CHECK` |

| RQ-ID | 機能名 | 対応業務課題ID |
|---|---|---|
| `RQ-FT-PRINT-HELLO` | 出力 | `RQ-BK-SHARED-CHECK-SCRIPT` |
| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |
"""


class RqIntegrityCheckerTest(TempDirMixin, unittest.TestCase):
    def test_valid_document_passes(self):
        path = write(self.tmp, "req.md", GOOD)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)
        self.assertIn("全てのチェックに合格しました", out)

    def test_requirement_without_bk_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-NF-RESPONSE-1S` | 応答 1 秒 | |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-NF-RESPONSE-1S", out)

    def test_orphan_bk_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-BK-UNUSED-THEME` | 使われない課題 | `RQ-BZ-HELLO-CHECK` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-BK-UNUSED-THEME", out)

    def test_invalid_category_fails(self):
        path = write(self.tmp, "req.md", GOOD + "\n| `RQ-XX-UNKNOWN` | 不明 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n")
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-XX-UNKNOWN", out)

    def test_missing_bz_fails_for_full_document(self):
        text = GOOD.replace("`RQ-BZ-HELLO-CHECK`", "業務")
        path = write(self.tmp, "req.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-BZ", out)

    def test_change_document_does_not_require_bz(self):
        text = """
        | RQ-ID | 区分 | 内容 | 対応業務課題ID |
        |---|---|---|---|
        | `RQ-BK-ADD-TIMESTAMP` | [追加] | 時刻を付ける | |
        | `RQ-FT-PRINT-TIMESTAMP` | [追加] | 時刻付き出力 | `RQ-BK-ADD-TIMESTAMP` |
        """
        path = write(self.tmp, "change.md", text)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertEqual(code, 0, out)

    def test_header_labels_are_not_ids(self):
        path = write(self.tmp, "req.md", GOOD)
        code, out = run_script("rq_integrity_checker.py", [str(path)])
        self.assertNotIn("RQ-BK-ID", out.split("結果")[-1])

    def test_missing_file_reports_reason(self):
        code, out = run_script("rq_integrity_checker.py", [str(self.tmp / "none.md")])
        self.assertEqual(code, 1)
        self.assertIn("見つかりません", out)


if __name__ == "__main__":
    unittest.main()
