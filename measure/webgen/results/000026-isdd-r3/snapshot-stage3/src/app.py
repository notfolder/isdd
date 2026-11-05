"""Entry point: reads PORT and DATA_DIR, prepares the database and serves the site."""

import os
from pathlib import Path

import storage
import web
from poll_service import PollService

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_DATA_DIR = "./data"


def main():
    """Start the web server in the foreground until it is stopped."""
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    data_dir = Path(os.environ.get("DATA_DIR") or DEFAULT_DATA_DIR)
    conn = storage.open_database(data_dir)
    server = web.create_server(HOST, port, PollService(conn))
    print(f"Surveys is running at http://{HOST}:{port} (data: {data_dir})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        conn.close()


if __name__ == "__main__":
    main()
