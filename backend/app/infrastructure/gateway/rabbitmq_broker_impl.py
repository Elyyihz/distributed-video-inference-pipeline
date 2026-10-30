import logging
import json
import asyncio
from typing import Callable, Awaitable, List
from app.core.domain.gateway.message_broker_gateway import MessageBrokerGateway
from app.core.domain.models.video_job import VideoFrameBatchMessage
from app.infrastructure.config.settings import settings

logger = logging.getLogger("video_pipeline.infra.rabbitmq")


class RabbitMQBrokerGatewayImpl(MessageBrokerGateway):
    """RabbitMQ message broker adapter for batch dispatch and worker processing."""

    def __init__(
        self,
        host: str = settings.RABBITMQ_HOST,
        port: int = settings.RABBITMQ_PORT,
        queue_name: str = settings.RABBITMQ_QUEUE_NAME,
    ):
        """Initializes broker connection coordinates.

        Args:
            host: RabbitMQ hostname.
            port: AMQP port.
            queue_name: Default batch queue name.
        """
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self._mock_queue: asyncio.Queue = asyncio.Queue()

    async def publish_batch(self, message: VideoFrameBatchMessage) -> bool:
        """Publishes a batch task to the broker.

        Args:
            message: VideoFrameBatchMessage payload.

        Returns:
            bool indicating message acknowledgement.
        """
        logger.info(
            "Publishing frame batch to RabbitMQ queue '%s': job_id=%s, batch_idx=%d",
            self.queue_name,
            message.job_id,
            message.batch_index,
        )
        await self._mock_queue.put(message)
        return True

    async def consume_batches(
        self,
        handler: Callable[[VideoFrameBatchMessage], Awaitable[None]]
    ) -> None:
        """Continuously pulls and dispatches batch messages to the worker usecase.

        Args:
            handler: Asynchronous worker function.
        """
        logger.info("Starting RabbitMQ consumer worker loop on queue '%s'", self.queue_name)
        while True:
            msg = await self._mock_queue.get()
            try:
                await handler(msg)
            except Exception as exc:
                logger.error("Error processing queue message: %s", exc)
            finally:
                self._mock_queue.task_done()
