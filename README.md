# 🎬 AI YouTube Studio (0 €)

Générateur automatique de vidéos YouTube professionnelles à partir d'un **simple titre ou sujet**.
Fonctionne à **0 €** sur les GPU gratuits de **Kaggle** (Tesla T4 16 Go).

---

## ⚡ En 3 étapes : Comment créer une vidéo

1. **Ouvrez votre notebook sur Kaggle** :
   👉 [https://www.kaggle.com/code/juliendescourbes/ai-youtube-studio](https://www.kaggle.com/code/juliendescourbes/ai-youtube-studio)
2. **Cliquez sur `[Edit]`** (bouton noir en haut à droite).
3. **Changez le titre** dans la première cellule sous le titre :
   ```python
   VIDEO_TITLE = "Votre sujet ou titre de vidéo YouTube"
   ```
4. **Cliquez sur "Run All"** :
   - L'**IA Directrice Artistique** analyse votre sujet, écrit le script sur-mesure et orchestre la mise en scène (pas de template répétitif !).
   - **Chatterbox V3** synthétise la voix française HD.
   - **MuseTalk** anime le présentateur face caméra avec synchronisation labiale.
   - **Pexels** télécharge des vidéos B-roll 1080p ciblées pour chaque séquence.
   - **FFmpeg** réalise le montage dynamique : alternance entre plans larges *Facecam* et plans *Picture-in-Picture* (avatar en vignette en bas à droite) avec musique Lo-Fi en fond et transitions sonores *Whoosh*.

La vidéo finale apparaît prête à être visionnée et téléchargée directement dans le notebook !

---

## 🌟 Pourquoi chaque vidéo est unique ?

Contrairement à des générateurs basiques qui répètent toujours le même format :
- L'**IA Directrice** analyse le thème de votre titre (tech, santé, finance, nature, société...).
- Elle adapte le nombre de scènes, le rythme de narration et les requêtes de recherche B-roll.
- Elle décide intelligemment quand montrer le présentateur en plein écran (pour capter l'attention ou conclure) et quand le basculer en vignette en bas à droite pour mettre en valeur les visuels à l'écran.

---

## 📁 Structure du Projet

```text
youtube-ai-studio/
├── README.md                     # Documentation
├── kaggle/
│   ├── notebook.ipynb            # Notebook interactif (titre modifiable en haut)
│   └── setup_environment.py      # Installation autonome sur Kaggle
├── src/
│   ├── director/
│   │   └── ai_director.py        # IA Scénariste et Directrice Artistique
│   ├── voice/
│   │   └── chatterbox_service.py # Synthèse vocale Chatterbox V3
│   ├── avatar/
│   │   └── musetalk_service.py   # Animation du présentateur (MuseTalk)
│   ├── broll/
│   │   └── pexels_service.py     # Récupération des B-rolls HD (Pexels)
│   ├── subtitles/
│   │   └── whisper_service.py    # Sous-titres Whisper
│   ├── editing/
│   │   └── scene_compositor.py   # Montage Facecam / PiP / Habillage sonore
│   └── pipeline.py               # Orchestrateur centralisé
└── assets/
    ├── default_avatar.png        # Portrait du présentateur par défaut
    └── audio/
        ├── background_music.mp3  # Musique d'ambiance Lo-Fi
        └── whoosh.wav            # Effets sonores de transition
```
