"""dependency_checker.py の単体テスト"""

import json
import unittest

from helpers import TempDirMixin, run_script, write


class DependencyCheckerTest(TempDirMixin, unittest.TestCase):
    def rules(self, rules):
        write(self.tmp, "scripts/isdd/dependencies.json", json.dumps({"rules": rules}, ensure_ascii=False))

    def run_checker(self, *src):
        return run_script("dependency_checker.py", ["scripts/isdd/dependencies.json", *(src or ("src",))], cwd=self.tmp)

    def test_empty_rules_pass(self):
        self.rules([])
        write(self.tmp, "src/app.py", "import requests\n")
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)
        self.assertIn("規則なし", out)

    def test_missing_rules_file_passes(self):
        write(self.tmp, "src/app.py", "import os\n")
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)

    def test_python_deny_external_module(self):
        self.rules([{"from": "src", "deny": ["requests"], "reason": "連携ライブラリを通す"}])
        write(self.tmp, "src/app.py", "import os\nimport requests\nfrom requests.adapters import HTTPAdapter\n")
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        self.assertIn("src/app.py:2", out)
        self.assertIn("src/app.py:3", out)
        self.assertIn("連携ライブラリを通す", out)

    def test_source_file_as_scope_checks_only_that_file(self):
        self.rules([{"from": "src", "deny": ["requests"], "reason": "連携ライブラリを通す"}])
        write(self.tmp, "src/app.py", "import os\n")
        write(self.tmp, "src/other.py", "import requests\n")
        code, out = self.run_checker("src/app.py")
        self.assertEqual(code, 0, out)
        code, out = self.run_checker("src")
        self.assertEqual(code, 1, out)

    def test_python_deny_project_dir_resolves_relative_and_absolute_imports(self):
        self.rules([{"from": "external/crm/src", "deny": ["src"], "reason": "ラッパーに業務ロジックを入れない"}])
        write(self.tmp, "src/__init__.py", "")
        write(self.tmp, "src/service.py", "def run():\n    pass\n")
        write(self.tmp, "external/crm/src/client.py", "from src.service import run\n")
        write(self.tmp, "external/crm/src/other.py", "from .client import Client\n")
        code, out = self.run_checker("src", "external/crm/src")
        self.assertEqual(code, 1, out)
        self.assertIn("external/crm/src/client.py:1 → src/service.py", out)
        self.assertNotIn("other.py", out)

    def test_python_allow_limits_project_imports_only(self):
        self.rules([{"from": "src/ui", "allow": ["src/service"]}])
        write(self.tmp, "src/__init__.py", "")
        write(self.tmp, "src/ui/__init__.py", "")
        write(self.tmp, "src/service/__init__.py", "")
        write(self.tmp, "src/db/__init__.py", "")
        write(self.tmp, "src/ui/view.py", "import json\nfrom src.service import x\nfrom src.ui import helper\nfrom src.db import conn\n")
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        self.assertIn("src/ui/view.py:4 → src/db", out)
        self.assertNotIn("view.py:2", out)
        self.assertNotIn("view.py:3", out)

    def test_typescript_relative_import_is_resolved(self):
        self.rules([{"from": "src/ui", "deny": ["src/db"]}])
        write(self.tmp, "src/db/index.ts", "export const q = 1;\n")
        write(self.tmp, "src/ui/view.ts", "import axios from 'axios';\nimport { q } from '../db';\n")
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        self.assertIn("src/ui/view.ts:2 → src/db/index.ts", out)

    def test_go_module_import_is_resolved(self):
        self.rules([{"from": "internal/ui", "deny": ["internal/db"]}])
        write(self.tmp, "go.mod", "module example.com/app\n\ngo 1.22\n")
        write(self.tmp, "internal/db/db.go", "package db\n")
        write(self.tmp, "internal/ui/ui.go", 'package ui\n\nimport (\n\t"fmt"\n\t"example.com/app/internal/db"\n)\n')
        code, out = self.run_checker("internal")
        self.assertEqual(code, 1, out)
        self.assertIn("internal/ui/ui.go:5 → internal/db", out)

    def test_unknown_language_is_not_checked(self):
        self.rules([{"from": "src", "deny": ["anything"]}])
        write(self.tmp, "src/main.rs", "use anything::x;\n")
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)
        self.assertIn("読めない言語のファイル 1 件", out)


if __name__ == "__main__":
    unittest.main()
