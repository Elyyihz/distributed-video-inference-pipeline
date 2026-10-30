import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.presentation.api.v1.router import router as api_router
from app.infrastructure.config.settings import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [API] [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("video_pipeline.main")

app = FastAPI(
    title="Pipeline Distribuído para Processamento de Vídeo em Lote",
    description="Orquestrador assíncrono com FastAPI, RabbitMQ, YOLO ONNX Runtime e PostgreSQL.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
