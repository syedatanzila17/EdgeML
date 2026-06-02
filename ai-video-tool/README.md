# AI Video Creation Tool

Generate professional AI-powered videos from a simple text prompt.

## How It Works

1. You describe a topic, pick a style and duration
2. **Claude** (Anthropic) generates a structured scene-by-scene script
3. **Pillow** renders each scene as a branded slide frame
4. **gTTS** converts narration text to speech audio
5. **MoviePy** assembles frames + audio → final MP4 with fade transitions

## Features

- 4 video styles: Educational, Promotional, Storytelling
- 4 colour themes: Deep Blue, Forest Green, Royal Purple, Dark Mode
- Configurable duration (15 s – 5 min)
- Voice speed control
- Real-time progress UI with script preview
- One-click MP4 download

## Quick Start

### Local (Python)

```bash
cd ai-video-tool/backend

# Install ffmpeg (required by MoviePy)
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS:         brew install ffmpeg

cp .env.sample .env
# Edit .env → add your ANTHROPIC_API_KEY

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

### Docker

```bash
cd ai-video-tool
cp backend/.env.sample .env
# Edit .env → add ANTHROPIC_API_KEY

docker-compose up --build
```

Open http://localhost:8000 in your browser.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/video/generate`       | Start a new video job |
| GET    | `/api/video/status/{id}`    | Poll job progress & script |
| GET    | `/api/video/download/{id}`  | Download finished MP4 |
| DELETE | `/api/video/{id}`           | Delete job & file |

### POST /api/video/generate

```json
{
  "topic": "How photosynthesis works",
  "style": "educational",
  "duration": 60,
  "color_theme": "blue",
  "voice_speed": 1.0
}
```

## Project Structure

```
ai-video-tool/
├── backend/
│   ├── main.py                 # FastAPI app & job management
│   ├── ai_script_generator.py  # Claude API → VideoScript
│   ├── video_creator.py        # Pillow + gTTS + MoviePy → MP4
│   ├── schemas.py              # Pydantic models
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.sample
├── frontend/
│   ├── index.html              # Single-page UI
│   ├── styles.css
│   └── app.js
└── docker-compose.yml
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Key from console.anthropic.com |
