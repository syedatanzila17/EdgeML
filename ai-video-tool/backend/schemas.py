from pydantic import BaseModel, Field
from typing import Optional, List


class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)
    style: str = Field(default="educational")   # educational | promotional | storytelling
    duration: int = Field(default=60, ge=15, le=300)
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    color_theme: str = Field(default="blue")    # blue | green | purple | dark


class Scene(BaseModel):
    title: str
    narration: str
    visual_description: str
    duration: float
    background_color: str = "#1a1a2e"


class VideoScript(BaseModel):
    title: str
    scenes: List[Scene]
    total_duration: float


class VideoJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    download_url: Optional[str] = None
    progress: int = 0
