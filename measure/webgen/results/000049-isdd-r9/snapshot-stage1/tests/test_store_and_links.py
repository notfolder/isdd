"""Unit tests for the SQLite store, sample data and WhatsApp links."""

import os
import tempfile
import unittest

from core.db import SAMPLE_BARBERS, SAMPLE_SERVICES, Store
from core.whatsapp import build_whatsapp_link, split_phone_list


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.tmp.name, "test.db"))
        self.store.init_schema()

    def tearDown(self):
        self.tmp.cleanup()

    def test_empty_store_has_no_rows(self):
        self.assertEqual(self.store.list_barbers(), [])
        self.assertEqual(self.store.list_services(), [])

    def test_sample_data_is_loaded_once_when_empty(self):
        self.assertTrue(self.store.seed_sample_data_if_empty())
        self.assertEqual(len(self.store.list_barbers()), len(SAMPLE_BARBERS))
        self.assertEqual(len(self.store.list_services()), len(SAMPLE_SERVICES))
        self.assertFalse(self.store.seed_sample_data_if_empty())
        self.assertEqual(len(self.store.list_barbers()), 3)

    def test_sample_counts_match_requirement(self):
        self.assertEqual(len(SAMPLE_BARBERS), 3)
        self.assertEqual(len(SAMPLE_SERVICES), 4)

    def test_add_and_list_keep_order(self):
        self.store.add_barber("First", "", "")
        self.store.add_barber("Second", "Beard", "+15550101")
        names = [b["name"] for b in self.store.list_barbers()]
        self.assertEqual(names, ["First", "Second"])

    def test_add_service_stores_cents(self):
        self.store.add_service("Cut", 1250, 20, "desc")
        row = self.store.list_services()[0]
        self.assertEqual(row["price_cents"], 1250)
        self.assertEqual(row["duration_min"], 20)

    def test_duplicate_names_are_allowed(self):
        self.store.add_barber("Same", "", "")
        self.store.add_barber("Same", "", "")
        self.assertEqual(len(self.store.list_barbers()), 2)


class WhatsAppLinkTests(unittest.TestCase):
    def test_link_has_digits_and_encoded_message(self):
        url = build_whatsapp_link("15550101", "Hi & welcome: 10:00?")
        self.assertEqual(url, "https://wa.me/15550101?text=Hi%20%26%20welcome%3A%2010%3A00%3F")

    def test_split_phone_list_trims_and_drops_blanks(self):
        self.assertEqual(split_phone_list(" a \n\n b,c ,\n"), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
