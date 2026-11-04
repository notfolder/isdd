"""サンプルの投入と起動時の初期化の単体テスト。"""

import tempfile
import unittest

from app import create_app
from app.db import connect_database, ensure_database_schema
from app.repository import SpeciesRepository
from app.seed import SAMPLE_SPECIES, seed_sample_species_if_empty


class SeedTest(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.connection = connect_database(self._dir.name)
        ensure_database_schema(self.connection)
        self.repo = SpeciesRepository(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        self._dir.cleanup()

    def test_empty_table_gets_twelve_samples(self) -> None:
        self.assertEqual(seed_sample_species_if_empty(self.repo), 12)
        self.assertEqual(len(self.repo.search()), len(SAMPLE_SPECIES))

    def test_samples_cover_every_conservation_status_and_habitat(self) -> None:
        seed_sample_species_if_empty(self.repo)
        rows = self.repo.search()
        self.assertEqual({r["conservation_status"] for r in rows}, {"LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD"})
        self.assertEqual({r["habitat"] for r in rows}, {"Terrestrial", "Freshwater", "Marine", "Mixed"})

    def test_second_run_does_nothing(self) -> None:
        seed_sample_species_if_empty(self.repo)
        self.assertEqual(seed_sample_species_if_empty(self.repo), 0)
        self.assertEqual(len(self.repo.search()), 12)

    def test_create_app_twice_does_not_duplicate_samples(self) -> None:
        with tempfile.TemporaryDirectory() as data_dir:
            create_app(data_dir)
            create_app(data_dir)
            conn = connect_database(data_dir)
            try:
                self.assertEqual(len(SpeciesRepository(conn).search()), 12)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
