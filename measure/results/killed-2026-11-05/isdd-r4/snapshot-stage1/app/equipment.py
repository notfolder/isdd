"""備品の検査・登録・修正・削除・一覧。"""

import re
import sqlite3

from .db import get_db

EQUIPMENT_NUMBER_PATTERN = re.compile(r"[A-Za-z0-9-]{1,20}")
NAME_MAX_LENGTH = 50


def validate_equipment(equipment_number, name):
    """備品の入力を検査する。

    引数: equipment_number（管理番号）、name（前後の空白を取った備品名）。
    戻り値: 入力欄の名前をキーにした、エラー文言の辞書（問題が無ければ空）。
    """
    errors = {}
    if not EQUIPMENT_NUMBER_PATTERN.fullmatch(equipment_number):
        errors["equipment_number"] = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
    if name == "":
        errors["name"] = "備品名を入力してください"
    elif len(name) > NAME_MAX_LENGTH:
        errors["name"] = "備品名は 50 文字以内で入力してください"
    return errors


def create_equipment(equipment_number, name):
    """備品を 1 件登録する。管理番号の重複は一意制約で検出する。

    戻り値: エラーの辞書（成功時は空）。
    """
    try:
        get_db().execute(
            "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
            (equipment_number, name),
        )
    except sqlite3.IntegrityError:
        return {"equipment_number": "この管理番号は既に使われています"}
    return {}


def update_equipment(original_number, equipment_number, name):
    """管理番号で備品を探し、管理番号と備品名を変える。

    引数: original_number（変更前の管理番号）、equipment_number（新しい管理番号）、name（新しい備品名）。
    戻り値: エラーの辞書（成功時は空）。対象の備品が無ければ LookupError。
    """
    try:
        cur = get_db().execute(
            "UPDATE equipment SET equipment_number = ?, name = ? WHERE equipment_number = ?",
            (equipment_number, name, original_number),
        )
    except sqlite3.IntegrityError:
        return {"equipment_number": "この管理番号は既に使われています"}
    if cur.rowcount == 0:
        raise LookupError(original_number)
    return {}


def delete_equipment(equipment_number):
    """管理番号の備品を 1 件削除する。削除できたら True。"""
    cur = get_db().execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
    return cur.rowcount == 1


def get_equipment(equipment_number):
    """管理番号で備品を 1 件取り出す。無ければ None。"""
    row = get_db().execute(
        "SELECT equipment_number, name FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()
    return dict(row) if row is not None else None


def list_loan_status():
    """全備品を管理番号の昇順で返す。この段では貸出の記録が無いため、すべて「空き」で名前と日付は空。

    戻り値: 行ごとの辞書（equipment_number・name・status・borrower_name・loan_date）のリスト。
    """
    rows = get_db().execute(
        "SELECT equipment_number, name FROM equipment ORDER BY equipment_number"
    ).fetchall()
    return [
        {
            "equipment_number": row["equipment_number"],
            "name": row["name"],
            "status": "空き",
            "borrower_name": "",
            "loan_date": "",
        }
        for row in rows
    ]
