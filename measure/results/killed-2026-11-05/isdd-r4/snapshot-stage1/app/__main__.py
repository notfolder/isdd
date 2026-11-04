"""起動の入口（python -m app）。社内ネットワークの全インターフェースで待ち受ける。"""

from waitress import serve

from . import create_app, load_settings


def start_server():
    """環境変数の設定で Web アプリを作り、Waitress で待ち受ける。"""
    settings = load_settings()
    app = create_app(settings)
    serve(app, host="0.0.0.0", port=settings["PORT"], threads=8)


if __name__ == "__main__":
    start_server()
