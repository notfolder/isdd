"""設定の読み取りの単体テスト。"""

import unittest
from pathlib import Path

from src.config import load_settings


class LoadSettingsTest(unittest.TestCase):
    def test_defaults_when_env_is_empty(self):
        settings = load_settings({})
        self.assertEqual(settings["port"], 8000)
        self.assertEqual(settings["data_dir"], Path("data"))
        self.assertEqual(settings["session_idle_timeout_seconds"], 1800)

    def test_env_overrides(self):
        settings = load_settings(
            {"PORT": "9100", "DATA_DIR": "/tmp/x", "SESSION_IDLE_TIMEOUT_SECONDS": "5"}
        )
        self.assertEqual(settings["port"], 9100)
        self.assertEqual(settings["data_dir"], Path("/tmp/x"))
        self.assertEqual(settings["session_idle_timeout_seconds"], 5)
