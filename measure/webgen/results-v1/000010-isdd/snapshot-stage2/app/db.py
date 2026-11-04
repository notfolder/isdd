"""データベースの作成と初期データ。"""

import os
import sqlite3

DB_FILE_NAME = "wheel.sqlite3"

SAMPLE_PRIZES = [
    ("Coffee Voucher", "A free coffee at the cafe"),
    ("Gift Card 500", "A 500 yen gift card"),
    ("Free Dessert", "One free dessert"),
    ("Movie Ticket", "One movie ticket"),
    ("Tote Bag", "A canvas tote bag"),
    ("Mystery Gift", "A surprise gift"),
]

SCHEMA = """
CREATE TABLE prize (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 200)
);
CREATE TABLE spin_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name TEXT NOT NULL CHECK (length(player_name) BETWEEN 1 AND 30),
    prize_id INTEGER NOT NULL REFERENCES prize(id),
    prize_name TEXT NOT NULL,
    spun_at TEXT NOT NULL
);
CREATE INDEX idx_spin_record_player_name ON spin_record (player_name);
"""


def open_database(data_dir):
    """DATA_DIR の DB ファイルのパスを返す。

    ディレクトリが無ければ作る。DB ファイルが無いときだけスキーマを作り、
    サンプル景品を入れる。ファイルが既にあれば何もしない。
    """
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, DB_FILE_NAME)
    if os.path.exists(path):
        return path
    connection = sqlite3.connect(path)
    try:
        with connection:
            connection.executescript(SCHEMA)
            connection.executemany(
                "INSERT INTO prize (name, description) VALUES (?, ?)", SAMPLE_PRIZES
            )
    finally:
        connection.close()
    return path
