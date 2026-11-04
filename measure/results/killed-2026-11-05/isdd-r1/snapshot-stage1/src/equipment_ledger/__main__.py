"""起動の入口。設定を読み、Waitress で待ち受ける。"""

from waitress import serve

from equipment_ledger.config import load_config
from equipment_ledger.web import create_app


def main():
    """設定を読んで Web アプリを作り、待ち受けを始める。"""
    config = load_config()
    app = create_app(config)
    print(f"備品台帳を {config['host']}:{config['port']} で起動します", flush=True)
    serve(app, host=config["host"], port=config["port"])


if __name__ == "__main__":
    main()
