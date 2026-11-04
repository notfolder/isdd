"""HTTP の要求を受けて、業務ロジックと画面の部品を組み合わせる。

要求ごとに DB 接続を開き、Cookie の sid からログイン者を得て、
担当者の操作は業務ロジックを呼ぶ前に検査する。操作の結果の知らせは
flash という Cookie に入れ、次の画面表示で一度だけ出す。
"""

import re
import time
import traceback
from datetime import date, datetime, timedelta, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, quote, unquote, urlsplit

from app import accounts, equipment, lending, sessions, templates
from app.db import open_connection

SESSION_COOKIE = "sid"
FLASH_COOKIE = "flash"
JST = timezone(timedelta(hours=9))
MAX_BODY_BYTES = 64 * 1024
CONFLICT_TEXT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
MANAGER_ONLY_TEXT = "この操作は担当者だけが行えます"
EQUIPMENT_PATH = re.compile(r"/equipment/([0-9]+)/(edit|delete|lend|return)/")
ACCOUNT_PATH = re.compile(r"/accounts/([0-9]{6})/(role|password|delete)/")


def _today_jst() -> date:
    return datetime.now(JST).date()


def _to_int(raw: Optional[str]) -> int:
    try:
        return int(raw or "")
    except ValueError:
        return -1


class RequestHandler(BaseHTTPRequestHandler):
    """HTTP の要求を画面の処理へ振り分けて応答する。

    settings は起動時に __main__ が設定する（DB の場所とセッションの秒数）。
    """

    settings = None
    server_version = "EquipmentLedger/1.0"
    sys_version = ""

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        """アクセスログは出さない（運用要件でログは不要）。"""
        return

    def do_GET(self) -> None:
        """GET の要求を処理する。"""
        self._handle("GET")

    def do_POST(self) -> None:
        """POST の要求を処理する。"""
        self._handle("POST")

    def _handle(self, method: str) -> None:
        try:
            self._route(method)
        except Exception:
            traceback.print_exc()
            self._send(500, "<!doctype html><meta charset=utf-8><p>サーバーでエラーが起きました。</p>".encode("utf-8"))

    def _route(self, method: str) -> None:
        parts = urlsplit(self.path)
        path = parts.path
        query = parse_qs(parts.query, keep_blank_values=True)
        form = self._read_form() if method == "POST" else {}
        conn = open_connection(self.settings.db_path)
        try:
            user = self._current_user(conn)
            self._dispatch(conn, method, path, query, form, user)
        finally:
            conn.close()

    def _dispatch(self, conn, method, path, query, form, user) -> None:
        if path == "/" and method == "GET":
            return self.lending_status_screen(conn, user)
        if path == "/accounts/register/":
            if method == "POST":
                return self._post_register(conn, user, form)
            return self.register_account_screen(conn, user)
        if path == "/login/":
            if method == "POST":
                return self._post_login(conn, form)
            return self.login_screen(conn, user)
        if path == "/logout/" and method == "POST":
            return self._post_logout(conn)

        is_manager_path = path == "/accounts/" or path == "/equipment/new/" or bool(
            EQUIPMENT_PATH.fullmatch(path) or ACCOUNT_PATH.fullmatch(path)
        )
        if is_manager_path:
            denied = sessions.require_manager(user)
            if denied == "login":
                return self._redirect("/login/")
            if denied == "forbidden":
                return self._redirect("/", flash=("message", MANAGER_ONLY_TEXT))

        if path == "/accounts/" and method == "GET":
            return self.account_list_screen(conn, user, query.get("reset", [None])[0])
        if path == "/equipment/new/":
            if method == "POST":
                return self._post_equipment_create(conn, user, form)
            return self.equipment_form_screen(conn, user, None)

        match = EQUIPMENT_PATH.fullmatch(path)
        if match:
            equipment_id, action = int(match.group(1)), match.group(2)
            if action == "edit":
                if method == "POST":
                    return self._post_equipment_update(conn, user, form, equipment_id)
                return self.equipment_form_screen(conn, user, equipment_id)
            if action == "delete" and method == "POST":
                return self._post_equipment_delete(conn, form, equipment_id)
            if action == "lend":
                if method == "POST":
                    return self._post_lend(conn, user, form, equipment_id)
                return self.lending_form_screen(conn, user, equipment_id)
            if action == "return" and method == "POST":
                return self._post_return(conn, equipment_id)

        match = ACCOUNT_PATH.fullmatch(path)
        if match and method == "POST":
            employee_number, action = match.group(1), match.group(2)
            if action == "role":
                return self._post_role(conn, form, employee_number)
            if action == "password":
                return self._post_password(conn, form, employee_number)
            if action == "delete":
                return self._post_account_delete(conn, employee_number)

        self._send(404, "<!doctype html><meta charset=utf-8><p>ページが見つかりません。</p>".encode("utf-8"))

    # --- 画面 -------------------------------------------------

    def lending_status_screen(self, conn, user) -> None:
        """貸出状況の画面（トップ）を返す。誰でも見られる。"""
        self._render("lending_status", {"user": user, "rows": lending.list_lending_status(conn)})

    def register_account_screen(self, conn, user) -> None:
        """アカウント登録の画面を空の入力欄で返す。"""
        self._render("register_account", {"user": user, "values": {}, "errors": {}})

    def login_screen(self, conn, user) -> None:
        """ログインの画面を返す。"""
        self._render("login", {"user": user, "values": {}, "errors": {}})

    def equipment_form_screen(self, conn, user, equipment_id: Optional[int]) -> None:
        """備品の登録（新規）または修正（既存）の画面を返す。担当者だけが使える。"""
        if equipment_id is None:
            ctx = {"user": user, "heading": "備品の登録", "action": "/equipment/new/",
                   "values": {}, "errors": {}}
            return self._render("equipment_form", ctx)
        row = self._find_equipment(conn, equipment_id)
        if row is None:
            return self._redirect("/", flash=("error", CONFLICT_TEXT))
        ctx = {"user": user, "heading": "備品の修正", "action": f"/equipment/{equipment_id}/edit/",
               "values": {"equipment_number": row["equipment_number"], "name": row["name"]},
               "version": row["version"], "errors": {}}
        return self._render("equipment_form", ctx)

    def lending_form_screen(self, conn, user, equipment_id: int) -> None:
        """貸出の登録の画面を返す。貸出中の備品なら貸出状況へ戻す。担当者だけが使える。"""
        row = self._find_equipment(conn, equipment_id)
        if row is None:
            return self._redirect("/", flash=("error", CONFLICT_TEXT))
        if row["employee_number"] is not None:
            return self._redirect("/", flash=("message", "この備品は既に貸出中です"))
        ctx = {"user": user, "equipment": row, "accounts": accounts.list_accounts(conn),
               "borrower": "", "lent_on": _today_jst().isoformat(), "errors": {}}
        return self._render("lending_form", ctx)

    def account_list_screen(self, conn, user, reset: Optional[str]) -> None:
        """アカウントの一覧を返す。reset に社員番号があれば、その行にパスワード再設定の欄を出す。"""
        ctx = {"user": user, "accounts": accounts.list_accounts(conn), "reset": reset, "errors": {}}
        self._render("account_list", ctx)

    # --- 操作（POST） -----------------------------------------------------

    def _post_register(self, conn, user, form) -> None:
        values = {"employee_number": form.get("employee_number", ""), "name": form.get("name", "")}
        problem = accounts.register_account(
            conn, values["employee_number"], values["name"], form.get("password", "")
        )
        if problem is None:
            return self._redirect("/login/", flash=("message", "登録しました。ログインしてください"))
        kind, field, text = problem
        ctx = {"user": user, "values": values, "errors": {}}
        if kind == "field":
            ctx["errors"][field] = text
        else:
            ctx["error"] = text
        return self._render("register_account", ctx)

    def _post_login(self, conn, form) -> None:
        employee_number = form.get("employee_number", "")
        matched = accounts.authenticate_account(conn, employee_number, form.get("password", ""))
        if matched is None:
            ctx = {"user": None, "values": {"employee_number": employee_number}, "errors": {},
                   "error": "社員番号またはパスワードが違います"}
            return self._render("login", ctx)
        token = sessions.create_session(conn, matched, int(time.time()))
        cookie = f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax"
        return self._redirect("/", cookie_headers=[cookie])

    def _post_logout(self, conn) -> None:
        token = self._cookie(SESSION_COOKIE)
        sessions.delete_session(conn, token)
        clear = f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
        return self._redirect("/", flash=("message", "ログアウトしました"), cookie_headers=[clear])

    def _post_equipment_create(self, conn, user, form) -> None:
        values = {"equipment_number": form.get("equipment_number", ""), "name": form.get("name", "")}
        problem = equipment.create_equipment(conn, values["equipment_number"], values["name"])
        if problem is None:
            return self._redirect("/", flash=("message", "備品を登録しました"))
        ctx = {"user": user, "heading": "備品の登録", "action": "/equipment/new/", "values": values, "errors": {}}
        self._apply_problem(ctx, problem)
        return self._render("equipment_form", ctx)

    def _post_equipment_update(self, conn, user, form, equipment_id: int) -> None:
        values = {"equipment_number": form.get("equipment_number", ""), "name": form.get("name", "")}
        version = _to_int(form.get("version"))
        problem = equipment.update_equipment(conn, equipment_id, version, values["equipment_number"], values["name"])
        if problem is None:
            return self._redirect("/", flash=("message", "備品を更新しました"))
        ctx = {"user": user, "heading": "備品の修正", "action": f"/equipment/{equipment_id}/edit/",
               "values": values, "version": version, "errors": {}}
        self._apply_problem(ctx, problem)
        return self._render("equipment_form", ctx)

    def _post_equipment_delete(self, conn, form, equipment_id: int) -> None:
        problem = equipment.delete_equipment(conn, equipment_id, _to_int(form.get("version")))
        if problem is None:
            return self._redirect("/", flash=("message", "備品を削除しました"))
        return self._redirect("/", flash=self._flash_of(problem))

    def _post_lend(self, conn, user, form, equipment_id: int) -> None:
        borrower = form.get("borrower", "")
        lent_on = form.get("lent_on", "")
        problem = lending.lend_equipment(conn, equipment_id, borrower, lent_on, _today_jst())
        if problem is None:
            return self._redirect("/", flash=("message", "貸出を登録しました"))
        if problem[0] == "field":
            row = self._find_equipment(conn, equipment_id)
            if row is None:
                return self._redirect("/", flash=("error", CONFLICT_TEXT))
            ctx = {"user": user, "equipment": row, "accounts": accounts.list_accounts(conn),
                   "borrower": borrower, "lent_on": lent_on, "errors": {}}
            self._apply_problem(ctx, problem)
            return self._render("lending_form", ctx)
        return self._redirect("/", flash=self._flash_of(problem))

    def _post_return(self, conn, equipment_id: int) -> None:
        problem = lending.return_equipment(conn, equipment_id)
        if problem is None:
            return self._redirect("/", flash=("message", "返却を登録しました"))
        return self._redirect("/", flash=self._flash_of(problem))

    def _post_role(self, conn, form, employee_number: str) -> None:
        make_manager = form.get("make_manager") == "1"
        problem = accounts.change_manager_role(conn, employee_number, make_manager)
        if problem is None:
            return self._redirect("/accounts/", flash=("message", "担当者の設定を変更しました"))
        return self._redirect("/accounts/", flash=self._flash_of(problem))

    def _post_password(self, conn, form, employee_number: str) -> None:
        problem = accounts.reset_password(conn, employee_number, form.get("new_password", ""))
        if problem is None:
            return self._redirect("/accounts/", flash=("message", "パスワードを再設定しました"))
        if problem[0] == "field":
            ctx = {"user": self._current_user(conn), "accounts": accounts.list_accounts(conn),
                   "reset": employee_number, "errors": {}}
            ctx["errors"]["new_password"] = problem[2]
            return self._render("account_list", ctx)
        return self._redirect("/accounts/", flash=self._flash_of(problem))

    def _post_account_delete(self, conn, employee_number: str) -> None:
        problem = accounts.delete_account(conn, employee_number)
        if problem is None:
            return self._redirect("/accounts/", flash=("message", "アカウントを削除しました"))
        return self._redirect("/accounts/", flash=self._flash_of(problem))

    # --- 補助 -------------------------------------------------------------

    def _find_equipment(self, conn, equipment_id: int) -> Optional[dict]:
        for row in lending.list_lending_status(conn):
            if row["id"] == equipment_id:
                return row
        return None

    @staticmethod
    def _apply_problem(ctx: dict, problem: Tuple[str, Optional[str], str]) -> None:
        kind, field, text = problem
        if kind == "field":
            ctx["errors"][field] = text
        else:
            ctx["error"] = text

    @staticmethod
    def _flash_of(problem: Tuple[str, Optional[str], str]) -> Tuple[str, str]:
        kind, _field, text = problem
        return ("message" if kind == "message" else "error", text)

    def _current_user(self, conn) -> Optional[dict]:
        token = self._cookie(SESSION_COOKIE)
        timeout = self.settings.idle_timeout_seconds
        return sessions.resolve_session(conn, token, timeout, int(time.time()))

    def _cookie(self, name: str) -> Optional[str]:
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            return None
        morsel = jar.get(name)
        return morsel.value if morsel is not None else None

    def _read_form(self) -> Dict[str, str]:
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return {key: values[0] for key, values in parse_qs(raw, keep_blank_values=True).items()}

    def _pop_flash(self) -> Optional[Tuple[str, str]]:
        raw = self._cookie(FLASH_COOKIE)
        if not raw:
            return None
        kind, _, text = unquote(raw).partition("|")
        return (kind, text) if text else None

    def _render(self, screen: str, ctx: dict) -> None:
        cookie_headers: List[str] = []
        flash = self._pop_flash()
        if flash is not None:
            kind, text = flash
            ctx.setdefault("message" if kind == "message" else "error", text)
            cookie_headers.append(f"{FLASH_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
        page = templates.render_page(screen, ctx).encode("utf-8")
        self._send(200, page, cookie_headers=cookie_headers)

    def _redirect(self, location: str, flash: Optional[Tuple[str, str]] = None,
                  cookie_headers: Optional[List[str]] = None) -> None:
        headers = list(cookie_headers or [])
        if flash is not None:
            value = quote(f"{flash[0]}|{flash[1]}", safe="")
            headers.append(f"{FLASH_COOKIE}={value}; Path=/; HttpOnly; SameSite=Lax")
        self._send(303, b"", cookie_headers=headers, location=location)

    def _send(self, status: int, body: bytes, cookie_headers: Optional[List[str]] = None,
              location: Optional[str] = None) -> None:
        self.send_response(status)
        if location is not None:
            self.send_header("Location", location)
        else:
            self.send_header("Content-Type", "text/html; charset=utf-8")
        for header in cookie_headers or []:
            self.send_header("Set-Cookie", header)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)
