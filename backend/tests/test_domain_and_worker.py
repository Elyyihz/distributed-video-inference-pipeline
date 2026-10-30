import pytest
from app.core.domain.models.video_job import VideoBatchJob, VideoFrameBatchMessage, BoundingBox
from app.core.domain.enum.job_status import JobStatus
from app.infrastructure.gateway.rabbitmq_broker_impl import RabbitMQBrokerGatewayImpl
from app.infrastructure.gateway.onnx_yolo_inference_impl import OnnxYoloInferenceGatewayImpl
from app.infrastructure.gateway.postgres_job_repository_impl import PostgresJobRepositoryGatewayImpl
from app.core.usecase.create_batch_job_usecase import CreateBatchJobUseCase
from app.core.usecase.process_frame_batch_worker_usecase import ProcessFrameBatchWorkerUseCase
from app.core.usecase.get_job_status_usecase import GetJobStatusUseCase


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
