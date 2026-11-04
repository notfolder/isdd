"""起動の入口。PORT と DATA_DIR の環境変数を読み、サーバーを前景で動かす。"""

import os
import sys
from http.server import ThreadingHTTPServer

from app.db import open_database
from app.server import _RequestHandler

DEFAULT_PORT = 8000
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    """DB を開き、127.0.0.1 の PORT で待ち受ける。Ctrl+C で止まる。"""
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    data_dir = os.environ.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data")
    db_path = open_database(data_dir)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _RequestHandler)
    httpd.db_path = db_path
    print(f"Wheel of Fortune is running at http://127.0.0.1:{port} (data: {db_path})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
