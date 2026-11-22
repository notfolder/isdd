"""台車の貸出の SQL。判定はここに書かない。"""

from app.core.db import get_db


def list_items(q=""):
    """物の一覧（番号の昇順）と、貸出中ならその貸出。q があれば番号か名前の一部で絞る。"""
    like = f"%{q}%"
    return get_db().execute(
        """
        SELECT i.code, i.name, l.employee_no AS borrower, l.lent_on, l.due_on
        FROM carts_items i
        LEFT JOIN carts_loans l ON l.item_code = i.code AND l.returned_on IS NULL
        WHERE i.code LIKE ? OR i.name LIKE ?
        ORDER BY i.code
        """,
        (like, like),
    ).fetchall()


def get_item(code):
    return get_db().execute("SELECT code, name FROM carts_items WHERE code = ?", (code,)).fetchone()


def insert_item(code, name):
    get_db().execute("INSERT INTO carts_items (code, name) VALUES (?, ?)", (code, name))


def update_item(code, name):
    get_db().execute("UPDATE carts_items SET name = ? WHERE code = ?", (name, code))


def delete_item(code):
    get_db().execute("DELETE FROM carts_items WHERE code = ?", (code,))


def find_active_employee(employee_no):
    """在籍している社員の行。退職者と存在しない番号は None。"""
    return get_db().execute(
        "SELECT employee_no, name FROM employees WHERE employee_no = ? AND status <> 'retired'",
        (employee_no,),
    ).fetchone()


def current_loan_of_item(code):
    """物の貸出中の記録。貸出中でなければ None。"""
    return get_db().execute(
        "SELECT * FROM carts_loans WHERE item_code = ? AND returned_on IS NULL", (code,)
    ).fetchone()


def open_loans_of_employee(employee_no):
    """社員が今持っている貸出の記録。"""
    return get_db().execute(
        "SELECT * FROM carts_loans WHERE employee_no = ? AND returned_on IS NULL", (employee_no,)
    ).fetchall()


def insert_loan(code, employee_no, lent_on, due_on):
    get_db().execute(
        "INSERT INTO carts_loans (item_code, employee_no, lent_on, due_on) VALUES (?, ?, ?, ?)",
        (code, employee_no, lent_on, due_on),
    )


def close_loan(loan_id, returned_on):
    get_db().execute("UPDATE carts_loans SET returned_on = ? WHERE id = ?", (returned_on, loan_id))


def history():
    """返却済みの貸出（新しい順）。物を削除していても名前を出せるよう、物は結合しない。"""
    return get_db().execute(
        """
        SELECT l.id, l.item_code, i.name AS item_name, l.employee_no, l.lent_on, l.due_on, l.returned_on
        FROM carts_loans l LEFT JOIN carts_items i ON i.code = l.item_code
        WHERE l.returned_on IS NOT NULL
        ORDER BY l.returned_on DESC, l.id DESC
        """
    ).fetchall()
