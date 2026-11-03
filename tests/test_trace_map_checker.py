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

    def run_with_change(self, trace_map: str, change_design: str, strict: bool = True):
        write(self.tmp, ".history/20260508-add-bye/change_detail_design.md", change_design)
        write(self.tmp, "docs/active_change", ".history/20260508-add-bye/\n")
        write(self.tmp, "docs/trace_map.md", trace_map)
        args = ["docs/detail_design.md", "docs/trace_map.md", "src", "--active-change", "docs/active_change"]
        return run_script("trace_map_checker.py", args + (["--strict"] if strict else []), cwd=self.tmp)

    def test_active_change_adds_design_ids(self):
        write(self.tmp, "src/hello.py", CODE + "\n    def print_bye(self) -> None:\n        print(\"Bye\")\n")
        change = "| DS-ID | 区分 |\n|---|---|\n| `DS-FN-PRINT-BYE-FT-PRINT-BYE` | [追加] |\n"
        extra = "| `DS-FN-PRINT-BYE-FT-PRINT-BYE` | `src/hello.py::HelloPrinter.print_bye` | |\n"
        code, out = self.run_checker(MAP + extra, strict=False)
        self.assertEqual(code, 1, out)
        code, out = self.run_with_change(MAP + extra, change)
        self.assertEqual(code, 0, out)
        self.assertIn("進行中の変更", out)

    def test_active_change_deleted_id_left_in_map_is_warning(self):
        change = "| DS-ID | 区分 |\n|---|---|\n| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | [削除] |\n"
        code, out = self.run_with_change(MAP, change, strict=False)
        self.assertEqual(code, 0, out)
        code, out = self.run_with_change(MAP, change, strict=True)
        self.assertEqual(code, 1, out)
        self.assertIn("削除する設計 ID が残っています", out)

    def test_active_change_pointer_to_missing_design_is_error(self):
        write(self.tmp, "docs/active_change", ".history/none/\n")
        write(self.tmp, "docs/trace_map.md", MAP)
        args = ["docs/detail_design.md", "docs/trace_map.md", "src", "--active-change", "docs/active_change"]
        code, out = run_script("trace_map_checker.py", args, cwd=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("change_detail_design.md", out)

    def test_absent_pointer_checks_canonical_only(self):
        write(self.tmp, "docs/trace_map.md", MAP)
        args = ["docs/detail_design.md", "docs/trace_map.md", "src", "--strict", "--active-change", "docs/active_change"]
        code, out = run_script("trace_map_checker.py", args, cwd=self.tmp)
        self.assertEqual(code, 0, out)
        self.assertNotIn("進行中の変更", out)

    def test_missing_map_is_error(self):
        code, out = run_script("trace_map_checker.py", ["docs/detail_design.md", "docs/none.md", "src"], cwd=self.tmp)
        self.assertNotEqual(code, 0, out)

    def test_code_realized_id_on_ds_md_row_must_be_mapped(self):
        # 第 7 章の DS-MD の行に並ぶ DS-IF は、そのファイルで実現する要素なので対応表に要る
        design = DESIGN + "\n## 7. コード設計\n\n| DS-ID | ファイル | 実現する設計 ID |\n|---|---|---|\n" \
            "| `DS-MD-HELLO-MODULE-FT-PRINT-HELLO` | src/hello.py | `DS-IF-CLI-ENTRY` |\n"
        write(self.tmp, "docs/detail_design.md", design)
        code, out = self.run_checker(MAP, strict=True)
        self.assertEqual(code, 1, out)
        self.assertIn("DS-IF-CLI-ENTRY", out)
        write(self.tmp, "src/hello.py", CODE + "\ndef main() -> None:\n    HelloPrinter().print_hello()\n")
        code, out = self.run_checker(MAP + "| `DS-IF-CLI-ENTRY` | `src/hello.py::main` | |\n")
        self.assertEqual(code, 0, out)

    def test_ds_ts_row_points_to_test_function(self):
        design = DESIGN + "\n### 8-2. E2E テストのシナリオ\n\n| DS-ID | 目的 |\n|---|---|\n| `DS-TS-HELLO-E2E` | 出力 |\n"
        write(self.tmp, "docs/detail_design.md", design)
        write(self.tmp, "e2e/test_hello.py", "def test_hello():\n    pass\n")
        write(self.tmp, "docs/trace_map.md", MAP)
        args = ["docs/detail_design.md", "docs/trace_map.md", "src", "--strict", "--tests", "e2e"]
        code, out = run_script("trace_map_checker.py", args, cwd=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("8-2 の E2E シナリオが対応表に未登録", out)
        write(self.tmp, "docs/trace_map.md", MAP + "| `DS-TS-HELLO-E2E` | `e2e/test_hello.py::test_hello` | |\n")
        code, out = run_script("trace_map_checker.py", args, cwd=self.tmp)
        self.assertEqual(code, 0, out)
        # テストディレクトリが無ければ DS-TS の警告は出ない
        write(self.tmp, "docs/trace_map.md", MAP)
        code, out = run_script("trace_map_checker.py", args[:-2] + ["--tests", "none"], cwd=self.tmp)
        self.assertEqual(code, 0, out)

    def test_non_ts_row_must_not_point_to_test_file(self):
        write(self.tmp, "e2e/test_hello.py", "def test_hello():\n    pass\n")
        write(self.tmp, "docs/trace_map.md", MAP + "| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `e2e/test_hello.py::test_hello` | |\n")
        args = ["docs/detail_design.md", "docs/trace_map.md", "src", "--tests", "e2e"]
        code, out = run_script("trace_map_checker.py", args, cwd=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("DS-TS の行にだけ", out)

    def test_class_granularity_accepts_unmapped_methods(self):
        write(self.tmp, "src/hello.py", CODE + "\n    def print_bye(self) -> None:\n        pass\n\ndef helper() -> None:\n    pass\n")
        write(self.tmp, "docs/trace_map.md", MAP)
        base = ["docs/detail_design.md", "docs/trace_map.md", "src", "--strict"]
        code, out = run_script("trace_map_checker.py", base, cwd=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("print_bye", out)
        code, out = run_script("trace_map_checker.py", base + ["--granularity", "class"], cwd=self.tmp)
        self.assertEqual(code, 0, out)
        # 設計書に DS-FN があれば、粒度にかかわらず対応表に要る
        code, out = run_script("trace_map_checker.py", base + ["--granularity=class"], cwd=self.tmp)
        self.assertEqual(code, 0, out)
        write(self.tmp, "docs/trace_map.md", MAP.replace("| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `src/hello.py::HelloPrinter.print_hello` | |\n", ""))
        code, out = run_script("trace_map_checker.py", base + ["--granularity", "class"], cwd=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("DS-FN-PRINT-HELLO-FT-PRINT-HELLO", out)

    def test_mapping_only_change_is_not_a_deletion(self):
        # 第 11 章で同じ ID を [削除]（旧い対応）と [追加]（新しい対応）の 2 行に書いても、要素は残るので警告しない
        change = ("| DS-ID | 対応要件ID | 区分 |\n|---|---|---|\n"
                  "| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `RQ-FT-PRINT-HELLO` | [削除] |\n"
                  "| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `RQ-FT-PRINT-GREETING` | [追加] |\n")
        code, out = self.run_with_change(MAP, change, strict=True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("削除する設計 ID が残っています", out)
        self.assertIn("削除する設計 ID 0 件", out)

    def test_id_on_unchanged_row_is_not_a_deletion_and_mixed_row_warns(self):
        # [削除] の行にある ID でも、「変更なし（既存）」の行に現れれば残る。[追加] と [削除] が同じ行なら警告
        change = ("| DS-ID | 対応要件ID | 区分 |\n|---|---|---|\n"
                  "| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `RQ-FT-PRINT-HELLO` | [削除] |\n"
                  "| `DS-FN-PRINT-HELLO-FT-PRINT-HELLO` | `RQ-FT-PRINT-GREETING` | 変更なし（既存） |\n")
        code, out = self.run_with_change(MAP, change, strict=True)
        self.assertEqual(code, 0, out)
        mixed = ("| DS-ID | 区分 |\n|---|---|\n"
                 "| `DS-CL-HELLO-PRINTER-FT-PRINT-HELLO` | [削除] 旧 / [追加] 新 |\n")
        code, out = self.run_with_change(MAP, mixed, strict=True)
        self.assertEqual(code, 1, out)
        self.assertIn("同じ行にある", out)
        self.assertNotIn("削除する設計 ID が残っています", out)

    def test_canonical_line_with_literal_deleted_word_is_kept(self):
        # 正本の行に「[削除]」の文字があっても（機能名など）、その行の ID は有効
        write(self.tmp, "docs/detail_design.md", DESIGN.replace("| メソッド |", "| [削除]処理のメソッド |"))
        code, out = self.run_checker(MAP)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
