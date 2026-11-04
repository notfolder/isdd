"""景品と抽選記録の読み書き。"""

import sqlite3


def _connect(db_path):
    connection = sqlite3.connect(db_path, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def list_prizes(db_path):
    """景品の一覧を id の昇順で返す。各要素は id・name・description を持つ辞書。"""
    connection = _connect(db_path)
    try:
        rows = connection.execute(
            "SELECT id, name, description FROM prize ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def insert_spin_record(db_path, player_name, prize_id, prize_name, spun_at):
    """抽選記録を 1 件追加し、追加した記録（id・player_name・prize_name・spun_at）を返す。"""
    connection = _connect(db_path)
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO spin_record (player_name, prize_id, prize_name, spun_at) "
                "VALUES (?, ?, ?, ?)",
                (player_name, prize_id, prize_name, spun_at),
            )
            record_id = cursor.lastrowid
    finally:
        connection.close()
    return {
        "id": record_id,
        "player_name": player_name,
        "prize_name": prize_name,
        "spun_at": spun_at,
    }


def find_records_by_name(db_path, player_name):
    """利用者名が完全一致する抽選記録を、spun_at の新しい順に返す。"""
    connection = _connect(db_path)
    try:
        rows = connection.execute(
            "SELECT id, prize_name, spun_at FROM spin_record "
            "WHERE player_name = ? ORDER BY spun_at DESC, id DESC",
            (player_name,),
        ).fetchall()
    finally:
        connection.close()
    return [dict(row) for row in rows]


def insert_prize(db_path, name):
    """景品を 1 件追加し、追加した景品（id・name・description）を返す。説明は空で登録する。"""
    connection = _connect(db_path)
    try:
        with connection:
            cursor = connection.execute(
                "INSERT INTO prize (name, description) VALUES (?, '')", (name,)
            )
            prize_id = cursor.lastrowid
    finally:
        connection.close()
    return {"id": prize_id, "name": name, "description": ""}


def delete_prize(db_path, prize_id):
    """指定した ID の景品を削除し、削除した件数（0 か 1）を返す。抽選記録は削除しない。"""
    connection = _connect(db_path)
    try:
        with connection:
            cursor = connection.execute("DELETE FROM prize WHERE id = ?", (prize_id,))
            deleted = cursor.rowcount
    finally:
        connection.close()
    return deleted
