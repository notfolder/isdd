"""備品の貸出の登録と返却、日本時間の今日の日付。書き込みは BEGIN IMMEDIATE の 1 つのトランザクションで行う。"""

import sqlite3
from datetime import date, datetime, timedelta, timezone

from src import validation

JST = timezone(timedelta(hours=9))
STATUS_OK = "ok"
STATUS_NOT_FOUND = "not_found"
STATUS_ALREADY_LENT = "already_lent"
STATUS_INVALID = "invalid"
STATUS_NOT_LENT = "not_lent"


def today_jst(now=None):
    """日本時間（UTC+9）の今日の日付を返す。

    引数 now は時刻を持つ datetime（省略時は現在時刻）。戻り値は date。
    """
    current = datetime.now(JST) if now is None else now.astimezone(JST)
    return current.date()


def lend_equipment(conn, equipment_number, employee_number, lent_on):
    """備品を社員に貸し出し、貸出の行を記録する。

    備品の存在、貸出の有無、借りる社員の存在を、BEGIN IMMEDIATE の中で確かめてから挿入する。
    同時に来た貸出は書き込みロックで順に処理されるため、先に記録された 1 件だけが残る。
    引数 lent_on は YYYY-MM-DD の文字列（検査済み）。
    戻り値は (エラーの辞書, 状態)。状態は STATUS_OK、STATUS_NOT_FOUND（備品が無い）、
    STATUS_ALREADY_LENT（貸出中）、STATUS_INVALID（借りる社員が無い。エラーの辞書に文言）。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone() is None:
            conn.execute("ROLLBACK")
            return {}, STATUS_NOT_FOUND
        if conn.execute(
            "SELECT 1 FROM lendings WHERE equipment_number = ?", (equipment_number,)
        ).fetchone() is not None:
            conn.execute("ROLLBACK")
            return {}, STATUS_ALREADY_LENT
        if conn.execute(
            "SELECT 1 FROM accounts WHERE employee_number = ?", (employee_number,)
        ).fetchone() is None:
            conn.execute("ROLLBACK")
            return {"borrower": validation.MSG_BORROWER_REQUIRED}, STATUS_INVALID
        conn.execute(
            "INSERT INTO lendings (equipment_number, employee_number, lent_on) VALUES (?, ?, ?)",
            (equipment_number, employee_number, lent_on),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        # 主キーの衝突（同時の貸出）は、先の貸出が確定していた場合だけ起きる。貸出中として扱う
        conn.execute("ROLLBACK")
        return {}, STATUS_ALREADY_LENT
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}, STATUS_OK


def return_equipment(conn, equipment_number):
    """備品を返却する。貸出の行を消す（返却の記録は残さない）。

    備品の存在を確かめ、貸出の行を BEGIN IMMEDIATE の中で削除する。
    同時に来た返却は先の 1 件だけが行われ、後の返却は貸出の行が無いため STATUS_NOT_LENT になる。
    戻り値は状態。STATUS_OK、STATUS_NOT_FOUND（備品が無い）、STATUS_NOT_LENT（貸出中ではない）。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone() is None:
            conn.execute("ROLLBACK")
            return STATUS_NOT_FOUND
        cursor = conn.execute(
            "DELETE FROM lendings WHERE equipment_number = ?", (equipment_number,)
        )
        if cursor.rowcount == 0:
            conn.execute("ROLLBACK")
            return STATUS_NOT_LENT
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return STATUS_OK
