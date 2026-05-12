"""
備品管理・貸出管理アプリのFastAPIエントリポイント。

要件トレーサビリティ:
  要件ID: RQ-UI-WEB-GUI-USE
  設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
  要件概要: Web GUIで備品台帳統一と貸出状況確認を提供する。
  設計概要: Nginx配下の `/api/` にFastAPIを配置し、認証・備品管理・ユーザー管理・貸出返却APIを提供する。
  呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE, DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET, DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-UPDATE-USER-FT-UPDATE-USER, DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
  呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
import sqlite3
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
EXTERNAL_SRC_DIR_CANDIDATES = [
    APP_DIR.parent / "external" / "neon-postgres" / "src",
    APP_DIR.parent.parent / "external" / "neon-postgres" / "src",
    Path("/workspace/external/neon-postgres/src"),
]
for _external_src_dir in EXTERNAL_SRC_DIR_CANDIDATES:
    if _external_src_dir.exists():
        sys.path.insert(0, str(_external_src_dir))
        break

try:
    from department_reader import get_department_name_by_login_id
except Exception:  # pragma: no cover - 外部連携未設定時は未取得扱いで継続
    def get_department_name_by_login_id(_: str) -> str | None:
        return None

SESSIONS: dict[str, dict[str, str]] = {}

app = FastAPI(title="Asset Lending API")


def hash_password(plain_password: str) -> str:
    """
    平文パスワードをSHA-256でハッシュ化する。

    Args:
      plain_password: 平文パスワード。

    Returns:
      ハッシュ化された文字列。

    要件トレーサビリティ:
      要件ID: RQ-NF-PASSWORD-HASH-STORAGE
      設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
      要件概要: パスワードはハッシュ化して保存する。
      設計概要: パスワード更新時および初期登録時にハッシュを生成して永続化する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def open_connection() -> sqlite3.Connection:
    """
    SQLite接続を生成する。

    Returns:
      Rowアクセスを有効にしたSQLite接続。

    要件トレーサビリティ:
      要件ID: RQ-DT-USE-SQLITE-LOCAL-DB
      設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
      要件概要: アプリ内DBとしてSQLiteを利用する。
      設計概要: 全API処理からSQLiteへ統一接続する。
      呼び出し先設計ID: DS-SC-USE-SQLITE-LOCAL-DB-DT-USE-SQLITE-LOCAL-DB
      呼び出し元設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET, DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-UPDATE-USER-FT-UPDATE-USER, DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_seed_users(connection: sqlite3.Connection) -> None:
    """
    初期ユーザーを存在確認の上で作成する。

    Args:
      connection: SQLite接続。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-USER
      設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
      要件概要: ユーザー登録機能を提供し、貸出先選択に利用できるようにする。
      設計概要: 初期管理者と一般ユーザーを準備し、画面操作とE2Eの前提を成立させる。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    existing = connection.execute("SELECT login_id FROM user_master").fetchall()
    if existing:
        return

    connection.execute(
        """
        INSERT INTO user_master (login_id, display_name, role, password_hash)
        VALUES (?, ?, ?, ?)
        """,
        ("admin", "管理者", "管理者", hash_password("admin")),
    )
    connection.execute(
        """
        INSERT INTO user_master (login_id, display_name, role, password_hash)
        VALUES (?, ?, ?, ?)
        """,
        ("user1", "一般ユーザー1", "一般ユーザー", hash_password("user1")),
    )
    connection.commit()


def initialize_database() -> None:
    """
    アプリ起動時にDBスキーマを初期化する。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED-FOR-UNIFIED-LEDGER
      設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      要件概要: 単一台帳を維持するためにDBを利用する。
      設計概要: 起動時に必要テーブルと制約を作成し、永続化基盤を成立させる。
      呼び出し先設計ID: DS-SC-ASSET-MASTER-INTERNAL-DATA-DT-ASSET-MASTER-INTERNAL-DATA, DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA, DS-SC-ERROR-LOG-INTERNAL-DATA-DT-ERROR-LOG-INTERNAL-DATA, DS-SC-ASSET-NUMBER-UNIQUE-DT-ASSET-NUMBER-UNIQUE, DS-SC-LOGIN-ID-UNIQUE-DT-LOGIN-ID-UNIQUE, DS-SC-BORROWER-MUST-BE-REGISTERED-USER-DT-BORROWER-MUST-BE-REGISTERED-USER
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    with open_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_master (
                login_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('管理者', '一般ユーザー')),
                password_hash TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS asset_master (
                asset_number TEXT PRIMARY KEY,
                asset_name TEXT NOT NULL,
                loan_status TEXT NOT NULL CHECK (loan_status IN ('貸出可能', '貸出中')),
                borrower_login_id TEXT,
                loan_date TEXT,
                return_due_date TEXT,
                FOREIGN KEY (borrower_login_id) REFERENCES user_master(login_id)
            )
            """
        )
        asset_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(asset_master)").fetchall()
        }
        if "return_due_date" not in asset_columns:
            connection.execute("ALTER TABLE asset_master ADD COLUMN return_due_date TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reservation (
                reservation_id TEXT PRIMARY KEY,
                asset_number TEXT NOT NULL,
                reserver_login_id TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reservation_status TEXT NOT NULL CHECK (reservation_status IN ('予約中', '貸出済み')),
                created_at TEXT NOT NULL,
                FOREIGN KEY (asset_number) REFERENCES asset_master(asset_number),
                FOREIGN KEY (reserver_login_id) REFERENCES user_master(login_id),
                CHECK (date(start_date) <= date(end_date))
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS error_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                screen_name TEXT NOT NULL,
                error_message TEXT NOT NULL
            )
            """
        )
        connection.commit()
        ensure_seed_users(connection)


def log_application_error(screen_name: str, error_message: str) -> None:
    """
    例外内容をerror_logテーブルへ保存する。

    Args:
      screen_name: エラー発生画面名。
      error_message: エラーメッセージ。

    要件トレーサビリティ:
      要件ID: RQ-OP-ERROR-LOG-CAPTURE
      設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
      要件概要: エラーログを記録する。
      設計概要: 例外発生時に時刻・画面名・エラー内容をerror_logへ保存する。
      呼び出し先設計ID: DS-SC-ERROR-LOG-INTERNAL-DATA-DT-ERROR-LOG-INTERNAL-DATA
      呼び出し元設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET, DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-UPDATE-USER-FT-UPDATE-USER, DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    with open_connection() as connection:
        connection.execute(
            """
            INSERT INTO error_log (occurred_at, screen_name, error_message)
            VALUES (?, ?, ?)
            """,
            (datetime.utcnow().isoformat(), screen_name, error_message),
        )
        connection.commit()


async def parse_json_body(request: Request) -> dict[str, Any]:
    """
    JSONボディを辞書として取得する。

    Args:
      request: FastAPIリクエスト。

    Returns:
      JSON辞書。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-ASSET
      設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      要件概要: 登録系機能は必要入力を受け付ける。
      設計概要: API入力を共通処理で取得し、バリデーションへ渡す。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET, DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-UPDATE-USER-FT-UPDATE-USER, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON形式が不正です")
    return body


def extract_token(authorization: str | None) -> str:
    """
    AuthorizationヘッダーからBearerトークンを抽出する。

    Args:
      authorization: Authorizationヘッダー。

    Returns:
      抽出したトークン。

    要件トレーサビリティ:
      要件ID: RQ-FT-AUTHENTICATE-USER
      設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      要件概要: ID/パスワード認証を行う。
      設計概要: 認証済みトークンを受け取り、API認可処理へ渡す。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
    """

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="認証情報が不足しています")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="トークンが不正です")
    return token


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, str]:
    """
    Authorizationヘッダーから現在ユーザー情報を取得する。

    Args:
      authorization: Authorizationヘッダー。

    Returns:
      `login_id`, `role` を含む辞書。

    要件トレーサビリティ:
      要件ID: RQ-FT-AUTHENTICATE-USER
      設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      要件概要: 認証済み利用者のみ機能を利用できる。
      設計概要: API毎に認証コンテキストを解決し、未認証アクセスを拒否する。
      呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      呼び出し元設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE, DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST, DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
    """

    token = extract_token(authorization)
    context = SESSIONS.get(token)
    if context is None:
        raise HTTPException(status_code=401, detail="セッションが無効です")
    return context


def require_admin(user_context: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
    """
    管理者権限を要求する。

    Args:
      user_context: 認証済みユーザー情報。

    Returns:
      管理者ユーザー情報。

    要件トレーサビリティ:
      要件ID: RQ-FT-AUTHORIZE-BY-ROLE
      設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
      要件概要: 管理者と一般ユーザーで操作権限を分離する。
      設計概要: 管理者専用APIに共通ガードを適用し、非管理者を拒否する。
      呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      呼び出し元設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET, DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN, DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-UPDATE-USER-FT-UPDATE-USER, DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    if user_context.get("role") != "管理者":
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return user_context


def fetch_asset_row(connection: sqlite3.Connection, asset_number: str) -> sqlite3.Row | None:
    """
    資産管理番号で備品レコードを取得する。

    Args:
      connection: SQLite接続。
      asset_number: 資産管理番号。

    Returns:
      備品レコード。存在しない場合はNone。

    要件トレーサビリティ:
      要件ID: RQ-DT-ASSET-ENTITY
      設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
      要件概要: 備品エンティティを台帳として管理する。
      設計概要: 備品更新・削除・貸出返却前に対象備品の存在と状態を参照する。
      呼び出し先設計ID: DS-SC-ASSET-ENTITY-DT-ASSET-ENTITY
      呼び出し元設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET, DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-REGISTER-RETURN-CLEAR-CURRENT-LOAN-FT-REGISTER-RETURN-CLEAR-CURRENT-LOAN
    """

    return connection.execute(
        "SELECT * FROM asset_master WHERE asset_number = ?",
        (asset_number,),
    ).fetchone()


def fetch_user_row(connection: sqlite3.Connection, login_id: str) -> sqlite3.Row | None:
    """
    ログインIDでユーザーレコードを取得する。

    Args:
      connection: SQLite接続。
      login_id: ログインID。

    Returns:
      ユーザーレコード。存在しない場合はNone。

    要件トレーサビリティ:
      要件ID: RQ-DT-USER-ENTITY
      設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      要件概要: ユーザーエンティティを認証・貸出先管理に利用する。
      設計概要: ログイン処理と貸出先検証の前提としてユーザー存在を確認する。
      呼び出し先設計ID: DS-SC-USER-ENTITY-DT-USER-ENTITY
      呼び出し元設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-REGISTER-LOAN-FT-REGISTER-LOAN, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
    """

    return connection.execute(
        "SELECT * FROM user_master WHERE login_id = ?",
        (login_id,),
    ).fetchone()


def parse_iso_date(value: str, field_name: str) -> date:
    """
    YYYY-MM-DD 形式の日付文字列を検証して date へ変換する。

    Args:
      value: 日付文字列。
      field_name: 入力項目名。

    Returns:
      変換済みの日付。

    Raises:
      HTTPException: 日付形式が不正な場合。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
      設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
      要件概要: 貸出時に貸出日と返却予定日を正しい日付で受け付ける。
      設計概要: 日付入力の共通検証を行い、形式不正を一律で拒否する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE, DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
    """

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name}はYYYY-MM-DD形式で入力してください",
        ) from exc


def is_period_overlapped(
    left_start: date,
    left_end: date,
    right_start: date,
    right_end: date,
) -> bool:
    """
    2つの期間が両端含みで重複するかを判定する。

    Args:
      left_start: 期間1開始日。
      left_end: 期間1終了日。
      right_start: 期間2開始日。
      right_end: 期間2終了日。

    Returns:
      重複する場合はTrue。

    要件トレーサビリティ:
      要件ID: RQ-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP
      設計ID: DS-FN-VALIDATE-RESERVATION-PERIOD-OVERLAP-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP
      要件概要: 予約期間の重複を両端含みで判定して拒否する。
      設計概要: 同一判定ロジックを共通化し、予約登録と貸出判定で再利用する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION, DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
    """

    return left_start <= right_end and right_start <= left_end


def find_overlapping_active_reservations(
    connection: sqlite3.Connection,
    asset_number: str,
    start_date_value: date,
    end_date_value: date,
) -> list[sqlite3.Row]:
    """
    指定期間に重複する予約中レコードを取得する。

    Args:
      connection: SQLite接続。
      asset_number: 資産管理番号。
      start_date_value: 判定開始日。
      end_date_value: 判定終了日。

    Returns:
      重複する予約中レコード一覧。

    要件トレーサビリティ:
      要件ID: RQ-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP
      設計ID: DS-FN-VALIDATE-RESERVATION-PERIOD-OVERLAP-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP
      要件概要: 同一備品で期間重複する予約を受け付けない。
      設計概要: 予約中レコードを対象に両端含み条件で重複を抽出する。
      呼び出し先設計ID: DS-SC-RESERVATION-NO-OVERLAP-INCLUSIVE-DT-RESERVATION-NO-OVERLAP-INCLUSIVE
      呼び出し元設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION, DS-FN-ENFORCE-RESERVATION-OWNER-LOAN-FT-ENFORCE-RESERVATION-OWNER-LOAN
    """

    return connection.execute(
        """
        SELECT reservation_id, reserver_login_id, start_date, end_date
        FROM reservation
        WHERE asset_number = ?
          AND reservation_status = '予約中'
          AND date(start_date) <= date(?)
          AND date(end_date) >= date(?)
        ORDER BY start_date ASC, reservation_id ASC
        """,
        (asset_number, end_date_value.isoformat(), start_date_value.isoformat()),
    ).fetchall()


def resolve_department_name(login_id: str) -> tuple[str, str]:
    """
    ログインIDから部署名と表示状態を解決する。

    Args:
      login_id: ログインID。

    Returns:
      (部署名, 表示状態) のタプル。

    要件トレーサビリティ:
      要件ID: RQ-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      要件概要: 部署名の取得結果を表示状態付きで扱えるようにする。
      設計概要: 取得成功時は部署名、失敗時は部署名不明として返す。
      呼び出し先設計ID: DS-IF-CONNECT-EXTERNAL-DEPARTMENT-DB-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
      呼び出し元設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT, DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
    """

    if not login_id:
        return "", ""

    try:
        department_name = get_department_name_by_login_id(login_id)
    except Exception:
        department_name = None

    if department_name:
        return department_name, "部署名"
    return "", "部署名不明"


@app.post("/api/departments/resolve")
async def resolve_departments(
    request: Request,
    _: dict[str, str] = Depends(get_current_user),
) -> dict[str, list[dict[str, str]]]:
    """
    複数ログインIDの部署名表示状態を取得する。

    Args:
      request: FastAPIリクエスト。
      _: 認証済みユーザー情報。

    Returns:
      login_idごとの部署名と表示状態一覧。

    要件トレーサビリティ:
      要件ID: RQ-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      要件概要: 一覧表示後に部署名を非同期解決し、取得中/成功/不明をクライアントで遷移表示できること。
      設計概要: login_id配列を受け取り、各IDの部署名表示状態をまとめて返却する。
      呼び出し先設計ID: DS-IF-CONNECT-EXTERNAL-DEPARTMENT-DB-EX-CONNECT-EXTERNAL-DEPARTMENT-DB, DS-MD-READ-ONLY-EXTERNAL-DEPARTMENT-DB-EX-READ-ONLY-EXTERNAL-DEPARTMENT-DB
      呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN, DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
    """

    try:
        body = await parse_json_body(request)
        raw_login_ids = body.get("login_ids")
        if not isinstance(raw_login_ids, list):
            raise HTTPException(status_code=400, detail="login_idsは配列で指定してください")

        login_ids = []
        seen_ids: set[str] = set()
        for value in raw_login_ids:
            login_id = str(value).strip()
            if not login_id or login_id in seen_ids:
                continue
            seen_ids.add(login_id)
            login_ids.append(login_id)

        async def _resolve_single_department(login_id: str) -> dict[str, str]:
            """
            単一ログインIDの部署名をスレッドで解決する。

            Args:
              login_id: ログインID。

            Returns:
              部署名解決結果。

            要件トレーサビリティ:
              要件ID: RQ-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
              設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
              要件概要: UI応答を阻害せず部署名解決を継続できること。
              設計概要: 外部DB参照をスレッドへ退避し、イベントループをブロックしない。
              呼び出し先設計ID: DS-IF-CONNECT-EXTERNAL-DEPARTMENT-DB-EX-CONNECT-EXTERNAL-DEPARTMENT-DB
              呼び出し元設計ID: DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
            """

            department_name, department_display_status = await asyncio.to_thread(
                resolve_department_name,
                login_id,
            )
            return {
                "login_id": login_id,
                "department_name": department_name,
                "department_display_status": department_display_status,
            }

        items = await asyncio.gather(
            *[_resolve_single_department(login_id) for login_id in login_ids]
        )
        return {"items": items}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="部署名取得に失敗しました")


@app.on_event("startup")
def on_startup() -> None:
    """
    アプリ起動時にDB初期化を実行する。

    要件トレーサビリティ:
      要件ID: RQ-DT-DB-REQUIRED-FOR-UNIFIED-LEDGER
      設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      要件概要: 台帳維持のためにDBを常時利用可能にする。
      設計概要: 起動時にスキーマ生成を自動実行し、初期状態を保証する。
      呼び出し先設計ID: DS-SC-DB-REQUIRED-FOR-UNIFIED-LEDGER-DT-DB-REQUIRED-FOR-UNIFIED-LEDGER
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    initialize_database()


@app.get("/api/health")
def health() -> dict[str, str]:
    """
    ヘルスチェック応答を返却する。

    Returns:
      稼働状態を示す辞書。

    要件トレーサビリティ:
      要件ID: RQ-NF-CONCURRENT-USERS-10
      設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
      要件概要: 同時利用前提でシステムが安定動作することを確認する。
      設計概要: E2Eと運用起動確認で利用する最小ヘルスエンドポイントを提供する。
      呼び出し先設計ID: なし
      呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
    """

    return {"status": "ok"}


@app.post("/api/auth/login")
async def login(request: Request) -> dict[str, str]:
    """
    ログイン認証を実行してセッショントークンを返却する。

    Args:
      request: FastAPIリクエスト。

    Returns:
      トークン、ログインID、表示名、ロール。

    要件トレーサビリティ:
      要件ID: RQ-FT-AUTHENTICATE-USER
      設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
      要件概要: ID/パスワードで認証し、未認証利用を防止する。
      設計概要: ログインIDとパスワードを照合し、成功時にトークンを発行する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
    """

    try:
        body = await parse_json_body(request)
        login_id = str(body.get("login_id", "")).strip()
        password = str(body.get("password", "")).strip()
        if not login_id or not password:
            raise HTTPException(status_code=400, detail="ログインIDとパスワードは必須です")

        with open_connection() as connection:
            user_row = fetch_user_row(connection, login_id)
            if user_row is None:
                raise HTTPException(status_code=401, detail="認証に失敗しました")

            if user_row["password_hash"] != hash_password(password):
                raise HTTPException(status_code=401, detail="認証に失敗しました")

        token = secrets.token_hex(24)
        SESSIONS[token] = {"login_id": user_row["login_id"], "role": user_row["role"]}
        return {
            "token": token,
            "login_id": user_row["login_id"],
            "display_name": user_row["display_name"],
            "role": user_row["role"],
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - 例外経路はE2Eで検証
        log_application_error("ログイン画面", str(exc))
        raise HTTPException(status_code=500, detail="システムエラーが発生しました")


@app.get("/api/assets")
def list_assets(_: dict[str, str] = Depends(get_current_user)) -> dict[str, list[dict[str, Any]]]:
    """
    備品一覧を資産管理番号昇順で取得する。

    Args:
      _: 認証済みユーザー情報。

    Returns:
      備品一覧。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
      設計ID: DS-FN-VIEW-ASSET-LIST-WITH-DEPARTMENT-FT-VIEW-ASSET-LIST-WITH-DEPARTMENT
      要件概要: 備品一覧に借用者部署名と予約導線を表示できるようにする。
      設計概要: 備品一覧へ返却予定日と借用者部署名の表示状態を付与して返却する。
      呼び出し先設計ID: DS-SC-ASSET-MASTER-INTERNAL-DATA-WITH-RETURN-DUE-DATE-DT-ASSET-MASTER-INTERNAL-DATA-WITH-RETURN-DUE-DATE, DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA, DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
    """

    try:
        with open_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    a.asset_number,
                    a.asset_name,
                    a.loan_status,
                    a.borrower_login_id,
                    a.loan_date,
                    a.return_due_date,
                    COALESCE(u.display_name, '') AS borrower_name
                FROM asset_master a
                LEFT JOIN user_master u ON a.borrower_login_id = u.login_id
                ORDER BY a.asset_number ASC
                """
            ).fetchall()

        assets = []
        for row in rows:
            borrower_login_id = row["borrower_login_id"] or ""
            assets.append(
                {
                    "asset_number": row["asset_number"],
                    "asset_name": row["asset_name"],
                    "loan_status": row["loan_status"],
                    "borrower_login_id": borrower_login_id,
                    "borrower_name": row["borrower_name"] or "",
                    "loan_date": row["loan_date"] or "",
                    "return_due_date": row["return_due_date"] or "",
                    "borrower_department_name": "",
                    "borrower_department_display_status": (
                        "取得しています..." if borrower_login_id else ""
                    ),
                }
            )
        return {"items": assets}
    except Exception as exc:  # pragma: no cover - 例外経路はE2Eで検証
        log_application_error("備品一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="一覧取得に失敗しました")


@app.post("/api/assets")
async def create_asset(
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    備品を登録する。

    Args:
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      登録結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-ASSET
      設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
      要件概要: 管理者が備品を新規登録できる。
      設計概要: 資産番号重複を禁止し、初期状態を貸出可能として登録する。
      呼び出し先設計ID: DS-SC-ASSET-NUMBER-UNIQUE-DT-ASSET-NUMBER-UNIQUE, DS-SC-ASSET-MASTER-INTERNAL-DATA-DT-ASSET-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
    """

    try:
        body = await parse_json_body(request)
        asset_number = str(body.get("asset_number", "")).strip()
        asset_name = str(body.get("asset_name", "")).strip()
        if not asset_number or not asset_name:
            raise HTTPException(status_code=400, detail="資産管理番号と備品名は必須です")

        with open_connection() as connection:
            exists = fetch_asset_row(connection, asset_number)
            if exists is not None:
                raise HTTPException(status_code=409, detail="資産管理番号が重複しています")

            connection.execute(
                """
                INSERT INTO asset_master (asset_number, asset_name, loan_status, borrower_login_id, loan_date, return_due_date)
                VALUES (?, ?, '貸出可能', NULL, NULL, NULL)
                """,
                (asset_number, asset_name),
            )
            connection.commit()
        return {"result": "created"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品登録画面", str(exc))
        raise HTTPException(status_code=500, detail="備品登録に失敗しました")


@app.put("/api/assets/{asset_number}")
async def update_asset(
    asset_number: str,
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    備品名を更新する。

    Args:
      asset_number: 資産管理番号。
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      更新結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-UPDATE-ASSET
      設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
      要件概要: 管理者が備品情報を更新できる。
      設計概要: 対象備品の存在確認後に備品名を更新する。
      呼び出し先設計ID: DS-SC-ASSET-MASTER-INTERNAL-DATA-DT-ASSET-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
    """

    try:
        body = await parse_json_body(request)
        asset_name = str(body.get("asset_name", "")).strip()
        if not asset_name:
            raise HTTPException(status_code=400, detail="備品名は必須です")

        with open_connection() as connection:
            target = fetch_asset_row(connection, asset_number)
            if target is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")

            connection.execute(
                "UPDATE asset_master SET asset_name = ? WHERE asset_number = ?",
                (asset_name, asset_number),
            )
            connection.commit()
        return {"result": "updated"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品編集画面", str(exc))
        raise HTTPException(status_code=500, detail="備品更新に失敗しました")


@app.delete("/api/assets/{asset_number}")
def delete_asset(
    asset_number: str,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    備品を削除する。

    Args:
      asset_number: 資産管理番号。
      _: 管理者情報。

    Returns:
      削除結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-ASSET-WITH-LOAN-CHECK
      設計ID: DS-FN-DELETE-ASSET-WITH-LOAN-CHECK-FT-DELETE-ASSET-WITH-LOAN-CHECK
      要件概要: 貸出中備品は削除不可とする。
      設計概要: 状態確認で貸出中を拒否し、貸出可能時のみ削除する。
      呼び出し先設計ID: DS-SC-ASSET-MASTER-INTERNAL-DATA-DT-ASSET-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
    """

    try:
        with open_connection() as connection:
            target = fetch_asset_row(connection, asset_number)
            if target is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")
            if target["loan_status"] == "貸出中":
                raise HTTPException(status_code=409, detail="貸出中の備品は削除できません")

            connection.execute(
                "DELETE FROM asset_master WHERE asset_number = ?",
                (asset_number,),
            )
            connection.commit()
        return {"result": "deleted"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="備品削除に失敗しました")


@app.post("/api/assets/{asset_number}/loan")
async def register_loan(
    asset_number: str,
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    備品の貸出登録を行う。

    Args:
      asset_number: 資産管理番号。
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      貸出登録結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
      設計ID: DS-FN-REGISTER-LOAN-WITH-RETURN-DUE-DATE-FT-REGISTER-LOAN-WITH-RETURN-DUE-DATE
      要件概要: 貸出登録時に返却予定日を必須化し、予約ルールと整合させる。
      設計概要: 貸出条件と予約者優先制御を検証し、貸出更新と予約状態遷移を同一処理で実行する。
      呼び出し先設計ID: DS-SC-RETURN-DUE-DATE-REQUIRED-WHEN-LOANED-DT-RETURN-DUE-DATE-REQUIRED-WHEN-LOANED, DS-SC-BORROWER-MUST-BE-REGISTERED-USER-DT-BORROWER-MUST-BE-REGISTERED-USER, DS-FN-ENFORCE-RESERVATION-OWNER-LOAN-FT-ENFORCE-RESERVATION-OWNER-LOAN, DS-FN-TRANSITION-RESERVATION-TO-LOANED-FT-TRANSITION-RESERVATION-TO-LOANED
      呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
    """

    try:
        body = await parse_json_body(request)
        borrower_login_id = str(body.get("borrower_login_id", "")).strip()
        loan_date = str(body.get("loan_date", "")).strip()
        return_due_date = str(body.get("return_due_date", "")).strip()
        if not borrower_login_id or not loan_date or not return_due_date:
            raise HTTPException(status_code=400, detail="借用者・貸出日・返却予定日は必須です")

        loan_date_value = parse_iso_date(loan_date, "貸出日")
        return_due_date_value = parse_iso_date(return_due_date, "返却予定日")
        if return_due_date_value < loan_date_value:
            raise HTTPException(status_code=400, detail="返却予定日は貸出日以降で入力してください")

        with open_connection() as connection:
            target = fetch_asset_row(connection, asset_number)
            if target is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")
            if target["loan_status"] != "貸出可能":
                raise HTTPException(status_code=409, detail="貸出可能な備品のみ貸出できます")

            borrower = fetch_user_row(connection, borrower_login_id)
            if borrower is None:
                raise HTTPException(status_code=404, detail="借用者ユーザーが見つかりません")

            overlapping_reservations = find_overlapping_active_reservations(
                connection,
                asset_number,
                loan_date_value,
                return_due_date_value,
            )
            for reservation in overlapping_reservations:
                if reservation["reserver_login_id"] != borrower_login_id:
                    raise HTTPException(
                        status_code=409,
                        detail="重複予約があるため予約者本人のみ貸出できます",
                    )

            connection.execute(
                """
                UPDATE asset_master
                SET loan_status = '貸出中', borrower_login_id = ?, loan_date = ?, return_due_date = ?
                WHERE asset_number = ?
                """,
                (borrower_login_id, loan_date, return_due_date, asset_number),
            )
            connection.execute(
                """
                UPDATE reservation
                SET reservation_status = '貸出済み'
                WHERE asset_number = ?
                  AND reserver_login_id = ?
                  AND reservation_status = '予約中'
                  AND date(start_date) <= date(?)
                  AND date(end_date) >= date(?)
                """,
                (
                    asset_number,
                    borrower_login_id,
                    return_due_date_value.isoformat(),
                    loan_date_value.isoformat(),
                ),
            )
            connection.commit()
        return {"result": "loan_registered"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="貸出登録に失敗しました")


@app.post("/api/assets/{asset_number}/return")
def register_return(
    asset_number: str,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    備品の返却登録を行う。

    Args:
      asset_number: 資産管理番号。
      _: 管理者情報。

    Returns:
      返却登録結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-LOANED-RESERVATION-ON-RETURN
      設計ID: DS-FN-DELETE-LOANED-RESERVATION-ON-RETURN-FT-DELETE-LOANED-RESERVATION-ON-RETURN
      要件概要: 返却時に同一備品の貸出済み予約のみ削除する。
      設計概要: 返却更新と同時に貸出済み予約を物理削除し、他予約は保持する。
      呼び出し先設計ID: DS-SC-DELETE-LOANED-RESERVATION-ON-RETURN-DT-DELETE-LOANED-RESERVATION-ON-RETURN, DS-SC-CURRENT-LOAN-NO-HISTORY-RETENTION-DT-CURRENT-LOAN-NO-HISTORY-RETENTION
      呼び出し元設計ID: DS-IF-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN-UI-ASSET-LIST-WITH-RESERVATION-BUTTON-SCREEN
    """

    try:
        with open_connection() as connection:
            target = fetch_asset_row(connection, asset_number)
            if target is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")
            if target["loan_status"] != "貸出中":
                raise HTTPException(status_code=409, detail="貸出中の備品のみ返却できます")

            connection.execute(
                """
                UPDATE asset_master
                SET loan_status = '貸出可能', borrower_login_id = NULL, loan_date = NULL, return_due_date = NULL
                WHERE asset_number = ?
                """,
                (asset_number,),
            )
            connection.execute(
                """
                DELETE FROM reservation
                WHERE asset_number = ?
                  AND reservation_status = '貸出済み'
                """,
                (asset_number,),
            )
            connection.commit()
        return {"result": "return_registered"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="返却登録に失敗しました")


@app.get("/api/assets/{asset_number}/reservations")
def list_reservations(
    asset_number: str,
    year_month: str = Query(default="", pattern=r"^$|^\d{4}-\d{2}$"),
    _: dict[str, str] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    指定備品の予約カレンダー情報を月次で取得する。

    Args:
      asset_number: 資産管理番号。
      year_month: 取得対象月（YYYY-MM）。空の場合は当月。
      _: 認証済みユーザー情報。

    Returns:
      対象月と予約一覧。

    要件トレーサビリティ:
      要件ID: RQ-FT-VIEW-ASSET-RESERVATION-CALENDAR
      設計ID: DS-FN-VIEW-ASSET-RESERVATION-CALENDAR-FT-VIEW-ASSET-RESERVATION-CALENDAR
      要件概要: 備品ごとの予約期間・予約者・部署名・状態を月次で参照できる。
      設計概要: 対象月と重なる予約を取得し、部署名表示状態を付与して返却する。
      呼び出し先設計ID: DS-SC-RESERVATION-INTERNAL-DATA-DT-RESERVATION-INTERNAL-DATA, DS-FN-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE-FT-DISPLAY-DEPARTMENT-NAME-ASYNC-STATE
      呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
    """

    try:
        if year_month:
            month_start = datetime.strptime(f"{year_month}-01", "%Y-%m-%d").date()
        else:
            today = date.today()
            month_start = date(today.year, today.month, 1)

        if month_start.month == 12:
            next_month_start = date(month_start.year + 1, 1, 1)
        else:
            next_month_start = date(month_start.year, month_start.month + 1, 1)
        month_end = next_month_start - timedelta(days=1)

        with open_connection() as connection:
            asset_row = fetch_asset_row(connection, asset_number)
            if asset_row is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")

            rows = connection.execute(
                """
                SELECT r.reservation_id, r.asset_number, r.reserver_login_id, r.start_date, r.end_date,
                       r.reservation_status, COALESCE(u.display_name, '') AS reserver_name
                FROM reservation r
                LEFT JOIN user_master u ON r.reserver_login_id = u.login_id
                WHERE r.asset_number = ?
                  AND date(r.start_date) <= date(?)
                  AND date(r.end_date) >= date(?)
                ORDER BY r.start_date ASC, r.reservation_id ASC
                """,
                (asset_number, month_end.isoformat(), month_start.isoformat()),
            ).fetchall()

        items = []
        for row in rows:
            items.append(
                {
                    "reservation_id": row["reservation_id"],
                    "asset_number": row["asset_number"],
                    "reserver_login_id": row["reserver_login_id"],
                    "reserver_name": row["reserver_name"] or "",
                    "reserver_department_name": "",
                    "reserver_department_display_status": "取得しています...",
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "reservation_status": row["reservation_status"],
                }
            )

        return {
            "asset_number": asset_number,
            "year_month": month_start.strftime("%Y-%m"),
            "items": items,
        }
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=400, detail="year_monthはYYYY-MM形式で入力してください")
    except Exception as exc:  # pragma: no cover
        log_application_error("備品予約カレンダー画面", str(exc))
        raise HTTPException(status_code=500, detail="予約カレンダー取得に失敗しました")


@app.post("/api/assets/{asset_number}/reservations")
async def register_reservation(
    asset_number: str,
    request: Request,
    user_context: dict[str, str] = Depends(get_current_user),
) -> dict[str, str]:
    """
    指定備品に期間指定の予約を登録する。

    Args:
      asset_number: 資産管理番号。
      request: FastAPIリクエスト。
      user_context: 認証済みユーザー情報。

    Returns:
      予約登録結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-RESERVATION
      設計ID: DS-FN-REGISTER-RESERVATION-FT-REGISTER-RESERVATION
      要件概要: 管理者と一般ユーザーが本人予約を期間指定で登録できる。
      設計概要: 本人予約・日付整合・重複判定・返却予定日欠落判定を通過した場合のみ登録する。
      呼び出し先設計ID: DS-FN-VALIDATE-RESERVATION-PERIOD-OVERLAP-FT-VALIDATE-RESERVATION-PERIOD-OVERLAP, DS-FN-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING-FT-REJECT-RESERVATION-WHEN-RETURN-DUE-DATE-MISSING, DS-SC-RESERVATION-INTERNAL-DATA-DT-RESERVATION-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
    """

    try:
        body = await parse_json_body(request)
        reserver_login_id = str(body.get("reserver_login_id", "")).strip()
        start_date = str(body.get("start_date", "")).strip()
        end_date = str(body.get("end_date", "")).strip()
        if not reserver_login_id or not start_date or not end_date:
            raise HTTPException(status_code=400, detail="予約者・開始日・終了日は必須です")

        if reserver_login_id != user_context["login_id"]:
            raise HTTPException(status_code=403, detail="予約者本人のみ登録できます")

        start_date_value = parse_iso_date(start_date, "予約開始日")
        end_date_value = parse_iso_date(end_date, "予約終了日")
        if end_date_value < start_date_value:
            raise HTTPException(status_code=400, detail="予約終了日は予約開始日以降で入力してください")
        if start_date_value < date.today():
            raise HTTPException(status_code=400, detail="予約開始日は当日以降で入力してください")

        with open_connection() as connection:
            asset_row = fetch_asset_row(connection, asset_number)
            if asset_row is None:
                raise HTTPException(status_code=404, detail="備品が見つかりません")

            if asset_row["loan_status"] == "貸出中" and not (asset_row["return_due_date"] or ""):
                raise HTTPException(
                    status_code=409,
                    detail="貸出中で返却予定日未設定のため予約できません",
                )

            overlapping_reservations = find_overlapping_active_reservations(
                connection,
                asset_number,
                start_date_value,
                end_date_value,
            )
            if overlapping_reservations:
                raise HTTPException(status_code=409, detail="期間が重複しています")

            if asset_row["loan_status"] == "貸出中":
                loan_start_date = parse_iso_date(asset_row["loan_date"], "貸出日")
                loan_end_date = parse_iso_date(asset_row["return_due_date"], "返却予定日")
                if is_period_overlapped(
                    start_date_value,
                    end_date_value,
                    loan_start_date,
                    loan_end_date,
                ):
                    raise HTTPException(status_code=409, detail="期間が重複しています")

            reservation_id = f"R{uuid.uuid4().hex[:12].upper()}"
            connection.execute(
                """
                INSERT INTO reservation (
                    reservation_id,
                    asset_number,
                    reserver_login_id,
                    start_date,
                    end_date,
                    reservation_status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, '予約中', ?)
                """,
                (
                    reservation_id,
                    asset_number,
                    reserver_login_id,
                    start_date_value.isoformat(),
                    end_date_value.isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
            connection.commit()
        return {"result": "reservation_registered"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品予約カレンダー画面", str(exc))
        raise HTTPException(status_code=500, detail="予約登録に失敗しました")


@app.delete("/api/reservations/{reservation_id}")
def cancel_reservation(
    reservation_id: str,
    user_context: dict[str, str] = Depends(get_current_user),
) -> dict[str, str]:
    """
    予約IDを指定して予約を取り消す。

    Args:
      reservation_id: 予約ID。
      user_context: 認証済みユーザー情報。

    Returns:
      予約取消結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-CANCEL-RESERVATION
      設計ID: DS-FN-CANCEL-RESERVATION-FT-CANCEL-RESERVATION
      要件概要: 予約者本人または管理者が予約を取り消せる。
      設計概要: 権限判定後に対象予約を物理削除する。
      呼び出し先設計ID: DS-SC-RESERVATION-DATA-RETENTION-UNTIL-RETURN-OR-CANCEL-DT-RESERVATION-DATA-RETENTION-UNTIL-RETURN-OR-CANCEL
      呼び出し元設計ID: DS-IF-ASSET-RESERVATION-CALENDAR-SCREEN-UI-ASSET-RESERVATION-CALENDAR-SCREEN
    """

    try:
        with open_connection() as connection:
            target = connection.execute(
                """
                SELECT reservation_id, reserver_login_id
                FROM reservation
                WHERE reservation_id = ?
                """,
                (reservation_id,),
            ).fetchone()
            if target is None:
                raise HTTPException(status_code=404, detail="予約が見つかりません")

            is_admin = user_context.get("role") == "管理者"
            is_owner = target["reserver_login_id"] == user_context.get("login_id")
            if not is_admin and not is_owner:
                raise HTTPException(status_code=403, detail="予約取消の権限がありません")

            connection.execute(
                "DELETE FROM reservation WHERE reservation_id = ?",
                (reservation_id,),
            )
            connection.commit()
        return {"result": "reservation_cancelled"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("備品予約カレンダー画面", str(exc))
        raise HTTPException(status_code=500, detail="予約取消に失敗しました")


@app.get("/api/users")
def list_users(_: dict[str, str] = Depends(require_admin)) -> dict[str, list[dict[str, str]]]:
    """
    ユーザー一覧を取得する。

    Args:
      _: 管理者情報。

    Returns:
      ユーザー一覧。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-USER
      設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
      要件概要: ユーザー管理の基礎として登録対象一覧を扱う。
      設計概要: ユーザー一覧画面向けにログインID、表示名、権限を返却する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    try:
        with open_connection() as connection:
            rows = connection.execute(
                "SELECT login_id, display_name, role FROM user_master ORDER BY login_id ASC"
            ).fetchall()

        users = []
        for row in rows:
            users.append(
                {
                    "login_id": row["login_id"],
                    "display_name": row["display_name"],
                    "role": row["role"],
                }
            )
        return {"items": users}
    except Exception as exc:  # pragma: no cover
        log_application_error("ユーザー一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="ユーザー一覧取得に失敗しました")


@app.post("/api/users")
async def create_user(
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    ユーザーを登録する。

    Args:
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      登録結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-REGISTER-USER
      設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
      要件概要: 管理者がユーザーを手動登録できる。
      設計概要: ログインID重複を禁止し、初期PWをハッシュ化して保存する。
      呼び出し先設計ID: DS-SC-LOGIN-ID-UNIQUE-DT-LOGIN-ID-UNIQUE, DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    try:
        body = await parse_json_body(request)
        login_id = str(body.get("login_id", "")).strip()
        display_name = str(body.get("display_name", "")).strip()
        role = str(body.get("role", "")).strip()
        initial_password = str(body.get("initial_password", "")).strip()
        if not login_id or not display_name or not role or not initial_password:
            raise HTTPException(status_code=400, detail="入力項目が不足しています")
        if role not in {"管理者", "一般ユーザー"}:
            raise HTTPException(status_code=400, detail="権限が不正です")

        with open_connection() as connection:
            exists = fetch_user_row(connection, login_id)
            if exists is not None:
                raise HTTPException(status_code=409, detail="ログインIDが重複しています")

            connection.execute(
                """
                INSERT INTO user_master (login_id, display_name, role, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (login_id, display_name, role, hash_password(initial_password)),
            )
            connection.commit()
        return {"result": "created"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("ユーザー登録画面", str(exc))
        raise HTTPException(status_code=500, detail="ユーザー登録に失敗しました")


@app.put("/api/users/{login_id}")
async def update_user(
    login_id: str,
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    ユーザー情報を更新する。

    Args:
      login_id: 対象ログインID。
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      更新結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-UPDATE-USER
      設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
      要件概要: 管理者が表示名と権限を更新できる。
      設計概要: 対象ユーザーの存在確認後に表示名と権限を更新する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    try:
        body = await parse_json_body(request)
        display_name = str(body.get("display_name", "")).strip()
        role = str(body.get("role", "")).strip()
        if not display_name or not role:
            raise HTTPException(status_code=400, detail="入力項目が不足しています")
        if role not in {"管理者", "一般ユーザー"}:
            raise HTTPException(status_code=400, detail="権限が不正です")

        with open_connection() as connection:
            target = fetch_user_row(connection, login_id)
            if target is None:
                raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

            connection.execute(
                "UPDATE user_master SET display_name = ?, role = ? WHERE login_id = ?",
                (display_name, role, login_id),
            )
            connection.commit()
        return {"result": "updated"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("ユーザー編集画面", str(exc))
        raise HTTPException(status_code=500, detail="ユーザー更新に失敗しました")


@app.delete("/api/users/{login_id}")
def delete_user(
    login_id: str,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    ユーザーを削除する。

    Args:
      login_id: 対象ログインID。
      _: 管理者情報。

    Returns:
      削除結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-DELETE-USER-WITH-LOAN-CHECK
      設計ID: DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK
      要件概要: 貸出中保有ユーザーは削除不可とする。
      設計概要: 貸出保有レコードを検査し、保有なしの場合のみ削除する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA, DS-SC-CURRENT-LOAN-STATE-INTERNAL-DATA-DT-CURRENT-LOAN-STATE-INTERNAL-DATA
      呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    try:
        with open_connection() as connection:
            target = fetch_user_row(connection, login_id)
            if target is None:
                raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

            borrowing = connection.execute(
                """
                SELECT 1 FROM asset_master
                WHERE borrower_login_id = ? AND loan_status = '貸出中'
                LIMIT 1
                """,
                (login_id,),
            ).fetchone()
            if borrowing is not None:
                raise HTTPException(status_code=409, detail="貸出中備品を保有するユーザーは削除できません")

            connection.execute("DELETE FROM user_master WHERE login_id = ?", (login_id,))
            connection.commit()
        return {"result": "deleted"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("ユーザー一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="ユーザー削除に失敗しました")


@app.post("/api/users/me/password")
async def change_own_password(
    request: Request,
    user_context: dict[str, str] = Depends(get_current_user),
) -> dict[str, str]:
    """
    利用者自身のパスワードを変更する。

    Args:
      request: FastAPIリクエスト。
      user_context: 認証済みユーザー情報。

    Returns:
      変更結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-CHANGE-OWN-PASSWORD
      設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
      要件概要: 利用者自身がパスワードを変更できる。
      設計概要: 旧PW一致を確認して新PWへ更新する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA, DS-MD-PASSWORD-HASH-STORAGE-NF-PASSWORD-HASH-STORAGE
      呼び出し元設計ID: DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
    """

    try:
        body = await parse_json_body(request)
        old_password = str(body.get("old_password", "")).strip()
        new_password = str(body.get("new_password", "")).strip()
        if not old_password or not new_password:
            raise HTTPException(status_code=400, detail="現在PWと新しいPWは必須です")

        with open_connection() as connection:
            target = fetch_user_row(connection, user_context["login_id"])
            if target is None:
                raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
            if target["password_hash"] != hash_password(old_password):
                raise HTTPException(status_code=409, detail="現在PWが一致しません")

            connection.execute(
                "UPDATE user_master SET password_hash = ? WHERE login_id = ?",
                (hash_password(new_password), user_context["login_id"]),
            )
            connection.commit()
        return {"result": "password_changed"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("パスワード変更画面", str(exc))
        raise HTTPException(status_code=500, detail="パスワード変更に失敗しました")


@app.post("/api/users/{login_id}/reset-password")
async def reset_user_password(
    login_id: str,
    request: Request,
    _: dict[str, str] = Depends(require_admin),
) -> dict[str, str]:
    """
    管理者が指定ユーザーの初期パスワードを再設定する。

    Args:
      login_id: 対象ログインID。
      request: FastAPIリクエスト。
      _: 管理者情報。

    Returns:
      再設定結果。

    要件トレーサビリティ:
      要件ID: RQ-FT-RESET-USER-PASSWORD
      設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
      要件概要: 管理者が初期PW再設定を実行できる。
      設計概要: 対象ユーザーの存在確認後に指定初期PWをハッシュ保存する。
      呼び出し先設計ID: DS-SC-USER-MASTER-INTERNAL-DATA-DT-USER-MASTER-INTERNAL-DATA, DS-MD-PASSWORD-HASH-STORAGE-NF-PASSWORD-HASH-STORAGE
      呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
    """

    try:
        body = await parse_json_body(request)
        initial_password = str(body.get("initial_password", "")).strip()
        if not initial_password:
            raise HTTPException(status_code=400, detail="初期PWは必須です")

        with open_connection() as connection:
            target = fetch_user_row(connection, login_id)
            if target is None:
                raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

            connection.execute(
                "UPDATE user_master SET password_hash = ? WHERE login_id = ?",
                (hash_password(initial_password), login_id),
            )
            connection.commit()
        return {"result": "password_reset"}
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        log_application_error("ユーザー一覧画面", str(exc))
        raise HTTPException(status_code=500, detail="初期PW再設定に失敗しました")
