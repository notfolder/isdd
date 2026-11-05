"""生物種の情報を SQLite に保存し、検索・取得・登録・修正・削除を行う。"""

import os
import sqlite3

from src.core.seed_data import sample_species

COLUMNS = (
    "scientific_name",
    "common_name",
    "taxonomic_class",
    "habitat",
    "diet",
    "lifespan_years",
    "body_mass_kg",
    "conservation_status",
    "description",
)

FILTER_COLUMNS = ("taxonomic_class", "habitat", "diet", "conservation_status")


def _escape_like(text):
    """LIKE の検索語で特別な文字（\\ % _）を文字として扱えるようにエスケープする。"""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class SpeciesStore:
    """生物種の保存先（1 つの SQLite ファイル）を操作する。"""

    def __init__(self, db_path):
        """db_path は SQLite ファイルのパス。"""
        self._db_path = db_path

    def _connect(self):
        """接続を開く。行は名前で引けるようにする。"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        """保存先の DB とテーブルを作る。

        テーブルが新しく作られたときだけ、サンプルの生物種を入れる。既にあれば何もしない。
        保存先のフォルダが無ければ作る。
        """
        folder = os.path.dirname(os.path.abspath(self._db_path))
        os.makedirs(folder, exist_ok=True)
        conn = self._connect()
        try:
            existed = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'species'"
            ).fetchone() is not None
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS species (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scientific_name TEXT NOT NULL,
                    common_name TEXT NOT NULL,
                    taxonomic_class TEXT NOT NULL,
                    habitat TEXT NOT NULL,
                    diet TEXT NOT NULL,
                    lifespan_years INTEGER,
                    body_mass_kg REAL,
                    conservation_status TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS species_scientific_name_key "
                "ON species (lower(trim(scientific_name)))"
            )
            if not existed:
                for species in sample_species():
                    conn.execute(self._insert_sql(), self._values(species))
            conn.commit()
        finally:
            conn.close()

    def list_species(self, conditions):
        """条件に合う生物種を、和名の昇順（同じなら学名の昇順）で返す。

        conditions は読み取り済みの検索条件（q と各選択欄）。空の条件は絞り込まない。
        q は学名・和名・説明に部分一致（大文字小文字を区別しない）。
        選択欄は AND で絞る。
        """
        clauses = []
        params = []
        query = conditions.get("q", "")
        if query:
            pattern = "%" + _escape_like(query.lower()) + "%"
            clauses.append(
                "(lower(scientific_name) LIKE ? ESCAPE '\\' "
                "OR lower(common_name) LIKE ? ESCAPE '\\' "
                "OR lower(description) LIKE ? ESCAPE '\\')"
            )
            params.extend([pattern, pattern, pattern])
        for column in FILTER_COLUMNS:
            value = conditions.get(column, "")
            if value:
                clauses.append(f"{column} = ?")
                params.append(value)
        sql = "SELECT * FROM species"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY common_name COLLATE NOCASE, scientific_name COLLATE NOCASE"
        conn = self._connect()
        try:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def get_species(self, species_id):
        """ID の生物種を返す。無ければ None。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
            return dict(row) if row is not None else None
        finally:
            conn.close()

    def is_scientific_name_taken(self, scientific_name, exclude_id=None):
        """学名（大文字小文字と前後の空白を無視）を、別の生物種が使っているかを返す。

        exclude_id に渡した ID の生物種は数えない（修正時に自分自身を除くため）。
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT 1 FROM species "
                "WHERE lower(trim(scientific_name)) = lower(trim(?)) AND id IS NOT ?",
                (scientific_name, exclude_id),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def create_species(self, values):
        """整えた値で生物種を 1 件登録し、新しい ID を返す。"""
        conn = self._connect()
        try:
            cursor = conn.execute(self._insert_sql(), self._values(values))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_species(self, species_id, values):
        """ID の生物種を整えた値で更新する。対象が無ければ False、更新できれば True。"""
        assignments = ", ".join(f"{column} = ?" for column in COLUMNS)
        conn = self._connect()
        try:
            cursor = conn.execute(
                f"UPDATE species SET {assignments} WHERE id = ?",
                self._values(values) + (species_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_species(self, species_id):
        """ID の生物種を削除する。対象が無ければ False、削除できれば True。"""
        conn = self._connect()
        try:
            cursor = conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    @staticmethod
    def _insert_sql():
        """1 件の挿入文。"""
        placeholders = ", ".join("?" for _ in COLUMNS)
        return f"INSERT INTO species ({', '.join(COLUMNS)}) VALUES ({placeholders})"

    @staticmethod
    def _values(values):
        """項目の値を、列の順の並びにする。"""
        return tuple(values.get(column) for column in COLUMNS)
