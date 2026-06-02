import json
import anthropic
from schemas import Scene, VideoScript

_STYLE_TIPS = {
    "educational": "clear, informative, well-structured — teach something valuable",
    "promotional": "engaging, benefit-focused, with a strong call-to-action",
    "storytelling": "narrative arc, emotional connection, vivid imagery",
}

_THEMES = {
    "blue": "#0f3460",
    "green": "#1a4a2e",
    "purple": "#2d1b69",
    "dark": "#111111",
}


def generate_video_script(topic: str, style: str, duration: int, theme: str = "blue") -> VideoScript:
    client = anthropic.Anthropic()

    num_scenes = max(3, min(10, duration // 12))
    bg_color = _THEMES.get(theme, "#0f3460")
    style_tip = _STYLE_TIPS.get(style, _STYLE_TIPS["educational"])

    prompt = f"""You are a professional video scriptwriter. Create a {style} video script about:

TOPIC: {topic}

Requirements:
- Total duration: ~{duration} seconds
- Number of scenes: {num_scenes}
- Style: {style_tip}
- Speaking pace: ~140 words per minute (narration must fit each scene's duration)

Return ONLY a valid JSON object — no markdown, no extra text — with this exact structure:
{{
  "title": "Compelling video title",
  "scenes": [
    {{
      "title": "Scene title (short, 3-6 words)",
      "narration": "Spoken text for this scene. Keep it natural and within the allotted duration.",
      "visual_description": "What appears on screen (icons, graphics, text overlays, etc.)",
      "duration": 15,
      "background_color": "{bg_color}"
    }}
  ],
  "total_duration": {duration}
}}

Ensure the narration for each scene fits comfortably within its `duration` seconds at 140 wpm.
Make the script compelling and well-paced."""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw)
    scenes = [Scene(**s) for s in data["scenes"]]
    return VideoScript(title=data["title"], scenes=scenes, total_duration=data["total_duration"])
