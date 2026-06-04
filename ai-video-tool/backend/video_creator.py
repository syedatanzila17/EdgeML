import os
import uuid
import textwrap
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
    CompositeVideoClip,
    TextClip,
    ColorClip,
)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

from schemas import Scene, VideoScript

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_W, VIDEO_H = 1280, 720

THEMES = {
    "blue":   {"bg": (26, 26, 46),   "accent": (15, 52, 96),   "title": (233, 69, 96),  "body": (255, 255, 255)},
    "green":  {"bg": (13, 17, 23),   "accent": (35, 134, 54),  "title": (86, 211, 100), "body": (255, 255, 255)},
    "purple": {"bg": (26, 10, 46),   "accent": (111, 66, 193), "title": (210, 168, 255),"body": (255, 255, 255)},
    "dark":   {"bg": (10, 10, 10),   "accent": (50, 50, 50),   "title": (240, 240, 240),"body": (200, 200, 200)},
}

_FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
_FONT_REG_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def _load_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _draw_rounded_rect(draw: ImageDraw.Draw, xy, radius: int, fill):
    x0, y0, x1, y1 = xy
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.ellipse([x0, y0, x0 + 2 * radius, y0 + 2 * radius], fill=fill)
    draw.ellipse([x1 - 2 * radius, y0, x1, y0 + 2 * radius], fill=fill)
    draw.ellipse([x0, y1 - 2 * radius, x0 + 2 * radius, y1], fill=fill)
    draw.ellipse([x1 - 2 * radius, y1 - 2 * radius, x1, y1], fill=fill)


def create_scene_frame(scene: Scene, theme_name: str, scene_num: int, total: int) -> np.ndarray:
    theme = THEMES.get(theme_name, THEMES["blue"])

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), theme["bg"])
    draw = ImageDraw.Draw(img)

    # Top accent bar with gradient simulation
    for i in range(12):
        alpha = int(255 * (1 - i / 12))
        r, g, b = theme["accent"]
        draw.line([(0, i), (VIDEO_W, i)], fill=(r, g, b))

    # Bottom accent bar
    for i in range(8):
        draw.line([(0, VIDEO_H - 8 + i), (VIDEO_W, VIDEO_H - 8 + i)], fill=theme["accent"])

    # Scene counter pill (top-right)
    pill_text = f"{scene_num}/{total}"
    counter_font = _load_font(_FONT_BOLD_PATHS, 22)
    _draw_rounded_rect(draw, (VIDEO_W - 90, 20, VIDEO_W - 20, 50), 12, theme["accent"])
    draw.text((VIDEO_W - 76, 27), pill_text, font=counter_font, fill=theme["title"])

    # Title
    title_font = _load_font(_FONT_BOLD_PATHS, 52)
    draw.text((80, 70), scene.title, font=title_font, fill=theme["title"])

    # Separator
    draw.rectangle([(80, 148), (VIDEO_W - 80, 152)], fill=theme["accent"])

    # Narration body (word-wrapped)
    body_font = _load_font(_FONT_REG_PATHS, 30)
    wrapped_lines = textwrap.wrap(scene.narration, width=62)
    y = 180
    for line in wrapped_lines[:9]:   # max 9 lines to stay in frame
        draw.text((80, y), line, font=body_font, fill=theme["body"])
        y += 44

    # Visual hint footer
    hint_font = _load_font(_FONT_REG_PATHS, 22)
    r, g, b = theme["body"]
    dim = (max(0, r - 100), max(0, g - 100), max(0, b - 100))
    hint = f"[ {scene.visual_description[:90]} ]"
    draw.text((80, VIDEO_H - 50), hint, font=hint_font, fill=dim)

    return np.array(img)


def generate_narration(text: str, path: str, slow: bool = False):
    tts = gTTS(text=text, lang="en", slow=slow)
    tts.save(path)


def create_video(script: VideoScript, theme_name: str = "blue", voice_speed: float = 1.0) -> str:
    job_id = str(uuid.uuid4())[:8]
    clips = []

    for i, scene in enumerate(script.scenes):
        frame = create_scene_frame(scene, theme_name, i + 1, len(script.scenes))

        audio_path = str(OUTPUT_DIR / f"{job_id}_s{i}.mp3")
        generate_narration(scene.narration, audio_path, slow=(voice_speed < 0.85))

        audio_clip = AudioFileClip(audio_path)
        # Use exact audio duration — never extend beyond what exists
        duration = audio_clip.duration
        fade = min(0.3, duration / 4)

        img_clip = (
            ImageClip(frame, duration=duration)
            .fx(fadein, fade)
            .fx(fadeout, fade)
            .set_audio(audio_clip)
        )
        clips.append(img_clip)

    final = concatenate_videoclips(clips, method="compose")
    out_path = str(OUTPUT_DIR / f"{job_id}_video.mp4")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)

    # Clean up per-scene audio
    for i in range(len(script.scenes)):
        p = OUTPUT_DIR / f"{job_id}_s{i}.mp3"
        if p.exists():
            p.unlink()

    return out_path
