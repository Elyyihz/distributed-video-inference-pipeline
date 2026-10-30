from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for distributed video inference pipeline."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "distributed-video-inference-pipeline"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database
    POSTGRES_USER: str = "pipeline_user"
    POSTGRES_PASSWORD: str = "pipeline_secret"
    POSTGRES_DB: str = "video_pipeline"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # RabbitMQ Broker
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_QUEUE_NAME: str = "video_frame_batches"

    # ONNX Model
    YOLO_MODEL_PATH: str = "/models/yolov8n.onnx"
    FRAMES_PER_BATCH: int = 50


settings = Settings()
