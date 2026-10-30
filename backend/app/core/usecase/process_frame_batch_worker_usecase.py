import logging
from app.core.domain.models.video_job import VideoFrameBatchMessage
from app.core.domain.enum.job_status import JobStatus
from app.core.domain.gateway.inference_gateway import InferenceGateway
from app.core.domain.gateway.job_repository_gateway import JobRepositoryGateway

logger = logging.getLogger("video_pipeline.usecase.worker")


class ProcessFrameBatchWorkerUseCase:
    """Worker processing routine executed when a frame batch is popped from RabbitMQ."""

    def __init__(
        self,
        inference_gateway: InferenceGateway,
        repository_gateway: JobRepositoryGateway,
    ):
        """Initializes worker with inference engine and persistence port.

        Args:
            inference_gateway: ONNX YOLO inference engine adapter.
            repository_gateway: Persistence gateway port.
        """
        self.inference_gateway = inference_gateway
        self.repository_gateway = repository_gateway

    async def execute(self, message: VideoFrameBatchMessage) -> None:
        """Processes frame batch inference and writes detections to DB.

        Args:
            message: VideoFrameBatchMessage metadata from queue.
        """
        logger.info(
            "Step started: Processing batch_index=%d (frames %d..%d) for job_id=%s",
            message.batch_index,
            message.start_frame,
            message.end_frame,
            message.job_id,
        )

        detections = await self.inference_gateway.infer_frame_batch(
            video_uri=message.video_uri,
            start_frame=message.start_frame,
            end_frame=message.end_frame,
        )

        frames_in_batch = message.end_frame - message.start_frame
        logger.info(
            "Decision taken: Inference yielded %d frame results for batch_index=%d",
            len(detections),
            message.batch_index,
        )

        # Retrieve current job to decide terminal status
        current_job = await self.repository_gateway.get_job_by_id(message.job_id)
        if not current_job:
            logger.error("Decision taken: Job %s not found in persistence; skipping update", message.job_id)
            return

        new_total_processed = current_job.processed_frames + frames_in_batch
        new_status = JobStatus.COMPLETED if new_total_processed >= current_job.total_frames else JobStatus.PROCESSING

        if new_status == JobStatus.COMPLETED:
            logger.info("Decision taken: All %d frames processed; transitioning job_id=%s to COMPLETED", current_job.total_frames, message.job_id)
        else:
            logger.info("Decision taken: Job %s progress at %d/%d frames", message.job_id, new_total_processed, current_job.total_frames)

        await self.repository_gateway.update_job_progress(
            job_id=message.job_id,
            processed_frames_delta=frames_in_batch,
            status=new_status,
            new_detections=detections,
        )

        logger.info("Step concluded: Batch %d successfully processed and saved for job_id=%s", message.batch_index, message.job_id)
