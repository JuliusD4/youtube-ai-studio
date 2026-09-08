"""
Pipeline principal de génération vidéo pour AI YouTube Studio (Phase 1).
Orchestre Chatterbox V3, Whisper, Pexels et FFmpeg avec journalisation claire de chaque étape.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.broll.pexels_service import PexelsService
from src.config import FINAL_DIR
from src.editing.ffmpeg_service import FFmpegService
from src.subtitles.whisper_service import WhisperService
from src.voice.chatterbox_service import ChatterboxService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("AIYouTubeStudio")


class YouTubeVideoPipeline:
    def __init__(self):
        self.voice_service = ChatterboxService()
        self.whisper_service = WhisperService()
        self.pexels_service = PexelsService()
        self.ffmpeg_service = FFmpegService()

    def run(
        self,
        script_text: str,
        broll_query: str = "technology artificial intelligence",
        custom_voice_sample: Optional[str] = None,
        output_filename: str = "video_test.mp4",
        skip_existing: bool = False,
    ) -> Dict[str, Any]:
        """
        Exécute la chaîne complète de génération de vidéo :
        [1/5] Chatterbox V3 : Synthèse vocale
        [2/5] Whisper : Transcription et synchronisation SRT
        [3/5] Pexels : Récupération d'un B-roll vidéo HD
        [4/5] FFmpeg : Montage et incrustation des sous-titres
        [5/5] Export : Validation du fichier final
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("DÉMARRAGE DU PIPELINE AI YOUTUBE STUDIO (0 €)")
        logger.info("=" * 60)
        logger.info(f"Texte du script ({len(script_text)} caractères) :\n{script_text}\n")

        results = {
            "script": script_text,
            "broll_query": broll_query,
            "steps": {},
        }

        # -------------------------------------------------------------
        # Étape 1 : Synthèse vocale (Chatterbox V3)
        # -------------------------------------------------------------
        logger.info("[1/5] 🎙️ Génération de la voix avec Chatterbox V3...")
        t0 = time.time()
        audio_path = self.voice_service.generate_voice(
            text=script_text,
            output_filename="test_voice.wav",
            audio_prompt_path=custom_voice_sample,
            language_id="fr",
        )
        t_audio = time.time() - t0
        logger.info(f"[1/5] ✅ Audio voix généré : {audio_path} ({t_audio:.2f}s)")
        results["steps"]["voice"] = {"path": str(audio_path), "duration_sec": t_audio}

        # -------------------------------------------------------------
        # Étape 2 : Sous-titres (Whisper)
        # -------------------------------------------------------------
        logger.info("[2/5] 📝 Génération des sous-titres SRT avec Whisper...")
        t0 = time.time()
        subtitles_path = self.whisper_service.transcribe_to_srt(
            audio_path=audio_path,
            output_filename="test_subtitles.srt",
            language="fr",
            fallback_text=script_text,
        )
        t_sub = time.time() - t0
        logger.info(f"[2/5] ✅ Sous-titres SRT générés : {subtitles_path} ({t_sub:.2f}s)")
        results["steps"]["subtitles"] = {"path": str(subtitles_path), "duration_sec": t_sub}

        # -------------------------------------------------------------
        # Étape 3 : B-Roll (Pexels)
        # -------------------------------------------------------------
        logger.info(f"[3/5] 🎬 Recherche et téléchargement du B-roll Pexels ('{broll_query}')...")
        t0 = time.time()
        broll_path = None
        try:
            broll_path = self.pexels_service.get_best_broll(
                query=broll_query,
                output_filename="test_broll.mp4",
                orientation="landscape",
                min_duration=3,
            )
            t_broll = time.time() - t0
            logger.info(f"[3/5] ✅ B-roll téléchargé : {broll_path} ({t_broll:.2f}s)")
            results["steps"]["broll"] = {"path": str(broll_path), "duration_sec": t_broll}
        except Exception as e:
            logger.warning(f"[3/5] ⚠️ Impossible de récupérer le B-roll Pexels ({e}). Utilisation d'un fond de secours.")
            results["steps"]["broll"] = {"error": str(e)}

        # -------------------------------------------------------------
        # Étape 4 & 5 : Montage et Export (FFmpeg)
        # -------------------------------------------------------------
        logger.info(f"[4/5] 🎞️ Montage et assemblage de la vidéo finale avec FFmpeg...")
        t0 = time.time()
        final_video_path = self.ffmpeg_service.assemble_video(
            audio_path=audio_path,
            visual_path=broll_path,
            subtitles_path=subtitles_path,
            output_filename=output_filename,
            burn_subtitles=True,
        )
        t_edit = time.time() - t0
        logger.info(f"[4/5] ✅ Montage terminé : {final_video_path} ({t_edit:.2f}s)")
        results["steps"]["editing"] = {"path": str(final_video_path), "duration_sec": t_edit}

        total_duration = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"[5/5] 🎉 EXPORT FINAL RÉUSSI : {final_video_path}")
        logger.info(f"Taille du fichier : {final_video_path.stat().st_size / (1024*1024):.2f} Mo")
        logger.info(f"Temps total d'exécution : {total_duration:.2f}s")
        logger.info("=" * 60)

        results["final_video"] = str(final_video_path)
        results["total_duration_sec"] = total_duration
        return results


def main():
    script_par_defaut = (
        "Bonjour et bienvenue sur ma chaîne YouTube. "
        "Aujourd'hui, nous explorons comment l'intelligence artificielle transforme "
        "notre manière de créer du contenu vidéo de façon 100% autonome et gratuite."
    )
    pipeline = YouTubeVideoPipeline()
    pipeline.run(
        script_text=script_par_defaut,
        broll_query="artificial intelligence technology futuristic",
    )


if __name__ == "__main__":
    main()
