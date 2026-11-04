"""備品の業務処理（登録、取得、修正、削除）と貸出状況の一覧。

修正と削除は版番号（version）で同時更新を検出する。他の担当者が先に更新・削除していたら、
操作を行わず RuleViolation（画面全体のエラー）を出す。
"""

from .errors import RuleViolation

CONFLICT_MESSAGE = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
NUMBER_TAKEN_MESSAGE = "この管理番号は既に使われています"


def create_equipment(conn, equipment_number: str, name: str) -> None:
    """備品を登録する。管理番号が重複していれば RuleViolation（入力欄 equipment_number）。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone():
            raise RuleViolation(NUMBER_TAKEN_MESSAGE, field="equipment_number")
        conn.execute(
            "INSERT INTO equipment (equipment_number, name, version) VALUES (?, ?, 1)",
            (equipment_number, name),
        )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def get_equipment(conn, equipment_number: str):
    """管理番号で備品を 1 件返す。無ければ None。"""
    return conn.execute(
        "SELECT equipment_number, name, version FROM equipment WHERE equipment_number = ?",
        (equipment_number,),
    ).fetchone()


def update_equipment(conn, equipment_number: str, new_number: str, new_name: str, expected_version: int) -> None:
    """備品を修正する。版番号が一致しなければ CONFLICT（画面全体のエラー）。

    管理番号を変えるとき、貸出の記録も同じトランザクションで付け替える。版番号は 1 増やす。
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT version FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None or row["version"] != expected_version:
            raise RuleViolation(CONFLICT_MESSAGE, level="error")
        if new_number != equipment_number and conn.execute(
            "SELECT 1 FROM equipment WHERE equipment_number = ?", (new_number,)
        ).fetchone():
            raise RuleViolation(NUMBER_TAKEN_MESSAGE, field="equipment_number")
        conn.execute("PRAGMA defer_foreign_keys = ON")
        conn.execute(
            "UPDATE equipment SET equipment_number = ?, name = ?, version = version + 1 "
            "WHERE equipment_number = ?",
            (new_number, new_name, equipment_number),
        )
        if new_number != equipment_number:
            conn.execute(
                "UPDATE loans SET equipment_number = ? WHERE equipment_number = ?",
                (new_number, equipment_number),
            )
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def delete_equipment(conn, equipment_number: str, expected_version: int) -> None:
    """備品を削除する。版番号が一致しなければ CONFLICT、貸出中なら拒否する。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT version FROM equipment WHERE equipment_number = ?", (equipment_number,)
        ).fetchone()
        if row is None or row["version"] != expected_version:
            raise RuleViolation(CONFLICT_MESSAGE, level="error")
        if conn.execute(
            "SELECT 1 FROM loans WHERE equipment_number = ?", (equipment_number,)
        ).fetchone():
            raise RuleViolation("この備品は貸出中のため削除できません。先に返却を処理してください")
        conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (equipment_number,))
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def list_lending_status(conn) -> list:
    """全備品の貸出状況を管理番号の昇順で返す（管理番号、備品名、版番号、貸出日、借りている社員の名前）。

    貸出中でない備品は貸出日と名前が None。
    """
    return conn.execute(
        "SELECT e.equipment_number, e.name, e.version, l.lent_on, a.name AS borrower_name "
        "FROM equipment e "
        "LEFT JOIN loans l ON l.equipment_number = e.equipment_number "
        "LEFT JOIN accounts a ON a.employee_number = l.borrower_employee_number "
        "ORDER BY e.equipment_number"
    ).fetchall()
