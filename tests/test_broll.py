"""
Tests unitaires pour le service Pexels B-roll.
"""

import unittest
from pathlib import Path
from src.broll.pexels_service import PexelsService
from src.config import PEXELS_API_KEY


class TestPexelsService(unittest.TestCase):
    def setUp(self):
        self.service = PexelsService(api_key=PEXELS_API_KEY)

    def test_search_broll(self):
        if not PEXELS_API_KEY:
            self.skipTest("PEXELS_API_KEY non disponible.")
        results = self.service.search_broll(
            query="technology nature",
            orientation="landscape",
            min_duration=3,
            per_page=2,
        )
        self.assertIsInstance(results, list)
        if results:
            first = results[0]
            self.assertIn("download_url", first)
            self.assertIn("duration", first)
            self.assertGreaterEqual(first["duration"], 3)


if __name__ == "__main__":
    unittest.main()
