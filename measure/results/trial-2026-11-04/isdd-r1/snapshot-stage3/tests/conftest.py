"""単体テストの共通の準備。一時的な DATA_DIR と SQLite 接続を用意する。"""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import db  # noqa: E402


@pytest.fixture
def conn(tmp_path):
    """空の表を持つ SQLite 接続を返す。テストの終わりに閉じる。"""
    connection = db.connect(str(tmp_path))
    db.init_schema(connection)
    yield connection
    connection.close()
