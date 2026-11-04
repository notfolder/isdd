"""アプリを waitress で起動する入口。"""

from waitress import serve

from .app import create_app
from .core.config import load_settings


def main() -> None:
    """設定を読み、社内ネットワーク向けに待ち受ける。"""
    settings = load_settings()
    app = create_app(settings)
    serve(app, host=settings["host"], port=settings["port"])


if __name__ == "__main__":
    main()
