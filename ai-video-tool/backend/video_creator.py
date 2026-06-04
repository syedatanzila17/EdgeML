import os
import uuid
import textwrap
import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

from schemas import Scene, VideoScript

logger = logging.getLogger(__name__)
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_W, VIDEO_H = 1280, 720

THEMES = {
    "blue": {
        "top":    (6, 8, 28),
        "bottom": (16, 42, 88),
        "circle": (50, 120, 240, 50),
        "accent": (80, 150, 255),
        "line":   (60, 120, 220),
        "title":  (255, 255, 255),
        "body":   (200, 220, 255),
        "box":    (10, 22, 60, 170),
        "dot_on": (80, 150, 255),
        "dot_off":(40, 60, 100),
    },
    "green": {
        "top":    (4, 14, 8),
        "bottom": (12, 48, 28),
        "circle": (40, 180, 90, 50),
        "accent": (60, 210, 110),
        "line":   (40, 160, 80),
        "title":  (255, 255, 255),
        "body":   (195, 255, 215),
        "box":    (6, 32, 16, 170),
        "dot_on": (60, 210, 110),
        "dot_off":(20, 70, 35),
    },
    "purple": {
        "top":    (14, 4, 32),
        "bottom": (42, 12, 88),
        "circle": (140, 70, 240, 50),
        "accent": (170, 110, 255),
        "line":   (120, 70, 210),
        "title":  (255, 255, 255),
        "body":   (225, 205, 255),
        "box":    (22, 8, 58, 170),
        "dot_on": (170, 110, 255),
        "dot_off":(60, 30, 100),
    },
    "dark": {
        "top":    (6, 6, 6),
        "bottom": (22, 22, 28),
        "circle": (80, 80, 110, 40),
        "accent": (180, 180, 220),
        "line":   (100, 100, 140),
        "title":  (255, 255, 255),
        "body":   (200, 200, 212),
        "box":    (12, 12, 18, 170),
        "dot_on": (180, 180, 220),
        "dot_off":(45, 45, 60),
    },
}

_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]


def _font(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _gradient_bg(w, h, c_top, c_bottom):
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / (h - 1)
        for ch in range(3):
            arr[y, :, ch] = int(c_top[ch] * (1 - t) + c_bottom[ch] * t)
    return arr


def _pill(draw, x, y, text, fnt, bg, fg):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 10
    r = (th + pad * 2) // 2
    x1, y1, x2, y2 = x, y, x + tw + pad * 2, y + th + pad * 2
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=bg)
    draw.text((x1 + pad, y1 + pad), text, font=fnt, fill=fg)


def create_scene_frame(scene: Scene, theme_name: str, scene_num: int, total: int) -> np.ndarray:
    t = THEMES.get(theme_name, THEMES["blue"])

    # --- gradient background ---
    bg_arr = _gradient_bg(VIDEO_W, VIDEO_H, t["top"], t["bottom"])
    base = Image.fromarray(bg_arr, "RGB")

    # --- RGBA overlay for transparent shapes ---
    ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    # large decorative circle — top-right, partially off-screen
    cr = 340
    d.ellipse([VIDEO_W - cr, -cr // 2, VIDEO_W + cr, cr + cr // 2], fill=t["circle"])

    # small circle — bottom-left
    cr2 = 200
    d.ellipse([-cr2 // 2, VIDEO_H - cr2, cr2, VIDEO_H + cr2 // 2], fill=t["circle"])

    # diagonal accent stripe top-left
    stripe_col = (*t["line"], 30)
    for off in range(0, 120, 20):
        d.line([(off, 0), (0, off)], fill=stripe_col, width=2)

    # composite overlay onto base
    frame = Image.alpha_composite(base.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(frame)

    # --- thin top accent bar ---
    for i in range(4):
        alpha = 255 - i * 40
        draw.line([(0, i), (VIDEO_W, i)], fill=t["accent"])

    # --- scene pill top-left ---
    pill_fnt = _font(_BOLD, 20)
    _pill(draw, 40, 32, f"  {scene_num} / {total}  ", pill_fnt,
          (*t["line"], 200), t["title"])

    # --- large scene title (centered) ---
    title_fnt = _font(_BOLD, 64)
    title = scene.title.upper()
    bbox = draw.textbbox((0, 0), title, font=title_fnt)
    tw = bbox[2] - bbox[0]
    tx = max(60, (VIDEO_W - tw) // 2)
    ty = 160
    # subtle shadow
    draw.text((tx + 3, ty + 3), title, font=title_fnt, fill=(0, 0, 0, 120))
    draw.text((tx, ty), title, font=title_fnt, fill=t["title"])

    # --- accent line under title ---
    line_y = ty + (bbox[3] - bbox[1]) + 18
    line_x1 = max(60, (VIDEO_W - 500) // 2)
    draw.rectangle([line_x1, line_y, line_x1 + 500, line_y + 3], fill=t["accent"])
    draw.rectangle([line_x1, line_y + 6, line_x1 + 200, line_y + 8], fill=(*t["accent"], 120))

    # --- narration box (frosted glass style) ---
    box_top = line_y + 28
    box_bot = VIDEO_H - 80
    box_l, box_r = 60, VIDEO_W - 60

    box_ov = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box_ov)
    bd.rounded_rectangle([box_l, box_top, box_r, box_bot], radius=16,
                          fill=t["box"], outline=(*t["line"], 80), width=1)
    frame = Image.alpha_composite(frame.convert("RGBA"), box_ov).convert("RGB")
    draw = ImageDraw.Draw(frame)

    # --- narration text ---
    body_fnt = _font(_REG, 28)
    max_chars = (box_r - box_l - 60) // 16
    lines = textwrap.wrap(scene.narration, width=max_chars)
    line_h = 40
    max_lines = (box_bot - box_top - 30) // line_h
    y_text = box_top + 20
    for line in lines[:max_lines]:
        draw.text((box_l + 30, y_text), line, font=body_fnt, fill=t["body"])
        y_text += line_h

    # --- progress dots bottom center ---
    dot_r = 6
    spacing = 22
    total_w = total * spacing
    start_x = (VIDEO_W - total_w) // 2
    dot_y = VIDEO_H - 28
    for i in range(total):
        col = t["dot_on"] if i < scene_num else t["dot_off"]
        cx = start_x + i * spacing + dot_r
        draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=col)

    return np.array(frame)


def _ken_burns(clip, zoom=1.06):
    """Slow zoom-in (Ken Burns) effect."""
    w, h = clip.size
    def make_frame(get_frame, t):
        frame = get_frame(t)
        scale = 1.0 + (zoom - 1.0) * (t / max(clip.duration, 0.001))
        nw, nh = int(w * scale), int(h * scale)
        img = Image.fromarray(frame).resize((nw, nh), Image.LANCZOS)
        x, y = (nw - w) // 2, (nh - h) // 2
        return np.array(img.crop((x, y, x + w, y + h)))
    return clip.fl(make_frame)


def generate_narration(text: str, path: str, slow: bool = False):
    gTTS(text=text, lang="en", slow=slow).save(path)


def create_video(script: VideoScript, theme_name: str = "blue", voice_speed: float = 1.0) -> str:
    job_id = str(uuid.uuid4())[:8]
    clips = []

    for i, scene in enumerate(script.scenes):
        frame = create_scene_frame(scene, theme_name, i + 1, len(script.scenes))

        audio_path = str(OUTPUT_DIR / f"{job_id}_s{i}.mp3")
        generate_narration(scene.narration, audio_path, slow=(voice_speed < 0.85))

        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        fade = min(0.25, duration / 5)

        img_clip = (
            ImageClip(frame, duration=duration)
            .fx(fadein, fade)
            .fx(fadeout, fade)
            .set_audio(audio_clip)
        )

        # Ken Burns zoom — skip on very short clips
        if duration > 2:
            img_clip = _ken_burns(img_clip)

        clips.append(img_clip)

    final = concatenate_videoclips(clips, method="compose")
    out_path = str(OUTPUT_DIR / f"{job_id}_video.mp4")
    final.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", logger=None)

    for i in range(len(script.scenes)):
        p = OUTPUT_DIR / f"{job_id}_s{i}.mp3"
        if p.exists():
            p.unlink()

    return out_path
