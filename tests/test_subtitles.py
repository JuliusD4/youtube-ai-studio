"""
Tests unitaires pour le service Whisper et le formatage SRT.
"""

import unittest
from pathlib import Path
from src.subtitles.whisper_service import format_timestamp, WhisperService


class TestWhisperService(unittest.TestCase):
    def test_format_timestamp(self):
        # 0 secondes -> 00:00:00,000
        self.assertEqual(format_timestamp(0), "00:00:00,000")
        # 65.5 secondes -> 00:01:05,500
        self.assertEqual(format_timestamp(65.5), "00:01:05,500")
        # 3661.123 secondes -> 01:01:01,123
        self.assertEqual(format_timestamp(3661.123), "01:01:01,123")

    def test_write_srt(self):
        service = WhisperService()
        output_path = Path("outputs/subtitles/test_temp.srt")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        segments = [
            {"start": 0.0, "end": 2.5, "text": "Bonjour tout le monde."},
            {"start": 2.5, "end": 5.0, "text": "Bienvenue dans cette vidéo IA."},
        ]
        service._write_srt(segments, output_path)

        self.assertTrue(output_path.exists())
        content = output_path.read_text(encoding="utf-8")
        self.assertIn("00:00:00,000 --> 00:00:02,500", content)
        self.assertIn("Bonjour tout le monde.", content)
        output_path.unlink()


if __name__ == "__main__":
    unittest.main()
