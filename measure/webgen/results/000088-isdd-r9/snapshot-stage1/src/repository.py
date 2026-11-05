"""SQLite storage for the species table.

The database file is <DATA_DIR>/species.sqlite3. Each operation opens its own
connection and runs in one transaction.
"""

import os
import sqlite3
from contextlib import contextmanager

from seed_data import sample_species_data
from validation import FILTER_VALUES, THREATENED_STATUSES

DB_FILE_NAME = "species.sqlite3"
SAMPLE_LOADED_KEY = "sample_data_loaded"

VALUE_COLUMNS = (
    "scientific_name",
    "common_name",
    "class_name",
    "family",
    "habitat",
    "diet",
    "conservation_status",
    "average_lifespan_years",
    "average_adult_mass_kg",
    "description",
)

_CREATE_SPECIES = """
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL,
    common_name TEXT NOT NULL,
    class_name TEXT NOT NULL,
    family TEXT NOT NULL DEFAULT '',
    habitat TEXT NOT NULL,
    diet TEXT NOT NULL,
    conservation_status TEXT NOT NULL,
    average_lifespan_years INTEGER,
    average_adult_mass_kg REAL,
    description TEXT NOT NULL DEFAULT ''
)
"""

_CREATE_UNIQUE_NAME = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_species_scientific_name ON species (lower(scientific_name))
"""

_CREATE_META = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""


class SpeciesRepository:
    """Reads and writes the species table."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, DB_FILE_NAME)

    @contextmanager
    def _transaction(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self):
        """Create the data directory and tables; load the sample species once."""
        os.makedirs(self.data_dir, exist_ok=True)
        with self._transaction() as conn:
            conn.execute(_CREATE_SPECIES)
            conn.execute(_CREATE_UNIQUE_NAME)
            conn.execute(_CREATE_META)
            loaded = conn.execute("SELECT value FROM meta WHERE key = ?", (SAMPLE_LOADED_KEY,)).fetchone()
            if loaded is None:
                for values in sample_species_data():
                    self._insert(conn, values)
                conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", (SAMPLE_LOADED_KEY, "1"))

    def search(self, text, filters):
        """Return species whose scientific or common name contains text and that match every filter.

        text is compared in lower case. filters maps a column name to one allowed value.
        The list is sorted by common name, then scientific name.
        """
        conditions = []
        params = []
        if text:
            conditions.append("(instr(lower(scientific_name), ?) > 0 OR instr(lower(common_name), ?) > 0)")
            params.extend([text, text])
        for column, value in filters.items():
            if column not in FILTER_VALUES:
                raise ValueError("unknown filter: " + column)
            conditions.append(column + " = ?")
            params.append(value)
        sql = "SELECT * FROM species"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY lower(common_name), lower(scientific_name)"
        with self._transaction() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def count_species(self):
        """Return the number of species."""
        with self._transaction() as conn:
            return conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]

    def count_threatened_species(self):
        """Return the number of species whose status is VU, EN or CR."""
        placeholders = ", ".join("?" for _ in THREATENED_STATUSES)
        sql = "SELECT COUNT(*) FROM species WHERE conservation_status IN (" + placeholders + ")"
        with self._transaction() as conn:
            return conn.execute(sql, THREATENED_STATUSES).fetchone()[0]

    def get(self, species_id):
        """Return the species with this id as a dictionary, or None when it does not exist."""
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
            return dict(row) if row is not None else None

    def create(self, values):
        """Insert a species from cleaned values and return its new id."""
        with self._transaction() as conn:
            return self._insert(conn, values)

    def update(self, species_id, values):
        """Replace the stored values of a species. Return False when it does not exist."""
        assignments = ", ".join(column + " = ?" for column in VALUE_COLUMNS)
        params = [values[column] for column in VALUE_COLUMNS]
        params.append(species_id)
        with self._transaction() as conn:
            cursor = conn.execute("UPDATE species SET " + assignments + " WHERE id = ?", params)
            return cursor.rowcount > 0

    def delete(self, species_id):
        """Delete a species. Return False when it does not exist."""
        with self._transaction() as conn:
            cursor = conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
            return cursor.rowcount > 0

    def is_scientific_name_taken(self, scientific_name, exclude_id=None):
        """Return True when another species has this scientific name (case-insensitive)."""
        sql = "SELECT 1 FROM species WHERE lower(scientific_name) = lower(?) AND id != ? LIMIT 1"
        with self._transaction() as conn:
            row = conn.execute(sql, (scientific_name, exclude_id if exclude_id is not None else -1)).fetchone()
            return row is not None

    def _insert(self, conn, values):
        columns = ", ".join(VALUE_COLUMNS)
        marks = ", ".join("?" for _ in VALUE_COLUMNS)
        cursor = conn.execute(
            "INSERT INTO species (" + columns + ") VALUES (" + marks + ")",
            [values[column] for column in VALUE_COLUMNS],
        )
        return cursor.lastrowid
