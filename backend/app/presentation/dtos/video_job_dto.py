from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BoundingBoxDto(BaseModel):
    """Data transfer representation of an object bounding box."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    class_name: str


class DetectionDto(BaseModel):
    """Detection output for a single frame."""

    frame_number: int
    timestamp_sec: float
    boxes: List[BoundingBoxDto]
    inference_latency_ms: float


class VideoJobCreateRequest(BaseModel):
    """Job creation submission payload."""

    filename: str = Field(..., example="traffic_cam_01.mp4")
    estimated_frames: int = Field(..., ge=1, example=300)
    storage_uri: str = Field(..., example="/storage/videos/traffic_cam_01.mp4")


class VideoJobResponse(BaseModel):
    """Job status and telemetry summary."""

    job_id: str
    filename: str
    total_frames: int
    processed_frames: int
    status: str
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    detections: List[DetectionDto]
    user_message: str = Field(..., description="Mensagem contextual direcionada ao usuário final.")
