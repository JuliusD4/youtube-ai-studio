# 🎬 AI YouTube Studio (0 €)

Générateur automatique de vidéos YouTube complètes à partir d'un simple sujet ou script, conçu pour tourner à **0 €** sur les GPU gratuits de **Kaggle** (Tesla T4 16 Go).

---

## ⚡ En 30 secondes : Comment lancer la génération

1. **Ouvrez Kaggle** : Rendez-vous sur votre compte [Kaggle](https://www.kaggle.com/).
2. **Ouvrez le notebook** : Importez ou ouvrez le notebook `kaggle/notebook.ipynb`.
3. **Activez l'accélérateur GPU & Internet** :
   - Dans le panneau latéral droit (*Session options*) :
   - **Accelerator** : `GPU T4 x2` (ou `GPU T4`)
   - **Internet** : `Internet on`
4. **Configurez votre script** :
   - Modifiez la variable `SCRIPT_TEXT` avec votre texte en français.
   - (Optionnel) Ajustez les mots-clés de recherche B-roll `BROLL_SEARCH`.
5. **Cliquez sur "Run All"** :
   - Kaggle installe automatiquement l'environnement.
   - **Chatterbox V3** synthétise la voix française HD.
   - **Whisper** génère les sous-titres SRT.
   - **Pexels** télécharge les séquences vidéo d'illustration B-roll.
   - **FFmpeg** assemble le tout et incruste les sous-titres.
6. **Téléchargez votre vidéo** :
   - La vidéo finale est prévisualisée directement dans le notebook et disponible dans l'onglet **Outputs** : `outputs/final/video_test.mp4`.

---

## 🔑 Configuration des Clés & Secrets (0 €)

Aucune carte bancaire requise.

### 1. Clé Pexels (Vidéos B-roll gratuites)
- Créez un compte gratuit sur [Pexels](https://www.pexels.com/api/).
- Récupérez votre clé API.
- Dans Kaggle : Menu du haut **Add-ons** > **Secrets** > Ajoutez un secret nommé `PEXELS_API_KEY`.
*(Alternativement, une clé est déjà pré-configurée par défaut dans votre fichier local `.env`).*

### 2. Personnaliser la Voix (Clonage vocal Chatterbox V3)
- Pour utiliser **votre propre voix** :
  1. Déposez un extrait de votre voix au format WAV (10 à 30 secondes d'audio clair) dans le dossier `assets/ma_voix.wav`.
  2. Passez le chemin `audio_prompt_path="assets/ma_voix.wav"` à l'appel de `pipeline.run()`.
  3. Chatterbox clonera fidèlement votre timbre de voix sans surcoût.

### 3. Redémarrer après l'arrêt d'une session Kaggle
Comme Kaggle est un environnement éphémère :
- À chaque nouvelle session, cliquez simplement sur **Run All**.
- La cellule 1 clone automatiquement la dernière version du code depuis GitHub (`git pull` / `git clone`).
- La cellule 2 réinstalle l'environnement en moins de 2 minutes.
- Vos modifications sur GitHub sont donc toujours prises en compte instantanément.

---

## 🛠️ Pilotage à distance depuis votre Mac (Optionnel)

Si vous souhaitez lancer la génération sur Kaggle directement depuis votre terminal sans ouvrir le navigateur :

```bash
# 1. Pousser et déclencher l'exécution sur Kaggle
python3 scripts/run_kaggle_kernel.py
```
Le script déploie le notebook, suit l'avancement en temps réel, et télécharge automatiquement la vidéo finale dans `outputs/final/video_test.mp4` dès qu'elle est prête !

---

## 📁 Structure du Projet

```text
video-ia-youtube/
├── README.md                     # Documentation utilisateur
├── requirements.txt              # Dépendances Python
├── .gitignore                    # Protection absolue des secrets et données
│
├── kaggle/
│   ├── notebook.ipynb            # Notebook interactif prêt pour Run All
│   ├── kernel-metadata.json      # Configuration Kaggle GPU & Internet
│   └── setup_environment.py      # Script d'installation autonome Kaggle
│
├── src/
│   ├── config.py                 # Configuration centrale et chemins
│   ├── pipeline.py               # Orchestrateur Phase 1
│   ├── voice/
│   │   └── chatterbox_service.py # Synthèse vocale HD (Chatterbox V3)
│   ├── broll/
│   │   └── pexels_service.py     # Recherche et téléchargement B-roll (Pexels)
│   ├── subtitles/
│   │   └── whisper_service.py    # Transcription et horodatage SRT (Whisper)
│   └── editing/
│       └── ffmpeg_service.py     # Montage vidéo et synchronisation (FFmpeg)
│
├── scripts/
│   └── run_kaggle_kernel.py      # Pilotage à distance de Kaggle
└── tests/                        # Tests unitaires de chaque composant
```

---

## 🗺️ Roadmap

- [x] **Phase 1** : Pipeline automatisé Script -> Chatterbox V3 -> Pexels -> Whisper -> FFmpeg -> `video_test.mp4` (0 €).
- [ ] **Phase 2** : Intégration avatar animé **MuseTalk** + moteur de génération vidéo IA **ComfyUI** / **LTX-Video** avec déchargement séquentiel de VRAM.
