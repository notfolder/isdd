"""データベースの接続と表の作成を確かめる。"""

from app import db


def test_init_schema_creates_all_tables(conn):
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"accounts", "equipment", "loans", "sessions"} <= names


def test_foreign_keys_are_enforced(conn):
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_connect_creates_data_dir(tmp_path):
    data_dir = tmp_path / "nested" / "data"
    connection = db.connect(str(data_dir))
    db.init_schema(connection)
    connection.close()
    assert (data_dir / db.DB_FILE).exists()
