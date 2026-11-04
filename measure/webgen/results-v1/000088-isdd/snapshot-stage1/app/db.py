"""SQLite への接続と表の作成。"""

import os
import sqlite3

from app.constants import CONSERVATION_STATUSES, DIETS, HABITATS, KINGDOMS

DATABASE_FILE_NAME = "species.db"


def _in_list(values) -> str:
    """SQL の IN 句に入れる文字列リストを作る（値は固定の選択肢だけ）。"""
    return ", ".join("'" + value.replace("'", "''") + "'" for value in values)


def _schema_sql() -> str:
    """species 表の定義を返す。"""
    return f"""
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL UNIQUE COLLATE NOCASE
        CHECK (length(scientific_name) BETWEEN 1 AND 100),
    common_name TEXT NOT NULL CHECK (length(common_name) BETWEEN 1 AND 100),
    kingdom TEXT NOT NULL CHECK (kingdom IN ({_in_list(KINGDOMS)})),
    taxonomic_class TEXT CHECK (taxonomic_class IS NULL OR length(taxonomic_class) <= 60),
    habitat TEXT NOT NULL CHECK (habitat IN ({_in_list(HABITATS)})),
    diet TEXT NOT NULL CHECK (diet IN ({_in_list(DIETS)})),
    conservation_status TEXT NOT NULL
        CHECK (conservation_status IN ({_in_list(CONSERVATION_STATUSES.keys())})),
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


def ensure_database_schema(connection: sqlite3.Connection) -> None:
    """species 表が無ければ作る。既にあれば何もしない。"""
    connection.executescript(_schema_sql())
    connection.commit()
