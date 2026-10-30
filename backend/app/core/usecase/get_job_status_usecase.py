import logging
from typing import Optional
from app.core.domain.models.video_job import VideoBatchJob
from app.core.domain.gateway.job_repository_gateway import JobRepositoryGateway

logger = logging.getLogger("video_pipeline.usecase.get_status")


class GetJobStatusUseCase:
    """Retrieves processing progress and object detections for a given batch job."""

    def __init__(self, repository_gateway: JobRepositoryGateway):
        """Initializes with persistence port.

        Args:
            repository_gateway: Persistence gateway port.
        """
        self.repository_gateway = repository_gateway

    async def execute(self, job_id: str) -> Optional[VideoBatchJob]:
        """Queries job details.

        Args:
            job_id: Unique job UUID.

        Returns:
            Optional VideoBatchJob entity if found.
        """
        logger.info("Step started: Querying job status for job_id=%s", job_id)
        job = await self.repository_gateway.get_job_by_id(job_id)
        if not job:
            logger.warning("Decision taken: Job %s not found in repository", job_id)
            return None

        logger.info("Step concluded: Found job %s with status=%s and %d frames processed", job_id, job.status.value, job.processed_frames)
        return job
