from abc import ABC, abstractmethod
from typing import Optional, List
from app.core.domain.models.video_job import VideoBatchJob, DetectionResult
from app.core.domain.enum.job_status import JobStatus


class JobRepositoryGateway(ABC):
    """Abstract interface defining persistence operations for video batch jobs."""

    @abstractmethod
    async def create_job(self, job: VideoBatchJob) -> VideoBatchJob:
        """Persists a new job entity in PostgreSQL.

        Args:
            job: Initial VideoBatchJob entity.

        Returns:
            Saved VideoBatchJob instance.
        """
        pass

    @abstractmethod
    async def get_job_by_id(self, job_id: str) -> Optional[VideoBatchJob]:
        """Retrieves a job by its unique identifier.

        Args:
            job_id: Unique UUID string.

        Returns:
            Optional VideoBatchJob entity if found.
        """
        pass

    @abstractmethod
    async def update_job_progress(
        self,
        job_id: str,
        processed_frames_delta: int,
        status: JobStatus,
        new_detections: List[DetectionResult]
    ) -> bool:
        """Appends detection outcomes and updates frame progress counters.

        Args:
            job_id: Target job UUID.
            processed_frames_delta: Number of newly inferred frames.
            status: Updated job status.
            new_detections: Detections extracted by worker.

        Returns:
            bool indicating update success.
        """
        pass
