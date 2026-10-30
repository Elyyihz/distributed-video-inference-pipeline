from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

from app.core.domain.enum.job_status import JobStatus


@dataclass
class BoundingBox:
    """Coordinates and confidence for a detected object bounding box.

    Attributes:
        x_min: Left horizontal pixel coordinate.
        y_min: Top vertical pixel coordinate.
        x_max: Right horizontal pixel coordinate.
        y_max: Bottom vertical pixel coordinate.
        confidence: Model prediction confidence score [0.0 - 1.0].
        class_name: Inferred object class label (e.g. 'car', 'person').
    """

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float
    class_name: str


@dataclass
class DetectionResult:
    """Aggregated detection outcome for a single processed frame.

    Attributes:
        frame_number: Index of frame in sequence.
        timestamp_sec: Video timeline offset in seconds.
        boxes: Identified bounding boxes.
        inference_latency_ms: Execution duration in milliseconds.
    """

    frame_number: int
    timestamp_sec: float
    boxes: List[BoundingBox] = field(default_factory=list)
    inference_latency_ms: float = 0.0


@dataclass
class VideoFrameBatchMessage:
    """Message payload published into RabbitMQ worker queue.

    Attributes:
        job_id: Parent batch job UUID.
        batch_index: Sequential index of the batch.
        video_uri: Storage URI or file path to video stream.
        start_frame: Beginning frame index.
        end_frame: Ending frame index.
    """

    job_id: str
    batch_index: int
    video_uri: str
    start_frame: int
    end_frame: int


@dataclass
class VideoBatchJob:
    """Aggregate root tracking a distributed video processing task.

    Attributes:
        job_id: Unique job UUID.
        filename: Name of source video file.
        total_frames: Estimated frame count.
        processed_frames: Count of frames successfully inferred.
        status: Current execution status.
        created_at: Submission timestamp.
        updated_at: Last heartbeat or progress timestamp.
        detections: Consolidated detection records across all batches.
    """

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    total_frames: int = 0
    processed_frames: int = 0
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detections: List[DetectionResult] = field(default_factory=list)
