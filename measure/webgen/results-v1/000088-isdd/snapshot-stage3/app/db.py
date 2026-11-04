"""SQLite への接続と表の作成。"""

import os
import sqlite3

from app.constants import CONSERVATION_STATUSES, DIETS, HABITATS, KINGDOMS

DATABASE_FILE_NAME = "species.db"

# 学名、界、保全状況は任意（NULL を許す）。旧い定義ではこの 3 列が NOT NULL だった。
LEGACY_NOT_NULL_COLUMNS: tuple[str, ...] = ("scientific_name", "kingdom", "conservation_status")

_COLUMNS: tuple[str, ...] = (
    "id", "scientific_name", "common_name", "kingdom", "taxonomic_class", "habitat", "diet",
    "conservation_status", "average_length_cm", "description", "created_at", "updated_at",
)


def _in_list(values) -> str:
    """SQL の IN 句に入れる文字列リストを作る（値は固定の選択肢だけ）。"""
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


def _table_sql(table_name: str, if_not_exists: bool) -> str:
    """species 表の定義を返す。移行では一時の名前で作る。"""
    prefix = "CREATE TABLE IF NOT EXISTS" if if_not_exists else "CREATE TABLE"
    return f"""
{prefix} {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT UNIQUE COLLATE NOCASE
        CHECK (scientific_name IS NULL OR length(scientific_name) BETWEEN 1 AND 100),
    common_name TEXT NOT NULL CHECK (length(common_name) BETWEEN 1 AND 100),
    kingdom TEXT CHECK (kingdom IS NULL OR kingdom IN ({_in_list(KINGDOMS)})),
    taxonomic_class TEXT CHECK (taxonomic_class IS NULL OR length(taxonomic_class) <= 60),
    habitat TEXT NOT NULL CHECK (habitat IN ({_in_list(HABITATS)})),
    diet TEXT NOT NULL CHECK (diet IN ({_in_list(DIETS)})),
    conservation_status TEXT
        CHECK (conservation_status IS NULL OR conservation_status IN ({_in_list(CONSERVATION_STATUSES.keys())})),
    average_length_cm REAL
        CHECK (average_length_cm IS NULL OR (average_length_cm > 0 AND average_length_cm <= 100000)),
    description TEXT CHECK (description IS NULL OR length(description) <= 2000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def connect_database(data_dir: str) -> sqlite3.Connection:
    """DATA_DIR の下の SQLite ファイルへ接続する。ディレクトリが無ければ作る。"""
    os.makedirs(data_dir, exist_ok=True)
    connection = sqlite3.connect(os.path.join(data_dir, DATABASE_FILE_NAME))
    connection.row_factory = sqlite3.Row
    return connection


def _is_legacy_schema(connection: sqlite3.Connection) -> bool:
    """species 表が旧い定義（学名・界・保全状況が NOT NULL）かどうかを返す。表が無ければ False。"""
    rows = connection.execute("PRAGMA table_info(species)").fetchall()
    not_null = {row["name"]: row["notnull"] for row in rows}
    return any(not_null.get(column) == 1 for column in LEGACY_NOT_NULL_COLUMNS)


def migrate_species_table(connection: sqlite3.Connection) -> bool:
    """旧い定義の species 表を新しい定義へ移す。移行したら True、何もしなければ False。

    新しい表を作り、全行を同じ値のまま写し、旧い表を消して改名する。1 つのトランザクションで行う。
    """
    if not _is_legacy_schema(connection):
        return False
    columns = ", ".join(_COLUMNS)
    try:
        connection.execute("BEGIN")
        connection.execute(_table_sql("species_new", if_not_exists=False))
        connection.execute(f"INSERT INTO species_new ({columns}) SELECT {columns} FROM species")
        connection.execute("DROP TABLE species")
        connection.execute("ALTER TABLE species_new RENAME TO species")
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    return True


def ensure_database_schema(connection: sqlite3.Connection) -> None:
    """species 表が無ければ作る。旧い定義なら新しい定義へ移す。既に新しい定義なら何もしない。"""
    migrate_species_table(connection)
    connection.execute(_table_sql("species", if_not_exists=True))
    connection.commit()
