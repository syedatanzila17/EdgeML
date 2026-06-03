import os
import uuid
import socket
import logging
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schemas import VideoRequest, VideoJobResponse
from ai_script_generator import generate_video_script
from video_creator import create_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Video Creation Tool",
    description="Generate professional AI-powered videos from a text prompt.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory job store (swap for Redis in production)
_jobs: dict = {}

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def _run_job(job_id: str, req: VideoRequest):
    try:
        _jobs[job_id].update(status="generating_script", progress=15)
        logger.info(f"[{job_id}] Generating script for: {req.topic!r}")

        script = generate_video_script(req.topic, req.style, req.duration, req.color_theme)
        _jobs[job_id].update(status="creating_video", progress=45, script=script.dict())
        logger.info(f"[{job_id}] Script ready — {len(script.scenes)} scenes")

        out_path = create_video(script, req.color_theme, req.voice_speed)
        _jobs[job_id].update(
            status="completed",
            progress=100,
            output_path=out_path,
            download_url=f"/api/video/download/{job_id}",
        )
        logger.info(f"[{job_id}] Video ready: {out_path}")

    except Exception as exc:
        logger.exception(f"[{job_id}] Job failed")
        _jobs[job_id].update(status="failed", error=str(exc))


@app.post("/api/video/generate", response_model=VideoJobResponse, tags=["video"])
async def generate_video(req: VideoRequest, background_tasks: BackgroundTasks):
    """Submit a new video-generation job. Returns a job_id for polling."""
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {"status": "queued", "progress": 0}
    background_tasks.add_task(_run_job, job_id, req)
    return VideoJobResponse(
        job_id=job_id,
        status="queued",
        message="Video generation started. Poll /api/video/status/{job_id} for progress.",
    )


@app.get("/api/video/status/{job_id}", tags=["video"])
async def get_status(job_id: str):
    """Poll job progress. Status: queued → generating_script → creating_video → completed | failed."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = _jobs[job_id]
    return {
        "job_id": job_id,
        "status": j.get("status"),
        "progress": j.get("progress", 0),
        "download_url": j.get("download_url"),
        "script": j.get("script"),
        "error": j.get("error"),
    }


@app.get("/api/video/download/{job_id}", tags=["video"])
async def download_video(job_id: str):
    """Download the finished MP4 file."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = _jobs[job_id]
    if j.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Video not ready yet.")
    path = j.get("output_path", "")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video file missing.")
    return FileResponse(path, media_type="video/mp4", filename="ai_generated_video.mp4")


@app.delete("/api/video/{job_id}", tags=["video"])
async def delete_job(job_id: str):
    """Remove a job and its output file."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = _jobs.pop(job_id)
    path = j.get("output_path", "")
    if path and os.path.exists(path):
        os.remove(path)
    return {"message": "Deleted"}


@app.get("/api/network-info", tags=["info"])
async def network_info():
    """Return local network addresses so the frontend can build a QR code for phone access."""
    ips: list[str] = []
    hostname = "unknown"
    try:
        hostname = socket.gethostname()
        # Primary outbound IP (the interface that reaches the internet)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
    except Exception:
        pass

    try:
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ":" not in ip and ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except Exception:
        pass

    return {"hostname": hostname, "ips": ips, "port": 8000}


# Serve the frontend SPA at /
_frontend = Path(__file__).parent.parent / "frontend"
if _frontend.exists():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
