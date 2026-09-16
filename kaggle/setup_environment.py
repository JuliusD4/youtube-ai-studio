"""
Script d'initialisation automatique et reproductible pour l'environnement Kaggle.
Installe les dépendances, vérifie le GPU T4, FFmpeg et prépare le projet.
"""

import os
import subprocess
import sys


def run_command(cmd, desc=""):
    print(f"--> {desc or cmd}...")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"⚠️ Avertissement lors de l'exécution de '{cmd}':\n{result.stderr}")
    else:
        print(f"✅ {desc or 'Succès'}")
    return result.returncode == 0


def setup_kaggle_environment():
    print("=" * 60)
    print("INITIALISATION AUTOMATIQUE DE L'ENVIRONNEMENT KAGGLE")
    print("=" * 60)

    # 1. Vérification du GPU
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"✅ GPU détecté : {device_name} ({vram_gb:.1f} Go VRAM)")
        else:
            print("⚠️ Aucun GPU CUDA détecté ! Activez l'accélérateur GPU (T4 x2) dans les paramètres du notebook Kaggle.")
    except Exception as e:
        print(f"Erreur vérification GPU : {e}")

    # 2. Vérification / Installation de FFmpeg
    ffmpeg_ok = subprocess.run("which ffmpeg", shell=True, capture_output=True).returncode == 0
    if not ffmpeg_ok:
        run_command("apt-get update && apt-get install -y ffmpeg", "Installation de FFmpeg système")
    else:
        print("✅ FFmpeg est déjà disponible.")

    # 3. Installation des paquets Python
    print("\n📦 Installation des packages IA légers & optimisés...")
    run_command("pip install --quiet --no-input python-dotenv requests tqdm", "Installation des utilitaires de base")
    run_command("pip install --quiet --no-input openai-whisper", "Installation de Whisper")

    # 4. Installation de Chatterbox V3
    try:
        import chatterbox
        print("✅ Chatterbox TTS est déjà installé.")
    except ImportError:
        print("Installation de Chatterbox TTS...")
        success = run_command("pip install --quiet --no-input chatterbox-tts", "Installation via pip de chatterbox-tts")
        if not success:
            run_command(
                "pip install --quiet --no-input git+https://github.com/resemble-ai/chatterbox.git",
                "Installation depuis le dépôt GitHub de Resemble AI",
            )

    # 5. Préparation de MuseTalk
    musetalk_dir = "/kaggle/working/MuseTalk"
    if not os.path.exists(musetalk_dir):
        print("Clonage de MuseTalk pour l'animation d'avatar...")
        run_command(f"GIT_TERMINAL_PROMPT=0 git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git {musetalk_dir}", "Clonage de MuseTalk")

    print("\n" + "=" * 60)
    print("🎉 ENVIRONNEMENT PRÊT POUR L'EXÉCUTION !")
    print("=" * 60)


if __name__ == "__main__":
    setup_kaggle_environment()
