"""環境変数の既定値と、秘密鍵の保存を確かめる。"""

from app import config


def test_defaults_when_env_is_empty():
    cfg = config.load_config({})
    assert cfg.port == 8000
    assert cfg.data_dir == "data"
    assert cfg.idle_timeout_seconds == 1800


def test_env_overrides():
    cfg = config.load_config({"PORT": "8785", "DATA_DIR": "/tmp/x", "SESSION_IDLE_TIMEOUT_SECONDS": "3"})
    assert (cfg.port, cfg.data_dir, cfg.idle_timeout_seconds) == (8785, "/tmp/x", 3)


def test_secret_key_is_created_once(tmp_path):
    first = config.load_or_create_secret_key(str(tmp_path))
    second = config.load_or_create_secret_key(str(tmp_path))
    assert first == second and len(first) == 64
