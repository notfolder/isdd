"""景品と当選記録の表の読み書き。"""

from typing import Any, Dict, List

from store.database import Database


class PrizeRepository:
    """景品（抽選の区分。はずれを含む）の表を読む。初期データの投入にも使う。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def list_all(self) -> List[Dict[str, Any]]:
        """表示順に並べた全景品を返す。"""
        with self._database.connection() as conn:
            rows = conn.execute(
                "SELECT id, name, description, weight, is_miss, position "
                "FROM prizes ORDER BY position, id"
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        """景品の件数を返す。"""
        with self._database.connection() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM prizes").fetchone()[0])

    def insert(self, name: str, description: str, weight: int, is_miss: int, position: int) -> int:
        """景品を 1 件追加し、採番された ID を返す。"""
        with self._database.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO prizes (name, description, weight, is_miss, position) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, description, weight, is_miss, position),
            )
            return int(cursor.lastrowid)


class RecordRepository:
    """当選記録の表を読み書きする。"""

    def __init__(self, database: Database) -> None:
        self._database = database

    def insert(self, player_name: str, prize_id: int, prize_name: str, won_at: str) -> int:
        """当選記録を 1 件追加し、採番された ID を返す。"""
        with self._database.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO winning_records (player_name, prize_id, prize_name, won_at) "
                "VALUES (?, ?, ?, ?)",
                (player_name, prize_id, prize_name, won_at),
            )
            return int(cursor.lastrowid)

    def find_by_player(self, player_name: str) -> List[Dict[str, Any]]:
        """利用者名が完全一致する記録を、新しい順に返す。"""
        with self._database.connection() as conn:
            rows = conn.execute(
                "SELECT id, prize_name, won_at FROM winning_records "
                "WHERE player_name = ? ORDER BY won_at DESC, id DESC",
                (player_name,),
            ).fetchall()
        return [dict(row) for row in rows]

    def count(self) -> int:
        """当選記録の件数を返す。"""
        with self._database.connection() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM winning_records").fetchone()[0])
