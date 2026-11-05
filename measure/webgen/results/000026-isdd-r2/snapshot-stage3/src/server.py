"""Entry point: create the polls web app and serve it on 127.0.0.1.

Environment variables:
  PORT      port to listen on (default 8000)
  DATA_DIR  directory for polls.db (default: the data directory next to this project)
"""
import os
from pathlib import Path

from flask import Flask

import db
import sample_data
import web

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


def create_app(data_dir=None):
    """Create the Flask app, prepare the database and load sample data when it has no polls.

    data_dir defaults to the DATA_DIR environment variable, then to the data directory of the project.
    """
    resolved_dir = data_dir or os.environ.get("DATA_DIR") or str(DEFAULT_DATA_DIR)
    app = Flask(__name__)
    app.config["DATA_DIR"] = resolved_dir

    conn = db.get_db(resolved_dir)
    try:
        db.init_db(conn)
        sample_data.seed_sample_data(conn)
    finally:
        conn.close()

    app.register_blueprint(web.bp)
    return app


def main():
    """Start the server in the foreground on 127.0.0.1 at the port given by PORT."""
    port = int(os.environ.get("PORT", "8000"))
    app = create_app()
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
