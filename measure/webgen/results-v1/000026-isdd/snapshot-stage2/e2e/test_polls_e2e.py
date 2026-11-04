"""E2E tests: start server.py as a child process on a free port and call it over HTTP.

Each test function is one E2E scenario from docs/detail_design.md section 8-2.
"""

import http.cookiejar
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Site:
    """HTTP client with a cookie jar, like one browser."""

    def __init__(self, base: str) -> None:
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), _NoRedirect())

    def get(self, path: str) -> tuple[int, str]:
        return self._send(urllib.request.Request(self.base + path))

    def post(self, path: str, data: dict) -> tuple[int, str, dict]:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(self.base + path, data=body, method="POST")
        status, text, headers = self._send_full(req)
        return status, text, headers

    def _send(self, req) -> tuple[int, str]:
        status, text, _ = self._send_full(req)
        return status, text

    def _send_full(self, req) -> tuple[int, str, dict]:
        try:
            with self.opener.open(req, timeout=10) as resp:
                return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8"), dict(exc.headers)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Return the redirect response itself so the test can read its Location header."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _start_server(data_dir: Path) -> tuple[subprocess.Popen, str]:
    port = _free_port()
    env = dict(os.environ, PORT=str(port), DATA_DIR=str(data_dir))
    proc = subprocess.Popen([sys.executable, "-m", "app"], env=env, cwd=str(PROJECT_DIR),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            urllib.request.urlopen(base + "/", timeout=1)
            return proc, base
        except (urllib.error.URLError, ConnectionError, OSError):
            if proc.poll() is not None:
                raise RuntimeError("server exited during start")
            time.sleep(0.2)
    proc.kill()
    raise RuntimeError("server did not start")


@pytest.fixture
def server(tmp_path: Path):
    proc, base = _start_server(tmp_path / "data")
    yield Site(base)
    proc.terminate()
    proc.wait(timeout=10)


def _poll_ids(text: str) -> list[int]:
    return [int(x) for x in re.findall(r'href="/polls/(\d+)"', text)]


def _option_ids(text: str) -> list[int]:
    return [int(x) for x in re.findall(r'name="option_id" value="(\d+)"', text)]


def test_browse_polls(server: Site) -> None:
    status, text = server.get("/")
    assert status == 200
    assert "Which programming language do you like most?" in text
    assert len(set(_poll_ids(text))) == 3
    first = sorted(set(_poll_ids(text)))[0]
    status, text = server.get(f"/polls/{first}")
    assert status == 200
    assert 'type="radio"' in text
    assert "Python" in text


def test_cast_vote(server: Site) -> None:
    _, text = server.get("/polls/1")
    option = _option_ids(text)[0]
    status, text, headers = server.post("/polls/1/vote", {"option_id": option})
    assert status == 303
    assert "/polls/1" in headers["Location"]
    status, text = server.get("/polls/1?thanks=1")
    assert "Thank you for your vote." in text
    assert "You have already voted" in text
    assert "%" in text


def test_reject_invalid_vote(server: Site) -> None:
    status, text, _ = server.post("/polls/1/vote", {})
    assert status == 400
    assert "Please choose an option." in text
    _, other_text = server.get("/polls/2")
    other_option = _option_ids(other_text)[0]
    status, text, _ = server.post("/polls/1/vote", {"option_id": other_option})
    assert status == 400
    assert "That option is not part of this poll." in text
    status, text = server.get("/polls/1")
    assert "You have already voted" not in text


def test_one_vote_per_poll(server: Site) -> None:
    _, text = server.get("/polls/1")
    first, second = _option_ids(text)[:2]
    assert server.post("/polls/1/vote", {"option_id": first})[0] == 303
    status, text, headers = server.post("/polls/1/vote", {"option_id": second})
    assert status == 303
    assert "thanks=1" not in headers["Location"]
    _, page = server.get("/polls/1")
    assert "You have already voted" in page
    assert "Thank you for your vote." not in page
    _, results = server.get("/results")
    total = re.search(r"Total votes: (\d+)", results)
    assert total is not None
    assert int(total.group(1)) == 12  # 11 sample votes in poll 1, plus the one vote cast here


def test_result_after_vote(server: Site) -> None:
    _, text = server.get("/polls/3")
    option = _option_ids(text)[0]
    server.post("/polls/3/vote", {"option_id": option})
    _, text = server.get("/polls/3")
    assert "You have already voted" in text
    assert "class=\"bar-fill\"" in text
    assert "%)" in text


def test_all_results(server: Site) -> None:
    status, text = server.get("/results")
    assert status == 200
    assert "Which season is your favorite?" in text
    assert "Where should we hold the team lunch?" in text
    assert "Total votes:" in text


def test_navigation(server: Site) -> None:
    for path in ["/", "/results", "/polls/1"]:
        _, text = server.get(path)
        assert 'href="/"' in text
        assert 'href="/results"' in text
        assert ">Polls<" in text and ">Results<" in text


def test_sample_data_on_empty_data_dir(server: Site) -> None:
    _, text = server.get("/results")
    assert "Total votes: 11" in text  # sample votes for poll 1 (5 + 3 + 1 + 2)
    _, polls = server.get("/")
    assert len(set(_poll_ids(polls))) == 3


def test_theme(server: Site) -> None:
    _, css = server.get("/static/style.css")
    assert "background: #FFFFE0" in css
    assert "--slate: #2F4F4F" in css
    assert "background: #ffffff" not in css.lower()
    assert "#000080" not in css.lower()
    _, page = server.get("/")
    assert "/static/style.css" in page


def test_voted_poll_state(server: Site) -> None:
    _, text = server.get("/polls/2")
    option = _option_ids(text)[0]
    assert server.post("/polls/2/vote", {"option_id": option})[0] == 303
    _, page = server.get("/polls/2")
    assert "You have already voted" in page
    assert 'type="radio" name="option_id" value=' in page and " disabled>" in page
    assert '<button type="submit" class="button" disabled>Vote</button>' in page
    assert "class=\"bar-fill\"" in page
    _, before = server.get("/results")
    before_total = int(re.search(r"Total votes: (\d+)", before).group(1))
    status, text, _ = server.post("/polls/2/vote", {"option_id": option})
    assert status == 303
    _, again = server.get("/polls/2")
    assert "Thank you for your vote." not in again
    _, after = server.get("/results")
    assert int(re.search(r"Total votes: (\d+)", after).group(1)) == before_total


def test_public_access(server: Site) -> None:
    status, text = server.get("/")
    assert status == 200
    assert "Polls" in text
