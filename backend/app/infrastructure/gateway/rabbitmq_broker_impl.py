import logging
import json
import asyncio
from typing import Callable, Awaitable, List, Dict, Any, Optional
from app.core.domain.gateway.message_broker_gateway import MessageBrokerGateway
from app.core.domain.models.video_job import VideoFrameBatchMessage
from app.infrastructure.config.settings import settings

logger = logging.getLogger("video_pipeline.infra.rabbitmq")


class RabbitMQBrokerGatewayImpl(MessageBrokerGateway):
    """RabbitMQ message broker adapter with DLQ (Dead Letter Queue) and exponential backoff."""

    def __init__(
        self,
        host: str = settings.RABBITMQ_HOST,
        port: int = settings.RABBITMQ_PORT,
        queue_name: str = settings.RABBITMQ_QUEUE_NAME,
    ):
        """Initializes broker connection coordinates and DLQ buffers.

        Args:
            host: RabbitMQ hostname.
            port: AMQP port.
            queue_name: Default batch queue name.
        """
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.dlq_queue_name = f"{queue_name}.dlq"
        self._mock_queue: asyncio.Queue = asyncio.Queue()
        self._dlq_messages: List[Dict[str, Any]] = []

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

    async def route_to_dlq(self, message: VideoFrameBatchMessage, reason: str) -> None:
        """Enqueues failed batch into Dead Letter Queue for post-mortem auditing.

        Args:
            message: Failed batch message.
            reason: Root cause error message.
        """
        logger.error(
            "Routing batch %d (job_id=%s) to DLQ '%s': %s",
            message.batch_index,
            message.job_id,
            self.dlq_queue_name,
            reason,
        )
        self._dlq_messages.append(
            {
                "message": message,
                "reason": reason,
                "dlq_queue": self.dlq_queue_name,
            }
        )

    def get_dlq_messages(self) -> List[Dict[str, Any]]:
        """Returns captured Dead Letter Queue payloads."""
        return list(self._dlq_messages)

    async def process_message_with_retry(
        self,
        msg: VideoFrameBatchMessage,
        handler: Callable[[VideoFrameBatchMessage], Awaitable[None]],
    ) -> bool:
        """Executes handler with exponential backoff retries and DLQ routing on exhaustion.

        Args:
            msg: Frame batch message.
            handler: Worker processing function.

        Returns:
            True if processed successfully, False if dead lettered.
        """
        while msg.retry_count <= msg.max_retries:
            try:
                await handler(msg)
                return True
            except Exception as exc:
                msg.retry_count += 1
                if msg.retry_count <= msg.max_retries:
                    backoff_delay = min(1.0, (2 ** msg.retry_count) * 0.05)
                    logger.warning(
                        "Attempt %d/%d failed for batch %d (%s); retrying in %.2fs",
                        msg.retry_count,
                        msg.max_retries,
                        msg.batch_index,
                        exc,
                        backoff_delay,
                    )
                    await asyncio.sleep(backoff_delay)
                else:
                    logger.error(
                        "Batch %d exceeded max retries (%d); dead lettering message",
                        msg.batch_index,
                        msg.max_retries,
                    )
                    await self.route_to_dlq(msg, reason=str(exc))
                    return False
        return False

    async def consume_batches(
        self,
        handler: Callable[[VideoFrameBatchMessage], Awaitable[None]]
    ) -> None:
        """Continuously pulls and dispatches batch messages with retry safety.

        Args:
            handler: Asynchronous worker function.
        """
        logger.info("Starting RabbitMQ consumer worker loop on queue '%s'", self.queue_name)
        while True:
            msg = await self._mock_queue.get()
            try:
                await self.process_message_with_retry(msg, handler)
            finally:
                self._mock_queue.task_done()
