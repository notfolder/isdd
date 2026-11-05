"""起動処理: 設定の読み込み、DB の初期化、初期データの投入、Web サーバーの起動。"""

import os

from store.db import init_db, seed_sample_polls
from web.app import create_app

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "./data"


def read_settings():
    """環境変数 PORT と DATA_DIR を読み、(ポート番号, データディレクトリ) を返す。"""
    port = int(os.environ.get("PORT") or DEFAULT_PORT)
    data_dir = os.environ.get("DATA_DIR") or DEFAULT_DATA_DIR
    return port, data_dir


def main():
    """DB を用意し、Web サーバーを 127.0.0.1 の PORT で起動する（前景で動く）。"""
    port, data_dir = read_settings()
    db_path = os.path.join(data_dir, "polls.db")
    init_db(db_path)
    seed_sample_polls(db_path)
    app = create_app(db_path)
    app.run(host=HOST, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
