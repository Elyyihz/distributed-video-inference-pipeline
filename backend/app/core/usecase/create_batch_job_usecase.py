import logging
import math
from app.core.domain.models.video_job import VideoBatchJob, VideoFrameBatchMessage
from app.core.domain.enum.job_status import JobStatus
from app.core.domain.gateway.job_repository_gateway import JobRepositoryGateway
from app.core.domain.gateway.message_broker_gateway import MessageBrokerGateway

logger = logging.getLogger("video_pipeline.usecase.create_job")


class CreateBatchJobUseCase:
    """Orchestrates job registration, frame partitioning, and queue dispatch."""

    def __init__(
        self,
        repository_gateway: JobRepositoryGateway,
        broker_gateway: MessageBrokerGateway,
        frames_per_batch: int = 50,
    ):
        """Initializes with repository and message broker ports.

        Args:
            repository_gateway: Persistence gateway port.
            broker_gateway: Message broker gateway port.
            frames_per_batch: Number of video frames allocated per queue task.
        """
        self.repository_gateway = repository_gateway
        self.broker_gateway = broker_gateway
        self.frames_per_batch = frames_per_batch

    async def execute(self, filename: str, estimated_frames: int, storage_uri: str) -> VideoBatchJob:
        """Submits video, decomposes into partitions, and dispatches to RabbitMQ.

        Args:
            filename: Source video file name.
            estimated_frames: Total estimated frame count.
            storage_uri: File location.

        Returns:
            Saved VideoBatchJob entity in QUEUED status.
        """
        logger.info("Step started: Registering video batch job for filename=%s, frames=%d", filename, estimated_frames)

        job = VideoBatchJob(
            filename=filename,
            total_frames=estimated_frames,
            processed_frames=0,
            status=JobStatus.QUEUED,
        )
        saved_job = await self.repository_gateway.create_job(job)

        # Calculate partition count
        batch_count = math.ceil(estimated_frames / self.frames_per_batch)
        logger.info("Decision taken: Partitioning %d frames into %d batches (chunk_size=%d)", estimated_frames, batch_count, self.frames_per_batch)

        for b_idx in range(batch_count):
            start = b_idx * self.frames_per_batch
            end = min(estimated_frames, start + self.frames_per_batch)
            msg = VideoFrameBatchMessage(
                job_id=saved_job.job_id,
                batch_index=b_idx,
                video_uri=storage_uri,
                start_frame=start,
                end_frame=end,
            )
            await self.broker_gateway.publish_batch(msg)

        logger.info("Step concluded: Dispatched all %d batches to RabbitMQ for job_id=%s", batch_count, saved_job.job_id)
        return saved_job
