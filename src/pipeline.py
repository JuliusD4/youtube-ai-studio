"""
Pipeline principal de génération vidéo pour AI YouTube Studio.
Orchestre l'IA Directrice Artistique, Chatterbox V3, MuseTalk, Pexels, Whisper
et le compositeur de montage dynamique YouTube.
"""

import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from src.avatar.musetalk_service import MuseTalkService
from src.broll.pexels_service import PexelsService
from src.config import FINAL_DIR
from src.director.ai_director import AIDirector, VideoScreenplay
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
        self.director = AIDirector()
        self.voice_service = ChatterboxService()
        self.avatar_service = MuseTalkService()
        self.whisper_service = WhisperService()
        self.pexels_service = PexelsService()
        self.compositor = YouTubeSceneCompositor()

    def create_video_from_title(
        self,
        video_title: str,
        avatar_image_path: Optional[Path] = None,
        custom_voice_sample: Optional[str] = None,
        output_filename: str = "video_youtube_finale.mp4",
    ) -> Dict[str, Any]:
        """
        MÉTHODE PRINCIPALE : L'utilisateur n'a besoin de fournir QUE le titre de sa vidéo !
        L'IA s'occupe de tout :
        1. Écriture du script YouTube dynamique et découpage en scènes uniques
        2. Synthèse vocale HD en français
        3. Animation du présentateur avatar (MuseTalk)
        4. Recherche de B-rolls spécifiques pour chaque séquence
        5. Sous-titres horodatés
        6. Montage pro (Facecam, PiP en bas à droite, musique de fond, bruitages Whoosh)
        """
        start_time = time.time()
        logger.info("=" * 65)
        logger.info(f"DÉMARRAGE DE LA CRÉATION POUR : '{video_title}'")
        logger.info("=" * 65)

        # -------------------------------------------------------------
        # Étape 1 : Direction Artistique et Scénario IA
        # -------------------------------------------------------------
        logger.info("[1/6] 🎬 L'IA Directrice conçoit le scénario et la mise en scène...")
        screenplay: VideoScreenplay = self.director.generate_screenplay(video_title)
        full_narration = " ".join(s.narration for s in screenplay.scenes)
        logger.info(f"[1/6] ✅ Scénario créé ({len(screenplay.scenes)} scènes, {len(full_narration.split())} mots) :")
        for sc in screenplay.scenes:
            logger.info(f"   - Scène {sc.scene_id} [{sc.layout}] : {sc.narration[:60]}... (B-roll: {sc.broll_query})")

        # -------------------------------------------------------------
        # Étape 2 : Synthèse Vocale (Chatterbox V3)
        # -------------------------------------------------------------
        logger.info("[2/6] 🎙️ Synthèse de la voix avec Chatterbox V3...")
        t0 = time.time()
        audio_path = self.voice_service.generate_voice(
            text=full_narration,
            output_filename="voice_track.wav",
            audio_prompt_path=custom_voice_sample,
            language_id="fr",
        )
        t_audio = time.time() - t0
        logger.info(f"[2/6] ✅ Audio voix généré : {audio_path} ({t_audio:.2f}s)")

        # -------------------------------------------------------------
        # Étape 3 : Avatar Présentateur (MuseTalk)
        # -------------------------------------------------------------
        logger.info("[3/6] 👤 Animation de l'avatar présentateur...")
        t0 = time.time()
        avatar_video_path = self.avatar_service.generate_avatar(
            audio_path=audio_path,
            avatar_image_path=avatar_image_path,
            output_filename="avatar_presenter.mp4",
        )
        t_avatar = time.time() - t0
        logger.info(f"[3/6] ✅ Présentateur généré : {avatar_video_path} ({t_avatar:.2f}s)")

        # -------------------------------------------------------------
        # Étape 4 : Recherche B-roll pour les scènes illustrées
        # -------------------------------------------------------------
        logger.info("[4/6] 🎬 Recherche et téléchargement du B-roll Pexels le plus adapté...")
        t0 = time.time()
        # Prendre la requête de la première scène illustrée
        broll_query = next((s.broll_query for s in screenplay.scenes if s.layout in ["PIP", "BROLL_FULL"]), "technology modern")
        try:
            broll_path = self.pexels_service.get_best_broll(
                query=broll_query,
                output_filename="broll_clip.mp4",
                orientation="landscape",
                min_duration=3,
            )
            logger.info(f"[4/6] ✅ B-roll téléchargé ('{broll_query}') : {broll_path}")
        except Exception as e:
            logger.warning(f"[4/6] ⚠️ B-roll indisponible ({e}). Utilisation du plan studio.")
            broll_path = avatar_video_path

        # -------------------------------------------------------------
        # Étape 5 : Sous-titres (Whisper)
        # -------------------------------------------------------------
        logger.info("[5/6] 📝 Transcription et sous-titres SRT avec Whisper...")
        t0 = time.time()
        subtitles_path = self.whisper_service.transcribe_to_srt(
            audio_path=audio_path,
            output_filename="subtitles.srt",
            language="fr",
            fallback_text=full_narration,
        )
        logger.info(f"[5/6] ✅ Sous-titres SRT générés : {subtitles_path}")

        # -------------------------------------------------------------
        # Étape 6 : Montage Pro YouTube Dynamique (FFmpeg)
        # -------------------------------------------------------------
        logger.info("[6/6] 🎞️ Montage YouTube dynamique (Facecam, PiP en bas à droite, musique & transitions Whoosh)...")
        t0 = time.time()
        final_video_path = self.compositor.render_dynamic_video(
            avatar_video_path=avatar_video_path,
            broll_video_path=broll_path,
            voice_audio_path=audio_path,
            subtitles_path=subtitles_path,
            output_filename=output_filename,
        )
        t_comp = time.time() - t0
        total_time = time.time() - start_time

        logger.info("=" * 65)
        logger.info(f"🎉 VIDÉO YOUTUBE FINALE TERMINÉE : {final_video_path}")
        logger.info(f"Titre : {video_title}")
        logger.info(f"Taille : {final_video_path.stat().st_size / (1024*1024):.2f} Mo | Temps total : {total_time:.2f}s")
        logger.info("=" * 65)

        return {
            "title": video_title,
            "screenplay": [asdict(s) for s in screenplay.scenes],
            "final_video": str(final_video_path),
            "total_time_sec": total_time,
        }

    # Compatibilité avec l'ancienne signature
    def run(self, script_text: str, broll_query: str = "technology", output_filename: str = "video_finale.mp4"):
        return self.create_video_from_title(video_title=script_text, output_filename=output_filename)


def main():
    pipeline = YouTubeVideoPipeline()
    pipeline.create_video_from_title(
        video_title="Comment l'Intelligence Artificielle va bouleverser notre avenir en 2026",
        output_filename="video_ia_2026.mp4",
    )


if __name__ == "__main__":
    main()
