import hashlib
import hmac
import html
import os
import re
import secrets
import sqlite3
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
PORT = int(os.environ.get("PORT", "8000"))
IDLE_TIMEOUT = int(os.environ.get("SESSION_IDLE_TIMEOUT_SECONDS", "1800"))
DB_PATH = os.path.join(DATA_DIR, "app.db")
SESSION_COOKIE = "sid"
PBKDF2_ITERATIONS = 200_000

ROLE_STAFF = "担当者"
ROLE_MEMBER = "社員"

EMP_RE = re.compile(r"[0-9]{6}")
EQ_RE = re.compile(r"[A-Za-z0-9-]{1,20}")

MSG_EMP_FORMAT = "社員番号は 6 桁の数字で入力してください"
MSG_EMP_DUP = "この社員番号は既に登録されています"
MSG_NAME_EMPTY = "名前を入力してください"
MSG_NAME_LONG = "名前は 30 文字以内で入力してください"
MSG_PW_SHORT = "パスワードは 8 文字以上で入力してください"
MSG_LOGIN_FAIL = "社員番号またはパスワードが違います"
MSG_STAFF_ONLY = "この操作は担当者だけが行えます"
MSG_EQ_FORMAT = "管理番号は半角の英数字とハイフンで 20 文字以内で入力してください"
MSG_EQ_DUP = "この管理番号は既に使われています"
MSG_EQ_NAME_EMPTY = "備品名を入力してください"
MSG_EQ_NAME_LONG = "備品名は 50 文字以内で入力してください"
MSG_REGISTERED = "登録しました。ログインしてください"

NOTICES = {
    "created": "備品を登録しました",
    "updated": "備品を修正しました",
    "deleted": "備品を削除しました",
}


def db():
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            employee_number TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            employee_number TEXT NOT NULL,
            last_seen INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS equipment (
            equipment_number TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        """
    )
    conn.close()


def hash_password(pw):
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex() + "$" + dk.hex()


# 存在しない社員番号でも同じ時間がかかるように、ログイン時にこの値と比べる。
DUMMY_HASH = hash_password("dummy-password-for-timing")


def verify_password(pw, stored):
    salt_hex, dk_hex = stored.split("$")
    dk = hashlib.pbkdf2_hmac(
        "sha256", pw.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(dk.hex(), dk_hex)


def current_user(conn, token):
    if not token:
        return None
    row = conn.execute(
        "SELECT s.last_seen, u.employee_number, u.name, u.role "
        "FROM sessions s JOIN users u ON u.employee_number = s.employee_number "
        "WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return None
    now = int(time.time())
    if now - row["last_seen"] > IDLE_TIMEOUT:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        return None
    conn.execute("UPDATE sessions SET last_seen = ? WHERE token = ?", (now, token))
    return row


def e(value):
    return html.escape(str(value), quote=True)


def layout(title, body, user):
    if user is not None:
        header = (
            '<span class="current-user">%s</span> '
            '<form method="post" action="/logout" class="inline">'
            '<button type="submit">ログアウト</button></form>'
        ) % e(user["name"])
    else:
        header = (
            '<a href="/login/">ログイン</a> '
            '<a href="/accounts/register/">アカウント登録</a>'
        )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ja"><head><meta charset="utf-8">'
        "<title>%s</title>"
        "<style>"
        "body{font-family:sans-serif;margin:24px;color:#222}"
        "header{display:flex;gap:12px;align-items:center;margin-bottom:16px}"
        "header a{margin-right:8px}"
        "form.inline{display:inline}"
        ".field{margin:12px 0}"
        ".field label{display:block;font-weight:bold}"
        ".field-error{color:#b00020;display:block}"
        ".error{color:#b00020;margin:12px 0}"
        ".message{background:#e8f4ea;padding:8px;margin:12px 0}"
        "table{border-collapse:collapse;width:100%%}"
        "th,td{border:1px solid #ccc;padding:6px;text-align:left}"
        "</style></head><body>"
        "<header>%s</header>"
        "<main>%s</main>"
        "</body></html>"
    ) % (e(title), header, body)


class Handler(BaseHTTPRequestHandler):
    server_version = "Equipment/1.0"

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        parts = urlsplit(self.path)
        path = parts.path.rstrip("/") or "/"
        query = {k: v[0] for k, v in parse_qs(parts.query).items()}
        form = {}
        if method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8", "replace")
            form = {k: v[0] for k, v in parse_qs(body, keep_blank_values=True).items()}

        self.token = None
        raw = self.headers.get("Cookie")
        if raw:
            jar = cookies.SimpleCookie()
            try:
                jar.load(raw)
                if SESSION_COOKIE in jar:
                    self.token = jar[SESSION_COOKIE].value
            except cookies.CookieError:
                self.token = None

        self.conn = db()
        self.set_cookies = []
        try:
            self.user = current_user(self.conn, self.token)
            self.route(method, path, query, form)
        except Exception:
            self.send_text(500, "サーバーでエラーが発生しました")
        finally:
            self.conn.close()

    # --- 応答の補助 ---

    def send_body(self, status, text, content_type="text/html; charset=utf-8", headers=None):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for c in self.set_cookies:
            self.send_header("Set-Cookie", c)
        for k, v in headers or []:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, status, text):
        self.send_body(status, layout("エラー", "<p>%s</p>" % e(text), self.user))

    def send_page(self, status, title, body):
        self.send_body(status, layout(title, body, self.user))

    def redirect(self, location):
        self.send_body(303, "", headers=[("Location", location)])

    def not_found(self):
        self.send_text(404, "ページが見つかりません")

    def session_cookie(self, token):
        return "%s=%s; Path=/; HttpOnly; SameSite=Lax" % (SESSION_COOKIE, token)

    def clear_session_cookie(self):
        return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax" % SESSION_COOKIE

    # --- ルーティング ---

    def route(self, method, path, query, form):
        m = re.fullmatch(r"/equipment/([A-Za-z0-9-]{1,20})/(edit|delete)", path)
        if path == "/" and method == "GET":
            return self.index(query)
        if path == "/accounts/register" and method == "GET":
            return self.register_form()
        if path == "/accounts/register" and method == "POST":
            return self.register_submit(form)
        if path == "/login" and method == "GET":
            return self.login_form(query)
        if path == "/login" and method == "POST":
            return self.login_submit(form)
        if path == "/logout" and method == "POST":
            return self.logout()
        if path == "/equipment/new":
            if self.user is None:
                return self.redirect("/login/")
            if self.user["role"] != ROLE_STAFF:
                return self.index(query, message=MSG_STAFF_ONLY, status=403)
            if method == "GET":
                return self.equipment_form(None, {"equipment_number": "", "name": ""}, {})
            if method == "POST":
                return self.equipment_submit(None, form)
        if m:
            number, action = m.group(1), m.group(2)
            if self.user is None:
                return self.redirect("/login/")
            if self.user["role"] != ROLE_STAFF:
                return self.index(query, message=MSG_STAFF_ONLY, status=403)
            row = self.conn.execute(
                "SELECT equipment_number, name FROM equipment WHERE equipment_number = ?",
                (number,),
            ).fetchone()
            if row is None:
                return self.not_found()
            if action == "edit" and method == "GET":
                return self.equipment_form(
                    number,
                    {"equipment_number": row["equipment_number"], "name": row["name"]},
                    {},
                )
            if action == "edit" and method == "POST":
                return self.equipment_submit(number, form)
            if action == "delete" and method == "POST":
                self.conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (number,))
                return self.redirect("/?notice=deleted")
        return self.not_found()

    # --- 貸出状況 ---

    def index(self, query, message=None, status=200):
        user = self.user
        staff = user is not None and user["role"] == ROLE_STAFF
        rows = self.conn.execute(
            "SELECT equipment_number, name FROM equipment ORDER BY equipment_number ASC"
        ).fetchall()

        notice = NOTICES.get(query.get("notice", ""))
        parts = ["<h1>貸出状況</h1>"]
        if message:
            parts.append('<div class="message">%s</div>' % e(message))
        elif notice:
            parts.append('<div class="message">%s</div>' % e(notice))
        if staff:
            parts.append('<p><a href="/equipment/new/">備品を登録</a></p>')

        head = "<th>管理番号</th><th>備品名</th><th>状態</th><th>借りている社員</th><th>貸出日</th>"
        if staff:
            head += "<th>操作</th>"
        parts.append("<table><thead><tr>%s</tr></thead><tbody>" % head)
        for r in rows:
            num = r["equipment_number"]
            cells = (
                "<td>%s</td><td>%s</td><td>空き</td><td></td><td></td>"
                % (e(num), e(r["name"]))
            )
            if staff:
                cells += (
                    '<td><form method="get" action="/equipment/%s/edit/" class="inline">'
                    '<button type="submit">修正</button></form> '
                    '<form method="post" action="/equipment/%s/delete/" class="inline" '
                    "onsubmit=\"return window.confirm('備品「%s」を削除しますか？')\">"
                    '<button type="submit">削除</button></form></td>'
                ) % (e(num), e(num), e(r["name"]))
            parts.append('<tr data-equipment-number="%s">%s</tr>' % (e(num), cells))
        parts.append("</tbody></table>")
        if not rows:
            parts.append("<p>備品は登録されていません</p>")

        self.send_page(status, "貸出状況", "".join(parts))

    # --- アカウント ---

    def register_form(self, values=None, errors=None):
        values = values or {"employee_number": "", "name": ""}
        errors = errors or {}
        body = self.register_html(values, errors)
        self.send_page(200, "アカウント登録", body)

    def register_html(self, values, errors):
        def field(name, label, input_type, value, input_id):
            err = errors.get(name)
            err_html = '<span class="field-error">%s</span>' % e(err) if err else ""
            return (
                '<div class="field"><label for="%s">%s</label>'
                '<input id="%s" name="%s" type="%s" value="%s">%s</div>'
            ) % (input_id, label, input_id, name, input_type, e(value), err_html)

        return (
            "<h1>アカウント登録</h1>"
            '<form method="post" action="/accounts/register/">'
            + field("employee_number", "社員番号（6 桁の数字）", "text",
                    values.get("employee_number", ""), "id_employee_number")
            + field("name", "名前", "text", values.get("name", ""), "id_name")
            + field("password", "パスワード（8 文字以上）", "password", "", "id_password")
            + '<button type="submit">登録</button></form>'
        )

    def register_submit(self, form):
        emp = form.get("employee_number", "")
        name = form.get("name", "").strip()
        pw = form.get("password", "")
        values = {"employee_number": emp, "name": name}
        errors = {}
        if not EMP_RE.fullmatch(emp):
            errors["employee_number"] = MSG_EMP_FORMAT
        if not name:
            errors["name"] = MSG_NAME_EMPTY
        elif len(name) > 30:
            errors["name"] = MSG_NAME_LONG
        if len(pw) < 8:
            errors["password"] = MSG_PW_SHORT
        if errors:
            return self.register_form(values, errors)

        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute("SELECT 1 FROM users WHERE employee_number = ?", (emp,)).fetchone():
                conn.execute("ROLLBACK")
                errors["employee_number"] = MSG_EMP_DUP
                return self.register_form(values, errors)
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            role = ROLE_STAFF if count == 0 else ROLE_MEMBER
            conn.execute(
                "INSERT INTO users (employee_number, name, password_hash, role, created_at) "
                "VALUES (?, ?, ?, ?, datetime('now'))",
                (emp, name, hash_password(pw), role),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            errors["employee_number"] = MSG_EMP_DUP
            return self.register_form(values, errors)
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return self.redirect("/login/?registered=1")

    # --- ログイン・ログアウト ---

    def login_form(self, query, emp="", error=None):
        notice = ""
        if query.get("registered") == "1":
            notice = '<div class="message">%s</div>' % e(MSG_REGISTERED)
        err_html = '<div class="error">%s</div>' % e(error) if error else ""
        body = (
            "<h1>ログイン</h1>" + notice + err_html
            + '<form method="post" action="/login/">'
            + '<div class="field"><label for="id_employee_number">社員番号</label>'
            + '<input id="id_employee_number" name="employee_number" type="text" value="%s"></div>' % e(emp)
            + '<div class="field"><label for="id_password">パスワード</label>'
            + '<input id="id_password" name="password" type="password" value=""></div>'
            + '<button type="submit">ログイン</button></form>'
        )
        self.send_page(200, "ログイン", body)

    def login_submit(self, form):
        emp = form.get("employee_number", "")
        pw = form.get("password", "")
        row = None
        if EMP_RE.fullmatch(emp):
            row = self.conn.execute(
                "SELECT employee_number, password_hash FROM users WHERE employee_number = ?",
                (emp,),
            ).fetchone()
        stored = row["password_hash"] if row else DUMMY_HASH
        ok = verify_password(pw, stored)
        if row is None or not ok:
            return self.login_form({}, emp=emp, error=MSG_LOGIN_FAIL)
        token = secrets.token_urlsafe(32)
        self.conn.execute(
            "INSERT INTO sessions (token, employee_number, last_seen) VALUES (?, ?, ?)",
            (token, emp, int(time.time())),
        )
        self.set_cookies.append(self.session_cookie(token))
        return self.redirect("/")

    def logout(self):
        if self.token:
            self.conn.execute("DELETE FROM sessions WHERE token = ?", (self.token,))
        self.set_cookies.append(self.clear_session_cookie())
        return self.redirect("/")

    # --- 備品の登録・修正 ---

    def equipment_form(self, original, values, errors):
        title = "備品の登録" if original is None else "備品の修正"
        def field(name, label, value, input_id):
            err = errors.get(name)
            err_html = '<span class="field-error">%s</span>' % e(err) if err else ""
            return (
                '<div class="field"><label for="%s">%s</label>'
                '<input id="%s" name="%s" type="text" value="%s">%s</div>'
            ) % (input_id, label, input_id, name, e(value), err_html)

        action = "/equipment/new/" if original is None else "/equipment/%s/edit/" % original
        body = (
            "<h1>%s</h1>" % e(title)
            + '<form method="post" action="%s">' % e(action)
            + field("equipment_number", "管理番号（半角英数字とハイフン・20 文字以内）",
                    values.get("equipment_number", ""), "id_equipment_number")
            + field("name", "備品名（50 文字以内）", values.get("name", ""), "id_name")
            + '<button type="submit">保存</button></form>'
            + '<p><a href="/">貸出状況に戻る</a></p>'
        )
        self.send_page(200, title, body)

    def equipment_submit(self, original, form):
        number = form.get("equipment_number", "")
        name = form.get("name", "").strip()
        values = {"equipment_number": number, "name": name}
        errors = {}
        if not EQ_RE.fullmatch(number):
            errors["equipment_number"] = MSG_EQ_FORMAT
        if not name:
            errors["name"] = MSG_EQ_NAME_EMPTY
        elif len(name) > 50:
            errors["name"] = MSG_EQ_NAME_LONG
        if not errors and (original is None or number != original):
            if self.conn.execute(
                "SELECT 1 FROM equipment WHERE equipment_number = ?", (number,)
            ).fetchone():
                errors["equipment_number"] = MSG_EQ_DUP
        if errors:
            return self.equipment_form(original, values, errors)

        try:
            if original is None:
                self.conn.execute(
                    "INSERT INTO equipment (equipment_number, name) VALUES (?, ?)",
                    (number, name),
                )
                return self.redirect("/?notice=created")
            self.conn.execute(
                "UPDATE equipment SET equipment_number = ?, name = ? WHERE equipment_number = ?",
                (number, name, original),
            )
            return self.redirect("/?notice=updated")
        except sqlite3.IntegrityError:
            errors["equipment_number"] = MSG_EQ_DUP
            return self.equipment_form(original, values, errors)


def main():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    print("listening on port %d" % PORT, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
