"""
Configuration centrale pour AI YouTube Studio.
Gère les variables d'environnement, les répertoires et les paramètres par défaut.
"""

import os
from pathlib import Path

# Chargement optionnel de .env si disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Chemins de base du projet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
AUDIO_DIR = OUTPUTS_DIR / "audio"
BROLL_DIR = OUTPUTS_DIR / "broll"
SUBTITLES_DIR = OUTPUTS_DIR / "subtitles"
FINAL_DIR = OUTPUTS_DIR / "final"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Création automatique des répertoires d'outputs
for dir_path in [OUTPUTS_DIR, AUDIO_DIR, BROLL_DIR, SUBTITLES_DIR, FINAL_DIR, ASSETS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Clés API
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
KAGGLE_API_TOKEN = os.environ.get("KAGGLE_API_TOKEN", "")

# Paramètres Voix (Chatterbox V3)
VOICE_LANGUAGE = os.environ.get("VOICE_LANGUAGE", "fr")
CHATTERBOX_MODEL = os.environ.get("CHATTERBOX_MODEL", "v3")  # "v3" ou "turbo"
CUSTOM_VOICE_SAMPLE = os.environ.get("CUSTOM_VOICE_SAMPLE", "")

# Paramètres Sous-titres (Whisper)
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")

# Paramètres Vidéo & Montage (FFmpeg)
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1920"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1080"))
VIDEO_FPS = int(os.environ.get("VIDEO_FPS", "30"))
