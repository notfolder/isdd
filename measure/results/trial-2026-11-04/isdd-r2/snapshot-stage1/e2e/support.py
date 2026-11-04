"""E2E テストの共通部品。アプリを別プロセスで起動し、HTTP で画面を操作して HTML を確かめる。

ブラウザは使わない。フォームの値、要素の id と class、文言、Cookie、リダイレクトを
HTTP のやり取りで確かめる。
"""

import http.client
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def seed_accounts(server: "AppServer", numbers: List[str], password: str = "password1") -> None:
    """テスト用に社員を DB へ直接入れる（社員番号の順に、最初の 1 件だけ担当者）。"""
    import sqlite3
    from app.security import hash_password
    from app.db import initialize_schema
    initialize_schema(server.db_path)
    digest = hash_password(password)
    conn = sqlite3.connect(str(server.db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        for number in numbers:
            role = "manager" if count == 0 else "member"
            conn.execute("INSERT INTO accounts (employee_number, name, password_hash, role) VALUES (?, ?, ?, ?)",
                         (number, "テスト" + number, digest, role))
            count += 1
        conn.commit()
    finally:
        conn.close()


def equipment_id(server: "AppServer", number: str) -> int:
    """管理番号から備品の id を DB で引く（テストの準備用）。"""
    import sqlite3
    conn = sqlite3.connect(str(server.db_path))
    try:
        row = conn.execute("SELECT id FROM equipment WHERE equipment_number = ?", (number,)).fetchone()
        return int(row[0])
    finally:
        conn.close()


class AppServer:
    """空の DATA_DIR でアプリを起動する。stop で止め、DATA_DIR を消す。"""

    def __init__(self, idle_timeout_seconds: int = 1800) -> None:
        self.port = _free_port()
        self.data_dir = Path(tempfile.mkdtemp(prefix="isdd-e2e-"))
        self.idle_timeout_seconds = idle_timeout_seconds
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> "AppServer":
        env = dict(os.environ)
        env.update({
            "PORT": str(self.port),
            "DATA_DIR": str(self.data_dir),
            "SESSION_IDLE_TIMEOUT_SECONDS": str(self.idle_timeout_seconds),
        })
        self.stderr_path = self.data_dir.parent / (self.data_dir.name + ".stderr")
        self.stderr_file = open(self.stderr_path, "wb")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "app"], cwd=str(PROJECT_ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=self.stderr_file,
        )
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.5):
                    return self
            except OSError:
                if self.process.poll() is not None:
                    self.stderr_file.close()
                    raise RuntimeError(self.stderr_path.read_text(encoding="utf-8", errors="replace"))
                time.sleep(0.1)
        raise RuntimeError("アプリが起動しませんでした")

    def stop(self) -> None:
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if not self.stderr_file.closed:
            self.stderr_file.close()
        shutil.rmtree(self.data_dir, ignore_errors=True)
        self.stderr_path.unlink(missing_ok=True)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "isdd.sqlite3"


class _Element:
    def __init__(self, tag: str, attrs: Dict[str, str], ancestors: Tuple[str, ...]) -> None:
        self.tag = tag
        self.attrs = attrs
        self.ancestors = ancestors
        self.text_parts: List[str] = []
        self.controls: List[dict] = []
        self.options: List[dict] = []
        self.cells: List[str] = []

    @property
    def text(self) -> str:
        return " ".join("".join(self.text_parts).split())

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()


class _Parser(HTMLParser):
    VOID = {"input", "br", "meta", "link", "img", "hr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[_Element] = []
        self.elements: List[_Element] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attr = {k: (v or "") for k, v in attrs}
        ancestors = tuple(e.tag for e in self.stack)
        if tag in ("input", "button", "select", "option"):
            element = _Element(tag, attr, ancestors)
            self.elements.append(element)
            if tag == "option":
                select = self._nearest("select")
                if select is not None:
                    select.options.append({"value": attr.get("value", ""), "selected": "selected" in attr})
                if select is not None:
                    self.stack.append(element)
                return
            form = self._nearest("form")
            if form is not None:
                form.controls.append({"kind": tag, "attrs": attr, "text": ""})
            if tag == "button":
                self.stack.append(element)
            if tag == "select":
                self.stack.append(element)
            return
        if tag in self.VOID:
            self.elements.append(_Element(tag, attr, ancestors))
            return
        self.stack.append(_Element(tag, attr, ancestors))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                element = self.stack.pop(index)
                if tag == "select":
                    selected = [o for o in element.options if o["selected"]]
                    element.attrs["_value"] = (selected or element.options or [{"value": ""}])[0]["value"]
                if tag == "td":
                    row = self._nearest("tr")
                    if row is not None:
                        row.cells.append(element.text)
                if tag == "button":
                    form = self._nearest("form")
                    if form is not None:
                        form.controls.append({"kind": "button", "attrs": element.attrs, "text": element.text})
                self.elements.append(element)
                return

    def handle_data(self, data: str) -> None:
        for element in self.stack:
            element.text_parts.append(data)

    def _nearest(self, tag: str) -> Optional[_Element]:
        for element in reversed(self.stack):
            if element.tag == tag:
                return element
        return None


class Page:
    """取得した HTML と、その中の要素を探す補助。"""

    def __init__(self, status: int, headers: List[Tuple[str, str]], body: str, url: str) -> None:
        self.status = status
        self.headers = headers
        self.body = body
        self.url = url
        parser = _Parser()
        parser.feed(body)
        self.elements = parser.elements

    def by_id(self, element_id: str) -> Optional[_Element]:
        for element in self.elements:
            if element.attrs.get("id") == element_id:
                return element
        return None

    def by_class(self, name: str) -> List[str]:
        return [e.text for e in self.elements if e.has_class(name)]

    def cells(self, data_attr: str, value: str) -> List[str]:
        """行の各セルの文言（ボタンの文言を除いた表示の文字）を返す。"""
        row = self.row(data_attr, value)
        return row.cells if row is not None else []

    def has_text(self, text: str) -> bool:
        return text in self.body or any(text in e.text for e in self.elements)

    def rows(self, data_attr: str) -> List[_Element]:
        return [e for e in self.elements
                if e.tag == "tr" and "tbody" in e.ancestors and data_attr in e.attrs]

    def row(self, data_attr: str, value: str) -> Optional[_Element]:
        for element in self.rows(data_attr):
            if element.attrs.get(data_attr) == value:
                return element
        return None

    def buttons(self, scope: Optional[_Element] = None) -> List[dict]:
        found = []
        for form in self.forms():
            for control in form["controls"]:
                if control["kind"] == "button":
                    found.append(control)
        return found

    def forms(self) -> List[dict]:
        return [{"attrs": e.attrs, "controls": e.controls} for e in self.elements if e.tag == "form"]

    def button_forms(self, text: str, row: Optional[_Element] = None) -> List[dict]:
        """指定の文言のボタンを含むフォームを返す（行の中に限るときは row を渡す）。"""
        found = []
        for form in self.forms():
            if any(c["kind"] == "button" and c["text"] == text for c in form["controls"]):
                if row is None or form["attrs"].get("action", "").startswith(row.attrs.get("data-action", "\0")):
                    found.append(form)
        return found


class Client:
    """Cookie を持つ HTTP クライアント。リダイレクトは利用者の代わりに 1 回ずつ辿る。"""

    def __init__(self, server: AppServer) -> None:
        self.server = server
        self.cookies: Dict[str, str] = {}

    def _send(self, method: str, path: str, form: Optional[Dict[str, str]] = None) -> Page:
        conn = http.client.HTTPConnection("127.0.0.1", self.server.port, timeout=10)
        headers = {}
        if self.cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        body = None
        if form is not None:
            body = "&".join(f"{_quote(k)}={_quote(v)}" for k, v in form.items()).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            headers["Content-Length"] = str(len(body))
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        headers_list = response.getheaders()
        conn.close()
        for key, value in headers_list:
            if key.lower() == "set-cookie":
                self._apply_cookie(value)
        return Page(response.status, headers_list, raw, path)

    def _apply_cookie(self, header: str) -> None:
        pair = header.split(";", 1)[0]
        name, _, value = pair.partition("=")
        if value == "" or "Max-Age=0" in header:
            self.cookies.pop(name, None)
        else:
            self.cookies[name] = value

    def get(self, path: str) -> Page:
        return self._follow(self._send("GET", path))

    def post(self, path: str, form: Dict[str, str]) -> Page:
        return self._follow(self._send("POST", path, form))

    def raw_post(self, path: str, form: Dict[str, str]) -> Page:
        return self._send("POST", path, form)

    def _follow(self, page: Page) -> Page:
        for _ in range(5):
            location = dict(page.headers).get("Location")
            if page.status not in (301, 302, 303) or location is None:
                return page
            page = self._send("GET", location)
        return page

    def submit(self, page: Page, button_text: str, values: Optional[Dict[str, str]] = None,
               must_contain: Optional[str] = None) -> Page:
        """ボタンの文言で送信するフォームを選び、入力欄の値を組み立てて送る。

        must_contain があれば、action かいずれかの値にその文字列を含むフォームだけを候補にする
        （一覧の行のボタンを選ぶため）。
        """
        for form in page.forms():
            controls = form["controls"]
            if not any(c["kind"] == "button" and c["text"] == button_text for c in controls):
                continue
            action = form["attrs"].get("action", "")
            if must_contain is not None:
                values_in_form = [str(c["attrs"].get("value", "")) for c in controls]
                if must_contain not in action and not any(must_contain in v for v in values_in_form):
                    continue
            fields: Dict[str, str] = {}
            for control in controls:
                attrs = control["attrs"]
                name = attrs.get("name")
                if control["kind"] == "input" and name and attrs.get("type") not in ("submit", "button"):
                    fields[name] = attrs.get("value", "")
                if control["kind"] == "select" and name:
                    fields[name] = attrs.get("_value", "")
                if control["kind"] == "button" and control["text"] == button_text and name:
                    fields[name] = attrs.get("value", "")
            fields.update(values or {})
            if form["attrs"].get("method", "get").lower() == "post":
                return self.post(action, fields)
            return self.get(action + ("?" + _query(fields) if fields else ""))
        raise AssertionError(f"ボタン「{button_text}」を含むフォームがありません（{page.url}）")


def _quote(value: str) -> str:
    from urllib.parse import quote
    return quote(value, safe="")


def _query(fields: Dict[str, str]) -> str:
    return "&".join(f"{_quote(k)}={_quote(v)}" for k, v in fields.items())
