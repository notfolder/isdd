"""ナビゲーションと配色の E2E テスト。"""

import unittest

from e2e.harness import SiteServer


class LayoutTest(unittest.TestCase):
    def setUp(self):
        self.site = SiteServer()

    def tearDown(self):
        self.site.stop()

    def test_navigation_and_style(self):
        for path in ["/", "/species/1", "/species/new"]:
            response = self.site.request("GET", path)
            self.assertEqual(response.status, 200, path)
            self.assertIn('href="/static/style.css"', response.body, path)
            self.assertIn('href="/"', response.body, path)
            self.assertIn('href="/species/new"', response.body, path)
            self.assertIn("Browse species", response.body, path)
            self.assertIn("Add species", response.body, path)

        stylesheet = self.site.request("GET", "/static/style.css")
        self.assertEqual(stylesheet.status, 200)
        css = stylesheet.body.upper()
        self.assertIn("#FAF0E6", css)  # linen（背景）
        self.assertIn("#800000", css)  # maroon（部品）


if __name__ == "__main__":
    unittest.main()
