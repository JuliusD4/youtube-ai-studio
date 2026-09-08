"""
Service Pexels pour la recherche et le téléchargement de vidéos B-roll libres de droits.
"""

import json
import logging
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import BROLL_DIR, PEXELS_API_KEY

logger = logging.getLogger(__name__)


class PexelsService:
    BASE_URL = "https://api.pexels.com/videos"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PEXELS_API_KEY
        if not self.api_key:
            logger.warning("PEXELS_API_KEY non fournie. Les appels réels à Pexels échoueront.")

    def search_broll(
        self,
        query: str,
        orientation: str = "landscape",
        min_duration: int = 3,
        max_duration: int = 60,
        per_page: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Recherche des vidéos B-roll correspondant à la requête.
        Retourne une liste de métadonnées de vidéos disponibles.
        """
        if not self.api_key:
            raise ValueError("Clé PEXELS_API_KEY manquante.")

        params = {
            "query": query,
            "orientation": orientation,
            "per_page": per_page,
        }
        url = f"{self.BASE_URL}/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": self.api_key,
                "User-Agent": "AI-YouTube-Studio/1.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Erreur lors de la recherche Pexels pour '{query}': {e}")
            raise

        results = []
        for video in data.get("videos", []):
            duration = video.get("duration", 0)
            if duration < min_duration or duration > max_duration:
                continue

            # Trouver le meilleur fichier vidéo (priorité 1080p landscape mp4)
            best_file = None
            for vf in video.get("video_files", []):
                if vf.get("file_type") != "video/mp4":
                    continue
                # Préférer HD 1920x1080
                w = vf.get("width") or 0
                h = vf.get("height") or 0
                if w >= 1280 and h >= 720:
                    if best_file is None or (w == 1920 and h == 1080):
                        best_file = vf

            # Si aucun HD trouvé, prendre le premier fichier mp4
            if not best_file:
                mp4_files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
                if mp4_files:
                    best_file = mp4_files[0]

            if best_file:
                results.append(
                    {
                        "id": video.get("id"),
                        "duration": duration,
                        "width": best_file.get("width"),
                        "height": best_file.get("height"),
                        "quality": best_file.get("quality"),
                        "page_url": video.get("url"),
                        "download_url": best_file.get("link"),
                    }
                )

        return results

    def download_broll(
        self,
        download_url: str,
        output_filename: str,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Télécharge une vidéo depuis son URL vers le dossier B-roll.
        """
        target_dir = output_dir or BROLL_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / output_filename

        logger.info(f"Téléchargement du B-roll vers {target_path}...")
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "AI-YouTube-Studio/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

        logger.info(f"B-roll téléchargé avec succès : {target_path} ({target_path.stat().st_size} octets)")
        return target_path

    def get_best_broll(
        self,
        query: str,
        output_filename: str,
        orientation: str = "landscape",
        min_duration: int = 3,
    ) -> Path:
        """
        Cherche et télécharge directement la meilleure vidéo B-roll pour une requête donnée.
        """
        videos = self.search_broll(query, orientation=orientation, min_duration=min_duration, per_page=5)
        if not videos:
            raise RuntimeError(f"Aucune vidéo B-roll trouvée sur Pexels pour la requête : '{query}'")

        best_video = videos[0]
        return self.download_broll(best_video["download_url"], output_filename)
