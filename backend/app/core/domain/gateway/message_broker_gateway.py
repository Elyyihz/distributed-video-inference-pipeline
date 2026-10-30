from abc import ABC, abstractmethod
from typing import Callable, Awaitable
from app.core.domain.models.video_job import VideoFrameBatchMessage


class MessageBrokerGateway(ABC):
    """Abstract interface defining message queue dispatch and subscription."""

    @abstractmethod
    async def publish_batch(self, message: VideoFrameBatchMessage) -> bool:
        """Publishes a video frame batch task into the worker queue.

        Args:
            message: VideoFrameBatchMessage metadata.

        Returns:
            bool indicating whether message was successfully acknowledged.
        """
        pass

    @abstractmethod
    async def consume_batches(
        self,
        handler: Callable[[VideoFrameBatchMessage], Awaitable[None]]
    ) -> None:
        """Starts asynchronous consumption of batch tasks from the broker.

        Args:
            handler: Asynchronous callback function invoked per message.
        """
        pass
