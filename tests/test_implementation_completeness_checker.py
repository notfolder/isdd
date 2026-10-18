"""implementation_completeness_checker.py の単体テスト"""

import json
import unittest

from helpers import TempDirMixin, run_script, write


class CompletenessCheckerTest(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        write(self.tmp, "e2e/test_cli.py", "def test_cli():\n    pass\n")
        write(self.tmp, "README.md", "# app\n\n## 起動方法\n\npython3 app.py\n")
        write(self.tmp, "docs/trace_map.md", "| DS-ID | 修飾名 | 備考 |\n|---|---|---|\n| `DS-MD-APP-FT-RUN` | `app.py` | |\n")

    def profile(self, **kw):
        data = {"runtime": "cli", "auth": False, "external": False, "e2e_dir": "e2e"}
        data.update(kw)
        write(self.tmp, "scripts/isdd/completeness.json", json.dumps(data))

    def run_checker(self):
        return run_script("implementation_completeness_checker.py", [str(self.tmp)])

    def test_cli_without_auth_passes(self):
        self.profile()
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)

    def test_container_requires_compose(self):
        self.profile(runtime="container")
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        write(self.tmp, "docker-compose.yml", "services: {}\n")
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)

    def test_auth_requires_initial_user(self):
        self.profile(auth=True)
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)
        write(self.tmp, "README.md", "# app\n\n## 起動方法\n\nrun\n\n## 初期ユーザー\n\nadmin\n")
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)

    def test_missing_e2e_fails(self):
        self.profile()
        (self.tmp / "e2e" / "test_cli.py").unlink()
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)

    def test_missing_trace_map_fails(self):
        self.profile()
        (self.tmp / "docs" / "trace_map.md").unlink()
        code, out = self.run_checker()
        self.assertEqual(code, 1, out)

    def test_without_profile_does_not_require_compose(self):
        code, out = self.run_checker()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
