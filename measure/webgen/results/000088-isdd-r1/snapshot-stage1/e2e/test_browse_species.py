"""一覧・詳細・初期起動の E2E テスト。"""

import os
import re
import unittest

from e2e.harness import SiteServer, result_count


class BrowseSpeciesTest(unittest.TestCase):
    def setUp(self):
        self.site = SiteServer()

    def tearDown(self):
        self.site.stop()

    def test_browse_species_list(self):
        response = self.site.request("GET", "/")
        self.assertEqual(response.status, 200)
        self.assertEqual(result_count(response.body), 12)
        body = response.body
        self.assertIn("Gray wolf", body)
        self.assertIn("Western honey bee", body)
        # 和名の昇順に並ぶこと
        self.assertLess(body.index("Asian elephant"), body.index("Atlantic salmon"))
        self.assertLess(body.index("Atlantic salmon"), body.index("Axolotl"))
        self.assertLess(body.index("Snow leopard"), body.index("Western honey bee"))
        # 上部のナビゲーション
        self.assertIn('href="/species/new"', body)
        self.assertIn("Browse species", body)
        self.assertIn("Add species", body)

    def test_view_species_detail(self):
        listing = self.site.request("GET", "/").body
        match = re.search(r'href="/species/(\d+)">Axolotl<', listing)
        self.assertIsNotNone(match)
        detail = self.site.request("GET", f"/species/{match.group(1)}")
        self.assertEqual(detail.status, 200)
        self.assertIn("Scientific name", detail.body)
        self.assertIn("Ambystoma mexicanum", detail.body)
        # 寿命の空欄は Unknown と表示される
        self.assertIn("Lifespan (years)", detail.body)
        self.assertIn("Unknown", detail.body)
        self.assertIn("Edit", detail.body)
        self.assertIn("Delete", detail.body)

    def test_missing_species_is_not_found(self):
        response = self.site.request("GET", "/species/99999")
        self.assertEqual(response.status, 404)
        self.assertIn("Species not found", response.body)


class FreshStartTest(unittest.TestCase):
    def test_fresh_start_shows_samples_and_keeps_them_after_restart(self):
        site = SiteServer()
        try:
            self.assertEqual(result_count(site.request("GET", "/").body), 12)
            data_dir = site.data_dir
        finally:
            site.stop()
        # 同じ保存先で起動し直しても、サンプルは重複して入らない
        again = SiteServer(data_dir=data_dir)
        try:
            self.assertEqual(result_count(again.request("GET", "/").body), 12)
            self.assertTrue(os.path.exists(os.path.join(data_dir, "species.db")))
        finally:
            again.stop()


if __name__ == "__main__":
    unittest.main()
