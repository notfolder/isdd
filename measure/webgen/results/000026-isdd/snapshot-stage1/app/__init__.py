"""Application factory for the Polls website."""

from pathlib import Path

from flask import Flask

from . import database, sample_data
from .views import bp


def create_app(data_dir: Path) -> Flask:
    """Create the Flask app, prepare the database under data_dir, and seed sample data when empty."""
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "polls.db"
    with database.open_database(db_path) as conn:
        database.init_schema(conn)
        sample_data.seed_sample_data(conn)

    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path)
    app.register_blueprint(bp)
    return app
