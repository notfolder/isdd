"""備品の貸出と返却。貸出の行は備品 1 件につき 0 か 1 件（管理番号が主キー）。返却した記録は残さない。"""

import sqlite3

LEND_OK = "lent"
LEND_ALREADY_LENT = "already_lent"
LEND_NO_EQUIPMENT = "no_equipment"
LEND_NO_BORROWER = "no_borrower"

RETURN_OK = "returned"
RETURN_ALREADY = "already_returned"
RETURN_NO_EQUIPMENT = "no_equipment"


def lend_equipment(conn: sqlite3.Connection, equipment_number: str, employee_number: str, lent_on: str) -> str:
    """貸出の行を 1 件追加する。書き込みのトランザクションを即時に開始し、先の登録だけを記録する。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)).fetchone() is None:
            result = LEND_NO_EQUIPMENT
        elif conn.execute("SELECT 1 FROM account WHERE employee_number = ?", (employee_number,)).fetchone() is None:
            result = LEND_NO_BORROWER
        else:
            try:
                conn.execute(
                    "INSERT INTO lending (equipment_number, employee_number, lent_on) VALUES (?, ?, ?)",
                    (equipment_number, employee_number, lent_on),
                )
                result = LEND_OK
            except sqlite3.IntegrityError:
                result = LEND_ALREADY_LENT
        conn.execute("COMMIT")
        return result
    except Exception:
        conn.execute("ROLLBACK")
        raise


def return_equipment(conn: sqlite3.Connection, equipment_number: str) -> str:
    """貸出の行を消して空きに戻す。記録は残さない。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)).fetchone() is None:
            conn.execute("ROLLBACK")
            return RETURN_NO_EQUIPMENT
        cursor = conn.execute("DELETE FROM lending WHERE equipment_number = ?", (equipment_number,))
        conn.execute("COMMIT")
        return RETURN_OK if cursor.rowcount > 0 else RETURN_ALREADY
    except Exception:
        conn.execute("ROLLBACK")
        raise
