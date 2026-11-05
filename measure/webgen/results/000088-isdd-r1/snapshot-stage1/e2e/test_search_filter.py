"""検索と絞り込みの E2E テスト。"""

import unittest
from urllib.parse import urlencode

from e2e.harness import SiteServer, result_count


class SearchFilterTest(unittest.TestCase):
    def setUp(self):
        self.site = SiteServer()

    def tearDown(self):
        self.site.stop()

    def search(self, **params):
        return self.site.request("GET", "/?" + urlencode(params))

    def test_search_species(self):
        response = self.search(q="wolf")
        self.assertEqual(response.status, 200)
        self.assertEqual(result_count(response.body), 1)
        self.assertIn("Gray wolf", response.body)
        self.assertNotIn("Asian elephant", response.body)

        none = self.search(q="zzz-no-such-species")
        self.assertIsNone(result_count(none.body))
        self.assertIn("No species match the current search and filters.", none.body)

    def test_filter_species(self):
        self.assertEqual(result_count(self.search(taxonomic_class="Birds").body), 2)
        self.assertEqual(
            result_count(self.search(taxonomic_class="Birds", diet="Carnivore").body), 2
        )
        marine_herbivores = self.search(habitat="Marine", diet="Herbivore").body
        self.assertEqual(result_count(marine_herbivores), 1)
        self.assertIn("Green sea turtle", marine_herbivores)
        self.assertEqual(result_count(self.search(conservation_status="Endangered").body), 2)
        self.assertEqual(result_count(self.search(q="mountain", habitat="Mountain").body), 1)

        # Clear（条件なし）で全件に戻る
        self.assertEqual(result_count(self.site.request("GET", "/").body), 12)


if __name__ == "__main__":
    unittest.main()
