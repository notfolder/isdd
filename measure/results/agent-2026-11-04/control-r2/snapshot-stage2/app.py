import hashlib
import hmac
import html
import os
import re
import secrets
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
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
JST = timezone(timedelta(hours=9))

ROLE_STAFF = "担当者"
ROLE_MEMBER = "社員"

EMP_RE = re.compile(r"[0-9]{6}")
EQ_RE = re.compile(r"[A-Za-z0-9-]{1,20}")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

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
MSG_STALE = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"
MSG_LOANED_DELETE = "この備品は貸出中のため削除できません。先に返却を処理してください"
MSG_BORROWER_EMPTY = "借りる社員を選んでください"
MSG_DATE_FORMAT = "貸出日は YYYY-MM-DD の形式で入力してください"
MSG_DATE_FUTURE = "貸出日に未来の日付は入力できません"
MSG_ALREADY_LENT = "この備品は既に貸出中です"
MSG_ALREADY_RETURNED = "この備品は既に返却されています"

NOTICES = {
    "created": "備品を登録しました",
    "updated": "備品を修正しました",
    "deleted": "備品を削除しました",
    "lent": "貸出を登録しました",
    "returned": "返却を処理しました",
}


def db():
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def today_jst():
    return datetime.now(JST).date()


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
        CREATE TABLE IF NOT EXISTS loans (
            equipment_number TEXT PRIMARY KEY,
            borrower TEXT NOT NULL,
            lent_on TEXT NOT NULL
        );
        """
    )
    # 段 1 の DB には修正の競合を見る版番号（rev）が無いので足す。
    cols = [r[1] for r in conn.execute("PRAGMA table_info(equipment)").fetchall()]
    if "rev" not in cols:
        conn.execute("ALTER TABLE equipment ADD COLUMN rev INTEGER NOT NULL DEFAULT 0")
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
        m = re.fullmatch(r"/equipment/([A-Za-z0-9-]{1,20})/(edit|delete|lend|return)", path)
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
            if action == "edit" and method == "POST":
                # 保存時に備品が消えていても、競合の案内を出すため行の存在は見ない。
                return self.equipment_submit(number, form)
            row = self.conn.execute(
                "SELECT equipment_number, name, rev FROM equipment WHERE equipment_number = ?",
                (number,),
            ).fetchone()
            if row is None:
                return self.not_found()
            if action == "edit" and method == "GET":
                return self.equipment_form(
                    number,
                    {"equipment_number": row["equipment_number"], "name": row["name"],
                     "rev": str(row["rev"])},
                    {},
                )
            if action == "delete" and method == "POST":
                return self.equipment_delete(number)
            if action == "lend" and method == "GET":
                return self.lend_form(row, {"borrower": "", "lent_on": today_jst().isoformat()}, {})
            if action == "lend" and method == "POST":
                return self.lend_submit(row, form)
            if action == "return" and method == "POST":
                return self.return_submit(number)
        return self.not_found()

    # --- 貸出状況 ---

    def index(self, query, message=None, status=200):
        user = self.user
        staff = user is not None and user["role"] == ROLE_STAFF
        rows = self.conn.execute(
            "SELECT e.equipment_number, e.name, l.lent_on, u.name AS borrower_name "
            "FROM equipment e "
            "LEFT JOIN loans l ON l.equipment_number = e.equipment_number "
            "LEFT JOIN users u ON u.employee_number = l.borrower "
            "ORDER BY e.equipment_number ASC"
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
            loaned = r["lent_on"] is not None
            if loaned:
                status_text = "貸出中"
                borrower_text = r["borrower_name"] or ""
                lent_text = r["lent_on"]
            else:
                status_text = "空き"
                borrower_text = ""
                lent_text = ""
            cells = (
                "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                % (e(num), e(r["name"]), status_text, e(borrower_text), e(lent_text))
            )
            if staff:
                cells += '<td>'
                if loaned:
                    cells += (
                        '<form method="post" action="/equipment/%s/return/" class="inline" '
                        "onsubmit=\"return window.confirm('備品「%s」を返却しますか？')\">"
                        '<button type="submit">返却</button></form> '
                    ) % (e(num), e(r["name"]))
                else:
                    cells += (
                        '<form method="get" action="/equipment/%s/lend/" class="inline">'
                        '<button type="submit">貸出</button></form> '
                    ) % e(num)
                cells += (
                    '<form method="get" action="/equipment/%s/edit/" class="inline">'
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

    # --- 備品の登録・修正・削除 ---

    def equipment_form(self, original, values, errors, page_error=None):
        title = "備品の登録" if original is None else "備品の修正"
        def field(name, label, value, input_id):
            err = errors.get(name)
            err_html = '<span class="field-error">%s</span>' % e(err) if err else ""
            return (
                '<div class="field"><label for="%s">%s</label>'
                '<input id="%s" name="%s" type="text" value="%s">%s</div>'
            ) % (input_id, label, input_id, name, e(value), err_html)

        action = "/equipment/new/" if original is None else "/equipment/%s/edit/" % original
        err_top = '<div class="error">%s</div>' % e(page_error) if page_error else ""
        hidden_rev = ""
        if original is not None:
            hidden_rev = '<input type="hidden" name="rev" value="%s">' % e(values.get("rev", ""))
        body = (
            "<h1>%s</h1>" % e(title)
            + err_top
            + '<form method="post" action="%s">' % e(action)
            + hidden_rev
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
        rev_raw = form.get("rev", "")
        values = {"equipment_number": number, "name": name, "rev": rev_raw}
        errors = {}
        if not EQ_RE.fullmatch(number):
            errors["equipment_number"] = MSG_EQ_FORMAT
        if not name:
            errors["name"] = MSG_EQ_NAME_EMPTY
        elif len(name) > 50:
            errors["name"] = MSG_EQ_NAME_LONG
        if errors:
            return self.equipment_form(original, values, errors)

        conn = self.conn
        try:
            rev = int(rev_raw)
        except ValueError:
            rev = -1
        conn.execute("BEGIN IMMEDIATE")
        try:
            if original is None:
                if conn.execute(
                    "SELECT 1 FROM equipment WHERE equipment_number = ?", (number,)
                ).fetchone():
                    conn.execute("ROLLBACK")
                    errors["equipment_number"] = MSG_EQ_DUP
                    return self.equipment_form(original, values, errors)
                conn.execute(
                    "INSERT INTO equipment (equipment_number, name, rev) VALUES (?, ?, 0)",
                    (number, name),
                )
                conn.execute("COMMIT")
                return self.redirect("/?notice=created")

            if not conn.execute(
                "SELECT 1 FROM equipment WHERE equipment_number = ? AND rev = ?",
                (original, rev),
            ).fetchone():
                conn.execute("ROLLBACK")
                return self.equipment_form(original, values, {}, page_error=MSG_STALE)
            if number != original and conn.execute(
                "SELECT 1 FROM equipment WHERE equipment_number = ?", (number,)
            ).fetchone():
                conn.execute("ROLLBACK")
                errors["equipment_number"] = MSG_EQ_DUP
                return self.equipment_form(original, values, errors)
            conn.execute(
                "UPDATE equipment SET equipment_number = ?, name = ?, rev = rev + 1 "
                "WHERE equipment_number = ?",
                (number, name, original),
            )
            if number != original:
                # 貸出の記録は備品の番号が変わっても引き継ぐ。
                conn.execute(
                    "UPDATE loans SET equipment_number = ? WHERE equipment_number = ?",
                    (number, original),
                )
            conn.execute("COMMIT")
            return self.redirect("/?notice=updated")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            errors["equipment_number"] = MSG_EQ_DUP
            return self.equipment_form(original, values, errors)
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def equipment_delete(self, number):
        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute(
                "SELECT 1 FROM loans WHERE equipment_number = ?", (number,)
            ).fetchone():
                conn.execute("ROLLBACK")
                return self.index({}, message=MSG_LOANED_DELETE)
            conn.execute("DELETE FROM equipment WHERE equipment_number = ?", (number,))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return self.redirect("/?notice=deleted")

    # --- 貸出・返却 ---

    def lend_form(self, row, values, errors):
        num = row["equipment_number"]
        users = self.conn.execute(
            "SELECT employee_number, name FROM users ORDER BY employee_number ASC"
        ).fetchall()
        options = ['<option value="">選んでください</option>']
        for u in users:
            selected = " selected" if u["employee_number"] == values.get("borrower") else ""
            options.append(
                '<option value="%s"%s>%s（%s）</option>'
                % (e(u["employee_number"]), selected, e(u["name"]), e(u["employee_number"]))
            )
        err_b = errors.get("borrower")
        err_d = errors.get("lent_on")
        body = (
            "<h1>貸出の登録</h1>"
            '<p class="lending-equipment">備品: %s %s</p>' % (e(num), e(row["name"]))
            + '<form method="post" action="/equipment/%s/lend/">' % e(num)
            + '<div class="field"><label for="id_borrower">借りる社員</label>'
            + '<select id="id_borrower" name="borrower">%s</select>' % "".join(options)
            + ('<span class="field-error">%s</span>' % e(err_b) if err_b else "")
            + "</div>"
            + '<div class="field"><label for="id_lent_on">貸出日（YYYY-MM-DD）</label>'
            + '<input id="id_lent_on" name="lent_on" type="text" value="%s">' % e(values.get("lent_on", ""))
            + ('<span class="field-error">%s</span>' % e(err_d) if err_d else "")
            + "</div>"
            + '<button type="submit">登録</button></form>'
            + '<p><a href="/">貸出状況に戻る</a></p>'
        )
        self.send_page(200, "貸出の登録", body)

    def lend_submit(self, row, form):
        number = row["equipment_number"]
        borrower = form.get("borrower", "")
        lent_on = form.get("lent_on", "").strip()
        values = {"borrower": borrower, "lent_on": lent_on}
        errors = {}
        user = None
        if borrower:
            user = self.conn.execute(
                "SELECT employee_number FROM users WHERE employee_number = ?", (borrower,)
            ).fetchone()
        if user is None:
            errors["borrower"] = MSG_BORROWER_EMPTY
        if not DATE_RE.fullmatch(lent_on):
            errors["lent_on"] = MSG_DATE_FORMAT
        else:
            try:
                d = date.fromisoformat(lent_on)
            except ValueError:
                errors["lent_on"] = MSG_DATE_FORMAT
            else:
                if d > today_jst():
                    errors["lent_on"] = MSG_DATE_FUTURE
        if errors:
            return self.lend_form(row, values, errors)

        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            if conn.execute(
                "SELECT 1 FROM loans WHERE equipment_number = ?", (number,)
            ).fetchone():
                conn.execute("ROLLBACK")
                return self.index({}, message=MSG_ALREADY_LENT)
            conn.execute(
                "INSERT INTO loans (equipment_number, borrower, lent_on) VALUES (?, ?, ?)",
                (number, borrower, lent_on),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            return self.index({}, message=MSG_ALREADY_LENT)
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return self.redirect("/?notice=lent")

    def return_submit(self, number):
        conn = self.conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            cur = conn.execute("DELETE FROM loans WHERE equipment_number = ?", (number,))
            if cur.rowcount == 0:
                conn.execute("ROLLBACK")
                return self.index({}, message=MSG_ALREADY_RETURNED)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return self.redirect("/?notice=returned")


def main():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    print("listening on port %d" % PORT, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
