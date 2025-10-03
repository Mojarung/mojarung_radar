from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.endpoints import health, news, sources
from app.db.redis import get_redis, close_redis

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting RADAR service")
    await get_redis()
    yield
    logger.info("Shutting down RADAR service")
    await close_redis()


app = FastAPI(
    title=settings.project_name,
    lifespan=lifespan
)

app.include_router(health.router, prefix=settings.api_v1_prefix, tags=["health"])
app.include_router(news.router, prefix=settings.api_v1_prefix, tags=["news"])
app.include_router(sources.router, prefix=settings.api_v1_prefix, tags=["sources"])


@app.get("/")
async def root():
    return {
        "service": "RADAR",
        "description": "Сервис поиска и оценки горячих новостей",
        "version": "0.1.0"
    }

