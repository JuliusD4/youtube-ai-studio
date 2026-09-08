"""
Tests unitaires pour le montage vidéo FFmpeg.
"""

import unittest
from pathlib import Path
from src.editing.ffmpeg_service import FFmpegService
from src.voice.chatterbox_service import ChatterboxService


class TestFFmpegService(unittest.TestCase):
    def setUp(self):
        self.service = FFmpegService(width=640, height=360, fps=24)

    def test_create_background_and_assemble(self):
        output_dir = Path("outputs/final")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Création d'un audio test
        voice_service = ChatterboxService()
        audio_path = voice_service.generate_voice(
            text="Test court pour le montage vidéo.",
            output_filename="unit_test_voice.wav",
        )
        self.assertTrue(audio_path.exists())

        # 2. Assemblage vidéo
        final_video = self.service.assemble_video(
            audio_path=audio_path,
            visual_path=None,
            subtitles_path=None,
            output_filename="unit_test_video.mp4",
            burn_subtitles=False,
        )
        self.assertTrue(final_video.exists())
        self.assertGreater(final_video.stat().st_size, 1000)

        # Nettoyage
        if audio_path.exists():
            audio_path.unlink()
        if final_video.exists():
            final_video.unlink()


if __name__ == "__main__":
    unittest.main()
