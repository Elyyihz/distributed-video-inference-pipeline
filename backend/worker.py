import asyncio
import logging
from app.infrastructure.gateway.rabbitmq_broker_impl import RabbitMQBrokerGatewayImpl
from app.infrastructure.gateway.onnx_yolo_inference_impl import OnnxYoloInferenceGatewayImpl
from app.infrastructure.gateway.postgres_job_repository_impl import PostgresJobRepositoryGatewayImpl
from app.core.usecase.process_frame_batch_worker_usecase import ProcessFrameBatchWorkerUseCase
from app.infrastructure.config.settings import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [WORKER] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("video_pipeline.worker_daemon")


async def main():
    """Starts the distributed inference worker consumer."""
    logger.info("Initializing Video Inference Distributed Worker...")

    broker = RabbitMQBrokerGatewayImpl()
    onnx_yolo = OnnxYoloInferenceGatewayImpl()
    repo = PostgresJobRepositoryGatewayImpl()

    worker_usecase = ProcessFrameBatchWorkerUseCase(
        inference_gateway=onnx_yolo,
        repository_gateway=repo,
    )

    logger.info("Worker listening for frame batch messages from RabbitMQ...")
    await broker.consume_batches(worker_usecase.execute)


if __name__ == "__main__":
    asyncio.run(main())
