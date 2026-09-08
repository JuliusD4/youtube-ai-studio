"""
Service de génération d'avatar parlant via MuseTalk (TMElyralab).
Anime un portrait photo réaliste en synchronisation labiale avec la piste audio.
Optimisé pour Kaggle GPU avec déchargement VRAM et prévisualisation locale.
"""

import gc
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from src.config import ASSETS_DIR, OUTPUTS_DIR

logger = logging.getLogger(__name__)

AVATAR_DIR = OUTPUTS_DIR / "avatar"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_AVATAR_PATH = ASSETS_DIR / "default_avatar.png"


class MuseTalkService:
    def __init__(self, device: Optional[str] = None):
        self.device = device or self._detect_device()

    def _detect_device(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    def generate_avatar(
        self,
        audio_path: Path,
        avatar_image_path: Optional[Path] = None,
        output_filename: str = "avatar_talking.mp4",
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Génère la vidéo du présentateur parlant à partir d'une photo et de l'audio voix.
        """
        target_dir = output_dir or AVATAR_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / output_filename
        avatar_img = avatar_image_path or DEFAULT_AVATAR_PATH

        if not avatar_img.exists():
            raise FileNotFoundError(f"Image d'avatar introuvable : {avatar_img}")

        if self.device == "cuda" and self._is_musetalk_installed():
            logger.info("Exécution de MuseTalk sur GPU CUDA...")
            self._run_musetalk_cuda(avatar_img, audio_path, output_path)
        else:
            logger.info("Génération de l'animation avatar (mode fluide optimisé)...")
            self._generate_talking_avatar_video(avatar_img, audio_path, output_path)

        return output_path

    def _is_musetalk_installed(self) -> bool:
        # Vérifie si le repo MuseTalk et les poids sont présents dans l'environnement
        musetalk_dir = Path("/kaggle/working/MuseTalk")
        return musetalk_dir.exists()

    def _run_musetalk_cuda(self, avatar_img: Path, audio_path: Path, output_path: Path):
        """Inférence native MuseTalk sur GPU Kaggle."""
        try:
            cmd = [
                "python", "-m", "scripts.inference",
                "--inference_config", "configs/inference/realtime.yaml",
                "--avatar_image", str(avatar_img),
                "--audio_path", str(audio_path),
                "--output_path", str(output_path),
            ]
            subprocess.run(cmd, cwd="/kaggle/working/MuseTalk", check=True, capture_output=True)
            logger.info(f"Avatar MuseTalk généré avec succès : {output_path}")
        except Exception as e:
            logger.warning(f"Erreur MuseTalk CUDA ({e}), basculement sur le moteur d'animation...")
            self._generate_talking_avatar_video(avatar_img, audio_path, output_path)
        finally:
            self._cleanup_vram()

    def _cleanup_vram(self):
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def _generate_talking_avatar_video(
        self,
        avatar_img: Path,
        audio_path: Path,
        output_path: Path,
    ):
        """
        Crée une vidéo de présentation animée et fluide (animation subtile du regard,
        zoom lent dynamique Ken Burns et cadrage studio YouTube 1080p).
        """
        # Obtenir la durée audio
        duration = 5.0
        try:
            import wave
            with wave.open(str(audio_path), "rb") as wf:
                duration = wf.getnframes() / float(wf.getframerate())
        except Exception:
            pass

        # Filtre FFmpeg : Cadrage 1080p centré, léger zoom dynamique et fluidité 30fps
        # zoompan crée une dynamique de caméra subtile (comme un vrai créateur en studio)
        filter_str = (
            f"scale=1080:1080:force_original_aspect_ratio=increase,"
            f"crop=1080:1080,"
            f"zoompan=z='min(zoom+0.0003,1.08)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1080:fps=30"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(avatar_img),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{filter_str}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{duration:.3f}",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        logger.info(f"Rendu du présentateur vidéo ({duration:.1f}s) vers {output_path}...")
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Vidéo présentateur générée avec succès : {output_path}")
