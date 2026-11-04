"""isdd_setup.py の単体テスト"""

import json
import subprocess
import unittest

from helpers import REPO, TempDirMixin, run_script, write

# 版は同梱先のスキルの SKILL.md から読むので、isdd-setup に複製したものを動かす
SETUP_DIR = REPO / "skills" / "isdd-setup" / "scripts"

MARK = "<!-- isdd-setup:begin -->"


class IsddSetupTest(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        write(self.tmp, "src/hello.py", "def hello():\n    pass\n")

    def setup(self, *extra):
        return run_script("isdd_setup.py", ["--src", "src", "--runtime", "cli", "--no-auth", "--no-external", *extra], cwd=self.tmp, scripts_dir=SETUP_DIR)

    def test_creates_scripts_and_profile(self):
        code, out = self.setup()
        self.assertEqual(code, 0, out)
        isdd = self.tmp / "scripts" / "isdd"
        for name in ("check.sh", "pre-commit", "trace_map_checker.py", "implementation_completeness_checker.py", "VERSION", "completeness.json"):
            self.assertTrue((isdd / name).exists(), name)
        profile = json.loads((isdd / "completeness.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["runtime"], "cli")
        self.assertFalse(profile["auth"])

    def test_check_sh_passes_active_change_pointer(self):
        self.setup()
        check_sh = (self.tmp / "scripts" / "isdd" / "check.sh").read_text(encoding="utf-8")
        self.assertIn('--active-change "docs/active_change"', check_sh)
        agents = (self.tmp / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/active_change", agents)

    def test_version_comes_from_skill(self):
        self.setup()
        version = (self.tmp / "scripts" / "isdd" / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^v\d+\.\d+\.\d+$")

    def test_removes_old_rq_copies(self):
        write(self.tmp, "scripts/isdd/rq_ds_link_checker.py", "# old\n")
        code, out = self.setup()
        self.assertEqual(code, 0, out)
        self.assertFalse((self.tmp / "scripts" / "isdd" / "rq_ds_link_checker.py").exists())
        self.assertIn("削除", out)

    def test_rules_block_is_replaced_not_duplicated(self):
        write(self.tmp, "AGENTS.md", "# AGENTS\n\n既存の文\n")
        self.setup()
        self.setup()
        text = (self.tmp / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(text.count(MARK), 1)
        self.assertIn("既存の文", text)

    def test_without_git_reports_skip(self):
        code, out = self.setup()
        self.assertIn(".git が無い", out)

    def test_existing_foreign_hook_is_kept(self):
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        write(self.tmp, ".git/hooks/pre-commit", "#!/bin/sh\necho mine\n")
        code, out = self.setup()
        self.assertEqual(code, 0, out)
        self.assertIn("echo mine", (self.tmp / ".git" / "hooks" / "pre-commit").read_text(encoding="utf-8"))
        self.assertIn("省略", out)

    def test_dependency_rules_template_created_and_kept(self):
        code, out = self.setup()
        self.assertEqual(code, 0, out)
        isdd = self.tmp / "scripts" / "isdd"
        self.assertTrue((isdd / "dependency_checker.py").exists())
        deps = isdd / "dependencies.json"
        self.assertEqual(json.loads(deps.read_text(encoding="utf-8"))["rules"], [])
        deps.write_text('{"rules": [{"from": "src", "deny": ["requests"]}]}', encoding="utf-8")
        code, out = self.setup()
        self.assertIn("保持", out)
        self.assertIn("requests", deps.read_text(encoding="utf-8"))

    def test_check_sh_runs_both_checkers_with_tests_and_granularity(self):
        self.setup("--granularity", "class", "--e2e-dir", "tests_e2e")
        check_sh = (self.tmp / "scripts" / "isdd" / "check.sh").read_text(encoding="utf-8")
        self.assertIn('--tests "tests_e2e"', check_sh)
        self.assertIn('--granularity "class"', check_sh)
        self.assertIn("dependency_checker.py scripts/isdd/dependencies.json", check_sh)
        agents = (self.tmp / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("dependencies.json", agents)
        self.assertIn("公開関数はクラスかファイルの登録で足りる", agents)

    def test_check_sh_fails_on_dependency_violation(self):
        write(self.tmp, "docs/requirements.md", "| RQ-BK-ID | 業務課題 |\n|---|---|\n| `RQ-BK-X` | 課題 |\n")
        write(self.tmp, "docs/detail_design.md", "| DS-ID |\n|---|\n| `DS-MD-HELLO` |\n")
        write(self.tmp, "docs/trace_map.md", "| DS-ID | 修飾名 | 備考 |\n|---|---|---|\n| `DS-MD-HELLO` | `src/hello.py` | |\n")
        write(self.tmp, "src/hello.py", "import requests\n")
        self.setup("--granularity", "class")
        (self.tmp / "scripts" / "isdd" / "dependencies.json").write_text('{"rules": [{"from": "src", "deny": ["requests"]}]}', encoding="utf-8")
        proc = subprocess.run(["bash", "scripts/isdd/check.sh"], cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("違反 1 件", proc.stdout)
        (self.tmp / "scripts" / "isdd" / "dependencies.json").write_text('{"rules": []}', encoding="utf-8")
        proc = subprocess.run(["bash", "scripts/isdd/check.sh", "--strict"], cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    # design-chapters.md 8-4 / trace-map-rules.md「受け入れ判定」: check.sh は acceptance_checker.py を呼び、e2e/results/ は git 管理外
    def test_check_sh_runs_acceptance_checker_and_ignores_results(self):
        write(self.tmp, ".gitignore", "*.pyc\n")
        code, out = self.setup("--e2e-dir", "tests_e2e")
        self.assertEqual(code, 0, out)
        isdd = self.tmp / "scripts" / "isdd"
        self.assertTrue((isdd / "acceptance_checker.py").exists())
        check_sh = (isdd / "check.sh").read_text(encoding="utf-8")
        self.assertIn('acceptance_checker.py "docs/requirements.md" "docs/detail_design.md" "docs/trace_map.md"', check_sh)
        self.assertIn('--junit "tests_e2e/results/*.xml"', check_sh)
        ignore = (self.tmp / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.pyc", ignore)
        self.assertEqual(ignore.count("tests_e2e/results/"), 1)
        self.setup("--e2e-dir", "tests_e2e")
        ignore = (self.tmp / ".gitignore").read_text(encoding="utf-8")
        self.assertEqual(ignore.count("tests_e2e/results/"), 1)

    # 受け入れ判定は既定では警告だけ（pre-commit を止めない）、--strict で失敗
    def test_check_sh_acceptance_is_warning_unless_strict(self):
        write(self.tmp, "docs/requirements.md", "| RQ-ID | 検証する要件ID | 対応業務課題ID |\n|---|---|---|\n| `RQ-TS-VERIFY-HELLO` | `RQ-FT-HELLO` | `RQ-BK-X` |\n")
        write(self.tmp, "docs/detail_design.md", "### 8-2. E2E テストのシナリオ\n| DS-ID |\n|---|\n| `DS-TS-HELLO` |\n## 11. 要件と設計の対応表\n| DS-ID | 対応要件ID |\n|---|---|\n| `DS-TS-HELLO` | `RQ-TS-VERIFY-HELLO` |\n")
        write(self.tmp, "docs/trace_map.md", "| DS-ID | 修飾名 | 備考 |\n|---|---|---|\n| `DS-TS-HELLO` | `e2e/test_hello.py::test_hello` | |\n")
        write(self.tmp, "e2e/test_hello.py", "def test_hello():\n    pass\n")
        self.setup("--granularity", "class")
        proc = subprocess.run(["bash", "scripts/isdd/check.sh"], cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("未実行", proc.stdout)
        proc = subprocess.run(["bash", "scripts/isdd/check.sh", "--strict"], cwd=self.tmp, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("受け入れ判定に失敗", proc.stdout)


if __name__ == "__main__":
    unittest.main()
