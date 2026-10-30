from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle state of an asynchronous batch video processing job."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
