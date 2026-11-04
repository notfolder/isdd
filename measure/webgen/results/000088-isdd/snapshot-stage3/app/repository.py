"""生物種の表への読み書き。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Mapping, Optional

SEARCHABLE_CRITERIA: tuple[str, ...] = ("kingdom", "habitat", "diet", "conservation_status")


def _now() -> str:
    """UTC の ISO 8601 文字列の現在時刻を返す。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _escape_like(text: str) -> str:
    """LIKE の特殊文字（\\、%、_）を検索語として扱えるようにエスケープする。"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _record_values(values: Mapping[str, str]) -> dict[str, object]:
    """入力値を表に入れる形にする。空の任意項目は NULL、平均体長は数値にする。"""
    average = values.get("average_length_cm", "")
    return {
        "scientific_name": values.get("scientific_name") or None,
        "common_name": values["common_name"],
        "kingdom": values.get("kingdom") or None,
        "taxonomic_class": values.get("taxonomic_class") or None,
        "habitat": values["habitat"],
        "diet": values["diet"],
        "conservation_status": values.get("conservation_status") or None,
        "average_length_cm": float(average) if average else None,
        "description": values.get("description") or None,
    }


class SpeciesRepository:
    """生物種の表の読み書きを 1 か所に集める。"""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def close(self) -> None:
        """接続を閉じる。"""
        self._connection.close()

    def search(self, keyword: str = "", criteria: Optional[Mapping[str, str]] = None) -> list[sqlite3.Row]:
        """キーワード（学名・和名・説明の部分一致、大文字小文字を区別しない）と条件を AND で組み合わせて検索する。"""
        clauses: list[str] = []
        params: list[str] = []
        if keyword:
            pattern = "%" + _escape_like(keyword) + "%"
            clauses.append(
                "(scientific_name LIKE ? ESCAPE '\\' OR common_name LIKE ? ESCAPE '\\' "
                "OR description LIKE ? ESCAPE '\\')"
            )
            params.extend([pattern, pattern, pattern])
        for column in SEARCHABLE_CRITERIA:
            value = (criteria or {}).get(column, "")
            if value:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = (
            "SELECT * FROM species" + where
            + " ORDER BY common_name COLLATE NOCASE, scientific_name COLLATE NOCASE"
        )
        return self._connection.execute(sql, params).fetchall()

    def get(self, species_id: int) -> Optional[sqlite3.Row]:
        """id の種を 1 件返す。無ければ None。"""
        return self._connection.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()

    def find_id_by_scientific_name(self, scientific_name: str, exclude_id: Optional[int] = None) -> Optional[int]:
        """学名（大文字小文字を区別しない）が一致する種の id を返す。exclude_id の種は対象にしない。"""
        sql = "SELECT id FROM species WHERE scientific_name = ? COLLATE NOCASE"
        params: list[object] = [scientific_name]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        row = self._connection.execute(sql, params).fetchone()
        return None if row is None else int(row["id"])

    def insert(self, values: Mapping[str, str]) -> int:
        """入力値の 1 件を追加し、新しい id を返す。学名の重複は IntegrityError になる。"""
        record = _record_values(values)
        now = _now()
        cursor = self._connection.execute(
            "INSERT INTO species (scientific_name, common_name, kingdom, taxonomic_class, habitat, diet, "
            "conservation_status, average_length_cm, description, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record["scientific_name"], record["common_name"], record["kingdom"], record["taxonomic_class"],
                record["habitat"], record["diet"], record["conservation_status"], record["average_length_cm"],
                record["description"], now, now,
            ),
        )
        self._connection.commit()
        return int(cursor.lastrowid)

    def update(self, species_id: int, values: Mapping[str, str]) -> None:
        """id の種を入力値で更新する。"""
        record = _record_values(values)
        self._connection.execute(
            "UPDATE species SET scientific_name = ?, common_name = ?, kingdom = ?, taxonomic_class = ?, "
            "habitat = ?, diet = ?, conservation_status = ?, average_length_cm = ?, description = ?, "
            "updated_at = ? WHERE id = ?",
            (
                record["scientific_name"], record["common_name"], record["kingdom"], record["taxonomic_class"],
                record["habitat"], record["diet"], record["conservation_status"], record["average_length_cm"],
                record["description"], _now(), species_id,
            ),
        )
        self._connection.commit()

    def delete(self, species_id: int) -> bool:
        """id の種を削除する。削除できたら True。"""
        cursor = self._connection.execute("DELETE FROM species WHERE id = ?", (species_id,))
        self._connection.commit()
        return cursor.rowcount > 0
