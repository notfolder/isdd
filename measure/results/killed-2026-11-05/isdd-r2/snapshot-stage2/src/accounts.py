"""アカウントの登録と、ログインの照合。パスワードはハッシュで保存する。"""

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone

PBKDF2_ITERATIONS = 260000
PBKDF2_ALGORITHM = "pbkdf2_sha256"
MSG_EMPLOYEE_NUMBER_DUPLICATE = "この社員番号は既に登録されています"
ROLE_MANAGER = "manager"
ROLE_EMPLOYEE = "employee"


def hash_password(password):
    """パスワードを PBKDF2-HMAC-SHA256 でハッシュ化する。

    16 バイトの無作為の塩を使う。戻り値は「方式$反復回数$塩$ハッシュ」の文字列。
    """
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password, stored_hash):
    """平文のパスワードが保存されたハッシュと一致するかを、定数時間の比較で確かめる。"""
    try:
        algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != PBKDF2_ALGORITHM:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
    )
    return hmac.compare_digest(digest, bytes.fromhex(digest_hex))


def register_account(conn, employee_number, name, password):
    """アカウントを登録する。

    アカウントが 0 件のときは担当者、1 件以上なら社員にする。件数の確認と挿入は
    BEGIN IMMEDIATE の 1 つのトランザクションで行い、同時の登録でも担当者は 1 人だけになる。
    戻り値は (エラーの辞書, 割り当てた役割)。成功時はエラーの辞書が空で、役割は
    ROLE_MANAGER か ROLE_EMPLOYEE。失敗時は役割が None。
    """
    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        role = ROLE_MANAGER if count == 0 else ROLE_EMPLOYEE
        conn.execute(
            "INSERT INTO accounts (employee_number, name, password_hash, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (employee_number, name, password_hash, role, created_at),
        )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        return {"employee_number": MSG_EMPLOYEE_NUMBER_DUPLICATE}, None
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {}, role


def verify_login(conn, employee_number, password):
    """社員番号とパスワードが一致するかを確かめる。

    戻り値は True（一致）か False。どちらが違うかは区別しない。
    """
    row = conn.execute(
        "SELECT password_hash FROM accounts WHERE employee_number = ?", (employee_number,)
    ).fetchone()
    if row is None:
        return False
    return _verify_password(password, row["password_hash"])


def list_borrowers(conn):
    """借りる社員の選択肢に使うアカウントを、社員番号の昇順で返す。

    戻り値は社員番号（employee_number）と名前（name）を持つ辞書のリスト。
    """
    rows = conn.execute(
        "SELECT employee_number, name FROM accounts ORDER BY employee_number"
    ).fetchall()
    return [{"employee_number": row["employee_number"], "name": row["name"]} for row in rows]
