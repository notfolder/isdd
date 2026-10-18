"""tools/build_skills.py の単体テスト。リポジトリを一時ディレクトリに写して壊し、--check が検出するかを確かめる。"""

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from helpers import REPO, TempDirMixin


class BuildSkillsTest(TempDirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        for name in ("shared", "skills", "tools"):
            shutil.copytree(REPO / name, self.tmp / name, ignore=shutil.ignore_patterns("__pycache__", "*-workspace"))

    def check(self):
        proc = subprocess.run([sys.executable, str(self.tmp / "tools" / "build_skills.py"), "--check"], capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    def test_repository_copy_is_consistent(self):
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_edited_copy_is_detected(self):
        target = self.tmp / "skills" / "isdd-design" / "references" / "document-rules.md"
        target.write_text(target.read_text(encoding="utf-8") + "\n追記\n", encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("正本と違う", out)

    def test_extra_file_is_detected(self):
        (self.tmp / "skills" / "isdd-design" / "references" / "extra.md").write_text("x", encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("余分", out)

    def test_missing_copy_is_detected(self):
        (self.tmp / "skills" / "isdd-design" / "scripts" / "rq_ds_link_checker.py").unlink()
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("未複製", out)

    def test_version_mismatch_is_detected(self):
        skill = self.tmp / "skills" / "isdd-setup" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        skill.write_text(text.replace('version: "', 'version: "x', 1), encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("version", out)

    def test_unused_shared_file_is_detected(self):
        (self.tmp / "shared" / "references" / "unused.md").write_text("x", encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unused.md", out)

    def test_build_repairs_copies(self):
        (self.tmp / "skills" / "isdd-design" / "scripts" / "rq_ds_link_checker.py").unlink()
        subprocess.run([sys.executable, str(self.tmp / "tools" / "build_skills.py")], check=True, capture_output=True)
        code, out = self.check()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
