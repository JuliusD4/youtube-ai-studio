"""
Service de sous-titrage automatique utilisant OpenAI Whisper.
Génère des fichiers de sous-titres .srt horodatés et synchronisés.
"""

import gc
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional

from src.config import SUBTITLES_DIR, WHISPER_MODEL_NAME

logger = logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """Convertit un timestamp en secondes vers le format SRT (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


class WhisperService:
    def __init__(self, model_name: str = WHISPER_MODEL_NAME, device: Optional[str] = None):
        self.model_name = model_name
        self.device = device or self._detect_device()
        self._model = None

    def _detect_device(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def _load_model(self):
        if self._model is not None:
            return self._model

        logger.info(f"Chargement du modèle Whisper ({self.model_name}) sur {self.device}...")
        try:
            import whisper
            self._model = whisper.load_model(self.model_name, device=self.device)
            return self._model
        except ImportError:
            logger.warning("Le package 'openai-whisper' n'est pas installé.")
            raise

    def _unload_model(self):
        if self._model is not None:
            logger.info("Déchargement de Whisper et libération de la mémoire...")
            del self._model
            self._model = None

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def transcribe_to_srt(
        self,
        audio_path: Path,
        output_filename: str = "test_subtitles.srt",
        output_dir: Optional[Path] = None,
        language: Optional[str] = "fr",
        fallback_text: Optional[str] = None,
    ) -> Path:
        """
        Transcrit un fichier audio et écrit les sous-titres au format SRT.
        """
        target_dir = output_dir or SUBTITLES_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / output_filename

        try:
            model = self._load_model()
            logger.info(f"Transcription Whisper en cours pour {audio_path}...")
            result = model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe",
                word_timestamps=True,
                verbose=False,
            )

            segments = result.get("segments", [])
            self._write_srt(segments, output_path)
            logger.info(f"Sous-titres SRT générés avec succès : {output_path}")

        except ImportError as e:
            logger.warning(f"Whisper indisponible ({e}). Génération de sous-titres de secours...")
            self._generate_fallback_srt(audio_path, output_path, fallback_text)
        finally:
            self._unload_model()

        return output_path

    def _write_srt(self, segments: List[Dict], output_path: Path):
        """Écrit les segments transcrits dans un fichier SRT valide."""
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                start = format_timestamp(seg["start"])
                end = format_timestamp(seg["end"])
                text = seg["text"].strip()
                f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

    def _generate_fallback_srt(self, audio_path: Path, output_path: Path, text: Optional[str]):
        """Génère un SRT simulé basé sur la durée réelle du fichier audio."""
        import wave
        duration = 5.0
        try:
            with wave.open(str(audio_path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)
        except Exception:
            pass

        content_text = text or "Sous-titres générés automatiquement par AI YouTube Studio."
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"1\n00:00:00,500 --> {format_timestamp(max(1.0, duration - 0.5))}\n{content_text}\n\n")
        logger.info(f"SRT de secours créé : {output_path} (durée={duration:.1f}s)")
