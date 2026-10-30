import logging
from fastapi import HTTPException
from app.core.usecase.create_batch_job_usecase import CreateBatchJobUseCase
from app.core.usecase.get_job_status_usecase import GetJobStatusUseCase
from app.presentation.dtos.video_job_dto import (
    VideoJobCreateRequest,
    VideoJobResponse,
    DetectionDto,
    BoundingBoxDto,
)
from app.core.domain.enum.job_status import JobStatus

logger = logging.getLogger("video_pipeline.presentation.controller")


class VideoJobController:
    """Handles HTTP requests and response mapping for batch video inference."""

    def __init__(
        self,
        create_job_use_case: CreateBatchJobUseCase,
        get_status_use_case: GetJobStatusUseCase,
    ):
        """Initializes controller with use case dependencies.

        Args:
            create_job_use_case: Job creation use case.
            get_status_use_case: Job status query use case.
        """
        self.create_job_use_case = create_job_use_case
        self.get_status_use_case = get_status_use_case

    async def submit_job(self, req: VideoJobCreateRequest) -> VideoJobResponse:
        """Receives and dispatches video job to distributed queue.

        Args:
            req: VideoJobCreateRequest payload.

        Returns:
            VideoJobResponse with job identifier and queued status.
        """
        logger.info("Step started: Submitting batch job for video=%s", req.filename)

        job = await self.create_job_use_case.execute(
            filename=req.filename,
            estimated_frames=req.estimated_frames,
            storage_uri=req.storage_uri,
        )

        user_msg = f"Job de processamento para '{req.filename}' enfileirado com sucesso. {req.estimated_frames} frames particionados."
        logger.info("Step concluded: Successfully enqueued job_id=%s", job.job_id)

        return VideoJobResponse(
            job_id=job.job_id,
            filename=job.filename,
            total_frames=job.total_frames,
            processed_frames=job.processed_frames,
            status=job.status.value,
            progress_percentage=0.0,
            created_at=job.created_at,
            updated_at=job.updated_at,
            detections=[],
            user_message=user_msg,
        )

    async def get_job_status(self, job_id: str) -> VideoJobResponse:
        """Retrieves real-time processing telemetry for a video job.

        Args:
            job_id: Unique UUID string.

        Returns:
            VideoJobResponse with detection metrics and progress percentage.

        Raises:
            HTTPException: If job_id does not exist.
        """
        job = await self.get_status_use_case.execute(job_id)
        if not job:
            logger.warning("Decision taken: Rejecting request due to non-existent job_id=%s", job_id)
            raise HTTPException(status_code=404, detail=f"Job de vídeo '{job_id}' não encontrado.")

        progress = 0.0
        if job.total_frames > 0:
            progress = round((job.processed_frames / job.total_frames) * 100.0, 1)

        # Presentation user message in pt-BR
        if job.status == JobStatus.COMPLETED:
            user_msg = f"Processamento concluído com sucesso. Todos os {job.total_frames} frames foram analisados."
        elif job.status == JobStatus.PROCESSING:
            user_msg = f"Processamento em andamento pelos workers distribuídos: {job.processed_frames}/{job.total_frames} frames ({progress}%)."
        else:
            user_msg = "Job aguardando alocação de worker na fila do RabbitMQ."

        dto_detections = [
            DetectionDto(
                frame_number=d.frame_number,
                timestamp_sec=d.timestamp_sec,
                inference_latency_ms=d.inference_latency_ms,
                boxes=[
                    BoundingBoxDto(
                        x_min=b.x_min,
                        y_min=b.y_min,
                        x_max=b.x_max,
                        y_max=b.y_max,
                        confidence=b.confidence,
                        class_name=b.class_name,
                    )
                    for b in d.boxes
                ],
            )
            for d in job.detections
        ]

        return VideoJobResponse(
            job_id=job.job_id,
            filename=job.filename,
            total_frames=job.total_frames,
            processed_frames=job.processed_frames,
            status=job.status.value,
            progress_percentage=progress,
            created_at=job.created_at,
            updated_at=job.updated_at,
            detections=dto_detections,
            user_message=user_msg,
        )
