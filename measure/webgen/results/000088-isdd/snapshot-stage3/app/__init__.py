"""Flask アプリケーションの組み立て。"""

from __future__ import annotations

import os

from flask import Flask

from app.db import connect_database, ensure_database_schema
from app.repository import SpeciesRepository
from app.routes import bp
from app.seed import seed_sample_species_if_empty

DEFAULT_DATA_DIR = "./data"


def create_app(data_dir: str | None = None) -> Flask:
    """DATA_DIR（引数、無ければ環境変数、無ければ ./data）を使ってアプリを作る。

    表を作り、表が空ならサンプルを入れてから返す。
    """
    resolved = data_dir or os.environ.get("DATA_DIR") or DEFAULT_DATA_DIR
    connection = connect_database(resolved)
    try:
        ensure_database_schema(connection)
        seed_sample_species_if_empty(SpeciesRepository(connection))
    finally:
        connection.close()

    app = Flask(__name__)
    app.config["DATA_DIR"] = resolved

    def open_repository() -> SpeciesRepository:
        """リクエストごとに新しい接続のリポジトリを開く（画面の処理は SQLite を直接扱わない）。"""
        return SpeciesRepository(connect_database(resolved))

    app.config["OPEN_REPOSITORY"] = open_repository
    app.register_blueprint(bp)
    return app
