"""
Tests unitaires pour l'initialisation et le fallback du service Chatterbox.
"""

import unittest
from pathlib import Path
from src.voice.chatterbox_service import ChatterboxService


class TestChatterboxService(unittest.TestCase):
    def test_voice_generation(self):
        service = ChatterboxService()
        output_file = Path("outputs/audio/unit_test_voice.wav")
        output_path = service.generate_voice(
            text="Bonjour, ceci est un test de synthèse vocale.",
            output_filename=output_file.name,
        )
        self.assertTrue(output_path.exists())
        self.assertGreater(output_path.stat().st_size, 100)
        output_path.unlink()


if __name__ == "__main__":
    unittest.main()
