import subprocess
import sys
import unittest


class HelloE2ETest(unittest.TestCase):
    def test_prints_hello(self):
        proc = subprocess.run([sys.executable, "src/hello.py"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "Hello, World!")
