"""備品・貸出・返却・権限に関する E2E テスト。"""

import sys
import threading
from pathlib import Path as _Path
_HERE = _Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


import unittest
from datetime import datetime, timedelta, timezone
from typing import Callable, List

from support import AppServer, Client, equipment_id, seed_accounts

JST = timezone(timedelta(hours=9))
CONFLICT = "他の担当者が先にこの備品を更新しました。貸出状況の画面から開き直してください"


def login(client: Client, number: str, password: str):
    page = client.get("/login/")
    return client.submit(page, "ログイン", {"employee_number": number, "password": password})


def create_equipment(client: Client, number: str, name: str):
    page = client.get("/equipment/new/")
    return client.submit(page, "保存", {"equipment_number": number, "name": name})


class EquipmentTestCase(unittest.TestCase):
    """担当者 123456 と社員 654321 を用意する共通の準備。"""

    def setUp(self) -> None:
        self.server = AppServer().start()
        self.addCleanup(self.server.stop)
        seed_accounts(self.server, ["123456", "654321"], password="password1")
        self.manager = Client(self.server)
        login(self.manager, "123456", "password1")
        self.member = Client(self.server)
        login(self.member, "654321", "password1")

    def lend(self, number: str, borrower: str = "654321") -> None:
        self.manager.post(f"/equipment/{equipment_id(self.server, number)}/lend/",
                          {"borrower": borrower, "lent_on": datetime.now(JST).date().isoformat()})


class TestViewLendingStatus(EquipmentTestCase):
    def test_view_lending_status(self) -> None:
        for number in ["EQ-0002", "EQ-0001", "EQ-0003"]:
            create_equipment(self.manager, number, "備品 " + number)
        self.lend("EQ-0002")
        page = Client(self.server).get("/")
        rows = page.rows("data-equipment-number")
        self.assertEqual([r.attrs["data-equipment-number"] for r in rows], ["EQ-0001", "EQ-0002", "EQ-0003"])
        lent = page.row("data-equipment-number", "EQ-0002")
        self.assertIn("貸出中", lent.text)
        self.assertIn("テスト654321", lent.text)
        self.assertIn(datetime.now(JST).date().isoformat(), lent.text)
        self.assertIn("空き", page.row("data-equipment-number", "EQ-0001").text)
        labels = [c["text"] for f in page.forms() for c in f["controls"] if c["kind"] == "button"]
        self.assertNotIn("修正", labels)
        self.assertNotIn("貸出", labels)


class TestEmptyEquipmentList(unittest.TestCase):
    def test_empty_equipment_list(self) -> None:
        server = AppServer().start()
        self.addCleanup(server.stop)
        page = Client(server).get("/")
        self.assertTrue(page.has_text("備品は登録されていません"))
        self.assertEqual(page.rows("data-equipment-number"), [])


class TestCreateEquipment(EquipmentTestCase):
    def test_create_equipment(self) -> None:
        page = create_equipment(self.manager, "EQ-0001", "ノート")
        self.assertTrue(page.has_text("備品を登録しました"))
        self.assertIn("空き", page.row("data-equipment-number", "EQ-0001").text)
        page = create_equipment(self.manager, "EQ-日本", "ノート")
        self.assertIn("管理番号は半角の英数字とハイフンで 20 文字以内で入力してください", page.by_class("field-error"))
        self.assertEqual(page.by_id("id_equipment_number").attrs.get("value"), "EQ-日本")
        page = create_equipment(self.manager, "A" * 21, "ノート")
        self.assertIn("管理番号は半角の英数字とハイフンで 20 文字以内で入力してください", page.by_class("field-error"))
        page = create_equipment(self.manager, "EQ-0002", "名" * 51)
        self.assertIn("備品名は 50 文字以内で入力してください", page.by_class("field-error"))
        page = create_equipment(self.manager, "EQ-0001", "重複")
        self.assertIn("この管理番号は既に使われています", page.by_class("field-error"))


class TestUpdateEquipment(EquipmentTestCase):
    def test_update_equipment(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        identifier = equipment_id(self.server, "EQ-0001")
        other = Client(self.server)
        login(other, "123456", "password1")
        page_a = self.manager.get(f"/equipment/{identifier}/edit/")
        page_b = other.get(f"/equipment/{identifier}/edit/")
        page_b = other.submit(page_b, "保存", {"name": "ノートPC"})
        self.assertTrue(page_b.has_text("備品を更新しました"))
        page_a = self.manager.submit(page_a, "保存", {"equipment_number": "EQ-0009"})
        self.assertEqual(page_a.by_class("error"), [CONFLICT])
        self.assertEqual(page_a.by_id("id_equipment_number").attrs.get("value"), "EQ-0009")
        top = self.manager.get("/")
        self.assertIn("ノートPC", top.row("data-equipment-number", "EQ-0001").text)


class TestDeleteEquipment(EquipmentTestCase):
    def test_delete_equipment(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        create_equipment(self.manager, "EQ-0002", "モニター")
        self.lend("EQ-0002")
        page = self.manager.get("/")
        page = self.manager.submit(page, "削除", must_contain=f"/equipment/{equipment_id(self.server, 'EQ-0001')}/delete/")
        self.assertTrue(page.has_text("備品を削除しました"))
        self.assertIsNone(page.row("data-equipment-number", "EQ-0001"))
        page = self.manager.submit(page, "削除", must_contain=f"/equipment/{equipment_id(self.server, 'EQ-0002')}/delete/")
        self.assertIn("この備品は貸出中のため削除できません。先に返却を処理してください", page.by_class("error"))
        self.assertIsNotNone(page.row("data-equipment-number", "EQ-0002"))


class TestLendEquipment(EquipmentTestCase):
    def test_lend_equipment(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        page = self.manager.get("/")
        page = self.manager.submit(page, "貸出", must_contain=f"/equipment/{equipment_id(self.server, 'EQ-0001')}/lend/")
        self.assertEqual(page.by_class("lending-equipment"), ["備品: EQ-0001 ノート"])
        page = self.manager.submit(page, "登録", {"borrower": ""})
        self.assertIn("借りる社員を選んでください", page.by_class("field-error"))
        tomorrow = (datetime.now(JST).date() + timedelta(days=1)).isoformat()
        page = self.manager.submit(page, "登録", {"borrower": "654321", "lent_on": tomorrow})
        self.assertIn("貸出日に未来の日付は入力できません", page.by_class("field-error"))
        page = self.manager.submit(page, "登録", {"borrower": "654321",
                                                  "lent_on": datetime.now(JST).date().isoformat()})
        self.assertTrue(page.has_text("貸出を登録しました"))
        self.assertIn("貸出中", page.row("data-equipment-number", "EQ-0001").text)
        page = self.manager.post(f"/equipment/{equipment_id(self.server, 'EQ-0001')}/lend/",
                                 {"borrower": "654321", "lent_on": datetime.now(JST).date().isoformat()})
        self.assertTrue(page.has_text("この備品は既に貸出中です"))


class TestReturnEquipment(EquipmentTestCase):
    def test_return_equipment(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        self.lend("EQ-0001")
        page = self.manager.get("/")
        page = self.manager.submit(page, "返却", must_contain=f"/equipment/{equipment_id(self.server, 'EQ-0001')}/return/")
        self.assertTrue(page.has_text("返却を登録しました"))
        self.assertIn("空き", page.row("data-equipment-number", "EQ-0001").text)
        page = self.manager.post(f"/equipment/{equipment_id(self.server, 'EQ-0001')}/return/", {})
        self.assertTrue(page.has_text("この備品は既に返却されています"))


class TestRestrictNonManager(EquipmentTestCase):
    def test_restrict_non_manager(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        identifier = equipment_id(self.server, "EQ-0001")
        page = self.member.get("/")
        labels = [c["text"] for f in page.forms() for c in f["controls"] if c["kind"] == "button"]
        for label in ["修正", "削除", "貸出", "返却"]:
            self.assertNotIn(label, labels)
        self.assertEqual(page.by_class("current-user"), ["テスト654321"])
        page = self.member.get("/equipment/new/")
        self.assertTrue(page.has_text("この操作は担当者だけが行えます"))
        page = self.member.post(f"/equipment/{identifier}/delete/", {"version": "1"})
        self.assertTrue(page.has_text("この操作は担当者だけが行えます"))
        self.assertIsNotNone(self.manager.get("/").row("data-equipment-number", "EQ-0001"))
        anonymous = Client(self.server)
        page = anonymous.post(f"/equipment/{identifier}/lend/", {"borrower": "654321", "lent_on": "2000-01-01"})
        self.assertIsNotNone(page.by_id("id_employee_number"))
        self.assertIsNotNone(anonymous.get("/accounts/").by_id("id_employee_number"))


def _race(calls: List[Callable[[], object]]) -> List[object]:
    """各呼び出しを、同時に開始させる（全員が開始の合図で待ってから一斉に送る）。結果は呼び出し順。"""
    barrier = threading.Barrier(len(calls))
    results: List[object] = [None] * len(calls)
    errors: List[BaseException] = []

    def run(index: int) -> None:
        try:
            barrier.wait()
            results[index] = calls[index]()
        except BaseException as error:  # 失敗をテストに伝えるため記録する
            errors.append(error)

    threads = [threading.Thread(target=run, args=(i,)) for i in range(len(calls))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if errors:
        raise errors[0]
    return results


class TestKeepLendingOnUpdate(EquipmentTestCase):
    def test_keep_lending_on_update(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        self.lend("EQ-0001")
        today = datetime.now(JST).date().isoformat()
        page = self.manager.get(f"/equipment/{equipment_id(self.server, 'EQ-0001')}/edit/")
        page = self.manager.submit(page, "保存", {"name": "ノートPC"})
        self.assertTrue(page.has_text("備品を更新しました"))
        row = self.manager.get("/").row("data-equipment-number", "EQ-0001").text
        self.assertIn("ノートPC", row)
        self.assertIn("貸出中", row)
        self.assertIn("テスト654321", row)
        self.assertIn(today, row)


class TestConcurrentLendReturn(EquipmentTestCase):
    def test_concurrent_lend_return(self) -> None:
        create_equipment(self.manager, "EQ-0001", "ノート")
        identifier = equipment_id(self.server, "EQ-0001")
        other = Client(self.server)
        login(other, "123456", "password1")
        today = datetime.now(JST).date().isoformat()
        lend_form = {"borrower": "654321", "lent_on": today}
        pages = _race([
            lambda: self.manager.post(f"/equipment/{identifier}/lend/", lend_form),
            lambda: other.post(f"/equipment/{identifier}/lend/", lend_form),
        ])
        messages = sorted(m for page in pages for m in page.by_class("message"))
        self.assertEqual(messages, sorted(["貸出を登録しました", "この備品は既に貸出中です"]))
        self.assertIn("貸出中", self.manager.get("/").row("data-equipment-number", "EQ-0001").text)

        pages = _race([
            lambda: self.manager.post(f"/equipment/{identifier}/return/", {}),
            lambda: other.post(f"/equipment/{identifier}/return/", {}),
        ])
        messages = sorted(m for page in pages for m in page.by_class("message"))
        self.assertEqual(messages, sorted(["返却を登録しました", "この備品は既に返却されています"]))
        self.assertIn("空き", self.manager.get("/").row("data-equipment-number", "EQ-0001").text)


if __name__ == "__main__":
    unittest.main()
