"""Entry point: reads PORT and DATA_DIR, prepares the database and serves the site."""

from http.server import ThreadingHTTPServer
import os
import sys

from core.db import Store
from web.app import AppHandler

HOST = "127.0.0.1"
DEFAULT_PORT = 8000
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE_NAME = "barbershop.db"


def read_port(value):
    """Parse the PORT setting.

    Args:
        value: the environment value, or None.
    Returns:
        the port number (1 to 65535).
    Raises:
        ValueError: when the value is not a number in range.
    """
    if value is None or value.strip() == "":
        return DEFAULT_PORT
    if not value.strip().isdigit():
        raise ValueError("PORT must be a number, got %r" % value)
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535, got %d" % port)
    return port


def prepare_store(data_dir):
    """Create DATA_DIR if needed, create the tables and load sample data when empty.

    Args:
        data_dir: directory for the database file.
    Returns:
        the Store.
    """
    os.makedirs(data_dir, exist_ok=True)
    store = Store(os.path.join(data_dir, DB_FILE_NAME))
    store.init_schema()
    store.seed_sample_data_if_empty()
    return store


def make_server(port, store):
    """Create the HTTP server bound to 127.0.0.1.

    Args:
        port: TCP port (0 picks a free port).
        store: the Store to use.
    Returns:
        a ThreadingHTTPServer ready for serve_forever().
    """
    server = ThreadingHTTPServer((HOST, port), AppHandler)
    server.store = store
    return server


def main():
    """Start the site. Runs until interrupted."""
    try:
        port = read_port(os.environ.get("PORT"))
    except ValueError as err:
        print("Error: %s" % err, file=sys.stderr)
        return 1
    data_dir = os.environ.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data")
    try:
        store = prepare_store(data_dir)
    except OSError as err:
        print("Error: cannot prepare DATA_DIR %s: %s" % (data_dir, err), file=sys.stderr)
        return 1
    try:
        server = make_server(port, store)
    except OSError as err:
        print("Error: cannot listen on %s:%d: %s" % (HOST, port, err), file=sys.stderr)
        return 1
    print("Barber Shop site: http://%s:%d/ (data: %s)" % (HOST, port, data_dir), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
