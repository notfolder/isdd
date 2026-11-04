"""一覧の並べ替え。和名・一般名で並べる。画面と DB に依存しない純粋な関数だけを置く。"""

from __future__ import annotations

from typing import Any, Sequence

# 並べ替えの値と選択欄の表示名。既定は名前の昇順。
SORT_ORDERS: dict[str, str] = {
    "name_asc": "Name (A to Z)",
    "name_desc": "Name (Z to A)",
}
DEFAULT_SORT_ORDER = "name_asc"


def _name_key(row: Any) -> tuple[str, int, str, int]:
    """和名・一般名（大文字小文字を区別しない）、次に学名（空は後ろ）、最後に id で並べる鍵を返す。"""
    scientific = row["scientific_name"]
    scientific_key = (0, scientific.casefold()) if scientific else (1, "")
    return (row["common_name"].casefold(), scientific_key[0], scientific_key[1], row["id"])


def sort_species_rows(rows: Sequence[Any], order: str) -> list[Any]:
    """行を名前で並べ替えた新しいリストを返す。order が name_desc なら昇順の逆順にする。"""
    return sorted(rows, key=_name_key, reverse=(order == "name_desc"))
