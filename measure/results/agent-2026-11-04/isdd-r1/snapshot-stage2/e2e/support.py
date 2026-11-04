"""E2E テスト用の支援: サーバーの起動、HTTP クライアント、HTML の簡易な解析。"""

import http.cookiejar
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, Iterator, List, Optional

ROOT = Path(__file__).resolve().parent.parent
VOID_TAGS = {"input", "meta", "br", "link", "img", "hr"}


def _python() -> str:
    venv = ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    """一時 DATA_DIR と空きポートで app を起動する。stop で止めて DATA_DIR を消す。"""

    def __init__(self, idle_timeout_seconds: int = 1800):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        env = dict(os.environ)
        env.update(
            {
                "PORT": str(self.port),
                "DATA_DIR": str(self.data_dir),
                "SESSION_IDLE_TIMEOUT_SECONDS": str(idle_timeout_seconds),
            }
        )
        self.log_path = self.data_dir / "server.log"
        self._log = open(self.log_path, "wb")
        self.proc = subprocess.Popen(
            [_python(), "-m", "app"], cwd=str(ROOT), env=env,
            stdout=self._log, stderr=subprocess.STDOUT,
        )
        self._wait_ready()

    def _wait_ready(self, timeout: float = 20.0) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("サーバーが起動できませんでした: " + self.log_path.read_text("utf-8", "replace"))
            try:
                urllib.request.urlopen(self.base + "/", timeout=2).read()
                return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("サーバーの起動を待てませんでした")

    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self._log.close()
        self.tmp.cleanup()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


class Response:
    def __init__(self, status: int, path: str, body: str, location: Optional[str]):
        self.status = status
        self.path = path
        self.body = body
        self.location = location
        self.page = Page(body)


class Client:
    """Cookie を保つ HTTP クライアント。follow=True のときは 3xx を追いかける。"""

    def __init__(self, base: str):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar), _NoRedirect()
        )

    def _once(self, method: str, path: str, form: Optional[Dict[str, str]]) -> Response:
        data = None
        headers = {}
        if form is not None:
            data = urllib.parse.urlencode(form).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=10) as res:
                body = res.read().decode("utf-8")
                return Response(res.status, path, body, None)
        except urllib.error.HTTPError as err:
            body = err.read().decode("utf-8", "replace")
            return Response(err.code, path, body, err.headers.get("Location"))

    def request(self, method: str, path: str, form: Optional[Dict[str, str]] = None, follow: bool = True) -> Response:
        res = self._once(method, path, form)
        hops = 0
        while follow and res.status in (301, 302, 303, 307, 308) and res.location and hops < 5:
            target = res.location
            next_path = target.replace(self.base, "") if target.startswith(self.base) else target
            res = self._once("GET", next_path, None)
            hops += 1
        return res

    def get(self, path: str, follow: bool = True) -> Response:
        return self.request("GET", path, None, follow)

    def post(self, path: str, form: Optional[Dict[str, str]] = None, follow: bool = True) -> Response:
        return self.request("POST", path, form or {}, follow)


class Node:
    def __init__(self, tag: str, attrs: Dict[str, str], parent: Optional["Node"]):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: List["Node"] = []
        self.data: List[str] = []

    @property
    def classes(self) -> List[str]:
        return self.attrs.get("class", "").split()

    def walk(self) -> Iterator["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()

    @property
    def text(self) -> str:
        parts = list(self.data)
        for child in self.children:
            parts.append(child.text)
        return "".join(parts).strip()


class Page:
    """HTML を木にして、クラス・id・タグで要素を探す。"""

    def __init__(self, html: str):
        self.raw = html
        self.root = Node("#root", {}, None)
        self._stack = [self.root]
        parser = _Builder(self)
        parser.feed(html)
        parser.close()

    def all(self, tag: Optional[str] = None, cls: Optional[str] = None) -> List[Node]:
        result = []
        for node in self.root.walk():
            if node is self.root:
                continue
            if tag is not None and node.tag != tag:
                continue
            if cls is not None and cls not in node.classes:
                continue
            result.append(node)
        return result

    def by_id(self, element_id: str) -> Optional[Node]:
        for node in self.root.walk():
            if node.attrs.get("id") == element_id:
                return node
        return None

    def value_of(self, element_id: str) -> Optional[str]:
        node = self.by_id(element_id)
        return None if node is None else node.attrs.get("value", "")

    def texts(self, cls: str) -> List[str]:
        return [n.text for n in self.all(cls=cls)]

    def has_link(self, text: str) -> bool:
        return any(n.text == text for n in self.all(tag="a"))

    def has_button(self, text: str) -> bool:
        return any(n.text == text for n in self.all(tag="button"))

    def buttons(self) -> List[str]:
        return [n.text for n in self.all(tag="button")]

    def field_errors(self, input_id: str) -> List[str]:
        """入力欄（id）を含む .field の中の .field-error の文言を返す。"""
        out: List[str] = []
        for field in self.all(cls="field"):
            if any(n.attrs.get("id") == input_id for n in field.walk()):
                out.extend(n.text for n in field.walk() if "field-error" in n.classes)
        return out

    def rows(self) -> List[Node]:
        return [n for n in self.all(tag="tr") if "data-equipment-number" in n.attrs]


class _Builder(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.page = page

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.page._stack[-1])
        self.page._stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.page._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.page._stack[-1])
        self.page._stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.page._stack) - 1, 0, -1):
            if self.page._stack[i].tag == tag:
                del self.page._stack[i:]
                return

    def handle_data(self, data):
        self.page._stack[-1].data.append(data)

