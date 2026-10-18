"""rq_ds_link_checker.py の単体テスト"""

import unittest

from helpers import TempDirMixin, run_script, write

REQ = """
| RQ-ID | 内容 | 対応業務課題ID |
|---|---|---|
| `RQ-FT-PRINT-HELLO` | 出力 | `RQ-BK-SHARED-CHECK-SCRIPT` |
| `RQ-TS-VERIFY-OUTPUT` | 出力の確認 | `RQ-BK-SHARED-CHECK-SCRIPT` |
| `RQ-EF-SOFT-SAVING-CHECK` | 工数削減 | `RQ-BK-SHARED-CHECK-SCRIPT` |
| `RQ-BZ-HELLO-CHECK` | 業務 | `RQ-BK-SHARED-CHECK-SCRIPT` |
"""

DESIGN = """
## 11. 要件と設計の対応表

| DS-ID | 対応要件ID |
|---|---|
| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `RQ-FT-PRINT-HELLO` |
| `DS-TS-OUTPUT-E2E-TS-VERIFY-OUTPUT` | `RQ-TS-VERIFY-OUTPUT` |

### 11-1. 除外要件

除外要件は無い。
"""


class RqDsLinkCheckerTest(TempDirMixin, unittest.TestCase):
    def run_checker(self, req: str, design: str):
        r = write(self.tmp, "req.md", req)
        d = write(self.tmp, "design.md", design)
        return run_script("rq_ds_link_checker.py", [str(r), str(d)])

    def test_complete_mapping_passes(self):
        code, out = self.run_checker(REQ, DESIGN)
        self.assertEqual(code, 0, out)

    def test_context_ids_need_no_design(self):
        # RQ-BK・RQ-BZ・RQ-EF は設計 ID の対応を求めない
        code, out = self.run_checker(REQ, DESIGN)
        self.assertNotIn("RQ-EF-SOFT-SAVING-CHECK には", out)
        self.assertEqual(code, 0, out)

    def test_unmapped_requirement_fails(self):
        req = REQ + "| `RQ-NF-RESPONSE-1S` | 応答 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
        code, out = self.run_checker(req, DESIGN)
        self.assertEqual(code, 1, out)
        self.assertIn("RQ-NF-RESPONSE-1S", out)

    def test_unmapped_design_fails(self):
        design = DESIGN + "\n| `DS-OP-ORPHAN-OP-NOTHING` | 何にも対応しない |\n"
        code, out = self.run_checker(REQ, design)
        self.assertEqual(code, 1, out)
        self.assertIn("DS-OP-ORPHAN-OP-NOTHING", out)

    def test_excluded_requirement_is_not_unmapped(self):
        req = REQ + "| `RQ-NF-SINGLE-LINE` | 1 行 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
        design = DESIGN.replace(
            "除外要件は無い。",
            "| RQ-ID | 除外理由 | 吸収先 DS-ID | 承認日 |\n|---|---|---|---|\n"
            "| `RQ-NF-SINGLE-LINE` | 出力関数で実現済み | | 2026-10-18 |",
        )
        code, out = self.run_checker(req, design)
        self.assertEqual(code, 0, out)
        self.assertIn("除外", out)

    def test_exclusion_section_ends_at_next_heading(self):
        req = REQ + "| `RQ-NF-SINGLE-LINE` | 1 行 | `RQ-BK-SHARED-CHECK-SCRIPT` |\n"
        design = DESIGN + "\n## 12. 付録\n\n`RQ-NF-SINGLE-LINE` に触れる文\n"
        code, out = self.run_checker(req, design)
        self.assertEqual(code, 1, out)

    def test_undefined_reference_fails(self):
        design = DESIGN + "| `DS-FN-GHOST-FT-GHOST` | `RQ-FT-GHOST` |\n"
        code, out = self.run_checker(REQ, design)
        self.assertEqual(code, 1, out)
        self.assertIn("未定義参照", out)
        self.assertIn("RQ-FT-GHOST", out)

    def test_deleted_lines_are_ignored(self):
        design = DESIGN + "| `DS-FN-OLD-FT-OLD` | `RQ-FT-OLD` | [削除] |\n"
        code, out = self.run_checker(REQ, design)
        self.assertEqual(code, 0, out)

    def test_missing_file_reports_reason(self):
        r = write(self.tmp, "req.md", REQ)
        code, out = run_script("rq_ds_link_checker.py", [str(r), str(self.tmp / "none.md")])
        self.assertEqual(code, 1)
        self.assertIn("見つかりません", out)


if __name__ == "__main__":
    unittest.main()
