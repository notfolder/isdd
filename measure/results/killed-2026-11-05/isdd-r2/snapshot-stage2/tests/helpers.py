"""テスト用の一時 DB を作る補助関数。"""

import tempfile
from pathlib import Path

from src import db


def make_data_dir():
    """空の一時ディレクトリを作り、スキーマを初期化して Path を返す。"""
    data_dir = Path(tempfile.mkdtemp(prefix="ledger-test-"))
    conn = db.connect(data_dir)
    db.init_schema(conn)
    conn.close()
    return data_dir
