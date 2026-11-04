"""設定の読み込みの単体テスト。"""

from pathlib import Path

from equipment_ledger.config import load_config


def test_defaults():
    config = load_config({})
    assert config["port"] == 8000
    assert config["host"] == "0.0.0.0"
    assert config["data_dir"] == Path("./data")
    assert config["idle_timeout_seconds"] == 1800


def test_environment_overrides():
    config = load_config({"PORT": "9001", "DATA_DIR": "/var/lib/ledger", "SESSION_IDLE_TIMEOUT_SECONDS": "60"})
    assert config["port"] == 9001
    assert config["data_dir"] == Path("/var/lib/ledger")
    assert config["idle_timeout_seconds"] == 60
