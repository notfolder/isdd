"""trace_map_checker.py の単体テスト"""

import unittest

from helpers import TempDirMixin, run_script, write

DESIGN = """
| DS-ID | 内容 |
|---|---|
| `DS-MD-HELLO-MODULE-FT-PRINT-HELLO` | モジュール |
| `DS-CL-HELLO-PRINTER-FT-PRINT-HELLO` | クラス |
| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | メソッド |
"""

MAP = """
| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-HELLO-MODULE-FT-PRINT-HELLO` | `src/hello.py` | |
| `DS-CL-HELLO-PRINTER-FT-PRINT-HELLO` | `src/hello.py::HelloPrinter` | |
| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `src/hello.py::HelloPrinter.print_hello` | |
"""

CODE = """
class HelloPrinter:
    def print_hello(self) -> None:
        print("Hello")

    def _internal(self) -> None:
        pass
"""


class TraceMapCheckerTest(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        write(self.tmp, "docs/detail_design.md", DESIGN)
        write(self.tmp, "src/hello.py", CODE)

    def run_checker(self, trace_map: str, strict: bool = True):
        write(self.tmp, "docs/trace_map.md", trace_map)
        args = ["docs/detail_design.md", "docs/trace_map.md", "src"] + (["--strict"] if strict else [])
        return run_script("trace_map_checker.py", args, cwd=self.tmp)

    def test_complete_map_passes_strict(self):
        code, out = self.run_checker(MAP)
        self.assertEqual(code, 0, out)

    def test_renamed_function_is_error(self):
        code, out = self.run_checker(MAP.replace("print_hello`", "print_hi`"), strict=False)
        self.assertEqual(code, 1, out)

    def test_unknown_ds_id_is_error(self):
        bad = MAP + "| `DS-FN-GHOST-FT-GHOST` | `src/hello.py::HelloPrinter.print_hello` | |\n"
        code, out = self.run_checker(bad, strict=False)
        self.assertEqual(code, 1, out)
        self.assertIn("DS-FN-GHOST-FT-GHOST", out)

    def test_unregistered_public_function_is_warning(self):
        write(self.tmp, "src/hello.py", CODE + "\ndef extra() -> None:\n    pass\n")
        code, _ = self.run_checker(MAP, strict=False)
        self.assertEqual(code, 0)
        code, out = self.run_checker(MAP, strict=True)
        self.assertEqual(code, 1, out)
        self.assertIn("extra", out)

    def test_private_and_test_files_are_ignored(self):
        write(self.tmp, "src/test_hello.py", "def test_x():\n    pass\n")
        code, out = self.run_checker(MAP)
        self.assertEqual(code, 0, out)

    def test_ds_md_must_point_to_file(self):
        bad = MAP.replace("| `src/hello.py` |", "| `src/hello.py::HelloPrinter` |")
        code, out = self.run_checker(bad, strict=False)
        self.assertEqual(code, 1, out)

    def test_typescript_arrow_function_is_symbol(self):
        write(self.tmp, "docs/detail_design.md", DESIGN + "| `DS-MD-UTIL-FT-PRINT-HELLO` | ts |\n| `DS-FN-FORMAT-FT-PRINT-HELLO` | ts |\n")
        write(self.tmp, "src/util.ts", "export const format = (s: string): string => s.trim();\n")
        extra = "| `DS-MD-UTIL-FT-PRINT-HELLO` | `src/util.ts` | |\n| `DS-FN-FORMAT-FT-PRINT-HELLO` | `src/util.ts::format` | |\n"
        code, out = self.run_checker(MAP + extra)
        self.assertEqual(code, 0, out)

    def test_file_only_language_is_not_checked_for_symbols(self):
        write(self.tmp, "docs/detail_design.md", DESIGN + "| `DS-MD-SVC-FT-PRINT-HELLO` | cs |\n| `DS-CL-SVC-FT-PRINT-HELLO` | cs |\n")
        write(self.tmp, "src/Svc.cs", "public class Svc { }\n")
        extra = "| `DS-MD-SVC-FT-PRINT-HELLO` | `src/Svc.cs` | |\n| `DS-CL-SVC-FT-PRINT-HELLO` | `src/Svc.cs::Svc` | |\n"
        code, out = self.run_checker(MAP + extra)
        self.assertEqual(code, 0, out)

    def test_missing_map_is_error(self):
        code, out = run_script("trace_map_checker.py", ["docs/detail_design.md", "docs/none.md", "src"], cwd=self.tmp)
        self.assertNotEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
