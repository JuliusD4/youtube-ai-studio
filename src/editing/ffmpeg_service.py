"""
Service de montage et d'assemblage vidéo automatique via FFmpeg.
Assure l'harmonisation des dimensions (1080p), l'alignement audio/vidéo et l'incrustation des sous-titres.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from src.config import FINAL_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH

logger = logging.getLogger(__name__)


class FFmpegService:
    def __init__(
        self,
        width: int = VIDEO_WIDTH,
        height: int = VIDEO_HEIGHT,
        fps: int = VIDEO_FPS,
    ):
        self.width = width
        self.height = height
        self.fps = fps

    def get_media_duration(self, file_path: Path) -> float:
        """Récupère la durée précise d'un fichier audio ou vidéo en secondes."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception as e:
            logger.warning(f"Impossible de lire la durée avec ffprobe ({e}), fallback wave...")
            try:
                import wave
                with wave.open(str(file_path), "rb") as wf:
                    return wf.getnframes() / float(wf.getframerate())
            except Exception:
                return 5.0

    def create_color_background(
        self,
        duration: float,
        output_path: Path,
        color: str = "#1A1A24",
    ) -> Path:
        """Génère un clip vidéo de fond uni aux dimensions cibles."""
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={self.width}x{self.height}:r={self.fps}:d={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    def assemble_video(
        self,
        audio_path: Path,
        visual_path: Optional[Path] = None,
        subtitles_path: Optional[Path] = None,
        output_filename: str = "video_test.mp4",
        output_dir: Optional[Path] = None,
        burn_subtitles: bool = True,
    ) -> Path:
        """
        Assemble la vidéo finale :
        - Synchronise la vidéo sur la durée exacte de l'audio.
        - Redimensionne en 1920x1080 (16:9) sans déformation.
        - Ajoute l'audio de la voix générée.
        - Incruste les sous-titres SRT de manière lisible.
        """
        target_dir = output_dir or FINAL_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / output_filename

        audio_duration = self.get_media_duration(audio_path)
        logger.info(f"Durée de la piste audio : {audio_duration:.2f} secondes.")

        # Si aucun visuel fourni, créer un fond propre
        temp_bg = None
        if visual_path is None or not visual_path.exists():
            temp_bg = target_dir / "temp_bg.mp4"
            logger.info("Aucun visuel fourni, génération d'un arrière-plan vidéo temporaire...")
            self.create_color_background(audio_duration, temp_bg)
            input_video = temp_bg
        else:
            input_video = visual_path

        # Préparation des filtres vidéo
        # 1. Mise à l'échelle 1920x1080 avec maintien du ratio d'aspect et padding centré
        scale_pad_filter = (
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={self.fps}"
        )

        video_filters = [scale_pad_filter]

        # 2. Incrustation des sous-titres si demandée et disponible
        if burn_subtitles and subtitles_path and subtitles_path.exists():
            # Échapper les caractères spéciaux dans le chemin pour le filtre subtitles FFmpeg
            srt_escaped = str(subtitles_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            subtitle_style = (
                "FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                "BorderStyle=3,Outline=2,Shadow=1,MarginV=40,Alignment=2"
            )
            video_filters.append(f"subtitles='{srt_escaped}':force_style='{subtitle_style}'")

        filter_complex = ",".join(video_filters)

        # Commande FFmpeg principale
        # -stream_loop -1 boucle la vidéo source si celle-ci est plus courte que l'audio
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(input_video),
            "-i", str(audio_path),
            "-filter_complex", f"[0:v]{filter_complex}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-t", f"{audio_duration:.3f}",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path),
        ]

        logger.info(f"Lancement de l'assemblage FFmpeg vers {output_path}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Vidéo assemblée avec succès : {output_path} ({output_path.stat().st_size} octets)")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur lors de l'assemblage FFmpeg : {e.stderr}")
            # Si le filtre subtitles a échoué (ex. libass manquant), réessayer sans sous-titres
            if burn_subtitles and "subtitles" in filter_complex:
                logger.warning("Nouvel essai FFmpeg sans filtre subtitles...")
                return self.assemble_video(
                    audio_path=audio_path,
                    visual_path=visual_path,
                    subtitles_path=None,
                    output_filename=output_filename,
                    output_dir=output_dir,
                    burn_subtitles=False,
                )
            raise
        finally:
            if temp_bg and temp_bg.exists():
                temp_bg.unlink(missing_ok=True)

        return output_path
