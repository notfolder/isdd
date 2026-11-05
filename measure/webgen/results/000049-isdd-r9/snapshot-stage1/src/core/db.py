"""SQLite storage for barbers and services."""

import sqlite3

SAMPLE_BARBERS = [
    ("Maria Lopez", "Fades and beard trims", "+1 555 0101"),
    ("James Carter", "Classic scissor cuts", "+1 555 0102"),
    ("Aiko Tanaka", "Hot towel shaves", "+81 90 5555 0103"),
]

SAMPLE_SERVICES = [
    ("Classic haircut", 2500, 30, "Scissor and clipper finish"),
    ("Beard trim", 1200, 15, "Shape and line-up"),
    ("Hot towel shave", 1800, 25, "Straight razor with hot towel"),
    ("Kids cut", 1500, 20, "For children under 12"),
]


class Store:
    """Reads and writes barbers and services in one SQLite file.

    Each call opens its own connection, so the store can be used from
    several request threads.
    """

    def __init__(self, db_path):
        """Create a store.

        Args:
            db_path: path of the SQLite file (created when missing).
        """
        self.db_path = db_path

    def _connect(self):
        """Open a connection with rows returned as mappings-like objects."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        """Create the tables when they do not exist yet."""
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS barbers ("
                    " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    " name TEXT NOT NULL,"
                    " specialty TEXT NOT NULL DEFAULT '',"
                    " phone TEXT NOT NULL DEFAULT '')"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS services ("
                    " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    " name TEXT NOT NULL,"
                    " price_cents INTEGER NOT NULL,"
                    " duration_min INTEGER NOT NULL,"
                    " description TEXT NOT NULL DEFAULT '')"
                )
        finally:
            conn.close()

    def seed_sample_data_if_empty(self):
        """Insert sample barbers and services when both tables are empty.

        Returns:
            True when sample data was inserted, False otherwise.
        """
        conn = self._connect()
        try:
            barbers = conn.execute("SELECT COUNT(*) FROM barbers").fetchone()[0]
            services = conn.execute("SELECT COUNT(*) FROM services").fetchone()[0]
            if barbers or services:
                return False
            with conn:
                conn.executemany(
                    "INSERT INTO barbers (name, specialty, phone) VALUES (?, ?, ?)",
                    SAMPLE_BARBERS,
                )
                conn.executemany(
                    "INSERT INTO services (name, price_cents, duration_min, description)"
                    " VALUES (?, ?, ?, ?)",
                    SAMPLE_SERVICES,
                )
            return True
        finally:
            conn.close()

    def list_barbers(self):
        """Return all barbers, oldest first, as a list of dicts."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, specialty, phone FROM barbers ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_barber(self, name, specialty, phone):
        """Insert a barber.

        Args:
            name: validated name.
            specialty: validated specialty (may be empty).
            phone: validated phone as typed (may be empty).
        Returns:
            the new row id.
        """
        conn = self._connect()
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO barbers (name, specialty, phone) VALUES (?, ?, ?)",
                    (name, specialty, phone),
                )
                return cur.lastrowid
        finally:
            conn.close()

    def list_services(self):
        """Return all services, oldest first, as a list of dicts."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, price_cents, duration_min, description"
                " FROM services ORDER BY id"
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def add_service(self, name, price_cents, duration_min, description):
        """Insert a service.

        Args:
            name: validated name.
            price_cents: price in cents (integer).
            duration_min: duration in minutes (integer).
            description: validated description (may be empty).
        Returns:
            the new row id.
        """
        conn = self._connect()
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO services (name, price_cents, duration_min, description)"
                    " VALUES (?, ?, ?, ?)",
                    (name, price_cents, duration_min, description),
                )
                return cur.lastrowid
        finally:
            conn.close()
