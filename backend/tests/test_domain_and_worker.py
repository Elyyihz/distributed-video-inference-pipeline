import pytest
import asyncio
from starlette.testclient import TestClient
from fastapi import FastAPI
from app.core.domain.models.video_job import VideoBatchJob, VideoFrameBatchMessage, BoundingBox
from app.core.domain.enum.job_status import JobStatus
from app.infrastructure.gateway.rabbitmq_broker_impl import RabbitMQBrokerGatewayImpl
from app.infrastructure.gateway.onnx_yolo_inference_impl import OnnxYoloInferenceGatewayImpl
from app.infrastructure.gateway.postgres_job_repository_impl import PostgresJobRepositoryGatewayImpl
from app.core.usecase.create_batch_job_usecase import CreateBatchJobUseCase
from app.core.usecase.process_frame_batch_worker_usecase import ProcessFrameBatchWorkerUseCase
from app.core.usecase.get_job_status_usecase import GetJobStatusUseCase
from app.presentation.api.v1.router import router, shared_repo


def test_domain_model_creation():
    """Validates default initialization of VideoBatchJob."""
    job = VideoBatchJob(filename="highway_feed.mp4", total_frames=120)
    assert job.job_id is not None
    assert job.status == JobStatus.PENDING
    assert job.total_frames == 120
    assert job.processed_frames == 0


@pytest.mark.asyncio
async def test_distributed_pipeline_lifecycle():
    """Tests job creation, partitioning into batches, and worker processing."""
    repo = PostgresJobRepositoryGatewayImpl()
    broker = RabbitMQBrokerGatewayImpl()
    onnx = OnnxYoloInferenceGatewayImpl()

    create_uc = CreateBatchJobUseCase(repository_gateway=repo, broker_gateway=broker, frames_per_batch=50)
    worker_uc = ProcessFrameBatchWorkerUseCase(inference_gateway=onnx, repository_gateway=repo)
    status_uc = GetJobStatusUseCase(repository_gateway=repo)

    # 1. Create job with 100 frames (should create 2 batches)
    job = await create_uc.execute("surveillance.mp4", 100, "/data/surveillance.mp4")
    assert job.status == JobStatus.QUEUED

    # 2. Simulate worker consuming Batch 0 (0..50)
    batch_0 = VideoFrameBatchMessage(
        job_id=job.job_id,
        batch_index=0,
        video_uri="/data/surveillance.mp4",
        start_frame=0,
        end_frame=50,
    )
    await worker_uc.execute(batch_0)

    # Verify intermediate progress
    mid_status = await status_uc.execute(job.job_id)
    assert mid_status is not None
    assert mid_status.processed_frames == 50
    assert mid_status.status == JobStatus.PROCESSING

    # 3. Simulate worker consuming Batch 1 (50..100)
    batch_1 = VideoFrameBatchMessage(
        job_id=job.job_id,
        batch_index=1,
        video_uri="/data/surveillance.mp4",
        start_frame=50,
        end_frame=100,
    )
    await worker_uc.execute(batch_1)

    # Verify terminal completed status
    final_status = await status_uc.execute(job.job_id)
    assert final_status is not None
    assert final_status.processed_frames == 100
    assert final_status.status == JobStatus.COMPLETED
    assert len(final_status.detections) == 100


@pytest.mark.asyncio
async def test_rabbitmq_exponential_backoff_and_dlq():
    """Validates message retries with backoff and eventual routing to Dead Letter Queue."""
    broker = RabbitMQBrokerGatewayImpl()

    failing_msg = VideoFrameBatchMessage(
        job_id="corrupted-job-123",
        batch_index=0,
        video_uri="/data/corrupted.mp4",
        start_frame=0,
        end_frame=10,
        retry_count=0,
        max_retries=2,
    )

    call_count = 0

    async def faulty_worker_handler(msg: VideoFrameBatchMessage):
        nonlocal call_count
        call_count += 1
        raise ValueError("Corrupted frame decode error")

    success = await broker.process_message_with_retry(failing_msg, faulty_worker_handler)

    assert success is False
    assert call_count == 3  # Initial try + 2 retries
    assert failing_msg.retry_count == 3

    dlq = broker.get_dlq_messages()
    assert len(dlq) == 1
    assert dlq[0]["message"].job_id == "corrupted-job-123"
    assert "Corrupted frame decode error" in dlq[0]["reason"]


def test_job_websocket_telemetry():
    """Validates WebSocket streaming real-time job progress."""
    app = FastAPI()
    app.include_router(router)

    # Pre-populate shared repository
    job = VideoBatchJob(
        job_id="ws-test-job-42",
        filename="drone_stream.mp4",
        total_frames=100,
        processed_frames=100,
        status=JobStatus.COMPLETED,
    )
    asyncio.run(shared_repo.create_job(job))

    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/jobs/ws-test-job-42") as websocket:
        data = websocket.receive_json()
        assert data["job_id"] == "ws-test-job-42"
        assert data["status"] == "COMPLETED"
        assert data["progress_percentage"] == 100.0
        assert data["fps"] == 30.0
