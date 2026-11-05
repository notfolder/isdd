"""起動の入口。環境変数 PORT と DATA_DIR を読み、DB を用意して 127.0.0.1 で待ち受ける。

使い方: PORT=8000 DATA_DIR=./data python3 src/server.py（通常は run.sh から起動する）
"""

import os
import sqlite3
import sys
from http.server import ThreadingHTTPServer

from service.wheel import WheelService
from store.database import Database
from store.seed import seed_sample_data
from web.router import RequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PORT = 8000
HOST = "127.0.0.1"


def read_port() -> int:
    """環境変数 PORT を読む。無ければ 8000。数字でない、または 1〜65535 の外なら ValueError。"""
    raw = os.environ.get("PORT", "").strip() or str(DEFAULT_PORT)
    if not raw.isdigit() or not 1 <= int(raw) <= 65535:
        raise ValueError(f"PORT must be a number from 1 to 65535, got {raw!r}")
    return int(raw)


def main() -> int:
    """DB を用意して HTTP サーバーを起動する。失敗したら理由を標準エラーに出して 1 を返す。"""
    try:
        port = read_port()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    data_dir = os.environ.get("DATA_DIR", "").strip() or os.path.join(PROJECT_ROOT, "data")
    try:
        os.makedirs(data_dir, exist_ok=True)
        database = Database(os.path.join(data_dir, "wheel.db"))
        database.init_schema()
        seed_sample_data(database)
    except (OSError, sqlite3.Error) as error:
        print(f"Cannot prepare the data directory {data_dir}: {error}", file=sys.stderr)
        return 1

    try:
        httpd = ThreadingHTTPServer((HOST, port), RequestHandler)
    except OSError as error:
        print(f"Cannot listen on {HOST}:{port}: {error}", file=sys.stderr)
        return 1

    httpd.wheel_service = WheelService(database)
    print(f"Prize wheel is running at http://{HOST}:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
