"""総務システム。機能は app/modules/ の下のパッケージとして足す。"""

import importlib
import os
import pkgutil
from pathlib import Path

from flask import Flask

from app.core import audit, auth, db, employees, home


def discover_modules():
    """app/modules の下のパッケージを名前順に読み込む。各パッケージは bp・TITLE・SCHEMA を持つ。"""
    import app.modules as pkg

    found = []
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        if info.ispkg:
            found.append(importlib.import_module(f"app.modules.{info.name}"))
    return found


def create_app(test_config=None):
    app = Flask(__name__, template_folder="core/templates")
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret"), DATABASE=str(data_dir / "soumu.sqlite3"))
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    modules = discover_modules()
    app.config["MODULES"] = [{"slug": m.bp.name, "title": m.TITLE} for m in modules]
    for blueprint in (home.bp, auth.bp, employees.bp, audit.bp):
        app.register_blueprint(blueprint)
    for m in modules:
        app.register_blueprint(m.bp)

    db.init_app(app)
    with app.app_context():
        db.init_db([m.SCHEMA for m in modules])
    return app
