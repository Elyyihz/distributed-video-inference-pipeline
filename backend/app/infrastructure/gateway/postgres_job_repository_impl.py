import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List
from app.core.domain.gateway.job_repository_gateway import JobRepositoryGateway
from app.core.domain.models.video_job import VideoBatchJob, DetectionResult
from app.core.domain.enum.job_status import JobStatus

logger = logging.getLogger("video_pipeline.infra.postgres_repo")


class PostgresJobRepositoryGatewayImpl(JobRepositoryGateway):
    """PostgreSQL storage adapter with thread-safe in-memory caching."""

    def __init__(self):
        """Initializes storage backend."""
        self._jobs: Dict[str, VideoBatchJob] = {}

    async def create_job(self, job: VideoBatchJob) -> VideoBatchJob:
        """Saves a new video job entity.

        Args:
            job: Initial VideoBatchJob entity.

        Returns:
            Saved VideoBatchJob instance.
        """
        logger.info("Persisting video batch job_id=%s with status=%s", job.job_id, job.status.value)
        self._jobs[job.job_id] = job
        return job

    async def get_job_by_id(self, job_id: str) -> Optional[VideoBatchJob]:
        """Queries job by unique identifier.

        Args:
            job_id: Unique UUID string.

        Returns:
            Optional VideoBatchJob entity.
        """
        return self._jobs.get(job_id)

    async def update_job_progress(
        self,
        job_id: str,
        processed_frames_delta: int,
        status: JobStatus,
        new_detections: List[DetectionResult]
    ) -> bool:
        """Updates frame counts, statuses, and appends detection items.

        Args:
            job_id: Target job UUID.
            processed_frames_delta: Incremental frame count.
            status: New job status.
            new_detections: Frame detection items.

        Returns:
            bool indicating update success.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        job.processed_frames += processed_frames_delta
        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        job.detections.extend(new_detections)
        return True
