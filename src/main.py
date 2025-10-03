from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.api import health_router, radar_router
from src.core.config import get_settings
from src.core.logging import setup_logging
from src.di import (
    AgentsProvider,
    ConfigProvider,
    DatabaseProvider,
    LLMProvider,
    RedisProvider,
    ServicesProvider,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging(log_level=settings.log_level, is_dev=settings.debug)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    container = make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
        RedisProvider(),
        LLMProvider(),
        ServicesProvider(),
        AgentsProvider(),
    )
    setup_dishka(container=container, app=app)

    app.include_router(health_router)
    app.include_router(radar_router)

    return app


app = create_app()

