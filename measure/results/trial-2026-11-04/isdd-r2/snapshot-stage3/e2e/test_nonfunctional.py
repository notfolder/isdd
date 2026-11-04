"""非機能要件の確認（応答時間、50 人の同時利用）。"""

import sys
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


import threading
import time
import unittest

from support import AppServer, Client, seed_accounts
from test_equipment import create_equipment, login  # noqa: F401


class TestResponseTime(unittest.TestCase):
    def test_response_time(self) -> None:
        server = AppServer().start()
        self.addCleanup(server.stop)
        seed_accounts(server, ["123456"])
        manager = Client(server)
        login(manager, "123456", "password1")
        for index in range(5):
            create_equipment(manager, f"EQ-{index:04d}", "備品")
        elapsed = []
        lock = threading.Lock()

        def worker() -> None:
            start = time.time()
            page = Client(server).get("/")
            with lock:
                elapsed.append((time.time() - start, page.status))

        threads = [threading.Thread(target=worker) for _ in range(50)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(elapsed), 50)
        self.assertTrue(all(status == 200 for _, status in elapsed))
        self.assertLess(max(seconds for seconds, _ in elapsed), 3.0)


class TestConcurrentUsers(unittest.TestCase):
    def test_concurrent_users(self) -> None:
        server = AppServer().start()
        self.addCleanup(server.stop)
        numbers = [f"{100000 + i}" for i in range(50)]
        seed_accounts(server, numbers)
        errors = []
        lock = threading.Lock()

        def member_session(number: str) -> None:
            try:
                client = Client(server)
                page = login(client, number, "password1")
                if page.by_class("current-user") == []:
                    raise AssertionError(f"ログインできません: {number}")
                page = client.get("/")
                if page.by_class("current-user") == []:
                    raise AssertionError(f"ログイン状態が続きません: {number}")
            except Exception as error:  # noqa: BLE001
                with lock:
                    errors.append(repr(error))

        threads = [threading.Thread(target=member_session, args=(n,)) for n in numbers]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])

        manager = Client(server)
        login(manager, numbers[0], "password1")

        def add_equipment(index: int) -> None:
            try:
                manager.post("/equipment/new/", {"equipment_number": f"CC-{index:03d}", "name": "同時"})
            except Exception as error:  # noqa: BLE001
                with lock:
                    errors.append(repr(error))

        writers = [threading.Thread(target=add_equipment, args=(i,)) for i in range(20)]
        for thread in writers:
            thread.start()
        for thread in writers:
            thread.join()
        self.assertEqual(errors, [])
        rows = manager.get("/").rows("data-equipment-number")
        self.assertEqual(len([r for r in rows if r.attrs["data-equipment-number"].startswith("CC-")]), 20)


if __name__ == "__main__":
    unittest.main()
