"""
Moteur de Composition Vidéo Dynamique YouTube.
Gère l'alternance de plans (Facecam plein écran, Picture-in-Picture bas-droite, B-roll impact),
l'ambiance musicale (ducking) et les transitions sonores (whoosh).
"""

import logging
import math
import os
import subprocess
from pathlib import Path
from typing import List, Optional

from src.config import ASSETS_DIR, FINAL_DIR, VIDEO_FPS, VIDEO_HEIGHT, VIDEO_WIDTH

logger = logging.getLogger(__name__)

WHOOSH_SFX_PATH = ASSETS_DIR / "audio" / "whoosh.wav"
BGM_MUSIC_PATH = ASSETS_DIR / "audio" / "background_music.mp3"


class YouTubeSceneCompositor:
    def __init__(
        self,
        width: int = VIDEO_WIDTH,
        height: int = VIDEO_HEIGHT,
        fps: int = VIDEO_FPS,
    ):
        self.width = width
        self.height = height
        self.fps = fps

    def get_duration(self, file_path: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(res.stdout.strip())
        except Exception:
            return 10.0

    def compute_scene_timeline(self, total_duration: float) -> List[dict]:
        """
        Découpe la durée totale en scènes rythmées avec alternance de cadrages :
        - Scène 1 : FACECAM (Accroche du spectateur)
        - Scène 2 : PIP (Démonstration B-roll + Présentateur en bulle en bas à droite)
        - Scène 3 : BROLL_FULL (Impact visuel plein écran)
        - Scène 4 : PIP (Explication approfondie)
        - Scène finale : FACECAM (Conclusion & Appel à l'action)
        """
        if total_duration <= 8.0:
            mid = total_duration * 0.4
            return [
                {"type": "FACECAM", "start": 0.0, "end": mid},
                {"type": "PIP", "start": mid, "end": total_duration},
            ]

        intro_dur = min(4.5, total_duration * 0.25)
        outro_dur = min(4.0, total_duration * 0.20)
        remaining = total_duration - intro_dur - outro_dur

        scenes = [
            {"type": "FACECAM", "start": 0.0, "end": intro_dur},
        ]

        current_time = intro_dur
        step = max(3.5, remaining / 3.0)
        toggle = True

        while current_time < (total_duration - outro_dur - 0.5):
            next_time = min(current_time + step, total_duration - outro_dur)
            scene_type = "PIP" if toggle else "BROLL_FULL"
            scenes.append({"type": scene_type, "start": current_time, "end": next_time})
            current_time = next_time
            toggle = not toggle

        scenes.append({"type": "FACECAM", "start": total_duration - outro_dur, "end": total_duration})
        return scenes

    def render_dynamic_video(
        self,
        avatar_video_path: Path,
        broll_video_path: Path,
        voice_audio_path: Path,
        subtitles_path: Optional[Path] = None,
        output_filename: str = "video_dynamique.mp4",
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Génère la vidéo finale avec alternance Facecam / PiP / B-roll,
        musique de fond et sous-titres synchronisés.
        """
        target_dir = output_dir or FINAL_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / output_filename

        total_duration = self.get_duration(voice_audio_path)
        timeline = self.compute_scene_timeline(total_duration)

        logger.info(f"Découpage en {len(timeline)} scènes dynamiques (durée totale : {total_duration:.1f}s) :")
        broll_intervals = []
        pip_intervals = []
        transitions = []

        for i, s in enumerate(timeline, 1):
            logger.info(f"  Plan {i} : [{s['type']}] de {s['start']:.1f}s à {s['end']:.1f}s ({s['end']-s['start']:.1f}s)")
            if s["type"] in ["PIP", "BROLL_FULL"]:
                broll_intervals.append(f"between(t,{s['start']:.2f},{s['end']:.2f})")
            if s["type"] == "PIP":
                pip_intervals.append(f"between(t,{s['start']:.2f},{s['end']:.2f})")
            if s["start"] > 0:
                transitions.append(s["start"])

        broll_enable = "+".join(broll_intervals) if broll_intervals else "0"
        pip_enable = "+".join(pip_intervals) if pip_intervals else "0"

        # Tailles et position de la vignette PiP
        pip_size = 380

        filter_complex_parts = [
            # 1. Préparation Facecam (fond principal quand le B-roll est inactif)
            f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height},setsar=1,fps={self.fps}[facecam]",
            # 2. Préparation B-roll 1080p
            f"[1:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height},setsar=1,fps={self.fps}[broll]",
            # 3. Préparation vignette miniature avatar avec cadre blanc studio
            f"[0:v]scale={pip_size}:{pip_size}:force_original_aspect_ratio=increase,crop={pip_size}:{pip_size},"
            f"drawbox=x=0:y=0:w={pip_size}:h={pip_size}:color=white@0.9:t=4,setsar=1,fps={self.fps}[pip_bubble]",
            # 4. Superposition dynamique du B-roll sur le Facecam aux moments opportuns
            f"[facecam][broll]overlay=0:0:enable='{broll_enable}':eof_action=repeat[layer1]",
            # 5. Superposition de la vignette PiP en bas à droite aux moments PIP
            f"[layer1][pip_bubble]overlay=W-w-50:H-h-50:enable='{pip_enable}'[v_composed]",
        ]

        # 6. Mixage audio
        has_bgm = BGM_MUSIC_PATH.exists()
        audio_inputs = ["-i", str(voice_audio_path)]
        amix_inputs = ["[2:a]volume=1.0[voice]"]
        amix_pads = ["[voice]"]

        input_index = 3
        if has_bgm:
            audio_inputs.extend(["-stream_loop", "-1", "-i", str(BGM_MUSIC_PATH)])
            amix_inputs.append(f"[{input_index}:a]volume=0.10[bgm]")
            amix_pads.append("[bgm]")
            input_index += 1

        # Intégration des effets sonores de transition (Whoosh) sur chaque changement de plan
        has_whoosh = WHOOSH_SFX_PATH.exists() and len(transitions) > 0
        if has_whoosh:
            for t_idx, t_time in enumerate(transitions[:4]):
                delay_ms = int(t_time * 1000)
                audio_inputs.extend(["-i", str(WHOOSH_SFX_PATH)])
                pad_name = f"[whoosh_{t_idx}]"
                amix_inputs.append(f"[{input_index}:a]adelay={delay_ms}|{delay_ms},volume=0.25{pad_name}")
                amix_pads.append(pad_name)
                input_index += 1

        # Graphe de mixage audio final
        filter_complex_parts.extend(amix_inputs)
        pads_str = "".join(amix_pads)
        filter_complex_parts.append(f"{pads_str}amix=inputs={len(amix_pads)}:duration=first[a_final]")

        # 7. Sous-titres : incrustation directe si supporté ou inclusion mov_text
        current_v = "[v_composed]"
        burn_success = False

        filter_complex_str = ";".join(filter_complex_parts)

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(avatar_video_path),
            "-stream_loop", "-1", "-i", str(broll_video_path),
            *audio_inputs,
            "-filter_complex", filter_complex_str,
            "-map", current_v,
            "-map", "[a_final]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "21",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_duration:.3f}",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]

        # Si des sous-titres existent, les intégrer comme piste mov_text propre
        if subtitles_path and subtitles_path.exists():
            cmd.extend([
                "-i", str(subtitles_path),
                "-c:s", "mov_text",
            ])

        logger.info(f"Rendu du montage YouTube dynamique ({total_duration:.1f}s) vers {output_path}...")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"🎉 Vidéo YouTube dynamique générée avec succès : {output_path} ({output_path.stat().st_size} octets)")

        return output_path
