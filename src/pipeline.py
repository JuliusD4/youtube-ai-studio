"""
Pipeline principal de génération vidéo pour AI YouTube Studio.
Orchestre Chatterbox V3, MuseTalk, Pexels, Whisper et le compositeur multi-plans YouTube.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.avatar.musetalk_service import MuseTalkService
from src.broll.pexels_service import PexelsService
from src.config import FINAL_DIR
from src.editing.scene_compositor import YouTubeSceneCompositor
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
        self.avatar_service = MuseTalkService()
        self.whisper_service = WhisperService()
        self.pexels_service = PexelsService()
        self.compositor = YouTubeSceneCompositor()

    def run(
        self,
        script_text: str,
        broll_query: str = "technology artificial intelligence",
        avatar_image_path: Optional[Path] = None,
        custom_voice_sample: Optional[str] = None,
        output_filename: str = "video_finale.mp4",
    ) -> Dict[str, Any]:
        """
        Exécute la chaîne complète de génération de vidéo YouTube dynamique :
        [1/5] Chatterbox V3 : Synthèse vocale française (ou clonée)
        [2/5] MuseTalk : Présentateur avatar animé
        [3/5] Pexels : Récupération des B-roll vidéo HD
        [4/5] Whisper : Sous-titres SRT horodatés
        [5/5] Montage Pro : Alternance Facecam + PiP bas-droite + Musique de fond + SFX
        """
        start_time = time.time()
        logger.info("=" * 65)
        logger.info("DÉMARRAGE DU PIPELINE YOUTUBE DYNAMIQUE (AVATAR + PIP + SFX)")
        logger.info("=" * 65)
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
            output_filename="voice_track.wav",
            audio_prompt_path=custom_voice_sample,
            language_id="fr",
        )
        t_audio = time.time() - t0
        logger.info(f"[1/5] ✅ Audio voix généré : {audio_path} ({t_audio:.2f}s)")
        results["steps"]["voice"] = {"path": str(audio_path), "duration_sec": t_audio}

        # -------------------------------------------------------------
        # Étape 2 : Avatar présentateur (MuseTalk)
        # -------------------------------------------------------------
        logger.info("[2/5] 👤 Animation de l'avatar présentateur...")
        t0 = time.time()
        avatar_video_path = self.avatar_service.generate_avatar(
            audio_path=audio_path,
            avatar_image_path=avatar_image_path,
            output_filename="avatar_presenter.mp4",
        )
        t_avatar = time.time() - t0
        logger.info(f"[2/5] ✅ Présentateur généré : {avatar_video_path} ({t_avatar:.2f}s)")
        results["steps"]["avatar"] = {"path": str(avatar_video_path), "duration_sec": t_avatar}

        # -------------------------------------------------------------
        # Étape 3 : B-Roll (Pexels)
        # -------------------------------------------------------------
        logger.info(f"[3/5] 🎬 Recherche et téléchargement du B-roll Pexels ('{broll_query}')...")
        t0 = time.time()
        broll_path = None
        try:
            broll_path = self.pexels_service.get_best_broll(
                query=broll_query,
                output_filename="broll_clip.mp4",
                orientation="landscape",
                min_duration=3,
            )
            t_broll = time.time() - t0
            logger.info(f"[3/5] ✅ B-roll téléchargé : {broll_path} ({t_broll:.2f}s)")
            results["steps"]["broll"] = {"path": str(broll_path), "duration_sec": t_broll}
        except Exception as e:
            logger.warning(f"[3/5] ⚠️ Erreur B-roll Pexels ({e}). Utilisation d'un fond de secours.")
            # Si pas de b-roll, utiliser l'avatar comme source principale
            broll_path = avatar_video_path
            results["steps"]["broll"] = {"error": str(e)}

        # -------------------------------------------------------------
        # Étape 4 : Sous-titres (Whisper)
        # -------------------------------------------------------------
        logger.info("[4/5] 📝 Génération des sous-titres SRT avec Whisper...")
        t0 = time.time()
        subtitles_path = self.whisper_service.transcribe_to_srt(
            audio_path=audio_path,
            output_filename="subtitles.srt",
            language="fr",
            fallback_text=script_text,
        )
        t_sub = time.time() - t0
        logger.info(f"[4/5] ✅ Sous-titres SRT générés : {subtitles_path} ({t_sub:.2f}s)")
        results["steps"]["subtitles"] = {"path": str(subtitles_path), "duration_sec": t_sub}

        # -------------------------------------------------------------
        # Étape 5 : Montage YouTube multi-plans dynamique
        # -------------------------------------------------------------
        logger.info("[5/5] 🎞️ Montage YouTube dynamique (Facecam, PiP en bas à droite, musique & transitions)...")
        t0 = time.time()
        final_video_path = self.compositor.render_dynamic_video(
            avatar_video_path=avatar_video_path,
            broll_video_path=broll_path,
            voice_audio_path=audio_path,
            subtitles_path=subtitles_path,
            output_filename=output_filename,
        )
        t_comp = time.time() - t0
        logger.info(f"[5/5] ✅ Montage dynamique terminé : {final_video_path} ({t_comp:.2f}s)")
        results["steps"]["composition"] = {"path": str(final_video_path), "duration_sec": t_comp}

        total_duration = time.time() - start_time
        logger.info("=" * 65)
        logger.info(f"🎉 VIDÉO YOUTUBE FINALE EXPORTÉE : {final_video_path}")
        logger.info(f"Taille du fichier : {final_video_path.stat().st_size / (1024*1024):.2f} Mo")
        logger.info(f"Temps total d'exécution : {total_duration:.2f}s")
        logger.info("=" * 65)

        results["final_video"] = str(final_video_path)
        results["total_duration_sec"] = total_duration
        return results


def main():
    script = (
        "Bonjour et bienvenue sur ma chaîne YouTube ! "
        "Aujourd'hui, nous explorons comment l'intelligence artificielle révolutionne la production vidéo. "
        "Regardez bien cet exemple à l'écran : le montage s'adapte automatiquement, intègre du B-roll "
        "et synchronise chaque élément à la perfection. "
        "N'hésitez pas à vous abonner pour ne rien manquer !"
    )
    pipeline = YouTubeVideoPipeline()
    pipeline.run(
        script_text=script,
        broll_query="artificial intelligence modern technology futuristic",
        output_filename="video_youtube_dynamique.mp4",
    )


if __name__ == "__main__":
    main()
