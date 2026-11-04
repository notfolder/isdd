"""E2E テストの補助（テスト用サーバーの起動、画面操作の共通処理）。"""

import socket
import threading

from waitress import create_server

from app import create_app


def free_port():
    """空いているローカルのポート番号を返す。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class RunningServer:
    """テスト用の Waitress を別スレッドで動かす。url と app を持つ。"""

    def __init__(self, app, port):
        self.app = app
        self.url = f"http://127.0.0.1:{port}"
        self._server = create_server(app, host="127.0.0.1", port=port, threads=8)
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            self._server.run()
        except OSError:
            # stop() で閉じたソケットを待っていた場合は終了として扱う
            pass

    def start(self):
        self._thread.start()

    def stop(self):
        self._server.close()
        self._thread.join(timeout=5)


def start_app_server(data_dir, idle_timeout=1800):
    """一時の DATA_DIR で Web アプリを作り、起動した RunningServer を返す。"""
    app = create_app(
        {"PORT": 0, "DATA_DIR": str(data_dir), "SESSION_IDLE_TIMEOUT_SECONDS": idle_timeout}
    )
    server = RunningServer(app, free_port())
    server.start()
    return server


def register(page, base, number, name, password="password1"):
    """アカウント登録画面で 1 件登録し、成功の案内を確かめる。"""
    page.goto(base + "/accounts/register/")
    page.fill("#id_employee_number", number)
    page.fill("#id_name", name)
    page.fill("#id_password", password)
    page.get_by_role("button", name="登録", exact=True).click()


def login(page, base, number, password="password1"):
    """ログイン画面からログインする。"""
    page.goto(base + "/login/")
    page.fill("#id_employee_number", number)
    page.fill("#id_password", password)
    page.get_by_role("button", name="ログイン", exact=True).click()


def logout(page):
    """ログアウトボタンを押す。"""
    page.get_by_role("button", name="ログアウト", exact=True).click()


def save_equipment(page, base, number, name):
    """備品の登録画面で 1 件登録する。"""
    page.goto(base + "/equipment/new/")
    page.fill("#id_equipment_number", number)
    page.fill("#id_name", name)
    page.get_by_role("button", name="保存", exact=True).click()
