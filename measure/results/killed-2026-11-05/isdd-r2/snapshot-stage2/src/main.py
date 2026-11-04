"""起動の入口。設定を読み、本番用サーバー waitress で待ち受ける。"""

from waitress import serve

from src.config import load_settings
from src.web import create_app


def main():
    """環境変数で設定を読み、すべての IP の PORT で待ち受ける。"""
    settings = load_settings()
    app = create_app(settings)
    print(f"起動しました: http://0.0.0.0:{settings['port']}/", flush=True)
    serve(app, host="0.0.0.0", port=settings["port"], threads=8)


if __name__ == "__main__":
    main()
