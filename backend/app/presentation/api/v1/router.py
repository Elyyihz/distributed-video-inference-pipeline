import asyncio
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.presentation.dtos.video_job_dto import VideoJobCreateRequest, VideoJobResponse
from app.presentation.api.v1.controllers.video_job_controller import VideoJobController
from app.infrastructure.gateway.rabbitmq_broker_impl import RabbitMQBrokerGatewayImpl
from app.infrastructure.gateway.postgres_job_repository_impl import PostgresJobRepositoryGatewayImpl
from app.core.usecase.create_batch_job_usecase import CreateBatchJobUseCase
from app.core.usecase.get_job_status_usecase import GetJobStatusUseCase
from app.core.domain.enum.job_status import JobStatus
from app.infrastructure.config.settings import settings

logger = logging.getLogger("video_pipeline.presentation.api")

router = APIRouter(prefix="/api/v1", tags=["Video Processing Pipeline"])

# Singleton shared storage & broker for API lifecycle
shared_repo = PostgresJobRepositoryGatewayImpl()
shared_broker = RabbitMQBrokerGatewayImpl()


def get_video_controller() -> VideoJobController:
    """Dependency injection factory wiring Clean Architecture layers."""
    create_usecase = CreateBatchJobUseCase(
        repository_gateway=shared_repo,
        broker_gateway=shared_broker,
        frames_per_batch=settings.FRAMES_PER_BATCH,
    )
    status_usecase = GetJobStatusUseCase(repository_gateway=shared_repo)
    return VideoJobController(create_usecase, status_usecase)


@router.post("/jobs", response_model=VideoJobResponse, status_code=202)
async def submit_video_job(
    request: VideoJobCreateRequest,
    controller: VideoJobController = Depends(get_video_controller),
) -> VideoJobResponse:
    """Submits a video for parallel batch inference processing."""
    return await controller.submit_job(request)


@router.get("/jobs/{job_id}", response_model=VideoJobResponse)
async def get_job_status(
    job_id: str,
    controller: VideoJobController = Depends(get_video_controller),
) -> VideoJobResponse:
    """Retrieves current processing progress, worker status, and detections."""
    return await controller.get_job_status(job_id)


@router.websocket("/ws/jobs/{job_id}")
async def job_telemetry_websocket(
    websocket: WebSocket,
    job_id: str,
):
    """Streams real-time frame telemetry, bounding box counts, and completion status over WebSocket."""
    await websocket.accept()
    try:
        while True:
            job = await shared_repo.get_job_by_id(job_id)
            if not job:
                await websocket.send_json({"error": "Job not found", "job_id": job_id})
                break

            progress = round((job.processed_frames / max(1, job.total_frames)) * 100.0, 1)
            payload = {
                "job_id": job.job_id,
                "status": job.status.value,
                "total_frames": job.total_frames,
                "processed_frames": job.processed_frames,
                "progress_percentage": progress,
                "detections_count": len(job.detections),
                "fps": 30.0,
            }
            await websocket.send_json(payload)

            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                break

            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for job %s", job_id)


@router.get("/health")
def health_check():
    """Readiness probe."""
    return {
        "status": "UP",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "rabbitmq": "connected",
        "postgres": "connected",
    }
