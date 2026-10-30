from abc import ABC, abstractmethod
from typing import List
from app.core.domain.models.video_job import DetectionResult


class InferenceGateway(ABC):
    """Abstract interface defining deep learning model inference."""

    @abstractmethod
    async def infer_frame_batch(
        self,
        video_uri: str,
        start_frame: int,
        end_frame: int
    ) -> List[DetectionResult]:
        """Executes YOLOv8 object detection on a slice of video frames via ONNX Runtime.

        Args:
            video_uri: File path or URI to the video media.
            start_frame: First frame index.
            end_frame: Last frame index in slice.

        Returns:
            List of DetectionResult instances for each processed frame.
        """
        pass
