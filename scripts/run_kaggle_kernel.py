"""
Script d'automatisation pour piloter l'exécution du notebook sur Kaggle à distance :
- Pousse le notebook et les métadonnées vers Kaggle
- Surveille l'état d'exécution en temps réel
- Télécharge les fichiers générés (notamment video_test.mp4)
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("KaggleRunner")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KAGGLE_DIR = PROJECT_ROOT / "kaggle"
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "final"


def ensure_kaggle_auth():
    token = os.environ.get("KAGGLE_API_TOKEN")
    if not token:
        logger.warning("KAGGLE_API_TOKEN non défini dans les variables d'environnement.")
    return token


def push_kernel():
    logger.info("Déploiement du kernel sur Kaggle via 'kaggle kernels push'...")
    cmd = ["kaggle", "kernels", "push", "-p", str(KAGGLE_DIR)]
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logger.error(f"Échec du déploiement : {result.stderr}")
        raise RuntimeError(result.stderr)
    logger.info(f"Résultat du push : {result.stdout.strip()}")


def monitor_kernel(kernel_slug: str = "juliendescourbes/ai-youtube-studio", timeout_min: int = 25):
    logger.info(f"Surveillance de l'état du kernel '{kernel_slug}'...")
    start_time = time.time()
    last_status = ""

    while True:
        elapsed = (time.time() - start_time) / 60
        if elapsed > timeout_min:
            logger.error(f"Timeout atteint après {timeout_min} minutes d'exécution.")
            break

        cmd = ["kaggle", "kernels", "status", kernel_slug]
        res = subprocess.run(cmd, capture_output=True, text=True)
        status_line = res.stdout.strip()

        if status_line != last_status:
            logger.info(f"Statut Kaggle : {status_line} (temps écoulé: {elapsed:.1f} min)")
            last_status = status_line

        if "complete" in status_line.lower():
            logger.info("🎉 Exécution sur Kaggle terminée avec succès !")
            return True
        elif "error" in status_line.lower() or "failed" in status_line.lower():
            logger.error(f"Le kernel s'est arrêté avec une erreur : {status_line}")
            # Afficher les logs
            log_res = subprocess.run(["kaggle", "kernels", "logs", kernel_slug], capture_output=True, text=True)
            print("\n--- DERNIERS LOGS KAGGLE ---")
            print(log_res.stdout)
            print("----------------------------\n")
            return False

        time.sleep(15)


def download_outputs(kernel_slug: str = "juliendescourbes/ai-youtube-studio"):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Téléchargement des résultats de génération vers {OUTPUTS_DIR}...")
    cmd = ["kaggle", "kernels", "output", kernel_slug, "-p", str(OUTPUTS_DIR)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        logger.info(f"Résultats téléchargés avec succès :\n{res.stdout}")
    else:
        logger.warning(f"Sortie du téléchargement : {res.stderr}")


def main():
    ensure_kaggle_auth()
    kernel_slug = "juliendescourbes/ai-youtube-studio"
    push_kernel()
    success = monitor_kernel(kernel_slug)
    if success:
        download_outputs(kernel_slug)


if __name__ == "__main__":
    main()
