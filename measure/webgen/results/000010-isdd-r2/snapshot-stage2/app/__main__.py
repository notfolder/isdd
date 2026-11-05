"""起動: 環境変数 PORT と DATA_DIR を読み、部品を組み立ててサーバーを前景で動かす。"""

import os
import sys
from pathlib import Path

from app.database import Database
from app.server import create_server
from app.service import SpinService

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DB_FILE_NAME = "wheel.sqlite3"


def main() -> int:
    """サーバーを起動する。Ctrl+C か終了シグナルで止まる。終了コードを返す。"""
    raw_port = os.environ.get("PORT", str(DEFAULT_PORT)).strip()
    try:
        port = int(raw_port)
    except ValueError:
        print(f"PORT must be a number, got: {raw_port!r}", file=sys.stderr)
        return 2

    data_dir = Path(os.environ.get("DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
    data_dir.mkdir(parents=True, exist_ok=True)

    database = Database(str(data_dir / DB_FILE_NAME))
    database.initialize()
    service = SpinService(database)

    server = create_server(HOST, port, service)
    print(f"Wheel of Fortune is running at http://{HOST}:{port}/ (data: {data_dir})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
