"""起動の入口。設定を読み、DB の準備をして HTTP サーバーを立てる。"""

from http.server import ThreadingHTTPServer

from app.config import load_settings
from app.db import initialize_schema
from app.web import RequestHandler


def main() -> int:
    """サーバーを起動し、止められるまで要求を受ける。

    全インターフェースで待ち受ける。社内ネットワークからだけ開く前提で、
    インターネットへの公開はネットワーク側で止める。

    Returns:
        終了コード（0）。
    """
    settings = load_settings()
    initialize_schema(settings.db_path)
    RequestHandler.settings = settings
    server = ThreadingHTTPServer(("0.0.0.0", settings.port), RequestHandler)
    server.daemon_threads = True
    print(f"listening on port {settings.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
