"""
Service de synthèse vocale Chatterbox V3 (Resemble AI).
Optimisé pour Kaggle GPU (T4 16Go), multilingue (Français) avec support de clonage de voix.
"""

import gc
import logging
import os
from pathlib import Path
from typing import Optional

from src.config import AUDIO_DIR, CHATTERBOX_MODEL, VOICE_LANGUAGE

logger = logging.getLogger(__name__)


class ChatterboxService:
    def __init__(
        self,
        language: str = VOICE_LANGUAGE,
        model_version: str = CHATTERBOX_MODEL,
        device: Optional[str] = None,
    ):
        self.language = language
        self.model_version = model_version
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
        """
        Charge Chatterbox Multilingual V3 uniquement au moment de la génération
        afin de minimiser l'empreinte VRAM.
        """
        if self._model is not None:
            return self._model

        logger.info(f"Chargement de Chatterbox Multilingual ({self.model_version}) sur {self.device}...")
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            self._model = ChatterboxMultilingualTTS.from_pretrained(
                device=self.device,
                t3_model=self.model_version,
            )
            logger.info("Chatterbox V3 chargé avec succès.")
            return self._model
        except ImportError:
            logger.warning("chatterbox-tts n'est pas installé dans cet environnement.")
            raise

    def _unload_model(self):
        """
        Décharge le modèle et libère la VRAM du GPU Kaggle.
        """
        if self._model is not None:
            logger.info("Déchargement de Chatterbox et libération de la VRAM...")
            del self._model
            self._model = None

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        except ImportError:
            pass

    def generate_voice(
        self,
        text: str,
        output_filename: str = "test_voice.wav",
        output_dir: Optional[Path] = None,
        audio_prompt_path: Optional[str] = None,
        language_id: Optional[str] = None,
    ) -> Path:
        """
        Génère un fichier audio WAV à partir du texte.
        Supporte l'échantillon vocal pour le clonage si audio_prompt_path est fourni.
        """
        target_dir = output_dir or AUDIO_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / output_filename
        lang = language_id or self.language

        try:
            model = self._load_model()
            import torchaudio as ta

            kwargs = {"language_id": lang}
            if audio_prompt_path and os.path.exists(audio_prompt_path):
                logger.info(f"Utilisation de l'échantillon vocal pour le clonage : {audio_prompt_path}")
                kwargs["audio_prompt_path"] = audio_prompt_path

            logger.info(f"Synthèse vocale en cours (langue={lang})...")
            wav = model.generate(text, **kwargs)

            ta.save(str(output_path), wav, model.sr)
            logger.info(f"Audio généré avec succès : {output_path}")

        except ImportError as e:
            # Mode fallback (si exécuté sur MacBook de dev sans chatterbox-tts installé)
            logger.warning(f"Chatterbox non disponible ({e}), tentative de génération de secours...")
            self._generate_fallback(text, output_path, lang)
        finally:
            self._unload_model()

        return output_path

    def _generate_fallback(self, text: str, output_path: Path, language: str):
        """
        Génération légère de secours pour les tests locaux (ex. sur MacBook sans GPU).
        Utilise un son de synthèse simple ou gTTS si disponible.
        """
        try:
            # Tentative via gTTS si disponible
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            mp3_tmp = output_path.with_suffix(".mp3")
            tts.save(str(mp3_tmp))
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3_tmp), "-ar", "24000", "-ac", "1", str(output_path)],
                check=True,
                capture_output=True,
            )
            if mp3_tmp.exists():
                mp3_tmp.unlink()
            logger.info(f"Audio de secours (gTTS) généré : {output_path}")
            return
        except Exception:
            pass

        # Fallback universel : générer un WAV avec une onde sinusoïdale modulée ou silence pour les tests
        import math
        import wave
        sample_rate = 24000
        # Durée proportionnelle au nombre de mots (environ 150 mots/minute = 2.5 mots/sec)
        words = len(text.split())
        duration = max(3.0, words / 2.5)
        num_samples = int(duration * sample_rate)

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            data = bytearray()
            for i in range(num_samples):
                # Onde douce à 440 Hz modulée pour simuler une voix lors des tests locaux
                t = i / sample_rate
                env = 0.5 * (1 + math.sin(2 * math.pi * 3 * t))
                val = int(env * 8000 * math.sin(2 * math.pi * 440 * t))
                data.extend(val.to_bytes(2, byteorder="little", signed=True))
            wav_file.writeframes(data)
        logger.info(f"Audio de test synthétisé localement : {output_path} ({duration:.1f}s)")
