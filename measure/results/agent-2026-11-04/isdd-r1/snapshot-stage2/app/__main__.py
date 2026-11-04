"""waitress でアプリを起動する。`python -m app` で呼ばれる。"""

import sys

from waitress import serve

from . import create_app
from .config import load_config

SERVER_THREADS = 8
LISTEN_HOST = "0.0.0.0"


def main() -> int:
    try:
        config = load_config()
    except ValueError as exc:
        print(f"設定エラー: {exc}", file=sys.stderr)
        return 2
    app = create_app(config)
    print(f"待ち受けを開始します: port {config['port']}, data {config['data_dir']}", flush=True)
    serve(app, host=LISTEN_HOST, port=int(config["port"]), threads=SERVER_THREADS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
